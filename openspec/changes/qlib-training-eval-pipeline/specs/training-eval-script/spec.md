## ADDED Requirements

### Requirement: Script executes full train-evaluate-backtest pipeline
The system SHALL provide a `train_eval.py` script that executes the following steps in sequence: (1) optionally sync Qlib data from MongoDB, (2) train a Qlib model with specified parameters, (3) evaluate training metrics (IC, rank IC, ICIR, group returns), (4) run backtest with the trained model, (5) record all results. Each step MUST complete before the next begins.

#### Scenario: Full pipeline with data sync
- **WHEN** user runs `py -3.12 train_eval.py --sync-data --model lgbm --factor alpha158 --instruments csi300`
- **THEN** script syncs Qlib data, trains model, evaluates metrics, runs backtest, and records experiment

#### Scenario: Pipeline without data sync
- **WHEN** user runs `py -3.12 train_eval.py --model lgbm --factor alpha158 --instruments csi500`
- **THEN** script skips data sync, trains model using existing Qlib data, evaluates, backtests, and records

### Requirement: Script supports configurable stock pool selection
The system SHALL support `--instruments` parameter accepting values `csi300` or `csi500` to select the stock pool for training and backtesting.

#### Scenario: Train on CSI 300
- **WHEN** user specifies `--instruments csi300`
- **THEN** script uses CSI 300 stock list for training and backtesting

#### Scenario: Train on CSI 500
- **WHEN** user specifies `--instruments csi500`
- **THEN** script uses CSI 500 stock list for training and backtesting

### Requirement: Script supports parameter search with multiple values
The system SHALL accept comma-separated multiple values for any hyperparameter (e.g., `--lgbm-n-estimators 500,1000,2000`). When multiple parameters have multiple values, the script SHALL compute the Cartesian product and train each combination serially.

#### Scenario: Single parameter with multiple values
- **WHEN** user specifies `--lgbm-n-estimators 500,1000 --lgbm-lr 0.01`
- **THEN** script trains 2 models: (n=500, lr=0.01) and (n=1000, lr=0.01)

#### Scenario: Multiple parameters with multiple values
- **WHEN** user specifies `--lgbm-n-estimators 500,1000 --lgbm-lr 0.01,0.005`
- **THEN** script trains 4 models: (500,0.01), (500,0.005), (1000,0.01), (1000,0.005)

### Requirement: Script supports early termination by minimum IC threshold
The system SHALL support `--min-ic` parameter (default 0.02). After training, if the model's rank IC is below this threshold, the script SHALL skip backtesting for that configuration and mark the experiment as `skipped_low_ic`.

#### Scenario: Model IC below threshold
- **WHEN** trained model has rank IC = 0.01 and `--min-ic 0.02` is specified
- **THEN** script skips backtesting, records experiment with status `skipped_low_ic`, and proceeds to next parameter combination

#### Scenario: Model IC above threshold
- **WHEN** trained model has rank IC = 0.05 and `--min-ic 0.02` is specified
- **THEN** script proceeds to run backtest for this model

### Requirement: Script supports early termination by target Sharpe ratio
The system SHALL support `--target-sharpe` parameter (default disabled). After backtesting, if the model's backtested Sharpe ratio meets or exceeds this target, the script SHALL stop the parameter search and report the winning configuration.

#### Scenario: Backtest Sharpe meets target
- **WHEN** backtested Sharpe = 2.1 and `--target-sharpe 2.0` is specified
- **THEN** script stops parameter search, reports this configuration as the best, and does not train remaining combinations

#### Scenario: Target Sharpe not reached
- **WHEN** backtested Sharpe = 1.5 and `--target-sharpe 2.0` is specified
- **THEN** script continues to next parameter combination

#### Scenario: Target Sharpe disabled
- **WHEN** `--target-sharpe` is not specified
- **THEN** script trains all parameter combinations regardless of backtest results

### Requirement: Script outputs comparison table of all experiments
After all parameter combinations are processed, the system SHALL output a comparison table showing: parameter values, rank IC, ICIR, long-short return, backtested Sharpe, annual return, max drawdown, and experiment status. The table SHALL be sorted by backtested Sharpe ratio (descending).

#### Scenario: Multiple experiments completed
- **WHEN** 4 parameter combinations have been trained and evaluated
- **THEN** script prints a formatted table with all results, sorted by Sharpe ratio, and highlights the best configuration

### Requirement: Script supports experiment tag for grouping
The system SHALL support `--tag` parameter to label all experiments in a single script run with the same tag for grouping and later retrieval.

#### Scenario: Tagged experiment run
- **WHEN** user runs script with `--tag weekly_lgbm_search`
- **THEN** all experiment records from this run are tagged `weekly_lgbm_search` in the database
