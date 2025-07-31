def is_valid_signal(signal, confidence_threshold):
    """Validate signals for scalping with strict criteria"""
    # Check for empty or missing TP array
    if not signal.get('tp') or len(signal['tp']) == 0:
        return False
        
    # Minimum confidence threshold
    if signal['confidence'] < confidence_threshold:
        return False
    
    # For scalping, we accept wide momentum range since we profit from any movement
    # Only reject extreme conditions where market might be frozen or overly volatile
    if signal['momentum'] < 15 or signal['momentum'] > 90:
        return False
    
    # Additional validation for scalping
    # Ensure reasonable SL distance (not too tight, not too wide)
    sl_distance = abs(signal['entry'] - signal['sl'])
    entry_pct = (sl_distance / signal['entry']) * 100
    if entry_pct < 0.2 or entry_pct > 3.0:  # 0.2% to 3% SL distance for scalping
        return False
    
    # Ensure first TP is achievable for scalping
    first_tp_distance = abs(signal['tp'][0] - signal['entry'])
    tp_pct = (first_tp_distance / signal['entry']) * 100
    if tp_pct < 0.15 or tp_pct > 2.0:  # 0.15% to 2% first TP for scalping
        return False
    
    # Ensure all TPs are in correct direction
    entry = signal['entry']
    side = signal['side']
    for i, tp in enumerate(signal['tp']):
        if side == 'LONG' and tp <= entry:
            return False  # TP must be above entry for LONG
        elif side == 'SHORT' and tp >= entry:
            return False  # TP must be below entry for SHORT
        
    return True