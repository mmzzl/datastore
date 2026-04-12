## 1. Data Layer & Setup

- [x] 1.1 Create `watch_list` and `market_signals` collections in MongoDB with appropriate indexes (e.g., index on `symbol` and `timestamp`).
- [x] 1.2 Implement `IndustryMapper` class to load `data/all_stock_industry.csv` into a memory map at startup.
- [x] 1.3 Implement ST stock filtering utility to exclude "ST" and "*ST" tickers from all pipelines.

## 2. Quant Signal Generation (Daily)

- [x] 2.1 Implement `DailySignalScanner` to fetch K-line data for HS300/500 stocks from MongoDB.
- [ ] 2.2 Implement technical indicator calculations (MA, RSI, MACD) using pandas.
- [x] 2.3 Implement pattern detection logic (Golden Cross, RSI Oversold) and add matching stocks to `watch_list` with 3-day TTL.

## 3. Sentiment Signal Generation (News)

- [x] 3.1 Implement `NewsSignalProcessor` to extract `stockList` and parse BK codes from real-time news.
- [x] 3.2 Implement BK-code to stock mapping logic using the `IndustryMapper`.
- [x] 3.3 Implement logic to add mapped non-ST stocks to `watch_list` with 24h TTL.

## 4. Intraday Monitoring System

- [x] 4.1 Implement `IntradayMonitor` worker to poll `watch_list` stocks every 30-60 seconds.
- [x] 4.2 Implement data freshness check to verify K-line timestamps before analysis.
- [x] 4.3 Implement minute-level breakout detection (Volume Surge, Price Breakout).
- [x] 4.4 Implement signal cooldown logic to prevent duplicate alerts for the same symbol/type.

## 5. API Integration & Delivery

- [x] 5.1 Refactor `apps/api/app/monitor/market_signals.py` to read from the `market_signals` MongoDB collection instead of in-memory lists.
- [x] 5.2 Update `/signals/latest` endpoint to support pagination and filtering.
- [x] 5.3 Integrate with the `notify` module to send real-time DingTalk notifications when high-confidence signals are generated.

## 6. Verification

- [ ] 6.1 Verify the full pipeline: News $\rightarrow$ BK Map $\rightarrow$ Watchlist $\rightarrow$ Minute Trigger $\rightarrow$ Signal.
- [ ] 6.2 Verify that ST stocks are successfully filtered at every stage.
- [ ] 6.3 Verify signal cooldown prevents spam.
