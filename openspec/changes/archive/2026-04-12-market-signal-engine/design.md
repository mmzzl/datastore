## Context

The current `market_signals.py` implementation is a mock system using static in-memory data. The objective is to replace this with a real-time signal generation engine that utilizes K-line data and news sentiment stored in MongoDB. We have identified a "Signal Funnel" approach to optimize performance and signal quality.

## Goals / Non-Goals

**Goals:**
- Implement a multi-tier filtering system: Daily Trend $\rightarrow$ News Hotspots $\rightarrow$ Minute-level monitoring.
- Create an automated pipeline from news BK codes to specific stock tickers via `all_stock_industry.csv`.
- Establish a persistent storage for signals and a dynamic `watch_list`.
- Ensure high-quality signals by implementing ST filtering and signal cooldown (anti-spam).
- Minimize MongoDB load by limiting high-frequency monitoring to a curated watch-list.

**Non-Goals:**
- Implement automated trading (execution). This system only generates signals.
- Real-time streaming of K-line data via WebSockets (will rely on MongoDB polling/updates).
- Advanced NLP for news (will use keyword/BK-code matching).

## Decisions

### 1. The "Signal Funnel" Architecture
**Decision**: Use a three-stage pipeline instead of full-market monitoring.
- **Rationale**: Monitoring 5000+ stocks at minute-intervals is resource-prohibitive. Reducing the set to ~100 stocks via daily and news filters keeps the system responsive.
- **Alternative**: Full-market minute scanning. Rejected due to DB load and high noise-to-signal ratio.

### 2. News $\rightarrow$ Stock Mapping
**Decision**: Load `data/all_stock_industry.csv` into a memory-mapped dictionary at startup.
- **Rationale**: CSV lookups during news processing would be too slow. A hash map allows $\mathcal{O}(1)$ lookup of BK codes to stock lists.
- **Process**: Extract `BKxxx` $\rightarrow$ Query Map $\rightarrow$ Filter ST $\rightarrow$ Add to `watch_list`.

### 3. Hybrid Scheduling
**Decision**: Use a combination of daily cron jobs, minute-level polling, and a dedicated monitor worker.
- **Daily**: Full scan of HS300/500 for technical patterns.
- **Intermediate**: 1-5 min check for new news and BK code extraction.
- **Fast**: 30-60s check for price/volume breakouts in the `watch_list`.

### 4. Data Model
**Decision**: Use two new MongoDB collections:
- `watch_list`: Stores `symbol`, `source` (quant/news), `expiry_date`.
- `market_signals`: Stores `symbol`, `type`, `value`, `timestamp`, `message`.
- **Rationale**: Decouples the "interest" (watch_list) from the "event" (signal).

## Risks / Trade-offs

- **[Risk] Data Lag** $\rightarrow$ **Mitigation**: Implement a timestamp check before triggering a signal to ensure K-line data is recent.
- **[Risk] Signal Spam** $\rightarrow$ **Mitigation**: Implement a cooldown window (e.g., 4 hours) for the same signal type on the same symbol.
- **[Risk] Watch-list Bloat** $\rightarrow$ **Mitigation**: Implement TTL (Time-To-Live) for entries based on the source (News: 24h, Daily: 3 days).
- **[Trade-off] Precision vs. Latency**: Polling every 30s is a compromise. True real-time would require Change Streams, but polling is simpler to maintain and sufficient for most strategies.
