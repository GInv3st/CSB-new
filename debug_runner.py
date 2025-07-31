import os
import sys
import time
import asyncio
import traceback
import logging
from dotenv import load_dotenv

from src.data import fetch_all_data
from src.strategies import run_all_strategies
from src.signal_builder import build_signal
from src.confidence import calculate_confidence
from src.momentum import calculate_momentum, momentum_category
from src.cache import SignalCache, TradeCache, StrategyHistory, perform_cache_maintenance
from src.telegram import TelegramBot
from src.validation import is_valid_signal

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# DEBUG: Force signal generation
SYMBOLS = ["BTCUSDT", "ETHUSDT", "DOGEUSDT"]
TIMEFRAMES = ["3m"]

async def debug_main():
    print("🔧 DEBUG MODE: Testing signal generation and Telegram sending")
    
    tg = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    # Test Telegram connection first
    try:
        await tg._send("🔧 DEBUG: Testing bot connection...")
        print("✅ Telegram connection working!")
    except Exception as e:
        print(f"❌ Telegram connection failed: {e}")
        return
    
    # Ensure cache directory exists
    os.makedirs(".cache", exist_ok=True)
    
    signal_cache = SignalCache(f".cache/signal_cache_debug.json")
    strategy_history = StrategyHistory(f".cache/strategy_history_debug.json")
    
    try:
        data = fetch_all_data(SYMBOLS, TIMEFRAMES)
        
        if not data:
            print("❌ No market data - testing with dummy signal")
            # Create a dummy signal for testing
            dummy_signal = {
                'symbol': 'BTCUSDT',
                'timeframe': '3m',
                'side': 'LONG',
                'strategy': 'DEBUG TEST',
                'entry': 100000.0,
                'sl': 99000.0,
                'tp': [101000.0, 102000.0],
                'sl_multiplier': 1.0,
                'tp_multipliers': [1.0, 2.0],
                'confidence': 0.85,
                'momentum': 65.0,
                'momentum_cat': 'BULLISH',
                'slno': 999,
                'opened_at': int(time.time())
            }
            
            print("📤 Sending DEBUG signal to Telegram...")
            await tg.send_signal(dummy_signal)
            print("✅ DEBUG signal sent!")
            return
            
        print(f"✅ Got data for {len(data)} pairs")
        
        signals = []
        for symbol in SYMBOLS:
            for tf in TIMEFRAMES:
                df = data.get((symbol, tf))
                if df is None or len(df) < 50:
                    continue
                    
                print(f"📈 {symbol} {tf}: {len(df)} candles")
                
                strategies = run_all_strategies(df)
                print(f"  🎯 {len(strategies)} strategies triggered")
                
                for strat in strategies:
                    signal = build_signal(symbol, tf, df, strat, 1.0, [0.8, 1.2, 1.8], strategy_history.next_slno())
                    if signal:
                        signal['confidence'] = calculate_confidence(signal, df, 0.7)
                        signal['momentum'] = calculate_momentum(df)
                        signal['momentum_cat'] = momentum_category(signal['momentum'])
                        
                        # DEBUG: Lower validation threshold
                        print(f"    Signal: {strat['strategy']} - Confidence: {signal['confidence']:.1%}, Momentum: {signal['momentum']:.1f}")
                        
                        # Force signal through with lower thresholds
                        if signal['confidence'] > 0.3:  # Much lower threshold
                            if not signal_cache.is_duplicate(signal):
                                signals.append(signal)
                                print(f"    ✅ ADDED DEBUG SIGNAL")
                            else:
                                print(f"    🔄 Duplicate filtered")
                        else:
                            print(f"    ❌ Low confidence: {signal['confidence']:.1%}")
        
        signals = sorted(signals, key=lambda x: x['confidence'], reverse=True)[:3]
        
        print(f"📤 Sending {len(signals)} DEBUG signals...")
        for signal in signals:
            await tg.send_signal(signal)
            signal_cache.add(signal)
            print(f"✅ Sent: {signal['strategy']} - {signal['symbol']}")
            
        if len(signals) == 0:
            await tg._send("🔧 DEBUG: No signals generated - market conditions not favorable")
            
    except Exception as e:
        error_msg = f"DEBUG Error: {traceback.format_exc()}"
        print(f"❌ {error_msg}")
        await tg._send(f"⚠️ Debug Error:\n{str(e)}")

if __name__ == "__main__":
    asyncio.run(debug_main())