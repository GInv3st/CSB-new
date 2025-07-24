import numpy as np
import pandas as pd
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from src.utils import vwap

# Scalping-focused proven strategies only
STRATEGY_LIST = [
    {
        "name": "RSI Oversold Bounce",
        "condition": lambda df: (
            RSIIndicator(df['close'], window=14).rsi().iloc[-1] < 30 and
            df['close'].iloc[-1] > df['open'].iloc[-1] and
            df['volume'].iloc[-1] > df['volume'].rolling(10).mean().iloc[-1] * 1.2
        ),
        "side": "LONG",
        "atr_mult": {"sl": 1.0, "tp": [0.8, 1.2, 1.8]}
    },
    {
        "name": "RSI Overbought Rejection",
        "condition": lambda df: (
            RSIIndicator(df['close'], window=14).rsi().iloc[-1] > 70 and
            df['close'].iloc[-1] < df['open'].iloc[-1] and
            df['volume'].iloc[-1] > df['volume'].rolling(10).mean().iloc[-1] * 1.2
        ),
        "side": "SHORT",
        "atr_mult": {"sl": 1.0, "tp": [0.8, 1.2, 1.8]}
    },
    {
        "name": "VWAP Breakout",
        "condition": lambda df: (
            df['close'].iloc[-1] > vwap(df) * 1.001 and
            df['close'].iloc[-2] <= vwap(df) and
            df['volume'].iloc[-1] > df['volume'].rolling(10).mean().iloc[-1] * 1.5 and
            df['close'].iloc[-1] > df['high'].rolling(5).max().iloc[-2]
        ),
        "side": "LONG",
        "atr_mult": {"sl": 0.8, "tp": [0.6, 1.0, 1.5]}
    },
    {
        "name": "VWAP Breakdown",
        "condition": lambda df: (
            df['close'].iloc[-1] < vwap(df) * 0.999 and
            df['close'].iloc[-2] >= vwap(df) and
            df['volume'].iloc[-1] > df['volume'].rolling(10).mean().iloc[-1] * 1.5 and
            df['close'].iloc[-1] < df['low'].rolling(5).min().iloc[-2]
        ),
        "side": "SHORT",
        "atr_mult": {"sl": 0.8, "tp": [0.6, 1.0, 1.5]}
    },
    {
        "name": "EMA Scalp Long",
        "condition": lambda df: (
            EMAIndicator(df['close'], window=5).ema_indicator().iloc[-1] > EMAIndicator(df['close'], window=13).ema_indicator().iloc[-1] and
            EMAIndicator(df['close'], window=5).ema_indicator().iloc[-2] <= EMAIndicator(df['close'], window=13).ema_indicator().iloc[-2] and
            df['close'].iloc[-1] > df['open'].iloc[-1] and
            df['volume'].iloc[-1] > df['volume'].rolling(8).mean().iloc[-1] * 1.3
        ),
        "side": "LONG",
        "atr_mult": {"sl": 0.9, "tp": [0.7, 1.1, 1.6]}
    },
    {
        "name": "EMA Scalp Short",
        "condition": lambda df: (
            EMAIndicator(df['close'], window=5).ema_indicator().iloc[-1] < EMAIndicator(df['close'], window=13).ema_indicator().iloc[-1] and
            EMAIndicator(df['close'], window=5).ema_indicator().iloc[-2] >= EMAIndicator(df['close'], window=13).ema_indicator().iloc[-2] and
            df['close'].iloc[-1] < df['open'].iloc[-1] and
            df['volume'].iloc[-1] > df['volume'].rolling(8).mean().iloc[-1] * 1.3
        ),
        "side": "SHORT",
        "atr_mult": {"sl": 0.9, "tp": [0.7, 1.1, 1.6]}
    },
    {
        "name": "Bollinger Band Squeeze Long",
        "condition": lambda df: (
            (BollingerBands(df['close'], window=15, window_dev=1.8).bollinger_hband() - BollingerBands(df['close'], window=15, window_dev=1.8).bollinger_lband()).iloc[-1] <
            (BollingerBands(df['close'], window=15, window_dev=1.8).bollinger_hband() - BollingerBands(df['close'], window=15, window_dev=1.8).bollinger_lband()).rolling(10).mean().iloc[-1] * 0.6 and
            df['close'].iloc[-1] > BollingerBands(df['close'], window=15, window_dev=1.8).bollinger_hband().iloc[-1] and
            df['volume'].iloc[-1] > df['volume'].rolling(10).mean().iloc[-1] * 1.4
        ),
        "side": "LONG",
        "atr_mult": {"sl": 1.1, "tp": [0.9, 1.4, 2.0]}
    },
    {
        "name": "Bollinger Band Squeeze Short",
        "condition": lambda df: (
            (BollingerBands(df['close'], window=15, window_dev=1.8).bollinger_hband() - BollingerBands(df['close'], window=15, window_dev=1.8).bollinger_lband()).iloc[-1] <
            (BollingerBands(df['close'], window=15, window_dev=1.8).bollinger_hband() - BollingerBands(df['close'], window=15, window_dev=1.8).bollinger_lband()).rolling(10).mean().iloc[-1] * 0.6 and
            df['close'].iloc[-1] < BollingerBands(df['close'], window=15, window_dev=1.8).bollinger_lband().iloc[-1] and
            df['volume'].iloc[-1] > df['volume'].rolling(10).mean().iloc[-1] * 1.4
        ),
        "side": "SHORT",
        "atr_mult": {"sl": 1.1, "tp": [0.9, 1.4, 2.0]}
    },
    {
        "name": "MACD Scalp Long",
        "condition": lambda df: (
            MACD(df['close'], window_fast=8, window_slow=17).macd_diff().iloc[-1] > 0 and
            MACD(df['close'], window_fast=8, window_slow=17).macd_diff().iloc[-2] <= 0 and
            df['volume'].iloc[-1] > df['volume'].rolling(10).mean().iloc[-1] * 1.2
        ),
        "side": "LONG",
        "atr_mult": {"sl": 0.8, "tp": [0.6, 1.0, 1.4]}
    },
    {
        "name": "MACD Scalp Short",
        "condition": lambda df: (
            MACD(df['close'], window_fast=8, window_slow=17).macd_diff().iloc[-1] < 0 and
            MACD(df['close'], window_fast=8, window_slow=17).macd_diff().iloc[-2] >= 0 and
            df['volume'].iloc[-1] > df['volume'].rolling(10).mean().iloc[-1] * 1.2
        ),
        "side": "SHORT",
        "atr_mult": {"sl": 0.8, "tp": [0.6, 1.0, 1.4]}
    },
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