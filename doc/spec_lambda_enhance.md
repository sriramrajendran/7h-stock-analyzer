# 7H Stock Analyzer - Lambda Specification

- lambda function that runs the stock analyzer runs on demand and on a cron schedule from event bridge
- lambda saves the recommendations to S3, that can be consumed by the frontend UI (S3 bucket is already created)
- lambda sends push notifications via pushover for significant recommendations
- lambda has a health check endpoint
- lambda has a run-now endpoint
- lambda has an endpoint to update watchlist, portfolio, us stocks, etfs, configurations,etc.,

- UI consumes the recommendations from S3 and displays them
- Recommendations are stored in S3 with a timestamp, with price and change percentage and target price and stop loss price
- UI can fetch recommendations from S3 and display them
- UI can trigger a manual run of the lambda function

## Recommendations 

- For Sell recommendations, provide a threshold price (stop loss)
    - include this for stocks with recommended buy or hold
- For Buy recommendations, provide a target price (current price + 10%)
- For Hold recommendations, provide a target price (current price)
- For Strong Buy recommendations, provide a target price (current price + 20%)
- For Strong Sell recommendations, provide a target price (current price - 20%)
- For the recommendations done, show the reason for the recommendation
- For the recommendations done, show the confidence level
- For the recommendations done, show the technical indicators used
- for the recommendations done, show the price chart

## Recon
- For the recommendations done, do a recon once a day on target price met or stop loss hit and # of days it took to reach there

## Purge
- For the recommendations done, purge the recommendations after 1000 days

## Scalability
- The lambda function should be able to handle multiple stocks at once
- The lambda function should be able to handle multiple recommendations at once
- The lambda function should be able to handle multiple technical indicators at once
- The lambda function should be able to handle multiple configurations at once
- The lambda function should be able to handle multiple watchlists at once
- The lambda function should be able to handle multiple portfolios at once
- The lambda function should be able to handle multiple us stocks at once
- The lambda function should be able to handle multiple etfs at once

## Security
- The lambda function should be secured with API keys
- The lambda function should be secured with IAM roles
- The lambda function should be secured with VPC
- The lambda function should be secured with environment variables
- The s3 bucket should be secured with bucket policies with super minimal permissions - for read and write
- The s3 bucket should be secured with IAM roles from lambda function
- The s3 bucket should be secured with encryption - without increasing the cost

# Logging

- The lambda function should log activities meaningfully without increasing the cost
- The lambda function should log all errors without increasing the cost
- The lambda function should log all warnings without increasing the cost
- The lambda function should log all info without increasing the cost

## Config data
- The config data should be stored in S3
- The config data should be updated via the UI
- The config data should be used by the lambda function


1️⃣ App Overview

Pulls historical OHLCV data for a configurable universe of stocks from Yahoo Finance.

Computes a suite of technical indicators (trend, momentum, volatility, volume).

Aggregates indicator signals into a quantitative score.

Generates BUY/HOLD/SELL recommendations for a given date.

Optionally caches data in S3 for repeated use and backtesting.

Fully stateless: works without local storage, designed for daily or on-demand runs.

2️⃣ Key Functional Modules
Module	Function
data_loader	Fetches OHLCV from Yahoo Finance. Supports batch requests and handles missing data.
indicator_engine	Computes technical indicators (EMA, SMA, MACD, RSI, ATR, Bollinger Bands, etc.)
signal_engine	Generates individual indicator signals and aggregates them into a score.
recommendation_engine	Converts aggregated scores into BUY/HOLD/SELL recommendations.
s3_cache	Optional: saves historical data and computed indicators in S3 for reuse.
async_fetch	Optional: parallelizes large universe data fetches to avoid Yahoo rate limits.
ui	CLI or Jupyter dashboard showing signals, scores, and charts.
3️⃣ Data Flow
[Tickers] 
   │
   ▼
[Data Loader] ──> Fetch OHLCV from Yahoo
   │
   ▼
[S3 Cache] (optional) ← Check cache first
   │
   ▼
[Indicator Engine] ──> Compute EMA, SMA, RSI, MACD, ATR, Bollinger Bands, Volume-based indicators
   │
   ▼
[Signal Engine] ──> Generate +1 / 0 / -1 per indicator
   │
   ▼
[Aggregator] ──> Weighted score (trend/momentum/volatility/volume)
   │
   ▼
[Recommendation Engine] ──> BUY / HOLD / SELL + score
   │
   ▼
[Output/UI] ──> Table / CSV / JSON / Jupyter dashboard

4️⃣ Indicator Suite

Trend

EMA (12, 26)

SMA (50, 200)

MACD

Momentum

RSI (14)

Stochastic Oscillator

CCI (20)

Volatility

ATR (14)

Bollinger Bands (20,2)

Volume

OBV

Volume MA (20)

Other

ADX (14)

Pivot Points

Scoring Logic

Trend: 40%

Momentum: 30%

Volatility: 20%

Volume: 10%

Final Signal

Score ≥ 0.5 → STRONG BUY

Score ≤ −0.5 → SELL

Score between → HOLD

5️⃣ S3 Caching (Optional)

Bucket structure:

s3://windsurf-stock-cache/{ticker}/{YYYY-MM-DD}.parquet


Use Case:

Avoid repeated pulls for the same day

Enable limited backtesting without local storage

Very cheap (<< $0.20/month for 500 tickers, 5 years)

PUT/GET Strategy:

Check cache first

If missing → fetch from Yahoo → store in S3

6️⃣ Rate Limiting & Fetching Strategy

Batch requests: fetch multiple tickers at once using yfinance.download

Async or ThreadPoolExecutor for >100 tickers

Delay 1–2 seconds per batch to avoid Yahoo temporary bans

Error handling: retry 2–3 times on network errors or missing data

7️⃣ Python Package Dependencies
pip install pandas numpy yfinance ta boto3 plotly concurrent.futures


Optional for backtesting:

pip install backtrader vectorbt

8️⃣ Example Stateless + S3 Fetch Code
import yfinance as yf
import pandas as pd
import boto3
import os
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

S3_BUCKET = "windsurf-stock-cache"
USE_S3 = True

s3 = boto3.client("s3")

def fetch_data(ticker, period="1y"):
    # Try S3 cache first
    if USE_S3:
        key = f"{ticker}/data.parquet"
        try:
            obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
            df = pd.read_parquet(obj['Body'])
            return df
        except:
            pass  # Not in cache, fetch from Yahoo
    
    # Fetch from Yahoo
    df = yf.download(ticker, period=period, progress=False)
    
    # Optional: save to S3
    if USE_S3 and not df.empty:
        df.to_parquet("/tmp/temp.parquet")
        s3.upload_file("/tmp/temp.parquet", S3_BUCKET, key)
    
    return df

def compute_signal(df):
    if df.empty: return 0
    df['EMA_12'] = EMAIndicator(df['Close'], window=12).ema_indicator()
    df['EMA_26'] = EMAIndicator(df['Close'], window=26).ema_indicator()
    df['RSI_14'] = RSIIndicator(df['Close'], window=14).rsi()
    
    trend_score = 1 if df['EMA_12'].iloc[-1] > df['EMA_26'].iloc[-1] else -1
    momentum_score = 1 if df['RSI_14'].iloc[-1] < 30 else -1 if df['RSI_14'].iloc[-1] > 70 else 0
    score = 0.4*trend_score + 0.6*momentum_score
    
    rec = "BUY" if score > 0.5 else "SELL" if score < -0.5 else "HOLD"
    return rec, score

tickers = ["AAPL", "MSFT", "TSLA"]
results = []
for t in tickers:
    df = fetch_data(t)
    rec, score = compute_signal(df)
    results.append((t, rec, score))

print(results)

9️⃣ Scaling Tips

Large universe (>500 tickers) → Async fetch with batches

Memory → Keep only last year of OHLCV in memory

Optional daily run → cron job / cloud function

Visualization → Plot signals with Plotly for dashboard insights

10️⃣ Recommended Roadmap

Build stateless pipeline for 10–20 tickers first

Add S3 caching to store historical OHLCV and indicators

Integrate all indicators and scoring logic

Scale to full stock universe

Add dashboard / CSV / JSON output

Optional: integrate paper trading API for experimentation

💡 Bottom line:

This app is low-cost, practical, and fully feasible.

Stateless + S3 caching gives speed + history + reliability.

You can expand it to hundreds of tickers with minimal cost.

It’s perfect for research, alerts, or lightweight trading strategies.