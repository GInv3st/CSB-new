import httpx
import pandas as pd
import numpy as np
import time
import logging
from ta.volatility import AverageTrueRange

logger = logging.getLogger(__name__)

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
        # Retry each API up to 3 times
        for retry in range(3):
            try:
                retry_suffix = f" (retry {retry+1})" if retry > 0 else ""
                logger.info(f"  📡 Trying API {i+1}{retry_suffix}: {url.split('//')[1].split('/')[0]}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                r = httpx.get(url, timeout=15, headers=headers)
            
                if r.status_code == 451:
                    logger.warning(f"  ❌ API {i+1}: Geo-blocked (451)")
                    break  # Don't retry geo-blocked APIs
                elif r.status_code != 200:
                    logger.warning(f"  ❌ API {i+1}: HTTP {r.status_code}")
                    if retry < 2:
                        time.sleep(1)  # Wait before retry
                        continue
                    else:
                        break
                    
                data = r.json()
                if not data or len(data) == 0:
                    logger.warning(f"  ❌ API {i+1}: Empty response")
                    if retry < 2:
                        time.sleep(1)
                        continue
                    else:
                        break
                    
                # Validate data quality
                if len(data) < 50:
                    logger.warning(f"  ❌ API {i+1}: Insufficient data ({len(data)} candles)")
                    if retry < 2:
                        time.sleep(1)
                        continue
                    else:
                        break
                    
                logger.info(f"  ✅ API {i+1}: Success - {len(data)} candles")
                
                df = pd.DataFrame(data, columns=[
                    "open_time", "open", "high", "low", "close", "volume",
                    "close_time", "qav", "trades", "taker_base_vol", "taker_quote_vol", "ignore"
                ])
                df = df.astype({
                    "open": float, "high": float, "low": float, "close": float, "volume": float
                })
                df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
                df.set_index("open_time", inplace=True)
                
                # Additional data validation
                if df['close'].isna().any() or df['volume'].isna().any():
                    logger.warning(f"  ❌ API {i+1}: Data contains NaN values")
                    if retry < 2:
                        time.sleep(1)
                        continue
                    else:
                        break
                        
                return df
                
            except Exception as e:
                logger.error(f"  ❌ API {i+1}: Exception - {str(e)}")
                if retry < 2:
                    time.sleep(2)  # Wait longer before retry on exception
                    continue
                else:
                    break
    
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
