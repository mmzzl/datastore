"""
Qlib Model Strategy

Uses trained Qlib models for stock selection.
"""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from .base import BaseStrategy, Signal, SignalType

logger = logging.getLogger(__name__)


class QlibModelStrategy(BaseStrategy):
    """
    Qlib Model-based Strategy.
    
    Loads a trained Qlib model and uses predictions for stock selection.
    Buy top-k stocks by prediction score.
    
    Parameters:
        model_id: Model identifier (required)
        topk: Number of top stocks to buy (default: 50)
    """
    
    def __init__(
        self,
        model_id: str,
        topk: int = 50,
        min_score: Optional[float] = None,
    ):
        """
        Initialize Qlib Model Strategy.
        
        Args:
            model_id: Qlib model identifier
            topk: Number of top stocks to select
            min_score: Minimum score threshold (optional)
        """
        if not model_id:
            raise ValueError("model_id is required")
        
        if topk < 1:
            raise ValueError(f"topk must be at least 1, got {topk}")
        
        self.model_id = model_id
        self.topk = topk
        self.min_score = min_score
        self._predictor = None
        self._model_manager = None
    
    def _get_predictor(self):
        """Get or create Qlib predictor instance."""
        if self._predictor is None:
            try:
                from app.qlib import QlibPredictor, ModelManager
                self._model_manager = ModelManager()
                self._predictor = QlibPredictor(model_manager=self._model_manager)
            except ImportError as e:
                logger.error(f"Failed to import Qlib modules: {e}")
                return None
        return self._predictor
    
    def generate_signals(self, data: pd.DataFrame) -> Signal:
        """
        Generate trading signal based on Qlib model predictions.
        
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
        """
        Predict and rank stocks using the Qlib model.
        
        Args:
            instruments: List of stock codes (default: CSI 300)
            date: Prediction date (default: today)
        
        Returns:
            List of top-k stocks with scores and rankings
        """
        predictor = self._get_predictor()
        if predictor is None:
            logger.error("Qlib predictor not available")
            return []
        
        try:
            predictions = predictor.predict(
                model_id=self.model_id,
                instruments=instruments,
                date=date,
                topk=self.topk,
            )
            
            if self.min_score is not None:
                predictions = [
                    p for p in predictions
                    if p.get("score", 0) >= self.min_score
                ]
            
            logger.info(f"Qlib model {self.model_id} selected {len(predictions)} stocks")
            return predictions
            
        except Exception as e:
            logger.error(f"Qlib prediction failed: {e}")
            return []
    
    def get_buy_signals(
        self,
        instruments: Optional[List[str]] = None,
        date: Optional[str] = None,
    ) -> List[Signal]:
        """
        Get buy signals for top-k stocks.
        
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
                    "name": pred.get("name"),
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
