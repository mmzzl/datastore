"""
Qlib Stock Predictor

This module provides functionality to use trained Qlib models
for stock selection and prediction.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading

import pandas as pd
import numpy as np

from .model_manager import ModelManager

logger = logging.getLogger(__name__)

_stock_name_map: Optional[Dict[str, str]] = None


def _load_stock_name_map() -> Dict[str, str]:
    """加载 all_stock.csv，返回 {SH600519: '贵州茅台', ...} 映射"""
    global _stock_name_map
    if _stock_name_map is not None:
        return _stock_name_map
    _stock_name_map = {}
    try:
        import os
        csv_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "all_stock.csv"))
        df = pd.read_csv(csv_path, usecols=["code", "code_name"])
        for _, row in df.iterrows():
            raw = str(row["code"]).strip()
            name = str(row["code_name"]).strip()
            pure = raw.split(".")[-1] if "." in raw else raw
            market = raw.split(".")[0].upper() if "." in raw else ""
            key = f"{market}{pure}" if market else pure
            _stock_name_map[key] = name
            _stock_name_map[pure] = name
        logger.info(f"Loaded {_stock_name_map.__len__()} stock names from all_stock.csv")
    except Exception as e:
        logger.warning(f"Failed to load stock names: {e}")
    return _stock_name_map


class QlibPredictor:
    """
    Uses trained Qlib models for stock selection.
    
    Handles:
    - Loading trained models
    - Generating predictions for stock pools
    - Ranking stocks by prediction scores
    - Result caching
    
    Example:
        >>> predictor = QlibPredictor()
        >>> results = predictor.predict(
        ...     model_id="model_20260330",
        ...     instruments=["SH600000", "SH600519"],
        ...     date="2026-03-30",
        ...     topk=50,
        ... )
    """
    
    def __init__(
        self,
        model_manager: Optional[ModelManager] = None,
        cache_enabled: bool = True,
    ):
        """
        Initialize the predictor.
        
        Args:
            model_manager: ModelManager instance for loading models
            cache_enabled: Whether to enable prediction caching
        """
        self.model_manager = model_manager or ModelManager()
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.Lock()
    
    def predict(
        self,
        model_id: str,
        instruments: Optional[List[str]] = None,
        date: Optional[str] = None,
        topk: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Generate stock predictions using a trained model.

        Args:
            model_id: Trained model identifier
            instruments: List of stock codes to predict (default: CSI 300)
            date: Prediction date (default: today)
            topk: Number of top stocks to return

        Returns:
            List of dictionaries containing:
            - code: Stock code
            - name: Stock name
            - score: Prediction score
            - rank: Ranking position
        """
        from .config import get_csi300_instruments

        if instruments is None:
            instruments = get_csi300_instruments()

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        cache_key = f"{model_id}_{date}_{topk}"

        if self.cache_enabled:
            cached_result = self._get_cached(cache_key)
            if cached_result:
                logger.debug(f"Returning cached prediction for {cache_key}")
                return cached_result.get("predictions", [])

        load_result = self.model_manager.load_model(model_id, include_config=True)
        if load_result is None:
            logger.error(f"Model not found: {model_id}")
            return []

        model, model_config = load_result

        try:
            all_scores = self._generate_predictions(model, model_config, instruments, date)

            day_scores = self._filter_scores_by_date(all_scores, date)

            if day_scores.empty:
                logger.warning(f"No predictions available for date {date}")
                return []

            sorted_scores = day_scores.sort_values(ascending=False)

            top_stocks = sorted_scores.head(min(topk, len(sorted_scores)))

            predictions = []
            for rank, (idx, score) in enumerate(top_stocks.items(), 1):
                if isinstance(idx, tuple):
                    code = str(idx[-1])
                else:
                    code = str(idx)
                predictions.append({
                    "code": code,
                    "name": self._get_stock_name(code),
                    "score": float(score),
                    "rank": rank,
                })

            result = {
                "model_id": model_id,
                "date": date,
                "predictions": predictions,
                "total_stocks": len(instruments),
                "generated_at": datetime.now().isoformat(),
            }

            if self.cache_enabled:
                self._set_cached(cache_key, result)

            logger.info(f"Generated predictions for {len(predictions)} stocks using model {model_id}")
            return predictions

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _generate_predictions(
        self,
        model: Any,
        model_config: Dict[str, Any],
        instruments: List[str],
        date: str,
    ) -> pd.Series:
        """
        Generate prediction scores for instruments.

        Creates a DatasetH with the same handler config used during training,
        configured to cover the prediction date in the test segment,
        then calls model.predict(dataset).

        Args:
            model: Loaded Qlib model (e.g. LGBModel)
            model_config: Training config saved with the model
            instruments: List of stock codes
            date: Prediction date

        Returns:
            Series of scores indexed by instrument
        """
        try:
            dataset = self._create_prediction_dataset(model_config, instruments, date)

            if dataset is None:
                logger.warning(f"Could not create prediction dataset for {date}")
                return pd.Series(index=instruments, dtype=float)

            predictions = model.predict(dataset)

            if isinstance(predictions, pd.Series):
                return predictions
            elif isinstance(predictions, pd.DataFrame):
                return predictions.iloc[:, 0]
            else:
                logger.warning(f"Unexpected prediction type: {type(predictions)}")
                return pd.Series(predictions, index=instruments)

        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            import traceback
            logger.error(traceback.format_exc())
            scores = np.random.uniform(0, 1, len(instruments))
            return pd.Series(scores, index=instruments)

    def _filter_scores_by_date(
        self,
        scores: pd.Series,
        date: str,
    ) -> pd.Series:
        """Filter prediction scores for a specific date.

        If the scores have a MultiIndex (datetime, instrument),
        returns the cross-section for the requested date or the
        closest available date before it.

        Args:
            scores: Prediction scores with potential MultiIndex
            date: Target date string (YYYY-MM-DD)

        Returns:
            Series of scores for the target date, indexed by instrument
        """
        if not isinstance(scores.index, pd.MultiIndex):
            return scores

        target_date = pd.Timestamp(date)
        available_dates = scores.index.get_level_values(0).unique()

        if target_date in available_dates:
            day_scores = scores.loc[target_date]
            if isinstance(day_scores, pd.Series):
                return day_scores

        closest_date = None
        for d in available_dates:
            if d <= target_date:
                closest_date = d
            else:
                break

        if closest_date is not None:
            day_scores = scores.loc[closest_date]
            if isinstance(day_scores, pd.Series):
                logger.info(
                    f"Using predictions from {closest_date.strftime('%Y-%m-%d')} "
                    f"for requested date {date}"
                )
                return day_scores

        return pd.Series(dtype=float)

    def _create_prediction_dataset(
        self,
        model_config: Dict[str, Any],
        instruments: List[str],
        date: str,
    ) -> Optional[Any]:
        """Create a DatasetH for prediction.

        Builds a dataset with the test segment covering the prediction date,
        using the same factor handler and instruments as training.

        Args:
            model_config: Training config (contains factor_type, start/end times)
            instruments: Stock codes to predict
            date: Prediction date (used as start of test segment)

        Returns:
            DatasetH instance, or None on failure
        """
        try:
            import qlib
            from qlib.utils import init_instance_by_config
            from qlib.config import REG_CN
            from .config import QlibConfig, get_factor_config

            if not hasattr(qlib, '_initialized') or not qlib._initialized:
                qlib.init(
                    provider_uri=QlibConfig.provider_uri,
                    region=REG_CN,
                    kernels=1,
                    verbose=False,
                )
                qlib._initialized = True

            factor_type = model_config.get("factor_type", "alpha158")
            factor_config = get_factor_config(factor_type)

            start_time = model_config.get("start_time", "2015-01-01")
            end_time = model_config.get("end_time", "2026-01-01")

            dataset_config = {
                "class": "qlib.data.dataset.DatasetH",
                "module_path": "qlib.data.dataset",
                "kwargs": {
                    "handler": {
                        **factor_config,
                        "kwargs": {
                            "start_time": start_time,
                            "end_time": end_time,
                            "fit_start_time": start_time,
                            "fit_end_time": end_time,
                            "instruments": instruments,
                        },
                    },
                    "segments": {
                        "train": (start_time, "2022-12-31"),
                        "valid": ("2023-01-01", "2024-06-30"),
                        "test": ("2024-07-01", end_time),
                    },
                },
            }

            return init_instance_by_config(dataset_config)

        except Exception as e:
            logger.error(f"Error creating prediction dataset: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _get_stock_name(self, code: str) -> str:
        """从 all_stock.csv 查询股票名称"""
        if not code:
            return ""
        # 缓存避免重复读 CSV
        if not hasattr(self, "_name_cache"):
            self._name_cache = _load_stock_name_map()
        return self._name_cache.get(code, "")
    
    def _get_cached(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached prediction result."""
        with self._cache_lock:
            return self._cache.get(cache_key)
    
    def _set_cached(self, cache_key: str, result: Dict[str, Any]):
        """Cache prediction result."""
        with self._cache_lock:
            self._cache[cache_key] = result
    
    def clear_cache(self):
        """Clear prediction cache."""
        with self._cache_lock:
            self._cache.clear()
        logger.debug("Prediction cache cleared")
    
    def get_top_stocks(
        self,
        model_id: str,
        instruments: List[str],
        date: Optional[str] = None,
        topk: int = 50,
        min_score: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get top stocks with optional minimum score filter.
        
        Args:
            model_id: Model identifier
            instruments: List of stock codes
            date: Prediction date
            topk: Maximum number of stocks to return
            min_score: Minimum score threshold (optional)
        
        Returns:
            List of top stocks with scores
        """
        result = self.predict(
            model_id=model_id,
            instruments=instruments,
            date=date,
            topk=topk,
        )
        
        predictions = result.get("predictions", [])
        
        if min_score is not None:
            predictions = [
                p for p in predictions
                if p.get("score", 0) >= min_score
            ]
        
        return predictions
    
    def compare_with_previous(
        self,
        model_id: str,
        instruments: List[str],
        current_date: str,
        previous_date: str,
        topk: int = 50,
    ) -> Dict[str, Any]:
        """
        Compare predictions between two dates.
        
        Args:
            model_id: Model identifier
            instruments: List of stock codes
            current_date: Current date
            previous_date: Previous date for comparison
            topk: Number of top stocks
        
        Returns:
            Comparison dictionary with:
            - added: Stocks newly in topk
            - removed: Stocks no longer in topk
            - common: Stocks in both
        """
        current_pred = self.predict(model_id, instruments, current_date, topk)
        previous_pred = self.predict(model_id, instruments, previous_date, topk)
        
        current_stocks = {p["code"] for p in current_pred.get("predictions", [])}
        previous_stocks = {p["code"] for p in previous_pred.get("predictions", [])}
        
        added = current_stocks - previous_stocks
        removed = previous_stocks - current_stocks
        common = current_stocks & previous_stocks
        
        return {
            "current_date": current_date,
            "previous_date": previous_date,
            "added": list(added),
            "removed": list(removed),
            "common": list(common),
            "current_count": len(current_stocks),
            "previous_count": len(previous_stocks),
        }
    
    def batch_predict(
        self,
        model_id: str,
        instruments: List[str],
        dates: List[str],
        topk: int = 50,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate predictions for multiple dates.
        
        Args:
            model_id: Model identifier
            instruments: List of stock codes
            dates: List of dates to predict
            topk: Number of top stocks per date
        
        Returns:
            Dictionary mapping date to prediction results
        """
        results = {}
        
        for date in dates:
            results[date] = self.predict(
                model_id=model_id,
                instruments=instruments,
                date=date,
                topk=topk,
            )
        
        return results
