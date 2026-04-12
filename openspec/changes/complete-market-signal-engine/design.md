## Context

The `DailySignalScanner` in `apps/api/app/monitor/daily_scanner.py` currently implements a technical signal scanning logic that is not integrated into the system's execution flow. The standalone scheduler (`scheduler_standalone.py`) manages several periodic tasks, but lacks a job to trigger this scanner. Additionally, while basic pandas logic for MA, RSI, and MACD exists, it hasn't been rigorously verified or integrated into the automated pipeline.

## Goals / Non-Goals

**Goals:**
- Automate the execution of `DailySignalScanner` via `scheduler_standalone.py`.
- Finalize and validate the technical indicator calculations for accuracy.
- Create a verification pipeline to ensure signals move from discovery (`DailySignalScanner`) to the `watch_list` and finally to real-time intraday monitoring.
- Ensure consistent ST stock filtering across the entire flow.

**Non-Goals:**
- Implementing new technical indicators beyond MA, RSI, and MACD.
- Modifying the core MongoDB schema (using existing `watch_list` and `market_signals` collections).
- Developing a new UI for signal management.

## Decisions

### 1. Scheduling Integration
- **Decision**: Add a new cron job to `scheduler_standalone.py` that imports and runs the `DailySignalScanner.scan()` method.
- **Rationale**: This follows the existing pattern of the standalone scheduler and ensures that the scan runs during a consistent post-market or pre-market window (e.g., 15:30 or 09:00).
- **Alternative**: Creating a separate systemd service for the scanner. (Rejected: adds operational complexity compared to the existing APScheduler setup).

### 2. Indicator Validation
- **Decision**: Use a set of known-good stock K-line data snapshots to create unit tests for the `calculate_indicators` method in `DailySignalScanner`.
- **Rationale**: Ensures that the pandas-based rolling windows and EWM calculations match expected technical analysis results.

### 3. End-to-End Verification
- **Decision**: Implement a specialized test script that mocks a "News Event" and "Technical Pattern", then verifies the stock's presence in `watch_list` and the subsequent trigger in `IntradayMonitor`.
- **Rationale**: Validates the connectivity between the disparate components of the signal engine.

## Risks / Trade-offs

- **[Risk]** High memory usage during the scan of HS300 and ZZ500 stocks. $\rightarrow$ **Mitigation**: Process stocks in batches and ensure MongoDB cursors are handled efficiently.
- **[Risk]** Data lag in MongoDB may lead to signals based on stale K-lines. $\rightarrow$ **Mitigation**: Implement a "data freshness" check within the scanner to skip stocks with missing recent dates.
- **[Risk]** Overlap between daily scans and intraday monitors causing duplicate notifications. $\rightarrow$ **Mitigation**: Ensure the `signal_cooldown` logic in `IntradayMonitor` is correctly tuned and verified.
