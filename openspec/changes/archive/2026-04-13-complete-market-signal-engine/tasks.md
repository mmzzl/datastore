## 1. Scheduler Integration

- [x] 1.1 Implement `run_daily_scanner_job` in `apps/api/scheduler_standalone.py` to import and execute `DailySignalScanner.scan()`
- [x] 1.2 Add a cron job to `setup_scheduler()` in `scheduler_standalone.py` to run the daily scan at a consistent time (e.g., 15:30)
- [x] 1.3 Verify that the scheduler correctly skips the scan on weekends

## 2. Indicator Logic Completion & Validation

- [x] 2.1 Review and refine the pandas implementation of MA, RSI, and MACD in `apps/api/app/monitor/daily_scanner.py` to ensure correctness
- [x] 2.2 Implement unit tests for `calculate_indicators` using a static dataset of K-line data to verify signal accuracy
- [x] 2.3 Verify that the `check_patterns` method correctly identifies `ma_golden_cross`, `rsi_oversold`, and `macd_golden_cross`

## 3. Pipeline Verification & Quality Assurance

- [x] 3.1 Implement an integration test script to verify the full flow: Technical Pattern $\rightarrow$ `watch_list` $\rightarrow$ `IntradayMonitor` trigger $\rightarrow$ `market_signals` record
- [x] 3.2 Verify that ST stocks are successfully filtered out of the `watch_list` during the daily scan
- [x] 3.3 Verify that `IntradayMonitor`'s signal cooldown logic prevents duplicate notifications for the same stock/pattern on the same day

## 4. Final Verification

- [x] 4.1 Run the full suite of new tests (unit and integration)
- [x] 4.2 Manually trigger a scan and verify the `watch_list` is updated in MongoDB
