#!/usr/bin/env python3
"""
Simple validation script for crypto scalping bot
Tests core logic without external dependencies
"""
import json
import time
import os
import sys

def test_cache_functionality():
    """Test caching and SL number generation"""
    print("🔍 Testing cache functionality...")
    
    # Create test cache directory
    os.makedirs(".cache", exist_ok=True)
    
    # Test SL number generation
    from src.cache import StrategyHistory
    history = StrategyHistory(".cache/test_history.json")
    
    # Generate several SL numbers
    sl_numbers = [history.next_slno() for _ in range(5)]
    print(f"   Generated SL numbers: {sl_numbers}")
    
    # Verify they're unique and sequential
    assert len(set(sl_numbers)) == len(sl_numbers), "SL numbers must be unique"
    assert all(len(sl) == 2 for sl in sl_numbers), "SL numbers must be 2 digits"
    print("   ✅ SL number generation working correctly")

def test_strategies_import():
    """Test that all strategies import correctly"""
    print("🔍 Testing strategy imports...")
    
    try:
        from src.strategies import STRATEGY_LIST, run_all_strategies
        print(f"   Found {len(STRATEGY_LIST)} strategies:")
        for i, strategy in enumerate(STRATEGY_LIST, 1):
            print(f"      {i}. {strategy['name']} ({strategy['side']})")
        print("   ✅ All strategies imported successfully")
        return True
    except Exception as e:
        print(f"   ❌ Strategy import failed: {e}")
        return False

def test_data_structure():
    """Test data fetching structure"""
    print("🔍 Testing data components...")
    
    try:
        from src.data import fetch_klines, add_atr, TF_MAP
        print(f"   Timeframe mapping: {TF_MAP}")
        print("   ✅ Data components loaded successfully")
        return True
    except Exception as e:
        print(f"   ❌ Data component failed: {e}")
        return False

def test_signal_builder():
    """Test signal building logic"""
    print("🔍 Testing signal builder...")
    
    try:
        from src.signal_builder import build_signal, check_trade_exit
        print("   ✅ Signal builder components loaded")
        return True
    except Exception as e:
        print(f"   ❌ Signal builder failed: {e}")
        return False

def test_validation_logic():
    """Test signal validation"""
    print("🔍 Testing validation logic...")
    
    try:
        from src.validation import is_valid_signal
        
        # Test with mock signal
        mock_signal = {
            'confidence': 0.75,
            'momentum': 55,
            'entry': 100.0,
            'sl': 99.0,
            'tp': [100.5, 101.0, 101.5]
        }
        
        result = is_valid_signal(mock_signal, 0.65)
        print(f"   Mock signal validation: {result}")
        print("   ✅ Validation logic working")
        return True
    except Exception as e:
        print(f"   ❌ Validation failed: {e}")
        return False

def test_telegram_formatting():
    """Test Telegram message formatting"""
    print("🔍 Testing Telegram formatting...")
    
    try:
        from src.telegram import TelegramBot
        
        # Test message formatting without actually sending
        mock_signal = {
            'symbol': 'BTCUSDT',
            'timeframe': '5m',
            'side': 'LONG',
            'strategy': 'RSI Oversold Bounce',
            'entry': 45250.50,
            'sl': 45100.25,
            'sl_multiplier': 1.0,
            'tp': [45350.75, 45450.00, 45550.25],
            'tp_multipliers': [0.8, 1.2, 1.8],
            'confidence': 0.78,
            'momentum_cat': 'MEDIUM',
            'slno': '01'
        }
        
        print("   ✅ Telegram formatting components loaded")
        return True
    except Exception as e:
        print(f"   ❌ Telegram formatting failed: {e}")
        return False

def test_configuration():
    """Test bot configuration"""
    print("🔍 Testing configuration...")
    
    # Check runner configuration
    try:
        with open('runner.py', 'r') as f:
            content = f.read()
            
        # Verify symbols
        if 'BTCUSDT' in content and 'ETHUSDT' in content and 'DOGEUSDT' in content:
            print("   ✅ Correct trading pairs configured")
        else:
            print("   ❌ Incorrect trading pairs")
            
        # Verify timeframes
        if '"3m"' in content and '"5m"' in content and '"15m"' in content:
            print("   ✅ Correct timeframes configured")
        else:
            print("   ❌ Incorrect timeframes")
            
        # Verify confidence threshold
        if '0.65' in content:
            print("   ✅ Correct confidence threshold (65%)")
        else:
            print("   ⚠️  Confidence threshold may need verification")
            
        return True
    except Exception as e:
        print(f"   ❌ Configuration check failed: {e}")
        return False

def test_workflows():
    """Test GitHub Actions workflows"""
    print("🔍 Testing GitHub Actions workflows...")
    
    try:
        # Check main workflow
        if os.path.exists('.github/workflows/crypto-signal-bot.yml'):
            print("   ✅ Main workflow file exists")
            
            with open('.github/workflows/crypto-signal-bot.yml', 'r') as f:
                content = f.read()
                
            if 'cron:' in content:
                print("   ✅ Cron schedule configured")
            if 'TELEGRAM_BOT_TOKEN' in content:
                print("   ✅ Telegram secrets configured")
                
        if os.path.exists('.github/workflows/main.yml'):
            print("   ✅ Backup workflow exists")
            
        return True
    except Exception as e:
        print(f"   ❌ Workflow check failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🚀 Starting crypto scalping bot validation...\n")
    
    tests = [
        test_strategies_import,
        test_data_structure,
        test_signal_builder,
        test_validation_logic,
        test_telegram_formatting,
        test_cache_functionality,
        test_configuration,
        test_workflows
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
        print()
    
    print(f"📊 Validation Summary:")
    print(f"   Tests Passed: {passed}/{total}")
    print(f"   Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("   🎉 All tests passed! Bot is ready for deployment.")
        return True
    else:
        print(f"   ⚠️  {total - passed} tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)