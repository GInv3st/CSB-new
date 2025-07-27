import httpx
import pandas as pd
import numpy as np
from ta.volatility import AverageTrueRange
import time

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# Mapping for CoinGecko IDs
COINGECKO_IDS = {
    "BTCUSDT": "bitcoin",
    "ETHUSDT": "ethereum",
    "DOGEUSDT": "dogecoin"
}

TF_MAP = {"3m": "1", "5m": "1", "15m": "1"} 

def fetch_klines(symbol, interval, hours=1, max_retries=5):
    coin_id = COINGECKO_IDS.get(symbol)
    if not coin_id:
        print(f"Unknown symbol for CoinGecko: {symbol}")
        return None

    end_time = int(time.time())
    start_time = int(end_time - (hours * 60 * 60))

    url = f"{COINGECKO_BASE}/coins/{coin_id}/market_chart/range?vs_currency=usd&from={start_time}&to={end_time}"
    
    for attempt in range(max_retries):
        try:
            r = httpx.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            
            prices = data.get("prices", [])
            
            if not prices:
                return None

            df = pd.DataFrame(prices, columns=["timestamp", "close"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            
            if interval == "3m":
                resample_freq = "3min"
            elif interval == "5m":
                resample_freq = "5min"
            elif interval == "15m":
                resample_freq = "15min"
            else:
                resample_freq = "1h" 

            ohlc_df = df["close"].resample(resample_freq).ohlc()
            volume_df = df["close"].resample(resample_freq).sum() 
            
            df_final = pd.DataFrame({
                "open": ohlc_df["open"],
                "high": ohlc_df["high"],
                "low": ohlc_df["low"],
                "close": ohlc_df["close"],
                "volume": volume_df
            })
            df_final.dropna(inplace=True)
            
            return df_final
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429: # Too Many Requests
                sleep_time = 2 ** attempt # Exponential backoff
                print(f"Rate limit hit for {symbol}. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                print(f"Error fetching CoinGecko data for {symbol} ({coin_id}): {e}")
                return None
        except Exception as e:
            print(f"Error fetching CoinGecko data for {symbol} ({coin_id}): {e}")
            return None
    print(f"Failed to fetch CoinGecko data for {symbol} after {max_retries} retries.")
    return None

def fetch_all_data(symbols, timeframes):
    data = {}
    for symbol in symbols:
        for tf in timeframes:
            df = fetch_klines(symbol, tf, hours=1) # Fetching data for the last 1 hour
            if df is not None:
                df = add_atr(df)
                data[(symbol, tf)] = df
            time.sleep(1) # Keep a small delay between symbols/timeframes
    return data

def add_atr(df, period=14):
    try:
        atr = AverageTrueRange(df["high"], df["low"], df["close"], window=period).average_true_range()
        df["ATR"] = atr
    except Exception:
        df["ATR"] = np.nan
    return df


