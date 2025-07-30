import json
import os
import time
import logging

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

def cleanup_old_files(directory=".cache", max_age_hours=24):
    """Remove old cache files to prevent storage bloat"""
    if not os.path.exists(directory):
        return
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    cleaned_count = 0
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > max_age_seconds and filename.endswith('.json'):
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                    print(f"🗑️ Cleaned old cache file: {filename}")
                except Exception as e:
                    print(f"⚠️ Failed to clean {filename}: {e}")
    
    if cleaned_count > 0:
        print(f"✅ Cleaned {cleaned_count} old cache files")

class SignalCache:
    def __init__(self, path):
        self.path = path
        self.cache = safe_load_json(self.path, [])
        self.max_entries = 50  # Reduced from 100
        self.max_age_hours = 6  # Only keep signals from last 6 hours
        self._cleanup_old_entries()

    def _cleanup_old_entries(self):
        """Remove old signals to prevent cache bloat"""
        current_time = int(time.time())
        max_age_seconds = self.max_age_hours * 3600
        
        # Remove entries older than max_age_hours
        self.cache = [
            entry for entry in self.cache 
            if current_time - entry.get('opened_at', 0) < max_age_seconds
        ]
        
        # Keep only the most recent max_entries
        if len(self.cache) > self.max_entries:
            self.cache = self.cache[-self.max_entries:]
            
        self._save()
        print(f"📊 Signal cache: {len(self.cache)} entries after cleanup")

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
        
        # Auto-cleanup when adding new entries
        if len(self.cache) > self.max_entries:
            self.cache = self.cache[-self.max_entries:]
            
        self._save()

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.cache, f)

class TradeCache:
    def __init__(self, path):
        self.path = path
        self.trades = safe_load_json(self.path, [])
        self.max_active_trades = 20  # Limit active trades
        self._cleanup_stale_trades()

    def _cleanup_stale_trades(self):
        """Remove trades older than 24 hours to prevent accumulation"""
        current_time = int(time.time())
        max_age_seconds = 24 * 3600  # 24 hours
        
        initial_count = len(self.trades)
        self.trades = [
            trade for trade in self.trades
            if current_time - trade.get('opened_at', 0) < max_age_seconds
        ]
        
        cleaned_count = initial_count - len(self.trades)
        if cleaned_count > 0:
            print(f"🗑️ Cleaned {cleaned_count} stale trades")
            self._save()

    def add(self, signal):
        # Don't add if trade already exists
        if not any(t['slno'] == signal['slno'] for t in self.trades):
            self.trades.append(signal)
            
            # Limit the number of active trades
            if len(self.trades) > self.max_active_trades:
                # Remove oldest trades first
                self.trades = sorted(self.trades, key=lambda x: x.get('opened_at', 0))
                self.trades = self.trades[-self.max_active_trades:]
                print(f"⚠️ Limited active trades to {self.max_active_trades}")
                
            self._save()

    def close(self, slno):
        initial_count = len(self.trades)
        self.trades = [t for t in self.trades if t['slno'] != slno]
        if len(self.trades) < initial_count:
            print(f"✅ Closed trade {slno}")
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
        self.max_records_per_strategy = 30  # Reduced from 50
        self.max_age_days = 7  # Keep only last 7 days
        self._cleanup_old_records()

    def _cleanup_old_records(self):
        """Remove old strategy records to prevent bloat"""
        current_time = int(time.time())
        max_age_seconds = self.max_age_days * 24 * 3600
        cleaned_strategies = 0
        
        for strategy in list(self.history.keys()):
            records = self.history[strategy]
            initial_count = len(records)
            
            # Remove old records
            records = [
                record for record in records
                if current_time - record.get('timestamp', 0) < max_age_seconds
            ]
            
            # Keep only recent records per strategy
            if len(records) > self.max_records_per_strategy:
                records = sorted(records, key=lambda x: x.get('timestamp', 0))
                records = records[-self.max_records_per_strategy:]
            
            self.history[strategy] = records
            
            if len(records) < initial_count:
                cleaned_strategies += 1
                
        if cleaned_strategies > 0:
            print(f"🗑️ Cleaned records for {cleaned_strategies} strategies")
            self._save()

    def get(self, strategy):
        return self.history.get(strategy, [])

    def add(self, strategy, record):
        if strategy not in self.history:
            self.history[strategy] = []
            
        self.history[strategy].append(record)
        
        # Auto-cleanup when adding
        if len(self.history[strategy]) > self.max_records_per_strategy:
            self.history[strategy] = self.history[strategy][-self.max_records_per_strategy:]
            
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

def perform_cache_maintenance():
    """Comprehensive cache cleanup - call this at bot startup"""
    print("🧹 Starting cache maintenance...")
    
    # Clean old files
    cleanup_old_files(".cache", max_age_hours=48)
    
    # Check total cache directory size
    cache_size = get_directory_size(".cache")
    max_size_mb = 10  # 10MB limit
    
    if cache_size > max_size_mb:
        print(f"⚠️ Cache directory is {cache_size:.1f}MB (limit: {max_size_mb}MB)")
        aggressive_cleanup()
    else:
        print(f"✅ Cache size OK: {cache_size:.1f}MB")

def get_directory_size(directory):
    """Get directory size in MB"""
    if not os.path.exists(directory):
        return 0
    
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.isfile(filepath):
                total_size += os.path.getsize(filepath)
    
    return total_size / (1024 * 1024)  # Convert to MB

def aggressive_cleanup():
    """Aggressive cleanup when storage limit is exceeded"""
    print("🚨 Performing aggressive cleanup...")
    
    cache_dir = ".cache"
    if not os.path.exists(cache_dir):
        return
    
    # Remove all files older than 12 hours
    current_time = time.time()
    max_age_seconds = 12 * 3600
    
    for filename in os.listdir(cache_dir):
        file_path = os.path.join(cache_dir, filename)
        if os.path.isfile(file_path):
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > max_age_seconds:
                try:
                    os.remove(file_path)
                    print(f"🗑️ Aggressively cleaned: {filename}")
                except Exception:
                    pass