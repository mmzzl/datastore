## Context

The Qlib ML pipeline currently operates as disconnected steps: data sync (API), training (API), evaluation (limited IC/estimated Sharpe), and backtest (separate API). There is no unified workflow that ties these together, and no structured way to search for optimal model configurations. The existing `QlibTrainer` computes only basic metrics (IC, estimated Sharpe from predictions) which don't reflect actual trading performance. The existing `AsyncBacktestEngine` and `QlibModelStrategy` already support running backtests with Qlib models, but they're only accessible via API — the training script can't directly invoke them.

Current architecture:
- `QlibBinConverter`: MongoDB → Qlib binary format (incremental/full)
- `QlibTrainer`: Trains LGBModel/PytorchMLP with Alpha158/Alpha360, computes basic metrics
- `QlibPredictor`: Uses trained models for stock selection
- `ModelManager`: Stores models (pickle + MongoDB metadata in `qlib_models` collection)
- `AsyncBacktestEngine`: Runs backtests with `QlibModelStrategy` or other strategies
- `RiskMetricsCalculator`: Computes Sharpe, max drawdown, win rate, etc. from backtest results

Stock pools: CSI 300 list exists in `config.py`. CSI 500 is not yet available.

## Goals / Non-Goals

**Goals:**
- Create a `train_eval.py` script that executes: data sync → training → IC evaluation → backtest validation in one invocation
- Support parameter search with multiple values per hyperparameter, training each combination serially
- Implement early termination: `--min-ic` to skip backtesting for low-IC models, `--target-sharpe` to stop search when a model reaches the target backtested Sharpe
- Record every experiment (config + training metrics + backtest results) in a MongoDB `experiments` collection for comparison and reproducibility
- Add CSI 500 stock list to `config.py`
- Enrich training evaluation with rank IC, ICIR, and group returns (long-short)

**Non-Goals:**
- Parallel training of multiple parameter combinations (serial only for now)
- Bayesian optimization or smart parameter search (user specifies combinations explicitly)
- Web UI for experiment management (CLI only)
- Modifying the existing API endpoints (script calls Python classes directly)
- Real-time or intraday training pipeline
- Auto-tuning or hyperparameter optimization algorithms

## Decisions

### D1: Script directly imports Python classes, not HTTP API calls

**Decision**: `train_eval.py` will directly import `QlibBinConverter`, `QlibTrainer`, `ModelManager`, `AsyncBacktestEngine`, etc. — no HTTP requests.

**Rationale**: Eliminates network overhead, authentication complexity, and the need to run the API server during training. The API is just a thin wrapper around these classes anyway. This also makes debugging easier.

**Alternative considered**: Call API endpoints via `requests` — would test the full stack but adds unnecessary latency and complexity for a batch training script.

### D2: Synchronous backtest execution for the script

**Decision**: The script will call the backtest engine synchronously (not via `asyncio`). The `AsyncBacktestEngine.run_backtest()` is async, but the script will use `asyncio.run()` or a sync wrapper to call it.

**Rationale**: The script is a batch process — there's no benefit from async since we train and evaluate one configuration at a time serially. Using `asyncio.run()` keeps the script simple while still leveraging the existing engine.

**Alternative considered**: Rewrite a sync backtest engine — unnecessary duplication; the async engine works fine when called from `asyncio.run()`.

### D3: Experiment records stored in MongoDB `experiments` collection

**Decision**: Create a new `ExperimentTracker` class that writes to a MongoDB `experiments` collection. Each experiment record includes: experiment tag, full config (model type, factor, hyperparams, stock pool, date range), training metrics (IC, rank IC, ICIR, group returns), backtest results (Sharpe, annual return, max drawdown, total return), model_id reference, and timestamps.

**Rationale**: MongoDB is already in use. The `experiments` collection provides structured, queryable records that persist across script runs. This is better than CSV/file-based logging because it supports rich queries (e.g., "find all experiments where IC > 0.05").

**Alternative considered**: Write results to CSV — simpler but less queryable, harder to store nested structures like backtest metrics. Could be added as an export format later.

### D4: Training evaluation enrichment (IC, rank IC, ICIR, group returns)

**Decision**: Enhance `QlibTrainer._calculate_metrics()` to also compute rank IC, ICIR (mean IC / std IC over time periods), and 5-group long-short returns. These are standard qlib evaluation metrics that provide a more complete picture of model quality than IC alone.

**Rationale**: The `--min-ic` early termination filter needs a robust metric. Raw IC is noisy; rank IC and ICIR are more stable. Group long-short returns directly indicate whether the model's predictions translate to profitable trades, making it a natural pre-filter before running the full backtest.

**Alternative considered**: Use only IC for filtering — too noisy, would let through models that look okay on IC but can't actually generate alpha.

### D5: Backtest uses QlibModelStrategy with the trained model

**Decision**: After training completes, the script creates a `QlibModelStrategy(model_id=<trained_model_id>, topk=50)` and runs it through `AsyncBacktestEngine` over the test period dates.

**Rationale**: `QlibModelStrategy` already exists and is integrated with `QlibPredictor` for stock selection. The backtest engine already computes `RiskMetrics` including real Sharpe ratio, max drawdown, annual return. This is the same path the API uses, ensuring consistency.

**Alternative considered**: Write a custom evaluation loop that simulates trading — would duplicate the existing backtest engine's logic unnecessarily.

### D6: CSI 500 stock list from baostock

**Decision**: Add a `CSI_500_STOCKS` list to `config.py`, similar to `CSI_300_STOCKS`. Since the list is large (500 stocks), fetch it from baostock API at config time or hardcode a recent snapshot.

**Rationale**: The user explicitly requested both 沪深300 and 中证500 as stock pool options. CSI 300 already exists; CSI 500 needs to be added. Given the list changes periodically, hardcoding a recent snapshot is pragmatic (same approach as CSI 300).

**Alternative considered**: Fetch dynamically from an API at runtime — adds latency and a dependency on external service availability. Hardcoding with periodic updates is simpler and matches the existing pattern.

### D7: Parameter search via Cartesian product of user-specified values

**Decision**: The script accepts multiple values per parameter (e.g., `--lgbm-n-estimators 500,1000,2000`), computes the Cartesian product of all parameter lists, and trains each combination serially.

**Rationale**: This is the simplest and most transparent approach. The user explicitly controls what combinations to try. No magic, no hidden algorithms.

**Alternative considered**: Grid search with automatic range generation — too opinionated, user loses control of exactly which combinations run.

## Risks / Trade-offs

- **[Long training time for large parameter grids]** → Mitigation: `--min-ic` early filter skips backtesting for unpromising models; `--target-sharpe` stops the entire search when goal is met. User controls grid size via parameter values.
- **[Backtest depends on Qlib data being synced]** → Mitigation: Script has `--sync-data` flag that runs `QlibBinConverter.incremental_sync()` before training. If skipped, user is responsible for data freshness.
- **[CSI 500 stock list may become stale]** → Mitigation: Same risk as CSI 300 list. Periodic manual updates are acceptable. Can add a helper script to refresh the list later.
- **[Memory usage when training many models serially]** → Mitigation: Each model is trained, evaluated, saved, and references released before the next training. Python GC handles cleanup. LGBM is memory-efficient.
- **[QlibModelStrategy backtest may be slow for 300+ stocks]** → Mitigation: The existing backtest engine fetches data per-instrument. For 300 stocks × multi-year test period, this could take minutes. Acceptable for a batch script, but worth noting in documentation.
