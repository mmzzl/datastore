## ADDED Requirements

### Requirement: User can run stock selection with strategy

The system SHALL allow users to run stock selection by choosing a strategy and stock pool.

#### Scenario: Run selection with built-in strategy
- **WHEN** user selects a built-in strategy (ma_cross, rsi, bollinger, macd)
- **AND** user selects a stock pool (hs300, zz500, all)
- **AND** user configures strategy parameters
- **AND** user submits the selection request
- **THEN** system creates a selection task
- **AND** system returns a task_id
- **AND** system sets task status to "pending"

#### Scenario: Run selection with plugin strategy
- **WHEN** user selects "plugin" as strategy type
- **AND** user provides a valid plugin_id
- **AND** user selects a stock pool
- **THEN** system loads the plugin strategy from registry
- **AND** system executes selection using the plugin strategy

#### Scenario: Invalid strategy type
- **WHEN** user provides an invalid strategy type
- **THEN** system returns HTTP 400 error
- **AND** error message lists valid strategy types

#### Scenario: Plugin strategy without plugin_id
- **WHEN** user selects "plugin" strategy but does not provide plugin_id
- **THEN** system returns HTTP 400 error
- **AND** error message indicates plugin_id is required

### Requirement: System calculates technical indicators for each stock

The system SHALL calculate standardized technical indicators for all stocks in the pool.

#### Scenario: Calculate indicators for valid stock
- **WHEN** system processes a stock with sufficient K-line data (>= 30 days)
- **THEN** system calculates MA5, MA10, MA20
- **AND** system calculates RSI (14-period)
- **AND** system calculates MACD, MACD signal, MACD histogram
- **AND** system calculates Bollinger Bands (20-period, 2 std)

#### Scenario: Skip stock with insufficient data
- **WHEN** stock has less than 30 days of K-line data
- **THEN** system skips the stock
- **AND** stock is not included in selection results

### Requirement: System filters stocks by signal and calculates score

The system SHALL filter stocks based on strategy signal and calculate a composite score.

#### Scenario: Filter stocks with buy signal
- **WHEN** strategy generates a BUY signal for a stock
- **THEN** system includes the stock in results
- **AND** system calculates score based on confidence and indicators

#### Scenario: Exclude stocks with hold or sell signal
- **WHEN** strategy generates HOLD or SELL signal
- **THEN** system excludes the stock from results

#### Scenario: Calculate score with confidence
- **GIVEN** stock has BUY signal with confidence value
- **WHEN** system calculates score
- **THEN** base_score = confidence * 100
- **AND** system adjusts score based on technical indicators:
  - RSI 30-50: +5 points
  - RSI > 70: -10 points
  - MACD histogram > 0: +5 points
  - MA5 > MA10 > MA20: +5 points
- **AND** final score is clamped between 0 and 100

### Requirement: System determines signal strength

The system SHALL classify signal strength based on confidence value.

#### Scenario: Strong signal
- **WHEN** confidence >= 0.8
- **THEN** signal_strength = "强"

#### Scenario: Medium signal
- **WHEN** confidence >= 0.5 and confidence < 0.8
- **THEN** signal_strength = "中"

#### Scenario: Weak signal
- **WHEN** confidence < 0.5
- **THEN** signal_strength = "弱"

### Requirement: System returns paginated selection results

The system SHALL return selection results with pagination support.

#### Scenario: Get selection result by task_id
- **WHEN** user requests result for a completed task
- **THEN** system returns task details including:
  - task_id, strategy_type, stock_pool, status
  - created_at, completed_at timestamps
  - total_stocks (pool size), selected_count
  - results array with stock details
  - ai_result (if available)

#### Scenario: Stock result item structure
- **WHEN** system returns a stock result item
- **THEN** item contains:
  - code, name, score, signal_type, signal_strength, confidence
  - industry (from industry classification)
  - indicators object (ma5, ma10, ma20, rsi, macd, macd_hist)
  - ai_analysis object (if available)

### Requirement: System respects user permissions

The system SHALL check permissions before allowing selection operations.

#### Scenario: User with selection:run permission
- **WHEN** user has "selection:run" permission
- **THEN** user can start a new selection task

#### Scenario: User without selection:run permission
- **WHEN** user lacks "selection:run" permission
- **THEN** system returns HTTP 403 error

#### Scenario: User with selection:view permission
- **WHEN** user has "selection:view" permission
- **THEN** user can view selection results and history

### Requirement: System provides stock pool information

The system SHALL provide available stock pools with metadata.

#### Scenario: List available stock pools
- **WHEN** user requests stock pool list
- **THEN** system returns pool information:
  - hs300: 沪深300 (300 stocks)
  - zz500: 中证500 (500 stocks)
  - all: 全市场 (estimated 5000 stocks)
