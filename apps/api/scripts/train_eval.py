"""
Train-Evaluate-Backtest Pipeline Script.

Executes the full ML model lifecycle:
  1. Sync Qlib data from MongoDB (optional)
  2. Train a Qlib model with specified parameters
  3. Evaluate training metrics (IC, rank IC, ICIR, group returns)
  4. Run backtest with the trained model
  5. Record experiment results in MongoDB

Supports parameter search via Cartesian product of comma-separated
hyperparameter values, with early termination by --min-ic and
--target-sharpe thresholds.

Usage:
  py -3.12 train_eval.py --model lgbm --factor alpha158 --instruments csi300 --tag my_exp
  py -3.12 train_eval.py --model lgbm --lgbm-n-estimators 500,1000 --min-ic 0.03 --tag grid
"""

import argparse
import asyncio
import itertools
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class ExperimentResult:
    experiment_id: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    training_metrics: Optional[Dict[str, Any]] = None
    backtest_result: Optional[Dict[str, Any]] = None
    model_id: Optional[str] = None
    status: str = "pending"
    error: Optional[str] = None


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train-Evaluate-Backtest Pipeline for Qlib models",
    )

    parser.add_argument("--model", default="lgbm", choices=["lgbm", "mlp"],
                        help="Model type (default: lgbm)")
    parser.add_argument("--factor", default="alpha158", choices=["alpha158", "alpha360"],
                        help="Factor type (default: alpha158)")
    parser.add_argument("--instruments", default="csi300", choices=["csi300", "csi500"],
                        help="Stock pool (default: csi300)")
    parser.add_argument("--start", default="2015-01-01",
                        help="Training data start date (default: 2015-01-01)")
    parser.add_argument("--end", default="2026-01-01",
                        help="Training data end date (default: 2026-01-01)")
    parser.add_argument("--sync-data", action="store_true",
                        help="Run QlibBinConverter.incremental_sync() before training")
    parser.add_argument("--min-ic", type=float, default=0.02,
                        help="Minimum rank IC to proceed to backtest (default: 0.02)")
    parser.add_argument("--target-sharpe", type=float, default=None,
                        help="Stop search when backtested Sharpe >= this value (default: disabled)")
    parser.add_argument("--tag", default=None,
                        help="Tag for grouping experiments")

    parser.add_argument("--lgbm-n-estimators", default=None,
                        help="Comma-separated n_estimators values (e.g., 500,1000)")
    parser.add_argument("--lgbm-lr", default=None,
                        help="Comma-separated learning_rate values (e.g., 0.01,0.005)")
    parser.add_argument("--lgbm-num-leaves", default=None,
                        help="Comma-separated num_leaves values (e.g., 31,63)")
    parser.add_argument("--lgbm-subsample", default=None,
                        help="Comma-separated subsample values (e.g., 0.8,0.9)")
    parser.add_argument("--lgbm-colsample-bytree", default=None,
                        help="Comma-separated colsample_bytree values")
    parser.add_argument("--mlp-hidden-sizes", default=None,
                        help="Comma-separated hidden size configs (e.g., 256-128-64,128-64)")
    parser.add_argument("--mlp-lr", default=None,
                        help="Comma-separated MLP learning rates")
    parser.add_argument("--mlp-batch-size", default=None,
                        help="Comma-separated batch sizes")
    parser.add_argument("--mlp-epochs", default=None,
                        help="Comma-separated epoch counts")

    parser.add_argument("--topk", type=int, default=50,
                        help="Top-K stocks for QlibModelStrategy (default: 50)")

    return parser.parse_args(argv)


def _parse_comma_values(value_str: Optional[str]) -> List[Any]:
    if value_str is None:
        return []
    parts = [v.strip() for v in value_str.split(",") if v.strip()]
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            try:
                result.append(float(p))
            except ValueError:
                result.append(p)
    return result


def build_param_grid(args: argparse.Namespace) -> List[Dict[str, Any]]:
    param_lists: Dict[str, List[Any]] = {}

    lgbm_n = _parse_comma_values(args.lgbm_n_estimators)
    lgbm_lr = _parse_comma_values(args.lgbm_lr)
    lgbm_leaves = _parse_comma_values(args.lgbm_num_leaves)
    lgbm_sub = _parse_comma_values(args.lgbm_subsample)
    lgbm_col = _parse_comma_values(args.lgbm_colsample_bytree)

    mlp_hidden = _parse_comma_values(args.mlp_hidden_sizes)
    mlp_lr = _parse_comma_values(args.mlp_lr)
    mlp_batch = _parse_comma_values(args.mlp_batch_size)
    mlp_epochs = _parse_comma_values(args.mlp_epochs)

    if args.model == "lgbm":
        if lgbm_n:
            param_lists["n_estimators"] = lgbm_n
        if lgbm_lr:
            param_lists["learning_rate"] = lgbm_lr
        if lgbm_leaves:
            param_lists["num_leaves"] = lgbm_leaves
        if lgbm_sub:
            param_lists["subsample"] = lgbm_sub
        if lgbm_col:
            param_lists["colsample_bytree"] = lgbm_col
    elif args.model == "mlp":
        if mlp_hidden:
            param_lists["hidden_sizes"] = mlp_hidden
        if mlp_lr:
            param_lists["lr"] = mlp_lr
        if mlp_batch:
            param_lists["batch_size"] = mlp_batch
        if mlp_epochs:
            param_lists["epochs"] = mlp_epochs

    if not param_lists:
        return [{}]

    keys = sorted(param_lists.keys())
    values = [param_lists[k] for k in keys]
    combinations = list(itertools.product(*values))

    grid = []
    for combo in combinations:
        grid.append({k: v for k, v in zip(keys, combo)})
    return grid


def build_training_config(
    args: argparse.Namespace,
    hyperparams: Dict[str, Any],
) -> Dict[str, Any]:
    from app.qlib.config import get_instruments

    instruments = get_instruments(args.instruments)

    config = {
        "model_type": args.model,
        "factor_type": args.factor,
        "instruments": instruments,
        "start_time": args.start,
        "end_time": args.end,
    }

    if args.model == "lgbm":
        config["lgbm_kwargs"] = {
            "loss": "mse",
            "colsample_bytree": hyperparams.get("colsample_bytree", 0.8),
            "learning_rate": hyperparams.get("learning_rate", 0.01),
            "n_estimators": hyperparams.get("n_estimators", 1000),
            "num_leaves": hyperparams.get("num_leaves", 63),
            "subsample": hyperparams.get("subsample", 0.8),
            "early_stopping_rounds": 50,
        }
    elif args.model == "mlp":
        hidden = hyperparams.get("hidden_sizes", "256-128-64")
        if isinstance(hidden, str):
            hidden_sizes = [int(x) for x in hidden.split("-")]
        else:
            hidden_sizes = [int(x) for x in str(hidden).split("-")]
        config["mlp_kwargs"] = {
            "hidden_sizes": hidden_sizes,
            "lr": hyperparams.get("lr", 0.001),
            "batch_size": hyperparams.get("batch_size", 4096),
            "epochs": hyperparams.get("epochs", 100),
        }

    config["hyperparams"] = hyperparams
    return config


def sync_data() -> Dict[str, Any]:
    logger.info("Step 1: Syncing Qlib data from MongoDB...")
    from app.qlib.bin_converter import QlibBinConverter

    converter = QlibBinConverter()
    summary = converter.incremental_sync()
    logger.info(f"Data sync complete: {summary}")
    return summary


def train_model(config: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("Step 2: Training model...")
    from app.qlib.trainer import QlibTrainer, TrainingStatus

    trainer = QlibTrainer()
    task_id = trainer.start_training(config)

    logger.info(f"Training task started: {task_id}")
    timeout = 3600
    start = time.time()
    while time.time() - start < timeout:
        status = trainer.get_status(task_id)
        current = status.get("status", "unknown")
        progress = status.get("progress", 0)
        if current in (TrainingStatus.COMPLETED, TrainingStatus.FAILED, TrainingStatus.CANCELLED):
            break
        logger.info(f"Training progress: {progress}% (status={current})")
        time.sleep(10)

    final = trainer.get_status(task_id)
    if final.get("status") != TrainingStatus.COMPLETED:
        error = final.get("error", "Training did not complete")
        raise RuntimeError(f"Training failed: {error}")

    model_id = final.get("model_id")
    metrics = final.get("metrics", {})
    logger.info(f"Training complete: model_id={model_id}, metrics={metrics}")
    return {"model_id": model_id, "metrics": metrics}


def evaluate_model(
    training_metrics: Dict[str, Any],
    min_ic: float,
) -> bool:
    rank_ic = training_metrics.get("rank_ic", 0.0)
    if rank_ic < min_ic:
        logger.info(
            f"Step 3: Evaluation - rank_ic={rank_ic:.4f} < min_ic={min_ic:.4f}, skipping backtest"
        )
        return False
    logger.info(f"Step 3: Evaluation - rank_ic={rank_ic:.4f} >= min_ic={min_ic:.4f}, proceeding to backtest")
    return True


def run_backtest(
    model_id: str,
    config: Dict[str, Any],
    topk: int = 50,
) -> Dict[str, Any]:
    logger.info(f"Step 4: Running backtest for model {model_id}...")
    from app.backtest.async_engine import AsyncBacktestEngine
    from app.qlib.config import get_instruments

    instruments = config.get("instruments")
    if isinstance(instruments, str):
        instruments = get_instruments(instruments)

    bt_config = {
        "strategy": "qlib_model",
        "params": {
            "model_id": model_id,
            "topk": topk,
        },
        "start_date": "2024-07-01",
        "end_date": config.get("end_time", "2026-01-01"),
        "initial_capital": 1000000.0,
        "instruments": instruments,
        "commission_rate": 0.0003,
        "slippage": 0.0001,
    }

    engine = AsyncBacktestEngine()

    async def _run():
        task_id = await engine.run_backtest(bt_config)
        while True:
            status = await engine.get_status(task_id)
            if status.get("status") in ("completed", "failed", "cancelled"):
                return task_id, status
            await asyncio.sleep(5)

    task_id, status = asyncio.run(_run())

    if status.get("status") != "completed":
        error = status.get("error", "Backtest failed")
        raise RuntimeError(f"Backtest failed: {error}")

    result = engine.get_task_result(task_id)
    if result and result.metrics:
        from app.backtest.risk_metrics import RiskMetricsCalculator
        metrics_dict = RiskMetricsCalculator.to_dict(result.metrics)
        logger.info(f"Backtest complete: Sharpe={metrics_dict.get('sharpe_ratio', 0):.2f}, "
                     f"Return={metrics_dict.get('annual_return', 0):.2%}")
        return metrics_dict

    return {"sharpe_ratio": 0.0, "annual_return": 0.0, "max_drawdown": 0.0,
            "total_return": 0.0, "win_rate": 0.0, "total_trades": 0}


def record_experiment(
    tracker: Any,
    tag: Optional[str],
    config: Dict[str, Any],
    training_metrics: Optional[Dict[str, Any]],
    backtest_result: Optional[Dict[str, Any]],
    model_id: Optional[str],
    status: str,
    error: Optional[str] = None,
) -> str:
    logger.info(f"Step 5: Recording experiment (status={status})...")
    exp_id = tracker.record_experiment(
        tag=tag,
        config=config,
        training_metrics=training_metrics,
        backtest_result=backtest_result,
        model_id=model_id,
        status=status,
        error=error,
    )
    logger.info(f"Experiment recorded: {exp_id}")
    return exp_id


def print_comparison_table(results: List[ExperimentResult]) -> None:
    if not results:
        logger.info("No experiments to compare.")
        return

    header = (
        f"{'#':<4} {'Model':<8} {'Factor':<10} {'Hyperparams':<30} "
        f"{'RankIC':>8} {'ICIR':>8} {'LS-Ret':>8} "
        f"{'Sharpe':>8} {'AnnRet':>8} {'MaxDD':>8} {'Status':<18}"
    )
    sep = "-" * len(header)

    sorted_results = sorted(
        results,
        key=lambda r: (r.backtest_result or {}).get("sharpe_ratio", float("-inf")),
        reverse=True,
    )

    print("\n" + "=" * len(header))
    print("EXPERIMENT COMPARISON TABLE (sorted by backtested Sharpe)")
    print("=" * len(header))
    print(header)
    print(sep)

    best_idx = 0
    for i, r in enumerate(sorted_results):
        hp = r.config.get("hyperparams", {})
        hp_str = ", ".join(f"{k}={v}" for k, v in hp.items()) if hp else "defaults"

        tm = r.training_metrics or {}
        br = r.backtest_result or {}

        rank_ic = tm.get("rank_ic", 0.0)
        icir = tm.get("icir", 0.0)
        ls_ret = tm.get("long_short_return", 0.0)
        sharpe = br.get("sharpe_ratio", 0.0)
        ann_ret = br.get("annual_return", 0.0)
        max_dd = br.get("max_drawdown", 0.0)
        status = r.status

        model = r.config.get("model_type", "?")
        factor = r.config.get("factor_type", "?")

        line = (
            f"{i+1:<4} {model:<8} {factor:<10} {hp_str:<30} "
            f"{rank_ic:>8.4f} {icir:>8.4f} {ls_ret:>8.4f} "
            f"{sharpe:>8.2f} {ann_ret:>8.2%} {max_dd:>8.2%} {status:<18}"
        )

        if i == best_idx and status == "completed" and sharpe > 0:
            line = ">>> " + line + " <<< BEST"
        print(line)

    print(sep)
    if sorted_results and sorted_results[0].status == "completed":
        best = sorted_results[0]
        hp = best.config.get("hyperparams", {})
        hp_str = ", ".join(f"{k}={v}" for k, v in hp.items()) if hp else "defaults"
        br = best.backtest_result or {}
        print(f"\nBest configuration: {hp_str}")
        print(f"  Sharpe Ratio: {br.get('sharpe_ratio', 0):.4f}")
        print(f"  Annual Return: {br.get('annual_return', 0):.2%}")
        print(f"  Max Drawdown:  {br.get('max_drawdown', 0):.2%}")
        print(f"  Model ID:      {best.model_id}")
    print()


def run_pipeline(args: argparse.Namespace) -> List[ExperimentResult]:
    if args.sync_data:
        sync_data()

    param_grid = build_param_grid(args)
    total = len(param_grid)
    logger.info(f"Parameter search: {total} combination(s) to train")

    from app.experiment.tracker import ExperimentTracker
    tracker = ExperimentTracker()

    all_results: List[ExperimentResult] = []
    target_met = False

    for idx, hyperparams in enumerate(param_grid, 1):
        exp = ExperimentResult()
        logger.info(f"\n{'='*60}")
        logger.info(f"Combination {idx}/{total}: {hyperparams if hyperparams else 'defaults'}")
        logger.info(f"{'='*60}")

        config = build_training_config(args, hyperparams)
        exp.config = config

        try:
            train_result = train_model(config)
            exp.model_id = train_result["model_id"]
            exp.training_metrics = train_result["metrics"]

            if not evaluate_model(train_result["metrics"], args.min_ic):
                exp.status = "skipped_low_ic"
                exp_id = record_experiment(
                    tracker, args.tag, config,
                    train_result["metrics"], None,
                    train_result["model_id"], "skipped_low_ic",
                )
                exp.experiment_id = exp_id
                all_results.append(exp)
                continue

            backtest_metrics = run_backtest(
                train_result["model_id"], config, topk=args.topk,
            )
            exp.backtest_result = backtest_metrics
            exp.status = "completed"

            exp_id = record_experiment(
                tracker, args.tag, config,
                train_result["metrics"], backtest_metrics,
                train_result["model_id"], "completed",
            )
            exp.experiment_id = exp_id

            if args.target_sharpe is not None:
                sharpe = backtest_metrics.get("sharpe_ratio", 0.0)
                if sharpe >= args.target_sharpe:
                    logger.info(
                        f"Target Sharpe {args.target_sharpe} reached! "
                        f"(actual={sharpe:.4f}) Stopping search."
                    )
                    target_met = True
                    all_results.append(exp)
                    break

        except Exception as e:
            logger.error(f"Pipeline failed for combination {idx}: {e}")
            exp.status = "failed"
            exp.error = str(e)
            try:
                exp_id = record_experiment(
                    tracker, args.tag, config,
                    exp.training_metrics, None,
                    exp.model_id, "failed", error=str(e),
                )
                exp.experiment_id = exp_id
            except Exception as record_err:
                logger.error(f"Failed to record failed experiment: {record_err}")

        all_results.append(exp)

    if target_met:
        remaining = total - idx
        if remaining > 0:
            logger.info(f"Skipped {remaining} remaining combination(s) due to target-sharpe")

    try:
        tracker.close()
    except Exception:
        pass

    print_comparison_table(all_results)
    return all_results


def main():
    args = parse_args()
    logger.info(
        f"Train-Eval Pipeline: model={args.model}, factor={args.factor}, "
        f"instruments={args.instruments}, tag={args.tag}"
    )
    results = run_pipeline(args)
    completed = sum(1 for r in results if r.status == "completed")
    skipped = sum(1 for r in results if r.status == "skipped_low_ic")
    failed = sum(1 for r in results if r.status == "failed")
    logger.info(f"\nPipeline finished: {completed} completed, {skipped} skipped, {failed} failed")
    return results


if __name__ == "__main__":
    main()
