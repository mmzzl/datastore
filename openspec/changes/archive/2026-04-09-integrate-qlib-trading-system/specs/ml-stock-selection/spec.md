# ML Stock Selection Specification

## ADDED Requirements

### Requirement: System SHALL select top stocks using trained Qlib models

The system MUST provide API endpoint to execute stock selection using a trained model on CSI 300 stock pool, returning ranked stock list with prediction scores.

#### Scenario: Successful stock selection
- **WHEN** POST /api/qlib/select is called with {model_id: "model_2026_03_30_001", date: "2026-03-30", topk: 50}
- **THEN** system loads specified model from MongoDB/filesystem
- **AND** predicts scores for all CSI 300 stocks as of specified date
- **AND** returns top 50 stocks ranked by score descending
- **AND** each entry includes: {code, name, score, rank}

#### Scenario: Model not found
- **WHEN** POST /api/qlib/select is called with invalid model_id
- **THEN** system returns HTTP 404 error
- **AND** error message indicates model not found

#### Scenario: Insufficient data for prediction
- **WHEN** requested date has no K-line data in MongoDB
- **THEN** system returns HTTP 400 error
- **AND** error message indicates data unavailability
- **AND** suggests using earlier date

### Requirement: System SHALL return prediction scores with stock recommendations

The system MUST include prediction scores in stock selection results, enabling users to understand model confidence for each stock.

#### Scenario: Score interpretation
- **WHEN** stock selection completes
- **THEN** each stock has a numeric score (higher = better)
- **AND** scores are normalized across the stock pool
- **AND** top-ranked stocks have highest scores

### Requirement: System SHALL support configurable topk parameter

The system MUST allow users to specify how many top stocks to return, with default value of 50.

#### Scenario: Custom topk value
- **WHEN** POST /api/qlib/select is called with topk=30
- **THEN** system returns exactly 30 stocks (or fewer if stock pool smaller)

#### Scenario: Default topk value
- **WHEN** POST /api/qlib/select is called without topk parameter
- **THEN** system returns top 50 stocks

#### Scenario: Topk exceeds stock pool
- **WHEN** topk=500 is requested but CSI 300 only has 300 stocks
- **THEN** system returns all 300 stocks
- **AND** logs warning about exceeding pool size

### Requirement: System SHALL cache selection results

The system MUST cache stock selection results in MongoDB to avoid redundant predictions for the same date and model.

#### Scenario: Cache hit
- **WHEN** POST /api/qlib/select is called with same model_id and date as previous call
- **THEN** system returns cached result from MongoDB
- **AND** does not re-run prediction

#### Scenario: Cache miss
- **WHEN** POST /api/qlib/select is called with new model_id or date
- **THEN** system executes prediction
- **AND** saves result to MongoDB selection_results collection

### Requirement: Frontend SHALL display stock selection results in table format

The frontend MUST provide a dedicated page for ML stock selection, displaying recommended stocks in sortable table with scores.

#### Scenario: Display stock selection page
- **WHEN** user navigates to /qlib/select
- **THEN** page shows model selector dropdown
- **AND** shows date picker for selection date
- **AND** shows "Run Selection" button
- **AND** shows results table with columns: Rank, Code, Name, Score

#### Scenario: Model selector shows available models
- **WHEN** stock selection page loads
- **THEN** model dropdown is populated from GET /api/qlib/models
- **AND** shows model_id and version for each model
- **AND** most recent model is selected by default

#### Scenario: Results table sorting
- **WHEN** user clicks column header (Rank, Code, Score)
- **THEN** table sorts by that column
- **AND** ascending/descending toggle on subsequent clicks

### Requirement: System SHALL provide stock selection history

The system MUST allow users to view past stock selection results for comparison and analysis.

#### Scenario: View historical selection
- **WHEN** user selects different date on stock selection page
- **AND** selection was previously run for that date
- **THEN** cached results are displayed immediately

#### Scenario: Compare selections across dates
- **WHEN** user requests selection for multiple dates
- **THEN** system returns results for each date
- **AND** user can compare which stocks appeared/disappeared
