import os
import sys
import time
import traceback
import logging
from dotenv import load_dotenv

from src.data import fetch_all_data
from src.strategies import run_all_strategies
from src.signal_builder import build_signal, check_trade_exit
from src.confidence import calculate_confidence
from src.momentum import calculate_momentum, momentum_category
from src.cache import SignalCache, TradeCache, StrategyHistory, perform_cache_maintenance
from src.telegram import TelegramBot
from src.validation import is_valid_signal

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Support environment-based timeframe filtering
TIMEFRAME_FILTER = os.getenv("TIMEFRAME")  # e.g., "3m", "5m", "15m"
MAX_SIGNALS_OVERRIDE = int(os.getenv("MAX_SIGNALS", "5"))

# Focus on specified pairs for scalping
SYMBOLS = ["BTCUSDT", "ETHUSDT", "DOGEUSDT"]
TIMEFRAMES = ["3m", "5m", "15m"]

# Filter timeframes if specified
if TIMEFRAME_FILTER:
    TIMEFRAMES = [tf for tf in TIMEFRAMES if tf == TIMEFRAME_FILTER]
    print(f"🎯 Filtering to timeframe: {TIMEFRAME_FILTER}")

CONFIDENCE_THRESHOLD = 0.65  # Lower for scalping opportunities
MAX_SIGNALS_PER_RUN = MAX_SIGNALS_OVERRIDE

async def main():
    # Perform cache maintenance at startup
    perform_cache_maintenance()
    
    # Ensure cache directory exists
    os.makedirs(".cache", exist_ok=True)
    
    print(f"🚀 Starting bot for timeframes: {TIMEFRAMES}")
    print(f"📊 Max signals per run: {MAX_SIGNALS_PER_RUN}")
    
    tg = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    # Use timeframe-specific cache files to avoid conflicts
    cache_suffix = f"_{TIMEFRAME_FILTER}" if TIMEFRAME_FILTER else ""
    signal_cache = SignalCache(f".cache/signal_cache{cache_suffix}.json")
    trade_cache = TradeCache(f".cache/active_trades{cache_suffix}.json")
    strategy_history = StrategyHistory(f".cache/strategy_history{cache_suffix}.json")

    try:
        # Validate cache sizes before processing
        print(f"📊 Cache status: Signals={len(signal_cache.cache)}, Trades={len(trade_cache.trades)}")
        
        data = fetch_all_data(SYMBOLS, TIMEFRAMES)
        signals = []
        for symbol in SYMBOLS:
            for tf in TIMEFRAMES:
                df = data.get((symbol, tf))
                if df is None or len(df) < 100:
                    continue
                strat_results = run_all_strategies(df)
                for strat in strat_results:
                    # Historical learning: get ATR multipliers for this strategy
                    hist = strategy_history.get(strat['strategy'])
                    winrate = strategy_history.winrate(strat['strategy'])
                    atr_mult = strat['atr_mult']
                    # Adapt multipliers if winrate is high/low
                    if winrate > 0.6:
                        sl_mult = atr_mult['sl'] + 0.2
                        tp_mult = [x + 0.2 for x in atr_mult['tp']]
                    elif winrate < 0.4:
                        sl_mult = max(atr_mult['sl'] - 0.2, 1.0)
                        tp_mult = [max(x - 0.2, 0.8) for x in atr_mult['tp']]
                    else:
                        sl_mult = atr_mult['sl']
                        tp_mult = atr_mult['tp']

                    signal = build_signal(symbol, tf, df, strat, sl_mult, tp_mult, strategy_history.next_slno())
                    if not signal:
                        continue
                    signal['confidence'] = calculate_confidence(signal, df, winrate)
                    signal['momentum'] = calculate_momentum(df)
                    signal['momentum_cat'] = momentum_category(signal['momentum'])
                    if is_valid_signal(signal, CONFIDENCE_THRESHOLD):
                        signals.append(signal)

        signals = [s for s in signals if not signal_cache.is_duplicate(s)]
        signals = sorted(signals, key=lambda x: x['confidence'], reverse=True)[:MAX_SIGNALS_PER_RUN]

        print(f"📤 Sending {len(signals)} signals...")
        for signal in signals:
            await tg.send_signal(signal)
            signal_cache.add(signal)
            trade_cache.add(signal)  # Add to active trades
            
        open_trades = trade_cache.get_all()
        print(f"📊 Monitoring {len(open_trades)} active trades...")
        
        for trade in open_trades:
            df = data.get((trade['symbol'], trade['timeframe']))
            if df is None:
                continue
            exit_info = check_trade_exit(trade, df)
            if exit_info['closed']:
                await tg.send_trade_close(trade, exit_info)
                trade_cache.close(trade['slno'])
                # Update strategy history
                profit = exit_info['exit_price'] - trade['entry'] if trade['side'] == "LONG" else trade['entry'] - exit_info['exit_price']
                strategy_history.add(trade['strategy'], {
                    "slno": trade['slno'],
                    "entry": trade['entry'],
                    "sl": trade['sl'],
                    "tp": trade['tp'],
                    "outcome": exit_info['reason'],
                    "profit": profit,
                    "profit_pct": (profit / trade['entry']) * 100,
                    "timestamp": int(time.time())
                })
                print(f"✅ Trade {trade['slno']} closed: {exit_info['reason']}")

        # Final cache status
        print(f"📈 Final cache status: Signals={len(signal_cache.cache)}, Trades={len(trade_cache.trades)}")

    except Exception as e:
        err = traceback.format_exc()
        await tg.send_error(f"Bot error ({TIMEFRAME_FILTER or 'ALL'}):\n{err}")
        logging.error(f"Bot error:\n{err}")
        print(f"❌ Error: {err}")