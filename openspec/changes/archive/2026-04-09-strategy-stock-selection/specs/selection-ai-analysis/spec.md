## ADDED Requirements

### Requirement: System performs AI analysis on selection results

The system SHALL analyze selection results using LLM to generate investment insights.

#### Scenario: AI analysis triggered after selection
- **WHEN** selection task completes with results
- **THEN** system triggers AI analysis automatically
- **AND** task status changes to "analyzing"

#### Scenario: AI analysis completes successfully
- **WHEN** LLM returns valid analysis
- **THEN** system parses the response
- **AND** system stores analysis results with the task
- **AND** task status changes to "completed"

#### Scenario: AI analysis fails
- **WHEN** LLM call fails or returns invalid response
- **THEN** system logs the error
- **AND** task still completes with results (without AI analysis)
- **AND** ai_result field is null

### Requirement: AI generates stock-level analysis

The system SHALL generate analysis for each selected stock.

#### Scenario: Stock analysis structure
- **WHEN** AI analyzes a selected stock
- **THEN** analysis contains:
  - sector: simplified industry name (e.g., "银行", "白酒")
  - sector_features: recent sector characteristics (max 30 chars)
  - risk_factors: array of 2-3 specific risks
  - operation_suggestion: actionable advice (max 50 chars)
  - brief_analysis: technical summary (max 30 chars)

#### Scenario: Risk factors are specific
- **WHEN** AI generates risk factors
- **THEN** risks are specific and actionable, not generic
- **AND** risks cover technical, fundamental, and market aspects

#### Scenario: Operation suggestion is actionable
- **WHEN** AI generates operation suggestion
- **THEN** suggestion includes:
  - Entry timing (pullback levels, breakout confirmation)
  - Position sizing (initial allocation, scale-in strategy)
  - Stop-loss and take-profit levels

### Requirement: AI generates overall summary

The system SHALL generate overall analysis summary for the selection.

#### Scenario: Summary structure
- **WHEN** AI generates summary
- **THEN** summary contains:
  - summary: overall selection analysis (max 50 chars)
  - sector_overview: sector distribution and characteristics (max 80 chars)
  - market_risk: current market risk assessment (max 50 chars)

#### Scenario: Sector overview includes distribution
- **WHEN** AI generates sector overview
- **THEN** overview identifies:
  - Primary sectors represented in results
  - Recent sector performance characteristics
  - Capital flow and policy impact

### Requirement: AI prompt includes market trend data

The system SHALL include market trend data in AI prompt for context.

#### Scenario: Market trend data in prompt
- **WHEN** building AI prompt
- **THEN** prompt includes:
  - Total stocks analyzed
  - MACD golden cross count and ratio
  - MA golden cross count and ratio
  - Bullish alignment count and ratio
  - RSI distribution (oversold, neutral, overbought)
  - Trend direction and strength judgment

### Requirement: AI respects market conditions in recommendations

The system SHALL provide market-adjusted recommendations.

#### Scenario: Strong market recommendations
- **WHEN** market trend is "看多" with "强" strength
- **THEN** AI suggestions can be more aggressive
- **AND** position sizing can be higher

#### Scenario: Weak market recommendations
- **WHEN** market trend is "看空" or "震荡" with "弱" strength
- **THEN** AI suggestions emphasize caution
- **AND** position sizing recommendations are conservative
- **AND** risk factors highlight systemic risk
