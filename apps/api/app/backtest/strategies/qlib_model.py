"""Qlib Model Strategy

Uses trained Qlib models for stock selection.
"""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from .base import BaseStrategy, Signal, SignalType

logger = logging.getLogger(__name__)


class QlibModelStrategy(BaseStrategy):
    """Qlib Model-based Strategy.

    Loads a trained Qlib model and uses predictions for stock selection.
    Buy top-k stocks by prediction score.

    On first predict_stocks() call, creates the prediction DatasetH once
    and runs model.predict() to get all test-period predictions. Results
    are cached by date for O(1) lookup on subsequent calls.

    Parameters:
    model_id: Model identifier (required)
    topk: Number of top stocks to buy (default: 50)
    """

    is_portfolio_strategy = True

    def __init__(
        self,
        model_id: str,
        topk: int = 50,
        min_score: Optional[float] = None,
    ):
        if not model_id:
            raise ValueError("model_id is required")

        if topk < 1:
            raise ValueError(f"topk must be at least 1, got {topk}")

        self.model_id = model_id
        self.topk = topk
        self.min_score = min_score
        self._predictions_by_date: Optional[Dict[str, List[Dict[str, Any]]]] = None

    def _ensure_predictions_loaded(self, instruments: Optional[List[str]] = None):
        """Load all predictions once and cache by date."""
        if self._predictions_by_date is not None:
            return

        try:
            from app.qlib.model_manager import ModelManager
            from app.qlib.config import get_csi300_instruments, get_instruments

            if instruments is None:
                instruments = get_csi300_instruments()

            manager = ModelManager()
            load_result = manager.load_model(self.model_id, include_config=True)
            if load_result is None:
                logger.error(f"Model not found: {self.model_id}")
                self._predictions_by_date = {}
                return

            model, model_config = load_result

            import qlib
            from qlib.utils import init_instance_by_config
            from qlib.config import REG_CN
            from app.qlib.config import QlibConfig, get_factor_config

            if not hasattr(qlib, '_initialized') or not qlib._initialized:
                qlib.init(
                    provider_uri=QlibConfig.provider_uri,
                    region=REG_CN,
                    kernels=1,
                    verbose=False,
                )
                qlib._initialized = True

            pool_name = model_config.get("instruments", "csi300")
            if isinstance(pool_name, str):
                try:
                    pool_instruments = get_instruments(pool_name)
                except ValueError:
                    pool_instruments = instruments
            else:
                pool_instruments = model_config.get("instruments", instruments)

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
                            "instruments": pool_instruments,
                        },
                    },
                    "segments": {
                        "train": (start_time, "2022-12-31"),
                        "valid": ("2023-01-01", "2024-06-30"),
                        "test": ("2024-07-01", end_time),
                    },
                },
            }

            logger.info("Creating prediction dataset (one-time)...")
            dataset = init_instance_by_config(dataset_config)

            logger.info("Running model.predict() on test segment...")
            all_predictions = model.predict(dataset)

            self._predictions_by_date = {}
            if isinstance(all_predictions, pd.Series) and isinstance(all_predictions.index, pd.MultiIndex):
                for date in all_predictions.index.get_level_values(0).unique():
                    try:
                        day_scores = all_predictions.loc[date]
                        if isinstance(day_scores, pd.Series):
                            sorted_scores = day_scores.sort_values(ascending=False)
                            top_stocks = sorted_scores.head(self.topk)
                            date_str = str(date)[:10]
                            preds = []
                            for rank, (instrument, score) in enumerate(top_stocks.items(), 1):
                                instrument_str = str(instrument)
                                if self.min_score is not None and float(score) < self.min_score:
                                    continue
                                preds.append({
                                    "code": instrument_str,
                                    "score": float(score),
                                    "rank": rank,
                                })
                            self._predictions_by_date[date_str] = preds
                    except Exception as e:
                        logger.warning(f"Error processing date {date}: {e}")
                        continue

            logger.info(
                f"Pre-computed predictions for {len(self._predictions_by_date)} dates"
            )

        except Exception as e:
            logger.error(f"Failed to load predictions: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self._predictions_by_date = {}

    def generate_signals(self, data: pd.DataFrame) -> Signal:
        """Generate trading signal based on Qlib model predictions.

        Note: This strategy is designed for multi-stock portfolio selection.
        When called with single stock data, it returns HOLD.
        Use predict_stocks() method for actual stock selection.

        Args:
            data: DataFrame with stock data

        Returns:
            Signal object (use predict_stocks for actual predictions)
        """
        return Signal(
            SignalType.HOLD,
            confidence=0.5,
            reason="Qlib strategy requires predict_stocks() for multi-stock selection",
            metadata={"model_id": self.model_id, "topk": self.topk}
        )

    def predict_stocks(
        self,
        instruments: Optional[List[str]] = None,
        date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Predict and rank stocks using the Qlib model.

        On first call, pre-computes all test-period predictions and caches
        them by date. Subsequent calls do O(1) date-keyed lookup.

        Args:
            instruments: List of stock codes (default: CSI 300)
            date: Prediction date (default: today)

        Returns:
            List of top-k stocks with scores and rankings
        """
        self._ensure_predictions_loaded(instruments)

        if self._predictions_by_date is None:
            return []

        if date is not None:
            date_key = str(date)[:10]
            result = self._predictions_by_date.get(date_key, [])
            if result:
                return result[:self.topk]

        if not self._predictions_by_date:
            logger.warning("No pre-computed predictions available")
            return []

        sorted_dates = sorted(self._predictions_by_date.keys())
        closest_date = None
        for d in sorted_dates:
            if d <= str(date)[:10]:
                closest_date = d
            else:
                break

        if closest_date:
            result = self._predictions_by_date[closest_date]
            logger.info(
                f"Qlib model {self.model_id}: using predictions from {closest_date} "
                f"for requested date {date} ({len(result)} stocks)"
            )
            return result[:self.topk]

        return []

    def get_buy_signals(
        self,
        instruments: Optional[List[str]] = None,
        date: Optional[str] = None,
    ) -> List[Signal]:
        """Get buy signals for top-k stocks.

        Args:
            instruments: List of stock codes
            date: Prediction date

        Returns:
            List of BUY signals for top stocks
        """
        predictions = self.predict_stocks(instruments, date)

        signals = []
        for pred in predictions:
            score = pred.get("score", 0)
            confidence = min(score + 0.5, 1.0) if score > 0 else 0.5

            signal = Signal(
                SignalType.BUY,
                confidence=confidence,
                reason=f"Ranked #{pred.get('rank', 0)} by Qlib model with score {score:.4f}",
                metadata={
                    "code": pred.get("code"),
                    "score": score,
                    "rank": pred.get("rank"),
                    "model_id": self.model_id,
                }
            )
            signals.append(signal)

        return signals

    def get_name(self) -> str:
        return f"Qlib Model Strategy ({self.model_id})"

    def get_params(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "topk": self.topk,
            "min_score": self.min_score,
        }

    def get_required_data_points(self) -> int:
        return 1
