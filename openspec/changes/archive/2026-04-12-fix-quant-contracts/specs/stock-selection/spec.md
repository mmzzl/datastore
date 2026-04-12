## MODIFIED Requirements

### Requirement: Strategy-based stock selection
The system SHALL execute a selection task and return a list of stocks that meet the strategy criteria, including a detailed log of all excluded stocks.

#### Scenario: Successful selection with logs
- **WHEN** user starts a selection task
- **THEN** the system returns the selected stocks AND a complete list of all stocks in the pool that were filtered out, specifying the reason for each.

### Requirement: Selection Task Status
The selection task status MUST reflect the current stage including "Analyzing" for AI analysis.

#### Scenario: Task progress tracking
- **WHEN** the engine completes the signal generation and starts AI analysis
- **THEN** the status MUST transition to `analyzing`.
