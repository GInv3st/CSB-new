import httpx
import pandas as pd
import numpy as np
from ta.volatility import AverageTrueRange

BINANCE_BASE = "https://api.binance.com/api/v3/klines"
TF_MAP = {"3m": "3m", "5m": "5m", "15m": "15m"}

def fetch_klines(symbol, interval, limit=200):
    # Try multiple APIs and backup sources
    apis = [
        f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}",
        f"https://api1.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}",
        f"https://api2.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}",
        f"https://api3.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}",
        f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}",
    ]
    
    for i, url in enumerate(apis):
        try:
            print(f"  📡 Trying API {i+1}: {url.split('//')[1].split('/')[0]}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            r = httpx.get(url, timeout=15, headers=headers)
            
            if r.status_code == 451:
                print(f"  ❌ API {i+1}: Geo-blocked (451)")
                continue
            elif r.status_code != 200:
                print(f"  ❌ API {i+1}: HTTP {r.status_code}")
                continue
                
            data = r.json()
            if not data or len(data) == 0:
                print(f"  ❌ API {i+1}: Empty response")
                continue
                
            print(f"  ✅ API {i+1}: Success - {len(data)} candles")
            
            df = pd.DataFrame(data, columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "qav", "trades", "taker_base_vol", "taker_quote_vol", "ignore"
            ])
            df = df.astype({
                "open": float, "high": float, "low": float, "close": float, "volume": float
            })
            df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
            df.set_index("open_time", inplace=True)
            return df
            
        except Exception as e:
            print(f"  ❌ API {i+1}: Exception - {str(e)}")
            continue
    
    print(f"  🚨 CRITICAL: All APIs failed for {symbol}")
    return None

def fetch_all_data(symbols, timeframes):
    data = {}
    for symbol in symbols:
        for tf in timeframes:
            print(f"📊 Fetching {symbol} {tf}...")
            df = fetch_klines(symbol, TF_MAP[tf])
            if df is not None:
                df = add_atr(df)
                data[(symbol, tf)] = df
                print(f"  ✅ {symbol} {tf}: {len(df)} candles")
            else:
                print(f"  ❌ {symbol} {tf}: Failed")
                data[(symbol, tf)] = None
    return data

def add_atr(df, period=14):
    try:
        atr = AverageTrueRange(df['high'], df['low'], df['close'], window=period).average_true_range()
        df['ATR'] = atr
    except Exception:
        df['ATR'] = np.nan
    return df
