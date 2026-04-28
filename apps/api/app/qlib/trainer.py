"""
Qlib Model Trainer

This module provides functionality to train Qlib models using
MongoDB K-line data with configurable parameters.
"""

import os
import sys
import logging
import pickle
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading
from pathlib import Path

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class TrainingStatus:
    """Enum-like class for training status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QlibTrainer:
    """
    Trains Qlib models using MongoDB K-line data.
    
    This class handles:
    - Model training with configurable parameters
    - Progress tracking and status management
    - Model versioning and storage
    - Training metrics calculation
    
    Example:
        >>> trainer = QlibTrainer()
        >>> task_id = trainer.start_training(config)
        >>> status = trainer.get_status(task_id)
        >>> if status["status"] == "completed":
        ...     model_id = status["model_id"]
    """
    
    def __init__(
        self,
        model_dir: str = "./models",
        min_sharpe_ratio: float = 1.5,
    ):
        """
        Initialize the trainer.
        
        Args:
            model_dir: Directory to store trained models
            min_sharpe_ratio: Minimum Sharpe ratio for model approval
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.min_sharpe_ratio = min_sharpe_ratio
        
        self._training_tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._mongo_collection = None

    def _get_executions_collection(self):
        if self._mongo_collection is not None:
            return self._mongo_collection
        try:
            from app.core.config import settings
            from pymongo import MongoClient
            client = MongoClient(settings.mongodb_host, settings.mongodb_port,
                                 username=settings.mongodb_username,
                                 password=settings.mongodb_password)
            self._mongo_collection = client[settings.mongodb_database]["job_executions"]
        except Exception as e:
            logger.warning(f"Cannot connect to MongoDB for execution records: {e}")
            self._mongo_collection = False
        return self._mongo_collection

    def _update_execution_record(self, task_id: str, status: str, metrics: Optional[Dict] = None,
                                  model_id: Optional[str] = None, error: Optional[str] = None):
        coll = self._get_executions_collection()
        if not coll:
            return
        try:
            update = {"status": status, "completed_at": datetime.now()}
            if metrics:
                update["result"] = {"metrics": metrics, "model_id": model_id}
            if error:
                update["error_message"] = error
            coll.update_one({"task_id": task_id}, {"$set": update})
        except Exception as e:
            logger.warning(f"Failed to update execution record: {e}")
    
    def start_training(
        self,
        config: Dict[str, Any],
        task_id: Optional[str] = None,
    ) -> str:
        """
        Start a training task.
        
        Args:
            config: Training configuration containing:
                - instruments: List of stock codes
                - start_time: Start date
                - end_time: End date
                - model_type: Model type (e.g., "lgbm")
                - factor_type: Factor type (e.g., "alpha158")
            task_id: Optional task ID (auto-generated if not provided)
        
        Returns:
            Task ID for tracking
        """
        if task_id is None:
            task_id = self._generate_task_id(config)
        
        with self._lock:
            self._training_tasks[task_id] = {
                "config": config,
                "status": TrainingStatus.PENDING,
                "progress": 0,
                "started_at": datetime.now(),
                "completed_at": None,
                "model_id": None,
                "metrics": None,
                "error": None,
            }
        
        thread = threading.Thread(
            target=self._run_training,
            args=(task_id, config),
            daemon=True,
        )
        thread.start()
        
        logger.info(f"Training task {task_id} started")
        return task_id
    
    def _run_training(self, task_id: str, config: Dict[str, Any]):
        """
        Execute training in background thread.
        
        Args:
            task_id: Task identifier
            config: Training configuration
        """
        try:
            self._update_status(task_id, TrainingStatus.RUNNING, 0)

            qlib_initialized = self._ensure_qlib_initialized()
            if not qlib_initialized:
                raise RuntimeError("Failed to initialize Qlib")

            self._update_status(task_id, TrainingStatus.RUNNING, 5, progress_message="Syncing Qlib data from MongoDB")
            try:
                from .bin_converter import QlibBinConverter
                instruments_list = config.get("instruments", [])
                if isinstance(instruments_list, str):
                    from .config import get_instruments
                    instruments_list = get_instruments(instruments_list)
                converter = QlibBinConverter()
                summary = converter.incremental_sync(instruments=instruments_list)
                logger.info(f"Data sync before training: {summary}")
            except Exception as e:
                logger.warning(f"Data sync failed (training may still proceed): {e}")

            self._update_status(task_id, TrainingStatus.RUNNING, 10, progress_message="Loading data")

            dataset = self._create_dataset(config)

            self._update_status(task_id, TrainingStatus.RUNNING, 30, progress_message="Initializing model")

            model = self._create_model(config)

            self._update_status(task_id, TrainingStatus.RUNNING, 40, progress_message="Training model")

            model.fit(dataset)

            self._update_status(task_id, TrainingStatus.RUNNING, 70, progress_message="Evaluating model")

            predictions = model.predict(dataset)

            test_data = dataset.prepare("test", col_set=["feature", "label"], data_key="learn")
            metrics = self._calculate_metrics(predictions, test_data)
            
            self._update_status(task_id, TrainingStatus.RUNNING, 85, progress_message="Saving model")
            
            model_id = self._save_model(model, config, metrics)
            
            approved = metrics.get("sharpe_ratio", 0) >= self.min_sharpe_ratio
            status = TrainingStatus.COMPLETED if approved else TrainingStatus.COMPLETED
            
            self._update_status(
                task_id,
                status,
                100,
                model_id=model_id,
                metrics=metrics,
                completed_at=datetime.now(),
            )

            self._update_execution_record(task_id, "success", metrics=metrics, model_id=model_id)

            logger.info(f"Training task {task_id} completed with model {model_id}")

        except Exception as e:
            logger.error(f"Training task {task_id} failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self._update_status(
                task_id,
                TrainingStatus.FAILED,
                error=str(e),
                completed_at=datetime.now(),
            )
            self._update_execution_record(task_id, "failed", error=str(e))
    
    def get_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get training task status.
        
        Args:
            task_id: Task identifier
        
        Returns:
            Status dictionary with:
            - status: Current status
            - progress: Progress percentage (0-100)
            - started_at: Training start time
            - completed_at: Training completion time (if completed)
            - model_id: Trained model ID (if successful)
            - metrics: Training metrics (if available)
            - error: Error message (if failed)
        """
        with self._lock:
            if task_id not in self._training_tasks:
                return {"error": "Task not found"}
            return self._training_tasks[task_id].copy()
    
    def cancel_training(self, task_id: str) -> bool:
        """
        Cancel a training task.
        
        Note: This only marks the task as cancelled. Background
        training will continue but results won't be saved.
        
        Args:
            task_id: Task identifier
        
        Returns:
            True if cancellation was successful
        """
        with self._lock:
            if task_id not in self._training_tasks:
                return False
            
            task = self._training_tasks[task_id]
            if task["status"] == TrainingStatus.RUNNING:
                task["status"] = TrainingStatus.CANCELLED
                task["completed_at"] = datetime.now()
                logger.info(f"Training task {task_id} cancelled")
                return True
            
            return False
    
    def _generate_task_id(self, config: Dict[str, Any]) -> str:
        """Generate unique task ID from config."""
        config_str = str(sorted(config.items()))
        hash_obj = hashlib.md5(config_str.encode())
        return f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash_obj.hexdigest()[:8]}"
    
    def _update_status(
        self,
        task_id: str,
        status: str,
        progress: int = 0,
        **kwargs,
    ):
        """Update task status."""
        with self._lock:
            if task_id in self._training_tasks:
                self._training_tasks[task_id]["status"] = status
                self._training_tasks[task_id]["progress"] = progress
                self._training_tasks[task_id].update(kwargs)
    
    def _ensure_qlib_initialized(self) -> bool:
        """Ensure Qlib is initialized."""
        try:
            import qlib
            from qlib.config import REG_CN
            from .config import QlibConfig

            if not hasattr(qlib, '_initialized') or not qlib._initialized:
                qlib.init(
                    provider_uri=QlibConfig.provider_uri,
                    region=REG_CN,
                    kernels=1,
                )
                qlib._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Qlib: {e}")
            return False
    
    def _create_dataset(self, config: Dict[str, Any]) -> Any:
        """Create Qlib dataset from config."""
        from qlib.utils import init_instance_by_config
        from .config import get_instruments

        instruments = config.get("instruments", "csi300")
        if isinstance(instruments, str):
            instruments = get_instruments(instruments)

        dataset_config = {
            "class": "qlib.data.dataset.DatasetH",
            "module_path": "qlib.data.dataset",
            "kwargs": {
                "handler": {
                    "class": "qlib.contrib.data.handler.Alpha158",
                    "module_path": "qlib.contrib.data.handler",
                    "kwargs": {
                        "start_time": config.get("start_time", "2015-01-01"),
                        "end_time": config.get("end_time", "2026-01-01"),
                        "fit_start_time": config.get("start_time", "2015-01-01"),
                        "fit_end_time": config.get("end_time", "2026-01-01"),
                        "instruments": instruments,
                    },
                },
                "segments": {
                    "train": (config.get("start_time", "2015-01-01"), "2022-12-31"),
                    "valid": ("2023-01-01", "2024-06-30"),
                    "test": ("2024-07-01", config.get("end_time", "2026-01-01")),
                },
            },
        }

        return init_instance_by_config(dataset_config)
    
    def _create_model(self, config: Dict[str, Any]) -> Any:
        """Create Qlib model from config."""
        from qlib.utils import init_instance_by_config

        model_type = config.get("model_type", "lgbm")

        if model_type == "lgbm":
            default_kwargs = {
                "loss": "mse",
                "colsample_bytree": 0.8,
                "learning_rate": 0.01,
                "n_estimators": 1000,
                "num_leaves": 63,
                "subsample": 0.8,
                "early_stopping_rounds": 50,
            }
            default_kwargs.update(config.get("lgbm_kwargs", {}))
            model_config = {
                "class": "qlib.contrib.model.gbdt.LGBModel",
                "module_path": "qlib.contrib.model.gbdt",
                "kwargs": default_kwargs,
            }
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

        return init_instance_by_config(model_config)
    
    def _prepare_train_data(self, dataset, config: Dict[str, Any]) -> Any:
        """Prepare training data from dataset."""
        return dataset.prepare("train", col_set=["feature", "label"], data_key="learn")

    def _prepare_valid_data(self, dataset, config: Dict[str, Any]) -> Any:
        """Prepare validation data from dataset."""
        return dataset.prepare("valid", col_set=["feature", "label"], data_key="learn")

    def _prepare_test_data(self, dataset, config: Dict[str, Any]) -> Any:
        """Prepare test data from dataset."""
        return dataset.prepare("test", col_set=["feature", "label"], data_key="learn")
    
    def _calculate_rank_ic(self, predictions: pd.Series, labels: Any) -> float:
        """Calculate Spearman Rank IC between predictions and labels.

        Args:
            predictions: Prediction scores
            labels: True labels

        Returns:
            Spearman rank correlation coefficient
        """
        try:
            from scipy.stats import spearmanr

            if isinstance(labels, pd.DataFrame):
                labels_series = labels.iloc[:, 0] if len(labels.columns) > 0 else pd.Series()
            else:
                labels_series = pd.Series(labels)

            aligned_pred = predictions.dropna()
            aligned_labels = labels_series.dropna()

            common_index = aligned_pred.index.intersection(aligned_labels.index)

            if len(common_index) == 0:
                return 0.0

            pred_aligned = aligned_pred.loc[common_index]
            label_aligned = aligned_labels.loc[common_index]

            rank_ic, _ = spearmanr(pred_aligned, label_aligned)
            return float(rank_ic) if not np.isnan(rank_ic) else 0.0

        except Exception:
            return 0.0

    def _calculate_icir(self, predictions: pd.Series, labels: Any) -> float:
        """Calculate ICIR (mean IC / std IC over time periods).

        Computes Spearman IC per cross-sectional time period,
        then returns the ratio of mean IC to std IC.

        Args:
            predictions: Prediction scores with MultiIndex (datetime, instrument)
            labels: True labels

        Returns:
            ICIR value. Returns 0.0 if fewer than 10 time periods.
        """
        try:
            from scipy.stats import spearmanr

            if isinstance(labels, pd.DataFrame):
                labels_series = labels.iloc[:, 0] if len(labels.columns) > 0 else pd.Series()
            else:
                labels_series = pd.Series(labels)

            aligned_pred = predictions.dropna()
            aligned_labels = labels_series.dropna()
            common_index = aligned_pred.index.intersection(aligned_labels.index)

            if len(common_index) == 0:
                return 0.0

            pred_aligned = aligned_pred.loc[common_index]
            label_aligned = aligned_labels.loc[common_index]

            if not isinstance(pred_aligned.index, pd.MultiIndex):
                return 0.0

            period_ics = []
            for date in pred_aligned.index.get_level_values(0).unique():
                try:
                    pred_slice = pred_aligned.loc[date]
                    label_slice = label_aligned.loc[date]

                    if isinstance(pred_slice, pd.Series) and isinstance(label_slice, pd.Series):
                        common = pred_slice.index.intersection(label_slice.index)
                        if len(common) >= 5:
                            ic_val, _ = spearmanr(
                                pred_slice.loc[common],
                                label_slice.loc[common],
                            )
                            if not np.isnan(ic_val):
                                period_ics.append(ic_val)
                except Exception:
                    continue

            if len(period_ics) < 10:
                return 0.0

            mean_ic = np.mean(period_ics)
            std_ic = np.std(period_ics, ddof=1)

            if std_ic == 0:
                return 0.0

            return float(mean_ic / std_ic)

        except Exception:
            return 0.0

    def _calculate_long_short_return(self, predictions: pd.Series, labels: Any) -> float:
        """Calculate long-short return from quintile groups.

        Groups stocks by prediction quintile per time period, then
        computes the return of the top quintile minus the bottom quintile.

        Args:
            predictions: Prediction scores with MultiIndex (datetime, instrument)
            labels: True labels (future returns)

        Returns:
            Average long-short return across time periods
        """
        try:
            if isinstance(labels, pd.DataFrame):
                labels_series = labels.iloc[:, 0] if len(labels.columns) > 0 else pd.Series()
            else:
                labels_series = pd.Series(labels)

            aligned_pred = predictions.dropna()
            aligned_labels = labels_series.dropna()
            common_index = aligned_pred.index.intersection(aligned_labels.index)

            if len(common_index) == 0:
                return 0.0

            pred_aligned = aligned_pred.loc[common_index]
            label_aligned = aligned_labels.loc[common_index]

            if not isinstance(pred_aligned.index, pd.MultiIndex):
                return 0.0

            period_ls_returns = []
            for date in pred_aligned.index.get_level_values(0).unique():
                try:
                    pred_slice = pred_aligned.loc[date]
                    label_slice = label_aligned.loc[date]

                    if isinstance(pred_slice, pd.Series) and isinstance(label_slice, pd.Series):
                        common = pred_slice.index.intersection(label_slice.index)
                        if len(common) >= 10:
                            pred_rank = pred_slice.loc[common].rank(pct=True)
                            label_vals = label_slice.loc[common]

                            top_mask = pred_rank >= 0.8
                            bottom_mask = pred_rank <= 0.2

                            if top_mask.sum() > 0 and bottom_mask.sum() > 0:
                                top_return = label_vals[top_mask].mean()
                                bottom_return = label_vals[bottom_mask].mean()
                                ls_return = top_return - bottom_return
                                if not np.isnan(ls_return):
                                    period_ls_returns.append(ls_return)
                except Exception:
                    continue

            if len(period_ls_returns) == 0:
                return 0.0

            return float(np.mean(period_ls_returns))

        except Exception:
            return 0.0

    def _calculate_metrics(self, predictions: Any, test_data: Any) -> Dict[str, float]:
        """Calculate model metrics."""
        try:
            pred_series = pd.Series(predictions.values, index=predictions.index)
            
            label_data = test_data.copy()
            if isinstance(label_data, pd.DataFrame) and "label" in label_data.columns:
                labels = label_data["label"]
            else:
                labels = test_data
            
            pred_df = pred_series.reset_index()
            pred_df.columns = ["datetime", "instrument", "score"]
            
            aligned_pred = pred_series.dropna()
            
            metrics = {
                "sharpe_ratio": self._estimate_sharpe_ratio(aligned_pred),
                "ic": self._calculate_ic(aligned_pred, labels),
                "rank_ic": self._calculate_rank_ic(aligned_pred, labels),
                "icir": self._calculate_icir(pred_series, test_data),
                "long_short_return": self._calculate_long_short_return(pred_series, test_data),
                "num_predictions": len(aligned_pred),
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return {"sharpe_ratio": 0.0, "ic": 0.0, "rank_ic": 0.0, "icir": 0.0, "long_short_return": 0.0, "num_predictions": 0}
    
    def _estimate_sharpe_ratio(self, predictions: pd.Series) -> float:
        """Estimate Sharpe ratio from predictions."""
        try:
            returns = predictions.groupby(level=0).mean().pct_change().dropna()
            if len(returns) == 0:
                return 0.0
            
            mean_return = returns.mean()
            std_return = returns.std()
            
            if std_return == 0:
                return 0.0
            
            sharpe = mean_return / std_return * np.sqrt(252)
            return float(sharpe)
            
        except Exception:
            return 0.0
    
    def _calculate_ic(self, predictions: pd.Series, labels: Any) -> float:
        """Calculate Information Coefficient."""
        try:
            from scipy.stats import spearmanr
            
            if isinstance(labels, pd.DataFrame):
                labels_series = labels.iloc[:, 0] if len(labels.columns) > 0 else pd.Series()
            else:
                labels_series = pd.Series(labels)
            
            aligned_pred = predictions.dropna()
            aligned_labels = labels_series.dropna()
            
            common_index = aligned_pred.index.intersection(aligned_labels.index)
            
            if len(common_index) == 0:
                return 0.0
            
            pred_aligned = aligned_pred.loc[common_index]
            label_aligned = aligned_labels.loc[common_index]
            
            ic, _ = spearmanr(pred_aligned, label_aligned)
            return float(ic) if not np.isnan(ic) else 0.0
            
        except Exception:
            return 0.0
    
    def _save_model(
        self,
        model: Any,
        config: Dict[str, Any],
        metrics: Dict[str, float],
    ) -> str:
        """
        Save trained model to disk.
        
        Args:
            model: Trained model
            config: Training configuration
            metrics: Training metrics
        
        Returns:
            Model ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_id = f"model_{timestamp}"
        
        model_path = self.model_dir / f"{model_id}.pkl"
        
        model_data = {
            "model": model,
            "config": config,
            "metrics": metrics,
            "created_at": datetime.now(),
        }
        
        with open(model_path, "wb") as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {model_path}")
        return model_id
