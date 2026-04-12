## MODIFIED Requirements

### Requirement: Backtest execution
The backtesting system SHALL verify the integrity and coverage of historical data for all involved symbols before starting the simulation.

#### Scenario: Data integrity check failure
- **WHEN** the requested backtest period contains gaps in K-line data for one or more stocks
- **THEN** the system MUST fail the task immediately with a `DATA_GAP_ERROR` and list the affected dates/symbols.

### Requirement: Backtest result serialization
The backtest result models MUST use Pydantic for serialization to prevent API 500 errors.

#### Scenario: Consistent result format
- **WHEN** the backtest engine produces a performance report
- **THEN** the data MUST be serialized via a Pydantic model before being returned to the API layer.
