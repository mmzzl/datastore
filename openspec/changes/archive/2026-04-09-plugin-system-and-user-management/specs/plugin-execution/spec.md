# Plugin Execution Specification

## ADDED Requirements

### Requirement: System SHALL support plugin strategy in backtest

The system MUST allow users to select plugin strategies for backtesting.

#### Scenario: Run backtest with plugin
- **WHEN** POST /api/backtest/run with {strategy: "plugin", plugin_id: "turtle_trading", ...params}
- **THEN** system loads the plugin strategy
- **AND** executes backtest with plugin's generate_signals method
- **AND** returns backtest results

#### Scenario: Plugin not found
- **WHEN** plugin_id does not exist
- **THEN** system returns HTTP 404
- **AND** error message indicates "Plugin not found"

#### Scenario: Plugin parameter validation
- **WHEN** params do not match plugin's manifest parameter definitions
- **THEN** system returns HTTP 400
- **AND** error message lists invalid parameters

### Requirement: System SHALL support plugin strategy in stock selection

The system MUST allow users to use plugin strategies for stock selection.

#### Scenario: Run selection with plugin
- **WHEN** POST /api/qlib/select with {strategy: "plugin", plugin_id: "turtle_trading", ...params}
- **THEN** system loads the plugin strategy
- **AND** executes selection with plugin's generate_signals method
- **AND** returns ranked stock list

### Requirement: System SHALL provide unified action runner

The system MUST provide a unified entry point for strategy execution.

#### Scenario: Execute action via run_action
- **WHEN** POST /api/action/run with action JSON: {command, instance, param}
- **THEN** system parses the action
- **AND** routes to appropriate handler
- **AND** returns result

#### Scenario: Invalid command
- **WHEN** action JSON contains unknown command
- **THEN** system returns HTTP 400
- **AND** error message indicates "Unknown command: <command>"

#### Scenario: Action logged
- **WHEN** any action is executed
- **THEN** system logs to action_logs collection: {action_id, command, user_id, params, result, duration_ms, created_at}

### Requirement: System SHALL validate action permissions

The system MUST check permissions before executing actions.

#### Scenario: User has required permission
- **WHEN** user has permission for the action's command
- **THEN** system executes the action

#### Scenario: User lacks required permission
- **WHEN** user lacks permission for backtest:run
- **THEN** system returns HTTP 403
- **AND** error message indicates "Missing permission: backtest:run"

### Requirement: System SHALL handle plugin execution errors gracefully

The system MUST catch and report plugin execution errors without crashing.

#### Scenario: Plugin throws exception
- **WHEN** plugin's generate_signals throws RuntimeError
- **THEN** system returns HTTP 500
- **AND** error message includes exception details
- **AND** main service remains running

#### Scenario: Plugin timeout
- **WHEN** plugin execution exceeds 30 seconds
- **THEN** system terminates execution
- **AND** returns HTTP 408 timeout error
- **AND** logs timeout event
