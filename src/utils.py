import time
import numpy as np

def generate_serial(symbol, tf, side):
    return f"{symbol}-{tf}-{side}-{int(time.time())}"

def vwap(df, period=20):
    """Calculate Volume Weighted Average Price for scalping"""
    recent_df = df.iloc[-period:] if len(df) > period else df
    pv = (recent_df['close'] * recent_df['volume']).sum()
    vol = recent_df['volume'].sum()
    return pv / vol if vol != 0 else recent_df['close'].iloc[-1]