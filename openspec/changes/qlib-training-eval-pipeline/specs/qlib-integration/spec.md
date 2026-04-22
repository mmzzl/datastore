## MODIFIED Requirements

### Requirement: Training evaluation includes rank IC, ICIR, and group returns
The system SHALL extend `QlibTrainer._calculate_metrics()` to compute and return the following additional metrics alongside existing IC and Sharpe estimates: rank_IC (Spearman rank correlation), ICIR (mean IC divided by standard deviation of IC computed per time period), and long_short_return (return of top-quintile minus bottom-quintile groups sorted by prediction score). The existing sharpe_ratio and ic metrics SHALL continue to be computed.

#### Scenario: Enriched metrics after training
- **WHEN** a model completes training and `_calculate_metrics()` is called
- **THEN** the returned metrics dictionary contains keys: `ic`, `rank_ic`, `icir`, `long_short_return`, `sharpe_ratio`, `num_predictions`

#### Scenario: ICIR computation with insufficient time periods
- **WHEN** there are fewer than 10 time periods for ICIR computation
- **THEN** ICIR SHALL be set to 0.0 to avoid unstable estimates

## ADDED Requirements

### Requirement: Training output feeds into backtest integration
After training completes, the trained model_id SHALL be directly usable by `QlibModelStrategy` for backtesting without manual intervention. The `QlibTrainer.start_training()` return value or status SHALL include the model_id that can be passed to the backtest engine.

#### Scenario: Trained model used in backtest
- **WHEN** training completes with model_id "model_20260421_183000"
- **THEN** `QlibModelStrategy(model_id="model_20260421_183000", topk=50)` can be created and used with `AsyncBacktestEngine` without any additional steps
