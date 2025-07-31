import time
import numpy as np
from src.utils import generate_serial

def build_signal(symbol, tf, df, strat, sl_mult, tp_mult, slno):
    try:
        side = strat['side']
        entry = float(df['close'].iloc[-1])
        atr = float(df['ATR'].iloc[-1])
        if np.isnan(atr) or atr == 0:
            return None

        # ATR-based SL/TP per strategy
        if side == "LONG":
            sl = entry - atr * sl_mult
            tp = [entry + atr * m for m in tp_mult]
        else:
            sl = entry + atr * sl_mult
            tp = [entry - atr * m for m in tp_mult]

        return {
            'slno': slno,
            'symbol': symbol,
            'timeframe': tf,
            'side': side,
            'entry': round(entry, 2),
            'sl': round(sl, 2),
            'sl_multiplier': sl_mult,
            'tp': [round(x, 2) for x in tp],
            'tp_multipliers': tp_mult,
            'atr_value': round(atr, 6),  # Include ATR value for analysis
            'strategy': strat['strategy'],
            'opened_at': int(time.time()),
            'entry_candle': len(df) - 1
        }
    except Exception:
        return None

def check_trade_exit(trade, df):
    side = trade['side']
    entry = trade['entry']
    sl = trade['sl']
    tp = trade['tp']
    current_price = float(df['close'].iloc[-1])
    atr = float(df['ATR'].iloc[-1])
    current_time = int(time.time())
    
    # Check if first TP was hit - if yes, move SL to entry
    first_tp_hit = False
    if side == 'LONG':
        if current_price >= tp[0]:
            first_tp_hit = True
            # Move SL to entry for risk-free trade
            effective_sl = entry
        else:
            effective_sl = sl
    else:
        if current_price <= tp[0]:
            first_tp_hit = True
            # Move SL to entry for risk-free trade
            effective_sl = entry
        else:
            effective_sl = sl

    # SL hit check (with dynamic SL if first TP was hit)
    if side == 'LONG':
        if current_price <= effective_sl:
            reason = 'SL Hit at Entry (Risk-Free)' if first_tp_hit else 'SL Hit'
            return {'closed': True, 'reason': reason, 'exit_price': effective_sl}
    else:
        if current_price >= effective_sl:
            reason = 'SL Hit at Entry (Risk-Free)' if first_tp_hit else 'SL Hit'
            return {'closed': True, 'reason': reason, 'exit_price': effective_sl}

    # TP hit checks
    if side == 'LONG':
        for i, t in enumerate(tp):
            if current_price >= t:
                return {'closed': True, 'reason': f'TP{i+1} Hit', 'exit_price': t}
    else:
        for i, t in enumerate(tp):
            if current_price <= t:
                return {'closed': True, 'reason': f'TP{i+1} Hit', 'exit_price': t}

    # Time-based exit for scalping - use actual time, not candle count
    trade_age_seconds = current_time - trade.get('opened_at', current_time)
    max_hold_time = 300  # 5 minutes max hold for scalping
    
    if trade_age_seconds >= max_hold_time:
        min_profit_atr = 0.3
        if side == 'LONG':
            if current_price >= entry + (atr * min_profit_atr):
                return {'closed': True, 'reason': 'Time Exit with Profit', 'exit_price': current_price}
        else:
            if current_price <= entry - (atr * min_profit_atr):
                return {'closed': True, 'reason': 'Time Exit with Profit', 'exit_price': current_price}

    return {'closed': False}