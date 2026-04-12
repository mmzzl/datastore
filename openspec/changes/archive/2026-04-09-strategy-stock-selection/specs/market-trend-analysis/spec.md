## ADDED Requirements

### Requirement: System calculates market trend indicators

The system SHALL calculate market-wide technical indicators across the stock pool.

#### Scenario: Calculate golden cross counts
- **WHEN** system analyzes market trend
- **THEN** system counts:
  - MACD golden cross: stocks with MACD histogram > 0
  - MA golden cross: stocks with MA5 > MA10
- **AND** system calculates ratios (count / total_stocks)

#### Scenario: Calculate bullish alignment counts
- **WHEN** system analyzes market trend
- **THEN** system counts:
  - Full bullish alignment: stocks with MA5 > MA10 > MA20
  - Partial bullish alignment: stocks with MA5 > MA10 (but not full alignment)
- **AND** system calculates ratios

#### Scenario: Calculate RSI distribution
- **WHEN** system analyzes market trend
- **THEN** system counts:
  - Oversold: stocks with RSI < 30
  - Neutral: stocks with 30 <= RSI <= 70
  - Overbought: stocks with RSI > 70

### Requirement: System determines trend direction and strength

The system SHALL judge market trend based on calculated indicators.

#### Scenario: Strong bullish trend
- **WHEN** MACD golden cross ratio > 60%
- **AND** full bullish alignment ratio > 50%
- **THEN** trend_direction = "看多"
- **AND** trend_strength = "强"

#### Scenario: Moderate bullish trend
- **WHEN** MACD golden cross ratio >= 40% and <= 60%
- **AND** full bullish alignment ratio >= 30% and <= 50%
- **THEN** trend_direction = "震荡"
- **AND** trend_strength = "中"

#### Scenario: Weak trend
- **WHEN** MACD golden cross ratio < 40%
- **OR** full bullish alignment ratio < 30%
- **THEN** trend_direction = "看空" or "震荡" (based on severity)
- **AND** trend_strength = "弱"

#### Scenario: Very weak trend
- **WHEN** MACD golden cross ratio < 20%
- **OR** full bullish alignment ratio < 10%
- **THEN** trend_direction = "看空"
- **AND** trend_strength = "强"

### Requirement: System includes trend data in selection result

The system SHALL include market trend data in the selection result response.

#### Scenario: Trend data structure
- **WHEN** system returns selection result
- **THEN** market_trend object contains:
  - total_stocks, analyzed_stocks
  - macd_golden_cross_count, macd_golden_cross_ratio
  - ma_golden_cross_count, ma_golden_cross_ratio
  - full_bullish_alignment_count, full_bullish_alignment_ratio
  - partial_bullish_alignment_count, partial_bullish_alignment_ratio
  - rsi_oversold_count, rsi_overbought_count, rsi_neutral_count
  - trend_direction, trend_strength

### Requirement: System calculates selected stock statistics

The system SHALL calculate how many selected stocks have favorable technical signals.

#### Scenario: Selected stock technical stats
- **WHEN** system generates market trend data
- **THEN** system counts:
  - selected_macd_golden_cross: how many selected stocks have MACD golden cross
  - selected_bullish_alignment: how many selected stocks have bullish alignment

#### Scenario: Compare selected vs pool
- **WHEN** selected stocks have higher ratio of golden crosses than pool average
- **THEN** it indicates strategy successfully filtered for technically strong stocks
