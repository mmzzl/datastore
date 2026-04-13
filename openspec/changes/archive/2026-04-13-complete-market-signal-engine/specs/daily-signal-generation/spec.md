## MODIFIED Requirements

### Requirement: Technical Indicator Accuracy
The system SHALL correctly calculate Moving Averages (MA5, MA20), RSI (14), and MACD (12, 26, 9) using pandas to identify technical patterns.

#### Scenario: Correct MA Golden Cross detection
- **WHEN** a stock's MA5 crosses above its MA20
- **THEN** the `DailySignalScanner` MUST identify a `ma_golden_cross` pattern

#### Scenario: Correct RSI Oversold detection
- **WHEN** the RSI(14) value falls below 30
- **THEN** the `DailySignalScanner` MUST identify an `rsi_oversold` pattern

#### Scenario: Correct MACD Golden Cross detection
- **WHEN** the MACD line crosses above the signal line
- **THEN** the `DailySignalScanner` MUST identify a `macd_golden_cross` pattern
