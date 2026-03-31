# Async Backtest Specification

## ADDED Requirements

### Requirement: System SHALL provide WebSocket endpoint for real-time backtest streaming

The system MUST implement WebSocket endpoint at /ws/backtest/{task_id} that streams backtest progress in real-time.

#### Scenario: WebSocket connection established
- **WHEN** client connects to WebSocket /ws/backtest/{task_id}
- **THEN** server acknowledges connection
- **AND** begins streaming backtest progress

#### Scenario: Progress update streamed
- **WHEN** backtest processes every 10th data point
- **THEN** server sends JSON message: {type: "progress", current: number, total: number, portfolio_value: number, return_pct: number, drawdown: number}
- **AND** client receives progress update in real-time

#### Scenario: Backtest completed
- **WHEN** backtest finishes processing all data points
- **THEN** server sends JSON message: {type: "completed", metrics: {total_return, annual_return, sharpe_ratio, max_drawdown, win_rate, num_trades}}
- **AND** WebSocket connection closes gracefully

#### Scenario: Backtest error
- **WHEN** backtest encounters an error during processing
- **THEN** server sends JSON message: {type: "error", message: string}
- **AND** WebSocket connection closes with error status

### Requirement: System SHALL support multiple backtest strategies

The system MUST support both traditional strategies (MA, RSI, Bollinger, MACD) and Qlib model strategies with unified interface.

#### Scenario: Run MA Cross strategy
- **WHEN** POST /api/backtest/run is called with {strategy: "ma_cross", params: {fast_period: 5, slow_period: 20}}
- **THEN** system creates backtest task
- **AND** returns task_id for WebSocket connection
- **AND** executes MA Cross strategy logic

#### Scenario: Run RSI strategy
- **WHEN** POST /api/backtest/run is called with {strategy: "rsi", params: {period: 14, oversold: 30, overbought: 70}}
- **THEN** system creates backtest task
- **AND** executes RSI strategy logic

#### Scenario: Run Qlib model strategy
- **WHEN** POST /api/backtest/run is called with {strategy: "qlib_model", params: {model_id: "...", topk: 50}}
- **THEN** system creates backtest task
- **AND** loads specified Qlib model
- **AND** executes model-based strategy

#### Scenario: Invalid strategy type
- **WHEN** POST /api/backtest/run is called with unknown strategy type
- **THEN** system returns HTTP 400 error
- **AND** error message lists valid strategy types

### Requirement: System SHALL store backtest results in MongoDB

The system MUST save backtest results to MongoDB backtest_results collection for historical reference and analysis.

#### Scenario: Save completed backtest result
- **WHEN** backtest completes successfully
- **THEN** system saves to MongoDB: {task_id, strategy, params, start_date, end_date, initial_capital, final_value, metrics, trades: [...], created_at}
- **AND** includes all trade details (buy/sell, price, quantity, date)

#### Scenario: Retrieve backtest history
- **WHEN** GET /api/backtest/results is called with pagination parameters
- **THEN** system returns paginated list of past backtest results
- **AND** each entry includes task_id, strategy, date range, key metrics

### Requirement: Frontend SHALL display real-time backtest visualization

The frontend MUST render backtest progress and results using ECharts with real-time updates from WebSocket.

#### Scenario: Display return curve chart
- **WHEN** backtest WebSocket connection receives progress updates
- **THEN** frontend updates return curve chart in real-time
- **AND** shows strategy return vs benchmark (沪深300) vs initial capital
- **AND** X-axis shows date/time, Y-axis shows portfolio value

#### Scenario: Display drawdown chart
- **WHEN** backtest progress updates
- **THEN** frontend updates drawdown chart in real-time
- **AND** shows drawdown percentage over time
- **AND** highlights maximum drawdown point

#### Scenario: Display risk metrics dashboard
- **WHEN** backtest completes
- **THEN** frontend displays risk metrics panel showing: Sharpe Ratio, Max Drawdown, Annual Return, Win Rate, Number of Trades
- **AND** color-codes metrics (green for positive, red for negative)

#### Scenario: Chart performance with high-frequency updates
- **WHEN** WebSocket sends updates every 100ms
- **THEN** frontend batches updates for rendering
- **AND** chart remains smooth (no jittering)
- **AND** CPU usage remains reasonable

### Requirement: System SHALL support backtest configuration

The system MUST allow users to configure backtest parameters including date range, initial capital, and strategy-specific settings.

#### Scenario: Configure backtest parameters
- **WHEN** user navigates to backtest page
- **THEN** page shows configuration form with: strategy selector, date range picker, initial capital input, strategy-specific parameters
- **AND** parameter fields dynamically update based on selected strategy

#### Scenario: Validate backtest configuration
- **WHEN** user submits backtest configuration with invalid parameters (e.g., start_date > end_date)
- **THEN** frontend shows validation error
- **AND** does not submit to backend

### Requirement: System SHALL support backtest cancellation

The system MUST allow users to cancel running backtest tasks.

#### Scenario: Cancel running backtest
- **WHEN** user clicks "Cancel" button during backtest execution
- **THEN** frontend sends cancellation signal via WebSocket
- **AND** backend stops backtest processing
- **AND** partial results are saved with "cancelled" status

### Requirement: System SHALL calculate comprehensive risk metrics

The system MUST calculate and return standard risk metrics including Sharpe ratio, maximum drawdown, win rate, and VaR.

#### Scenario: Calculate Sharpe ratio
- **WHEN** backtest completes
- **THEN** system calculates annualized Sharpe ratio using daily returns
- **AND** assumes risk-free rate of 0 for simplicity

#### Scenario: Calculate maximum drawdown
- **WHEN** backtest completes
- **THEN** system calculates maximum drawdown from peak portfolio value
- **AND** returns as negative percentage

#### Scenario: Calculate win rate
- **WHEN** backtest completes with multiple trades
- **THEN** system calculates percentage of profitable trades
- **AND** returns as decimal (e.g., 0.65 for 65%)
