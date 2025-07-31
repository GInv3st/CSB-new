import numpy as np
import pandas as pd
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from src.utils import vwap

# ONLY proven, standard scalping strategies used by professional traders
STRATEGY_LIST = [
    # RSI Mean Reversion - Most popular scalping strategy
    {
        "name": "RSI Oversold Scalp",
        "condition": lambda df: (
            RSIIndicator(df['close'], window=14).rsi().iloc[-1] < 45  # Much more sensitive for scalping
        ),
        "side": "LONG",
        "atr_mult": {"sl": 1.0, "tp": [0.8, 1.2, 1.8]}
    },
    {
        "name": "RSI Overbought Scalp",
        "condition": lambda df: (
            RSIIndicator(df['close'], window=14).rsi().iloc[-1] > 55  # Much more sensitive for scalping
        ),
        "side": "SHORT",
        "atr_mult": {"sl": 1.0, "tp": [0.8, 1.2, 1.8]}
    },
    
    # EMA Trend - Simplified trend following 
    {
        "name": "EMA Trend Long",
        "condition": lambda df: (
            EMAIndicator(df['close'], window=9).ema_indicator().iloc[-1] > EMAIndicator(df['close'], window=21).ema_indicator().iloc[-1] and
            df['close'].iloc[-1] > df['close'].iloc[-2]  # Price moving up
        ),
        "side": "LONG",
        "atr_mult": {"sl": 0.8, "tp": [0.6, 1.0, 1.5]}
    },
    {
        "name": "EMA Trend Short",
        "condition": lambda df: (
            EMAIndicator(df['close'], window=9).ema_indicator().iloc[-1] < EMAIndicator(df['close'], window=21).ema_indicator().iloc[-1] and
            df['close'].iloc[-1] < df['close'].iloc[-2]  # Price moving down
        ),
        "side": "SHORT",
        "atr_mult": {"sl": 0.8, "tp": [0.6, 1.0, 1.5]}
    },
    
    # VWAP - Simplified price action around VWAP
    {
        "name": "VWAP Long",
        "condition": lambda df: (
            df['close'].iloc[-1] > vwap(df) and  # Price above VWAP
            df['close'].iloc[-1] > df['open'].iloc[-1]  # Green candle
        ),
        "side": "LONG",
        "atr_mult": {"sl": 0.7, "tp": [0.5, 0.8, 1.2]}
    },
    {
        "name": "VWAP Short",
        "condition": lambda df: (
            df['close'].iloc[-1] < vwap(df) and  # Price below VWAP
            df['close'].iloc[-1] < df['open'].iloc[-1]  # Red candle
        ),
        "side": "SHORT",
        "atr_mult": {"sl": 0.7, "tp": [0.5, 0.8, 1.2]}
    },
    
    # MACD - Simplified momentum 
    {
        "name": "MACD Long",
        "condition": lambda df: (
            MACD(df['close'], window_fast=12, window_slow=26).macd_diff().iloc[-1] > 0 and  # MACD positive
            df['close'].iloc[-1] > df['close'].iloc[-3]  # Price higher than 3 candles ago
        ),
        "side": "LONG",
        "atr_mult": {"sl": 0.9, "tp": [0.7, 1.1, 1.6]}
    },
    {
        "name": "MACD Short",
        "condition": lambda df: (
            MACD(df['close'], window_fast=12, window_slow=26).macd_diff().iloc[-1] < 0 and  # MACD negative
            df['close'].iloc[-1] < df['close'].iloc[-3]  # Price lower than 3 candles ago
        ),
        "side": "SHORT",
        "atr_mult": {"sl": 0.9, "tp": [0.7, 1.1, 1.6]}
    },
    
    # Price Action - Simple momentum scalping
    {
        "name": "Momentum Long",
        "condition": lambda df: (
            df['close'].iloc[-1] > df['close'].iloc[-2] and  # Current > Previous
            df['close'].iloc[-1] > df['open'].iloc[-1] and   # Green candle
            df['volume'].iloc[-1] > df['volume'].rolling(5).mean().iloc[-1]  # Higher volume
        ),
        "side": "LONG",
        "atr_mult": {"sl": 0.8, "tp": [0.6, 1.0, 1.4]}
    },
    {
        "name": "Momentum Short",
        "condition": lambda df: (
            df['close'].iloc[-1] < df['close'].iloc[-2] and  # Current < Previous
            df['close'].iloc[-1] < df['open'].iloc[-1] and   # Red candle
            df['volume'].iloc[-1] > df['volume'].rolling(5).mean().iloc[-1]  # Higher volume
        ),
        "side": "SHORT",
        "atr_mult": {"sl": 0.8, "tp": [0.6, 1.0, 1.4]}
    }
]

def run_all_strategies(df):
    results = []
    for strat in STRATEGY_LIST:
        try:
            if strat["condition"](df):
                results.append({
                    "strategy": strat["name"],
                    "side": strat["side"],
                    "atr_mult": strat["atr_mult"]
                })
        except Exception:
            continue
    return results