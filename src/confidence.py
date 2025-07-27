def calculate_confidence(signal, df, winrate):
    """Calculate confidence score for scalping signals"""
    score = 0.4 + (winrate - 0.5) * 0.4  # 0.2 to 0.6 based on winrate
    
    # Volume confirmation - crucial for scalping
    vol_ratio = df['volume'].iloc[-1] / df['volume'].rolling(10).mean().iloc[-1]
    if vol_ratio > 1.5: score += 0.15
    elif vol_ratio > 1.2: score += 0.1
    elif vol_ratio > 1.0: score += 0.05
    
    # Price action strength
    price_change = abs(df['close'].iloc[-1] - df['open'].iloc[-1]) / df['open'].iloc[-1]
    if price_change > 0.003: score += 0.1  # Strong candle
    elif price_change > 0.001: score += 0.05
    
    # ATR: lower volatility = higher confidence for scalping
    atr = df['ATR'].iloc[-1]
    close = df['close'].iloc[-1]
    atr_pct = (atr / close) * 100
    if atr_pct < 1.0: score += 0.1
    elif atr_pct < 1.5: score += 0.05

    # Momentum alignment
    from ta.momentum import RSIIndicator
    rsi = RSIIndicator(df['close'], window=14).rsi().iloc[-1]
    if signal['side'] == 'LONG' and 40 <= rsi <= 60: score += 0.05
    if signal['side'] == 'SHORT' and 40 <= rsi <= 60: score += 0.05
    
    # EMA trend alignment
    from ta.trend import EMAIndicator
    ema_fast = EMAIndicator(df['close'], window=5).ema_indicator().iloc[-1]
    ema_slow = EMAIndicator(df['close'], window=13).ema_indicator().iloc[-1]
    
    if signal['side'] == 'LONG' and ema_fast > ema_slow: score += 0.05
    if signal['side'] == 'SHORT' and ema_fast < ema_slow: score += 0.05

    return min(max(score, 0), 1.0)