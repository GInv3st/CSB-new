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
from src.cache import SignalCache, TradeCache, StrategyHistory
from src.telegram import TelegramBot
from src.validation import is_valid_signal

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# Focus on specified pairs for scalping
SYMBOLS = ["BTCUSDT", "ETHUSDT", "DOGEUSDT"]
TIMEFRAMES = ["3m", "5m", "15m"]
CONFIDENCE_THRESHOLD = 0.65  # Lower for scalping opportunities
MAX_SIGNALS_PER_RUN = 5  # More signals for scalping

async def main():
    # Ensure cache directory exists
    os.makedirs(".cache", exist_ok=True)
    
    tg = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    signal_cache = SignalCache(".cache/signal_cache.json")
    trade_cache = TradeCache(".cache/active_trades.json")
    strategy_history = StrategyHistory(".cache/strategy_history.json")

    try:
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

        for signal in signals:
            await tg.send_signal(signal)
            signal_cache.add(signal)
            trade_cache.add(signal)  # Add to active trades
        open_trades = trade_cache.get_all()
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

    except Exception as e:
        err = traceback.format_exc()
        await tg.send_error(f"Bot error:\n{err}")
        logging.error(f"Bot error:\n{err}")