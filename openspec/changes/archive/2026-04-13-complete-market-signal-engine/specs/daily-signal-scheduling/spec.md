## ADDED Requirements

### Requirement: Automated Daily Scan Trigger
The system SHALL trigger the `DailySignalScanner.scan()` method automatically once per trading day.

#### Scenario: Successful daily trigger
- **WHEN** the scheduled time (e.g., 15:30) is reached on a trading day
- **THEN** the `DailySignalScanner` starts scanning HS300 and ZZ500 stocks

#### Scenario: Weekend skip
- **WHEN** the scheduled time is reached on a Saturday or Sunday
- **THEN** the system skips the scan and logs the skipping action
