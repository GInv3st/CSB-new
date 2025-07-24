import json
import os
import time

def safe_load_json(path, default):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w") as f:
            json.dump(default, f)
    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            with open(path, "w") as f2:
                json.dump(default, f2)
            return default

class SignalCache:
    def __init__(self, path):
        self.path = path
        self.cache = safe_load_json(self.path, [])

    def is_duplicate(self, signal):
        """Check for duplicate signals - scalping allows faster repeats"""
        now = int(time.time())
        for s in self.cache:
            # Check for same symbol+timeframe+side combination within 1 hour
            if (s.get('symbol') == signal['symbol'] and 
                s.get('timeframe') == signal['timeframe'] and 
                s.get('side') == signal['side'] and 
                now - s['opened_at'] < 3600):  # 1 hour for scalping
                return True
        return False

    def add(self, signal):
        self.cache.append({
            'slno': signal['slno'], 
            'symbol': signal['symbol'],
            'timeframe': signal['timeframe'],
            'side': signal['side'],
            'opened_at': int(time.time())
        })
        # Keep only last 100 entries to prevent file bloat
        self.cache = self.cache[-100:]
        self._save()

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.cache, f)

class TradeCache:
    def __init__(self, path):
        self.path = path
        self.trades = safe_load_json(self.path, [])

    def add(self, signal):
        if not any(t['slno'] == signal['slno'] for t in self.trades):
            self.trades.append(signal)
            self._save()

    def close(self, slno):
        self.trades = [t for t in self.trades if t['slno'] != slno]
        self._save()

    def get_all(self):
        return self.trades

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.trades, f)

class StrategyHistory:
    def __init__(self, path):
        self.path = path
        self.history = safe_load_json(self.path, {})

    def get(self, strategy):
        return self.history.get(strategy, [])

    def add(self, strategy, record):
        if strategy not in self.history:
            self.history[strategy] = []
        self.history[strategy].append(record)
        self.history[strategy] = self.history[strategy][-50:]
        self._save()

    def winrate(self, strategy):
        hist = self.get(strategy)
        if not hist:
            return 0.5
        wins = sum(1 for s in hist if "TP" in s.get("outcome", ""))
        return wins / len(hist)

    def next_slno(self):
        # Returns a 2-digit serial number as string, rolling from 01-99
        # Load from global counter file to ensure unique SL numbers across restarts
        counter_file = ".cache/slno_counter.json"
        try:
            if os.path.exists(counter_file):
                with open(counter_file, "r") as f:
                    data = json.load(f)
                    current = data.get("counter", 1)
            else:
                current = 1
                
            # Increment and save
            next_num = (current % 99) + 1  # Roll from 01-99
            with open(counter_file, "w") as f:
                json.dump({"counter": next_num}, f)
                
            return f"{next_num:02d}"
        except:
            return "01"

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.history, f)