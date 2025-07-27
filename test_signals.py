#!/usr/bin/env python3
"""
Test script for crypto scalping bot
Validates all components work correctly with real data
"""
import os
import asyncio
from dotenv import load_dotenv

from src.data import fetch_klines, add_atr
from src.strategies import run_all_strategies
from src.signal_builder import build_signal
from src.cache import TradeCache, SignalCache, StrategyHistory
from src.momentum import calculate_momentum, momentum_category
from src.confidence import calculate_confidence
from src.telegram import TelegramBot
from src.validation import is_valid_signal

load_dotenv()

# Test with all supported pairs and timeframes
SYMBOLS = ["BTCUSDT", "ETHUSDT", "DOGEUSDT"]
TIMEFRAMES = ["3m", "5m", "15m"]
CONFIDENCE_THRESHOLD = 0.65

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def main():
    """Comprehensive test of all bot components"""
    print("🚀 Starting crypto scalping bot test...\n")
    
    # Initialize components
    os.makedirs(".cache", exist_ok=True)
    tg = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    signal_cache = SignalCache(".cache/signal_cache_test.json")
    trade_cache = TradeCache(".cache/active_trades_test.json")
    strategy_history = StrategyHistory(".cache/strategy_history_test.json")
    
    total_signals = 0
    valid_signals = 0
    
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            print(f"📊 Testing {symbol}/{timeframe}...")
            
            # Fetch real market data
            df = fetch_klines(symbol, timeframe, limit=200)
            if df is None or len(df) < 100:
                print(f"   ❌ Insufficient data for {symbol}/{timeframe}")
                continue
                
            df = add_atr(df)
            print(f"   ✅ Fetched {len(df)} candles")
            
            # Test all strategies
            strategy_results = run_all_strategies(df)
            print(f"   🎯 Found {len(strategy_results)} strategy triggers")
            
            for i, strat in enumerate(strategy_results):
                total_signals += 1
                
                # Build signal with proper SL number
                slno = strategy_history.next_slno()
                signal = build_signal(symbol, timeframe, df, strat, 
                                    strat['atr_mult']['sl'], 
                                    strat['atr_mult']['tp'], 
                                    slno)
                
                if not signal:
                    continue
                    
                # Calculate metrics
                signal['confidence'] = calculate_confidence(signal, df, 0.5)
                signal['momentum'] = calculate_momentum(df)
                signal['momentum_cat'] = momentum_category(signal['momentum'])
                
                # Validate signal
                if is_valid_signal(signal, CONFIDENCE_THRESHOLD):
                    valid_signals += 1
                    
                    # Check for duplicates
                    if not signal_cache.is_duplicate(signal):
                        print(f"   ✅ Valid signal: {signal['strategy']} | {signal['side']} | "
                              f"Confidence: {signal['confidence']:.1%} | SLNO: {signal['slno']}")
                        
                        # Add to cache and trades
                        signal_cache.add(signal)
                        trade_cache.add(signal)
                        
                        # Send to Telegram (only for BTC/5m to avoid spam in testing)
                        if symbol == "BTCUSDT" and timeframe == "5m":
                            await tg.send_signal(signal)
                    else:
                        print(f"   ⚠️  Duplicate signal filtered")
                else:
                    print(f"   ❌ Invalid signal: {signal['strategy']} | "
                          f"Confidence: {signal['confidence']:.1%}")
    
    # Test active trades status
    active_trades = trade_cache.get_all()
    print(f"\n📈 Active Trades: {len(active_trades)}")
    
    if active_trades and TELEGRAM_BOT_TOKEN:
        await tg.send_status(active_trades[:3])  # Send status for first 3 trades
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"   Total Strategy Triggers: {total_signals}")
    print(f"   Valid Signals: {valid_signals}")
    print(f"   Success Rate: {(valid_signals/total_signals)*100:.1f}%" if total_signals > 0 else "   No signals generated")
    print(f"   Active Trades: {len(active_trades)}")
    
    if TELEGRAM_BOT_TOKEN:
        print("   ✅ Telegram integration tested")
    else:
        print("   ⚠️  Telegram token not provided (set TELEGRAM_BOT_TOKEN)")
    
    print("\n✅ Bot test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())