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
            RSIIndicator(df['close'], window=14).rsi().iloc[-1] < 30 and
            df['close'].iloc[-1] > df['open'].iloc[-1]
        ),
        "side": "LONG",
        "atr_mult": {"sl": 1.0, "tp": [0.8, 1.2, 1.8]}
    },
    {
        "name": "RSI Overbought Scalp",
        "condition": lambda df: (
            RSIIndicator(df['close'], window=14).rsi().iloc[-1] > 70 and
            df['close'].iloc[-1] < df['open'].iloc[-1]
        ),
        "side": "SHORT",
        "atr_mult": {"sl": 1.0, "tp": [0.8, 1.2, 1.8]}
    },
    
    # EMA Crossover - Classic trend following scalp
    {
        "name": "EMA Cross Long",
        "condition": lambda df: (
            EMAIndicator(df['close'], window=9).ema_indicator().iloc[-1] > EMAIndicator(df['close'], window=21).ema_indicator().iloc[-1] and
            EMAIndicator(df['close'], window=9).ema_indicator().iloc[-2] <= EMAIndicator(df['close'], window=21).ema_indicator().iloc[-2]
        ),
        "side": "LONG",
        "atr_mult": {"sl": 0.8, "tp": [0.6, 1.0, 1.5]}
    },
    {
        "name": "EMA Cross Short",
        "condition": lambda df: (
            EMAIndicator(df['close'], window=9).ema_indicator().iloc[-1] < EMAIndicator(df['close'], window=21).ema_indicator().iloc[-1] and
            EMAIndicator(df['close'], window=9).ema_indicator().iloc[-2] >= EMAIndicator(df['close'], window=21).ema_indicator().iloc[-2]
        ),
        "side": "SHORT",
        "atr_mult": {"sl": 0.8, "tp": [0.6, 1.0, 1.5]}
    },
    
    # VWAP - Institution level used by all pro scalpers
    {
        "name": "VWAP Breakout Long",
        "condition": lambda df: (
            df['close'].iloc[-1] > vwap(df) and
            df['close'].iloc[-2] <= vwap(df)
        ),
        "side": "LONG",
        "atr_mult": {"sl": 0.7, "tp": [0.5, 0.8, 1.2]}
    },
    {
        "name": "VWAP Breakdown Short",
        "condition": lambda df: (
            df['close'].iloc[-1] < vwap(df) and
            df['close'].iloc[-2] >= vwap(df)
        ),
        "side": "SHORT",
        "atr_mult": {"sl": 0.7, "tp": [0.5, 0.8, 1.2]}
    },
    
    # MACD - Standard momentum scalping
    {
        "name": "MACD Bull Cross",
        "condition": lambda df: (
            MACD(df['close'], window_fast=12, window_slow=26).macd_diff().iloc[-1] > 0 and
            MACD(df['close'], window_fast=12, window_slow=26).macd_diff().iloc[-2] <= 0
        ),
        "side": "LONG",
        "atr_mult": {"sl": 0.9, "tp": [0.7, 1.1, 1.6]}
    },
    {
        "name": "MACD Bear Cross",
        "condition": lambda df: (
            MACD(df['close'], window_fast=12, window_slow=26).macd_diff().iloc[-1] < 0 and
            MACD(df['close'], window_fast=12, window_slow=26).macd_diff().iloc[-2] >= 0
        ),
        "side": "SHORT",
        "atr_mult": {"sl": 0.9, "tp": [0.7, 1.1, 1.6]}
    },
    
    # Bollinger Bands - Simple breakout/breakdown only
    {
        "name": "BB Breakout Long",
        "condition": lambda df: (
            df['close'].iloc[-1] > BollingerBands(df['close'], window=20, window_dev=2).bollinger_hband().iloc[-1] and
            df['close'].iloc[-2] <= BollingerBands(df['close'], window=20, window_dev=2).bollinger_hband().iloc[-2]
        ),
        "side": "LONG",
        "atr_mult": {"sl": 1.0, "tp": [0.8, 1.3, 2.0]}
    },
    {
        "name": "BB Breakdown Short",
        "condition": lambda df: (
            df['close'].iloc[-1] < BollingerBands(df['close'], window=20, window_dev=2).bollinger_lband().iloc[-1] and
            df['close'].iloc[-2] >= BollingerBands(df['close'], window=20, window_dev=2).bollinger_lband().iloc[-2]
        ),
        "side": "SHORT",
        "atr_mult": {"sl": 1.0, "tp": [0.8, 1.3, 2.0]}
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