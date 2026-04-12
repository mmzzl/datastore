## ADDED Requirements

### Requirement: High-Frequency Watch-list Polling
The system SHALL monitor all stocks currently in the `watch_list` every 30-60 seconds.

#### Scenario: Fetching latest minute data
- **WHEN** the monitoring cycle triggers
- **THEN** the system fetches the most recent minute-level K-lines for all symbols in the `watch_list` from MongoDB

### Requirement: Intraday Breakout Detection
The system SHALL trigger a market signal when a stock in the `watch_list` exhibits significant volume or price breakthroughs.

#### Scenario: Volume Surge Trigger
- **WHEN** a stock's current 1-min volume is > 3x its recent average and price is increasing
- **THEN** the system generates a "Volume Surge" market signal

#### Scenario: Price Breakout Trigger
- **WHEN** the current price breaks above the day's high for a stock in the `watch_list`
- **THEN** the system generates a "Price Breakout" market signal

### Requirement: Data Freshness Validation
The system MUST verify that the K-line data being analyzed is current before triggering a signal.

#### Scenario: Stale data rejection
- **WHEN** the latest K-line timestamp is older than 5 minutes
- **THEN** the system SHALL NOT trigger a signal and logs a data lag warning
