import os
import sys
import time
import traceback
import logging
import signal
import atexit
import gc
from datetime import datetime, timezone
import pandas as pd
from dotenv import load_dotenv

# Configure logging properly
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s UTC - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Set timezone to UTC globally
os.environ['TZ'] = 'UTC'
time.tzset() if hasattr(time, 'tzset') else None

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

CONFIDENCE_THRESHOLD = 0.55  # Back to proven working threshold
MAX_SIGNALS_PER_RUN = MAX_SIGNALS_OVERRIDE

# Global shutdown flag
shutdown_requested = False

def signal_handler(signum, frame):
    global shutdown_requested
    shutdown_requested = True
    logger.info(f"Shutdown signal {signum} received. Gracefully shutting down...")

def cleanup_on_exit():
    """Cleanup function called on exit"""
    logger.info("Performing cleanup before exit...")
    gc.collect()  # Force garbage collection
    
# Register signal handlers for graceful shutdown
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
atexit.register(cleanup_on_exit)

async def main():
    # Perform cache maintenance at startup
    perform_cache_maintenance()
    
    # Ensure cache directory exists
    os.makedirs(".cache", exist_ok=True)
    
    print(f"🚀 Starting bot for timeframes: {TIMEFRAMES}")
    print(f"📊 Max signals per run: {MAX_SIGNALS_PER_RUN}")
    
    tg = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    # Test Telegram connection first
    logger.info("Testing Telegram connection...")
    try:
        await tg.test_connection()
        logger.info("✅ Telegram connection successful")
    except Exception as e:
        logger.error(f"❌ Telegram connection failed: {e}")
        await tg.send_error(f"Bot startup failed - Telegram connection error: {e}")
        return
    
    # Use timeframe-specific cache files to avoid conflicts
    cache_suffix = f"_{TIMEFRAME_FILTER}" if TIMEFRAME_FILTER else ""
    signal_cache = SignalCache(f".cache/signal_cache{cache_suffix}.json")
    trade_cache = TradeCache(f".cache/active_trades{cache_suffix}.json")
    strategy_history = StrategyHistory(f".cache/strategy_history{cache_suffix}.json")

    try:
        # Validate cache sizes before processing
        print(f"📊 Cache status: Signals={len(signal_cache.cache)}, Trades={len(trade_cache.trades)}")
        
        print(f"📡 Fetching market data for {SYMBOLS} on {TIMEFRAMES}")
        data = fetch_all_data(SYMBOLS, TIMEFRAMES)
        
        if not data:
            error_msg = f"🚨 CRITICAL: No market data fetched for any pairs!\nSymbols: {SYMBOLS}\nTimeframes: {TIMEFRAMES}\nThis indicates API failures or geo-blocking."
            print(error_msg)
            await tg.send_error(error_msg)
            return
            
        # Check how many pairs actually got data
        successful_pairs = len([k for k, v in data.items() if v is not None])
        total_pairs = len(SYMBOLS) * len(TIMEFRAMES)
        
        if successful_pairs == 0:
            error_msg = f"🚨 CRITICAL: 0/{total_pairs} pairs got data - All APIs failed!"
            print(error_msg)
            await tg.send_error(error_msg)
            return
        elif successful_pairs < total_pairs:
            warning_msg = f"⚠️ Warning: Only {successful_pairs}/{total_pairs} pairs got data"
            print(warning_msg)
            await tg._send(warning_msg)
        else:
            print(f"✅ Successfully fetched data for all {successful_pairs} pairs")
            
        signals = []
        for symbol in SYMBOLS:
            if shutdown_requested:
                logger.info("Shutdown requested, stopping signal generation")
                break
            for tf in TIMEFRAMES:
                if shutdown_requested:
                    logger.info("Shutdown requested, stopping timeframe processing")
                    break
                df = data.get((symbol, tf))
                if df is None or len(df) < 100:
                    continue
                    
                # CRITICAL FIX: Determine market direction first
                price_change_5 = ((df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5]) * 100
                price_change_10 = ((df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10]) * 100
                
                # Determine dominant market direction
                if price_change_5 > 0.05 and price_change_10 > 0.1:
                    market_direction = "BULLISH"
                elif price_change_5 < -0.05 and price_change_10 < -0.1:
                    market_direction = "BEARISH"
                else:
                    market_direction = "NEUTRAL"
                
                logger.info(f"{symbol} {tf}: Market direction = {market_direction}")
                
                strat_results = run_all_strategies(df)
                
                # CRITICAL FIX: Filter strategies by market direction
                filtered_strategies = []
                for strat in strat_results:
                    if market_direction == "BULLISH" and strat['side'] == "LONG":
                        filtered_strategies.append(strat)
                    elif market_direction == "BEARISH" and strat['side'] == "SHORT":
                        filtered_strategies.append(strat)
                    elif market_direction == "NEUTRAL":
                        # In neutral market, take the strongest signal only
                        filtered_strategies.append(strat)
                        break  # Only one signal in neutral market
                
                logger.info(f"{symbol} {tf}: {len(strat_results)} strategies triggered, {len(filtered_strategies)} after direction filter")
                
                for strat in filtered_strategies:
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

        # Only send signals when REAL strategies trigger - no forced signals
        if len(signals) == 0:
            print("📊 No strategies triggered this run - market conditions not met")
            # No status messages - only send when real signals are generated

        print(f"📤 Sending {len(signals)} signals...")
        if len(signals) > 0:
            for signal in signals:
                await tg.send_signal(signal)
                signal_cache.add(signal)
                trade_cache.add(signal)  # Add to active trades
        # No status messages when no signals - only logical signals when strategies trigger
            
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
        logger.info(f"📈 Final cache status: Signals={len(signal_cache.cache)}, Trades={len(trade_cache.trades)}")
        
        # Memory cleanup
        del data
        gc.collect()
        logger.info("Memory cleanup completed")

    except Exception as e:
        err = traceback.format_exc()
        await tg.send_error(f"Bot error ({TIMEFRAME_FILTER or 'ALL'}):\n{err}")
        logging.error(f"Bot error:\n{err}")
        print(f"❌ Error: {err}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())