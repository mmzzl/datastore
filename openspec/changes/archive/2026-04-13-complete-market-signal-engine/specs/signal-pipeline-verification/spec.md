## ADDED Requirements

### Requirement: End-to-End Signal Flow Validation
The system SHALL provide a mechanism to verify the complete path from signal discovery to final alert generation.

#### Scenario: Full pipeline success
- **WHEN** a mock technical pattern is injected into a stock's K-line data
- **THEN** the stock MUST appear in the `watch_list` after a scan
- **AND** the `IntradayMonitor` MUST detect the trigger condition
- **AND** a signal MUST be recorded in the `market_signals` collection

#### Scenario: ST Filter validation
- **WHEN** a stock matching a signal pattern is marked as an ST stock
- **THEN** the `DailySignalScanner` MUST NOT add it to the `watch_list`
