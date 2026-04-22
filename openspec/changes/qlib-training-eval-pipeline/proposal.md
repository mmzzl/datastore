## Why

Qlib model training is a manual, multi-step process: call the data sync API, then the training API, then separately check results and manually run backtests. There is no way to systematically search for the best model and hyperparameters — each experiment requires manual orchestration, and training results (IC, Sharpe) are not validated through backtesting, so it's unclear whether a model is actually profitable. Training and evaluation are disconnected, and there's no structured record of experiments for comparison.

## What Changes

- Add a **train-and-evaluate script** (`train_eval.py`) that executes the full pipeline: data sync → training → IC evaluation → backtest validation, all in one invocation with configurable parameters
- Support **multi-parameter search**: the script accepts multiple values per hyperparameter, trains each combination serially, and produces a comparison table
- Add **early termination conditions**: `--min-ic` to skip backtesting for models with insufficient IC (saves time), `--target-sharpe` to stop the search when a model achieves the target backtested Sharpe ratio (saves compute)
- Add an **experiments collection** in MongoDB to record each experiment's configuration, training metrics, and backtest results for reproducibility and comparison
- Support **stock pool selection**:沪深300 (CSI 300) and 中证500 (CSI 500) as instrument pools
- Integrate with the **existing backtest system** to automatically run backtests after training, producing real Sharpe ratios and return curves instead of estimated ones

## Capabilities

### New Capabilities
- `training-eval-script`: CLI script that orchestrates the full train-evaluate-backtest pipeline with parameter search, early termination, and experiment recording
- `experiment-tracker`: MongoDB-backed experiment record storage and comparison, tracking configs, metrics, and backtest results per experiment
- `csi500-instruments`: CSI 500 (中证500) stock list configuration, complementing the existing CSI 300 list

### Modified Capabilities
- `qlib-integration`: Training evaluation will include backtest validation (not just IC/Sharpe estimation), and trainer output will feed into the experiment tracker

## Impact

- **`apps/api/scripts/`**: New `train_eval.py` script
- **`apps/api/app/qlib/config.py`**: Add CSI 500 stock list and instruments selection helper
- **`apps/api/app/qlib/trainer.py`**: Expose richer evaluation metrics (ICIR, rank IC, group returns) during training
- **`apps/api/app/experiment/`**: New module for experiment tracking (MongoDB collection, model class)
- **`apps/api/app/qlib/`**: Integration between trainer output and backtest system
- **Dependencies**: No new external dependencies; uses existing backtest infrastructure
