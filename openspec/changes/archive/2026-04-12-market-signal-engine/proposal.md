## Why

The current market signals system uses static test data and lacks real-time signal generation logic. To provide actionable trading insights, the system needs a dynamic engine that transforms K-line and news data into trading signals based on technical analysis and sentiment.

## What Changes

- **Implement a "Signal Funnel" Architecture**: Transition from static data to a multi-tier filtering process (Daily $\rightarrow$ News $\rightarrow$ Minute).
- **Technical Signal Generator**: Create a quantitative engine to scan HS300/500 stocks for technical patterns (Golden Cross, RSI oversold, etc.) using MongoDB data.
- **Sentiment Signal Generator**: Implement a news-to-stock mapping system that extracts BK codes from news and maps them to stocks via `data/all_stock_industry.csv`.
- **Intraday Monitoring System**: Create a high-frequency worker to monitor a dynamic `watch_list` for minute-level volume/price breakouts.
- **Signal Persistence**: Replace the in-memory `_signals` list with a MongoDB collection for historical tracking.
- **ST Stock Filtering**: Implement a mandatory filter to exclude ST stocks from all signal pipelines.
- **Signal Cooling Mechanism**: Add a throttling layer to prevent duplicate signal spam for the same stock.

## Capabilities

### New Capabilities
- `signal-generation`: Logic for computing technical indicators and detecting signal patterns from K-line data.
- `sentiment-mapping`: Mapping real-time news BK codes to specific stocks and industry sectors.
- `market-monitoring`: High-frequency monitoring of a targeted watch-list for intraday triggers.
- `signal-management`: Persistence, cooldown, and retrieval of generated market signals.

### Modified Capabilities
- None

## Impact

- **Code**: `apps/api/app/monitor/market_signals.py` will be refactored from a mock API to a consumer of the new signal engine.
- **Data**: New MongoDB collections for `watch_list` and `market_signals`.
- **Resources**: Increased MongoDB read load during scanning periods; new background worker processes for monitoring.
- **Dependencies**: Addition of quantitative analysis libraries (e.g., `pandas` for technical calculations) if not already fully utilized.
