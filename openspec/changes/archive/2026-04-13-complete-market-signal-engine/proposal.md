## Why

The `market-signal-engine` was partially implemented but left in an inconsistent state. Key components like the `DailySignalScanner` are present in the codebase but not integrated into the scheduler, and several critical technical indicators and verification steps remain incomplete. This change aims to finalize the pipeline to ensure daily technical signals are automatically generated and monitored.

## What Changes

- Integrate `DailySignalScanner` into the standalone scheduler (`scheduler_standalone.py`) for automated daily execution.
- Complete and verify the implementation of technical indicators (MA, RSI, MACD) within `DailySignalScanner`.
- Implement a verification suite to validate the full pipeline: News $\rightarrow$ BK Map $\rightarrow$ Watchlist $\rightarrow$ Minute Trigger $\rightarrow$ Signal.
- Ensure ST stock filtering is consistently applied across all signal generation stages.
- Verify and fix signal cooldown logic to prevent alert spam.

## Capabilities

### New Capabilities
- `daily-signal-scheduling`: Automated daily trigger and execution of the technical signal scanner.
- `signal-pipeline-verification`: End-to-end validation of the market signal flow from source to notification.

### Modified Capabilities
- `daily-signal-generation`: Complete the implementation of technical indicators and pattern detection logic.

## Impact

- `apps/api/scheduler_standalone.py`: Addition of new scheduled jobs.
- `apps/api/app/monitor/daily_scanner.py`: Logic completion and potential refactoring for reliability.
- `apps/api/tests/`: New integration tests for the signal pipeline.
