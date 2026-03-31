# Position Management Specification

## ADDED Requirements

### Requirement: System SHALL enforce position size limits

The system MUST prevent positions from exceeding configurable maximum percentage of total portfolio.

#### Scenario: Reject oversized position
- **WHEN** user attempts to add position that would exceed 10% of portfolio value
- **THEN** system returns HTTP 400 error
- **AND** error message indicates position size limit exceeded
- **AND** suggests maximum allowed quantity

#### Scenario: Calculate position size correctly
- **WHEN** user adds position with valid size
- **THEN** system calculates percentage based on current portfolio market value
- **AND** allows position if percentage ≤ 10%

### Requirement: System SHALL enforce industry concentration limits

The system MUST prevent excessive concentration in any single industry.

#### Scenario: Reject concentrated industry position
- **WHEN** user attempts to add position in industry that already has 30% allocation
- **THEN** system returns HTTP 400 error
- **AND** error message indicates industry concentration limit exceeded
- **AND** shows current industry allocation

#### Scenario: Warn on approaching limit
- **WHEN** position addition would bring industry concentration to 25-30%
- **THEN** system accepts position but includes warning in response
- **AND** recommends diversification

### Requirement: System SHALL provide position sizing recommendations

The system MUST suggest optimal position sizes based on risk budget and stock-specific risk.

#### Scenario: Generate position recommendation
- **WHEN** GET /api/positions/recommend is called with stock code
- **THEN** system calculates recommended position size based on: portfolio total value, VaR budget, stock volatility
- **AND** returns {code, recommended_quantity, recommended_value, max_quantity, reasoning}

#### Scenario: Adjust recommendation for aggressive style
- **WHEN** user has aggressive risk profile configured
- **THEN** recommendations allow higher individual position sizes
- **AND** suggest concentrated positions in high-conviction stocks

### Requirement: System SHALL track position-level VaR contribution

The system MUST calculate and track VaR contribution for each individual position.

#### Scenario: Calculate position VaR
- **WHEN** position is added or updated
- **THEN** system calculates position's contribution to portfolio VaR
- **AND** stores in position metadata

#### Scenario: Aggregate position VaRs
- **WHEN** portfolio VaR is calculated
- **THEN** system considers correlations between positions
- **AND** aggregates to portfolio-level VaR

### Requirement: System SHALL provide risk-adjusted performance metrics

The system MUST calculate position-level performance metrics adjusted for risk.

#### Scenario: Calculate position Sharpe ratio
- **WHEN** risk report is generated
- **THEN** for each position, system calculates position Sharpe ratio
- **AND** compares to portfolio Sharpe ratio

#### Scenario: Identify underperforming positions
- **WHEN** position Sharpe ratio is significantly below portfolio Sharpe
- **THEN** risk report includes recommendation to review position

### Requirement: Frontend SHALL display position risk metrics

The frontend MUST show position-level risk metrics on holdings page.

#### Scenario: Show position risk indicators
- **WHEN** user views holdings page
- **THEN** each position shows: pnl_pct, VaR contribution, position % of portfolio, industry
- **AND** color-codes positions by risk level

#### Scenario: Position detail modal
- **WHEN** user clicks on position row
- **THEN** modal shows detailed risk metrics: cost basis, current value, unrealized PnL, days held, volatility, VaR, position score

### Requirement: System SHALL prevent adding positions with insufficient data

The system MUST ensure positions are only added for stocks with adequate historical data for risk calculation.

#### Scenario: Reject position for new IPO
- **WHEN** user attempts to add position for stock with < 30 trading days of data
- **THEN** system returns HTTP 400 error
- **AND** error message indicates insufficient historical data

### Requirement: System SHALL support position notes and tags

The system MUST allow users to add notes and tags to positions for organization and tracking.

#### Scenario: Add position note
- **WHEN** user adds note to position via API
- **THEN** system stores note with position
- **AND** note is displayed in position details

#### Scenario: Filter positions by tag
- **WHEN** user filters holdings by tag on frontend
- **THEN** only positions with matching tag are shown
