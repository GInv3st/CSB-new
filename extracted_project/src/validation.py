def is_valid_signal(signal, confidence_threshold):
    """Validate signals for scalping with strict criteria"""
    # Minimum confidence threshold
    if signal['confidence'] < confidence_threshold:
        return False
    
    # Momentum should not be extreme for scalping
    if signal['momentum'] < 35 or signal['momentum'] > 75:
        return False
    
    # Additional validation for scalping
    # Ensure reasonable SL distance (not too tight, not too wide)
    sl_distance = abs(signal['entry'] - signal['sl'])
    entry_pct = (sl_distance / signal['entry']) * 100
    if entry_pct < 0.3 or entry_pct > 2.0:  # 0.3% to 2% SL distance
        return False
    
    # Ensure first TP is achievable
    first_tp_distance = abs(signal['tp'][0] - signal['entry'])
    tp_pct = (first_tp_distance / signal['entry']) * 100
    if tp_pct < 0.2 or tp_pct > 1.5:  # 0.2% to 1.5% first TP
        return False
        
    return True