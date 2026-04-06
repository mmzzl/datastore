## ADDED Requirements

### Requirement: System saves selection task to database

The system SHALL persist selection tasks and results to MongoDB.

#### Scenario: Save task on creation
- **WHEN** user starts a new selection task
- **THEN** system creates a document in stock_selections collection
- **AND** document contains:
  - task_id (UUID)
  - strategy_type, strategy_params, plugin_id (if applicable)
  - stock_pool, status, created_at
  - total_stocks, selected_count (updated after completion)

#### Scenario: Update task on completion
- **WHEN** selection task completes
- **THEN** system updates document with:
  - status = "completed"
  - completed_at timestamp
  - results array with stock details
  - market_trend object
  - ai_result object (if analysis succeeded)

#### Scenario: Handle task failure
- **WHEN** selection task fails
- **THEN** system updates document with:
  - status = "failed"
  - error message

### Requirement: System provides paginated history query

The system SHALL allow users to query selection history with pagination.

#### Scenario: Query history with pagination
- **WHEN** user requests history with page and page_size parameters
- **THEN** system returns history items sorted by created_at descending
- **AND** system returns total count, current page, page_size

#### Scenario: History item structure
- **WHEN** system returns history item
- **THEN** item contains:
  - id (task_id)
  - strategy_type
  - stock_pool
  - created_at
  - selected_count
  - status

#### Scenario: Default pagination
- **WHEN** user does not specify page parameters
- **THEN** system uses defaults:
  - page = 1
  - page_size = 20
- **AND** page_size is limited to max 100

### Requirement: System stores complete selection results

The system SHALL store full results for later retrieval.

#### Scenario: Store stock result details
- **WHEN** system saves a stock result
- **THEN** stored data includes:
  - code, name, score, signal_type, signal_strength, confidence
  - industry
  - indicators (ma5, ma10, ma20, rsi, macd, macd_hist)

#### Scenario: Store AI analysis results
- **WHEN** system saves AI analysis
- **THEN** stored data includes:
  - stock_analyses array
  - summary, sector_overview, market_risk

#### Scenario: Retrieve historical result
- **WHEN** user requests a historical task by task_id
- **THEN** system returns complete result including:
  - All task metadata
  - All stock results
  - AI analysis (if available)
  - Market trend data

### Requirement: System supports history filtering

The system SHALL support filtering history by various criteria.

#### Scenario: Filter by status
- **WHEN** user provides status filter
- **THEN** system returns only tasks with matching status

#### Scenario: Filter by stock pool
- **WHEN** user provides stock_pool filter
- **THEN** system returns only tasks for that stock pool

#### Scenario: Filter by date range
- **WHEN** user provides start_date and end_date
- **THEN** system returns tasks created within the date range

### Requirement: History respects user permissions

The system SHALL check permissions for history access.

#### Scenario: User with selection:view permission
- **WHEN** user has "selection:view" permission
- **THEN** user can query history
- **AND** user can retrieve historical task details

#### Scenario: User without selection:view permission
- **WHEN** user lacks "selection:view" permission
- **THEN** system returns HTTP 403 error
