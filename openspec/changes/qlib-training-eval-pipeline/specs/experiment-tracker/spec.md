## ADDED Requirements

### Requirement: Experiment records stored in MongoDB
The system SHALL store each experiment as a document in a MongoDB `experiments` collection. Each document MUST contain: experiment_id (auto-generated), tag (optional), config (model_type, factor_type, hyperparams, instruments, start_time, end_time, train/valid/test segments), training_metrics (IC, rank_IC, ICIR, long_short_return, num_predictions), backtest_result (Sharpe, annual_return, max_drawdown, total_return, total_trades, win_rate), model_id (reference to trained model), status (completed, skipped_low_ic, failed), created_at, completed_at timestamps.

#### Scenario: Successful experiment record
- **WHEN** a model is trained with config {model: lgbm, factor: alpha158, n_estimators: 1000} and achieves IC=0.05, backtest Sharpe=1.8
- **THEN** an experiment document is created with full config, training_metrics, backtest_result, model_id, and status="completed"

#### Scenario: Skipped experiment record
- **WHEN** a model is trained but its IC is below min-ic threshold
- **THEN** an experiment document is created with full config, training_metrics, model_id, status="skipped_low_ic", and backtest_result=null

#### Scenario: Failed experiment record
- **WHEN** a model training fails with an exception
- **THEN** an experiment document is created with full config, status="failed", error=message, and training_metrics=null, backtest_result=null

### Requirement: Experiment tracker supports querying experiments by tag
The system SHALL provide a method to retrieve all experiments matching a given tag, sorted by creation time.

#### Scenario: Query by tag
- **WHEN** user queries experiments with tag "weekly_lgbm_search"
- **THEN** all experiments with that tag are returned, sorted by created_at descending

### Requirement: Experiment tracker supports retrieving best experiment by metric
The system SHALL provide a method to find the best experiment by any numeric metric (e.g., backtest Sharpe, IC, annual_return) within a given tag or across all experiments.

#### Scenario: Find best by Sharpe
- **WHEN** user queries for best experiment by "backtest_result.sharpe_ratio"
- **THEN** the experiment with the highest Sharpe ratio is returned

#### Scenario: Find best within tag
- **WHEN** user queries for best experiment by "training_metrics.rank_ic" within tag "weekly_lgbm_search"
- **THEN** only experiments with that tag are considered, and the one with highest rank IC is returned

### Requirement: Experiment tracker supports experiment comparison
The system SHALL provide a method to compare multiple experiments by their metrics, returning a structured comparison dictionary.

#### Scenario: Compare experiments
- **WHEN** user provides a list of experiment IDs ["exp_001", "exp_002", "exp_003"]
- **THEN** a dictionary mapping each experiment_id to its config, training_metrics, and backtest_result is returned
