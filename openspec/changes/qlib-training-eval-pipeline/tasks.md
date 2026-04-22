## 1. CSI 500 Stock List & Instruments Helper

- [x] 1.1 Add `CSI_500_STOCKS` list to `apps/api/app/qlib/config.py` (same format as `CSI_300_STOCKS`, SH/SZ prefixed codes)
- [x] 1.2 Add `get_csi500_instruments()` function to `apps/api/app/qlib/config.py`
- [x] 1.3 Add `get_instruments(pool_name: str)` helper function that accepts "csi300" or "csi500" and returns the corresponding list, raising ValueError for invalid pool names

## 2. Experiment Tracker Module

- [x] 2.1 Create `apps/api/app/experiment/__init__.py` with exports
- [x] 2.2 Create `apps/api/app/experiment/tracker.py` with `ExperimentTracker` class — MongoDB `experiments` collection CRUD
- [x] 2.3 Implement `ExperimentTracker.record_experiment(tag, config, training_metrics, backtest_result, model_id, status)` — inserts document
- [x] 2.4 Implement `ExperimentTracker.get_by_tag(tag, sort_by, limit)` — query experiments by tag
- [x] 2.5 Implement `ExperimentTracker.get_best(metric, tag)` — find best experiment by numeric metric
- [x] 2.6 Implement `ExperimentTracker.compare(experiment_ids)` — compare multiple experiments
- [x] 2.7 Write unit tests for `ExperimentTracker` in `apps/api/tests/experiment/test_tracker.py`

## 3. Training Evaluation Enrichment

- [x] 3.1 Add `_calculate_rank_ic()` method to `QlibTrainer` — Spearman rank correlation between predictions and labels
- [x] 3.2 Add `_calculate_icir()` method to `QlibTrainer` — compute IC per time period, return mean/std ratio (return 0.0 if < 10 periods)
- [x] 3.3 Add `_calculate_long_short_return()` method to `QlibTrainer` — group stocks by prediction quintile, return top-minus-bottom return
- [x] 3.4 Update `_calculate_metrics()` to include `rank_ic`, `icir`, `long_short_return` in returned dict
- [x] 3.5 Write unit tests for new metrics methods in `apps/api/tests/qlib/test_trainer_metrics.py`

## 4. Train-Eval Script

- [x] 4.1 Create `apps/api/scripts/train_eval.py` with argparse CLI interface — define all arguments: `--model`, `--factor`, `--instruments`, `--start`, `--end`, `--sync-data`, `--min-ic`, `--target-sharpe`, `--tag`, plus model-specific hyperparameters (comma-separated for multiple values)
- [x] 4.2 Implement `sync_data()` step — import and call `QlibBinConverter.incremental_sync()` when `--sync-data` flag is set
- [x] 4.3 Implement `train_model(config)` step — import `QlibTrainer`, call `start_training(config)`, poll `get_status()` until completed, return model_id and metrics
- [x] 4.4 Implement `evaluate_model(model_id, config)` step — check rank_ic against `--min-ic` threshold, return skip decision
- [x] 4.5 Implement `run_backtest(model_id, config)` step — create `QlibModelStrategy`, configure `AsyncBacktestEngine`, run backtest synchronously via `asyncio.run()`, return `RiskMetrics`
- [x] 4.6 Implement `record_experiment()` step — call `ExperimentTracker.record_experiment()` with all config, metrics, and backtest results
- [x] 4.7 Implement parameter search loop — compute Cartesian product of all multi-value parameters, iterate serially, apply early termination logic (`--min-ic` skip, `--target-sharpe` stop)
- [x] 4.8 Implement comparison table output — after all experiments, format and print table sorted by backtested Sharpe ratio, highlight best configuration
- [x] 4.9 Add error handling — catch training/backtest failures, record as failed experiments, continue to next parameter combination

## 5. Integration Verification

- [x] 5.1 Verify CSI 500 stock list is correct and `get_instruments()` works for both pools
- [x] 5.2 Verify enriched training metrics (rank_ic, icir, long_short_return) are computed and returned correctly
- [ ] 5.3 Run `train_eval.py` with a single parameter set on CSI 300 and verify full pipeline: sync → train → evaluate → backtest → record
- [ ] 5.4 Run `train_eval.py` with multiple parameter values and verify comparison table output
- [ ] 5.5 Verify `--min-ic` correctly skips backtesting for low-IC models
- [ ] 5.6 Verify `--target-sharpe` correctly stops search when target is met (End of file - total 44 lines)
