# Risk Monitoring Specification

## ADDED Requirements

### Requirement: System SHALL generate daily post-market risk reports

The system MUST execute risk report generation every trading day at 15:30 (after market close at 15:00).

#### Scenario: Generate risk report on trading day
- **WHEN** 15:30 arrives on Monday-Friday (cron: "30 15 * * 1-5")
- **THEN** system initiates risk report generation
- **AND** calculates risk metrics for all user holdings
- **AND** saves report to MongoDB risk_reports collection

#### Scenario: Skip weekend execution
- **WHEN** 15:30 arrives on Saturday or Sunday
- **THEN** system skips risk report generation
- **AND** logs "Weekend, skipping risk report"

#### Scenario: Risk report failure handling
- **WHEN** risk report generation fails due to data unavailability
- **THEN** system logs error
- **AND** sends DingTalk alert about failure
- **AND** retries after 5 minutes (max 3 retries)

### Requirement: System SHALL calculate portfolio-level VaR

The system MUST calculate Value at Risk at 95% confidence level for the entire portfolio.

#### Scenario: Calculate portfolio VaR
- **WHEN** risk report is generated
- **THEN** system calculates 95% VaR based on historical portfolio volatility
- **AND** returns VaR as decimal (e.g., 0.05 for 5%)
- **AND** stores in risk report

#### Scenario: VaR exceeds threshold
- **WHEN** portfolio VaR > 5% (user-defined threshold)
- **THEN** risk report includes warning flag
- **AND** recommendation suggests reducing position sizes

### Requirement: System SHALL calculate individual stock risk metrics

The system MUST calculate risk metrics for each holding position.

#### Scenario: Calculate stock-level metrics
- **WHEN** risk report is generated for user with holdings
- **THEN** for each holding, system calculates: {code, name, quantity, cost_price, current_price, pnl_pct, var_95, risk_score}
- **AND** stores in holdings_risk array

#### Scenario: Stock approaching stop-loss
- **WHEN** holding pnl_pct < -8% (close to -10% stop-loss)
- **THEN** risk report includes warning in recommendations
- **AND** recommends monitoring or reducing position

### Requirement: System SHALL calculate industry concentration

The system MUST calculate portfolio concentration across industries and flag excessive concentration.

#### Scenario: Calculate industry distribution
- **WHEN** risk report is generated
- **THEN** system categorizes each holding by industry
- **AND** calculates percentage allocation per industry
- **AND** stores in portfolio_risk.industry_concentration

#### Scenario: High industry concentration warning
- **WHEN** any single industry exceeds 50% of portfolio
- **THEN** risk report includes recommendation to diversify
- **AND** specifies which industry is over-concentrated

### Requirement: System SHALL generate risk score and level

The system MUST compute an overall risk score (0-100) and categorize into risk levels (low/medium/high).

#### Scenario: Calculate risk score
- **WHEN** risk report is generated
- **THEN** system computes risk_score based on: VaR contribution (max 30 points), industry concentration (max 30 points), loss-making positions ratio (max 40 points)
- **AND** total score ranges from 0 to 100

#### Scenario: Assign risk level
- **WHEN** risk_score is calculated
- **THEN** system assigns level: "low" (0-30), "medium" (30-60), "high" (60-100)

### Requirement: System SHALL generate actionable recommendations

The system MUST provide specific, actionable recommendations based on identified risks.

#### Scenario: Generate recommendations
- **WHEN** risk report is generated
- **THEN** system generates recommendations array
- **AND** each recommendation is a clear action item
- **AND** recommendations are prioritized by severity

#### Scenario: No recommendations for low-risk portfolio
- **WHEN** risk_score < 30 and no individual risks identified
- **THEN** recommendations array is empty
- **OR** contains positive note: "Portfolio risk is within acceptable range"

### Requirement: System SHALL send risk reports via DingTalk

The system MUST send daily risk summary via DingTalk webhook.

#### Scenario: Send DingTalk notification
- **WHEN** risk report generation completes
- **THEN** system formats risk summary as Markdown
- **AND** sends to configured DingTalk webhook
- **AND** includes: risk_score, risk_level, top 3 recommendations, link to full report

#### Scenario: DingTalk disabled
- **WHEN** user has not configured DingTalk webhook
- **THEN** system skips DingTalk notification
- **AND** logs "DingTalk not configured, skipping notification"

### Requirement: Frontend SHALL display risk report page

The frontend MUST provide a dedicated page for viewing daily risk reports with visualization.

#### Scenario: Display latest risk report
- **WHEN** user navigates to /risk-report
- **THEN** page shows most recent risk report by default
- **AND** displays risk score with color-coded indicator
- **AND** shows risk level badge
- **AND** lists all holdings with individual risk scores

#### Scenario: View historical risk reports
- **WHEN** user clicks date picker on risk report page
- **THEN** user can select past dates
- **AND** risk report for selected date loads

#### Scenario: Risk score visualization
- **WHEN** risk report page loads
- **THEN** risk score displays as gauge chart (0-100)
- **AND** color zones show low/medium/high ranges
- **AND** current score is highlighted

### Requirement: System SHALL store risk reports for 90 days

The system MUST retain risk reports in MongoDB for 90 days, with older reports archived or deleted.

#### Scenario: Retrieve reports within retention period
- **WHEN** GET /api/risk/reports is called for date within 90 days
- **THEN** system returns report from MongoDB

#### Scenario: Report older than retention period
- **WHEN** report date > 90 days old
- **THEN** system returns HTTP 404
- **AND** suggests contacting admin for archived data
