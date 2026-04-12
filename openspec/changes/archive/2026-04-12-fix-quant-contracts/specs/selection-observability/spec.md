## ADDED Requirements

### Requirement: Detailed Filtration Logging
The stock selection engine SHALL record the specific reason why each stock in a pool was excluded from the final results.

#### Scenario: Log insufficient data
- **WHEN** a stock has fewer than the required minimum number of K-line candles
- **THEN** system adds an entry to the task's filtration log: `{ "code": "...", "reason": "INSUFFICIENT_DATA", "detail": "..." }`

#### Scenario: Log strategy mismatch
- **WHEN** a stock's indicators do not meet the strategy's BUY criteria
- **THEN** system adds an entry to the task's filtration log: `{ "code": "...", "reason": "STRATEGY_MISMATCH", "detail": "..." }`

### Requirement: Observable Task State
The selection task SHALL expose these filtration logs via the API so the frontend can display them to the user.

#### Scenario: Fetch selection results with logs
- **WHEN** user calls `/api/stock-selection/{task_id}`
- **THEN** the response SHALL include a `filtration_logs` array containing all excluded stocks and their reasons.
