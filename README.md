# 🚀 Crypto Scalping Bot

**Professional real-time crypto scalping bot** optimized for **BTC, ETH, and DOGE** trading pairs on **3m, 5m, and 15m** timeframes.

## ⚡ Features

- **Scalping-Focused Strategies**: RSI bounces, VWAP breaks, EMA crosses, Bollinger squeezes, MACD signals
- **Smart Risk Management**: Dynamic SL to entry after first TP hit
- **Real-Time Signals**: Telegram notifications with confidence scores
- **24x7 Operation**: Optimized GitHub Actions workflow within free tier limits
- **Proven Strategies Only**: No experimental or dummy logic

## 🔧 Quick Deployment

1. **Fork this repository** to your GitHub account  
2. **Go to your forked repository** → `Settings` → `Secrets and variables` → `Actions`  
3. **Add these repository secrets:**
   - `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token  
   - `TELEGRAM_CHAT_ID`: Your Telegram Chat ID  
   - `WEBHOOK_SECRET`: Any random string (for security)  
4. **Enable GitHub Actions** in the `Actions` tab  
5. **Push any commit** or trigger manually to start  

## ⏰ Schedule

- **Peak Hours**: Every 15 minutes (00:00–02:00, 06:00–10:00, 12:00–16:00, 20:00–23:59 UTC)  
- **Off-Peak**: Every 30 minutes (other hours)  
- **Backup**: Every 2 hours (fallback workflow)  
- **Monthly Usage**: ~1,800 minutes (within GitHub's 2,000 free minutes)  

## 📁 Project Structure

.github/workflows/
├── crypto-signal-bot.yml # Main optimized workflow
└── main.yml # Backup workflow
src/
├── cache.py # Signal & trade caching with SL tracking
├── confidence.py # Scalping-optimized confidence scoring
├── data.py # Real-time Binance data fetching
├── momentum.py # RSI + Stochastic momentum analysis
├── signal_builder.py # Signal generation & exit logic
├── strategies.py # 6 proven scalping strategies
├── telegram.py # Professional signal formatting
├── utils.py # VWAP calculation utilities
└── validation.py # Strict scalping signal validation
runner.py # Main bot orchestrator
start.py # Entry point with logging
requirements.txt # Dependencies (all free APIs)

markdown
Copy code

## 🎯 Trading Pairs & Timeframes

- **Symbols**: BTCUSDT, ETHUSDT, DOGEUSDT  
- **Timeframes**: 3m, 5m, 15m  
- **Max Signals**: 5 per run  
- **Confidence**: ≥65% minimum  

## 📊 Strategies Implemented

1. **RSI Oversold/Overbought Bounce** – Volume-confirmed reversals  
2. **VWAP Breakout/Breakdown** – High-volume VWAP breaks  
3. **EMA Scalp Signals** – Fast EMA (5) vs Slow EMA (13) crosses  
4. **Bollinger Squeeze** – Low volatility breakouts  
5. **MACD Scalp** – Fast MACD (8,17) crossovers  

## 🛡️ Risk Management

- **Dynamic Stop Loss**: Moves to entry after first TP hit  
- **Time-Based Exits**: Close after 20 candles with minimal profit  
- **ATR-Based Sizing**: 0.8–1.1x ATR for SL, 0.6–2.0x ATR for TPs  
- **Volume Confirmation**: All signals require above-average volume  

## ✅ What's Fixed

- ✅ SL number tracking (01–99 rolling)  
- ✅ Real-time Binance data (no paid APIs)  
- ✅ Scalping-optimized strategies  
- ✅ Smart trade management  
- ✅ 24x7 GitHub Actions scheduling  
- ✅ Professional Telegram formatting  
- ✅ Comprehensive error handling