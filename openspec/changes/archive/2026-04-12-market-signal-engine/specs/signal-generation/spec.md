## ADDED Requirements

### Requirement: Technical Pattern Detection
The system SHALL compute technical indicators (MA, RSI, MACD) for stocks in the HS300/500 index using MongoDB K-line data and detect bullish/bearish patterns.

#### Scenario: MA Golden Cross detection
- **WHEN** MA5 crosses above MA20 for a stock in HS300
- **THEN** the system marks the stock as a technical potential candidate and adds it to the `watch_list`

#### Scenario: RSI Oversold detection
- **WHEN** RSI(14) drops below 30
- **THEN** the system marks the stock as an oversold candidate and adds it to the `watch_list`

### Requirement: ST Stock Exclusion
The system MUST exclude any stock flagged as ST or *ST from all signal generation processes.

#### Scenario: ST stock filtered from scan
- **WHEN** the daily scan identifies a technical pattern for a stock named "ST-XYZ"
- **THEN** the system SHALL discard this candidate and NOT add it to the `watch_list`
