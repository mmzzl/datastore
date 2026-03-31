"""
Bollinger Bands Strategy

Generates buy/sell signals based on Bollinger Bands.
"""

import logging
from typing import Dict, Any
import pandas as pd
import numpy as np

from .base import BaseStrategy, Signal, SignalType

logger = logging.getLogger(__name__)


class BollingerStrategy(BaseStrategy):
    """
    Bollinger Bands Strategy.
    
    Buy when price < lower band.
    Sell when price > upper band.
    
    Parameters:
        period: Bollinger Band period (default: 20)
        num_std: Number of standard deviations (default: 2)
    """
    
    def __init__(self, period: int = 20, num_std: float = 2.0):
        """
        Initialize Bollinger Bands Strategy.
        
        Args:
            period: Period for moving average and std
            num_std: Number of standard deviations for bands
        """
        if period < 2:
            raise ValueError(f"period must be at least 2, got {period}")
        
        if num_std <= 0:
            raise ValueError(f"num_std must be positive, got {num_std}")
        
        self.period = period
        self.num_std = num_std
    
    def _calculate_bands(
        self,
        close: pd.Series,
    ) -> tuple:
        """
        Calculate Bollinger Bands.
        
        Args:
            close: Close price series
        
        Returns:
            Tuple of (middle_band, upper_band, lower_band)
        """
        middle_band = close.rolling(window=self.period).mean()
        std = close.rolling(window=self.period).std()
        
        upper_band = middle_band + (std * self.num_std)
        lower_band = middle_band - (std * self.num_std)
        
        return middle_band, upper_band, lower_band
    
    def generate_signals(self, data: pd.DataFrame) -> Signal:
        """
        Generate trading signal based on Bollinger Bands.
        
        Args:
            data: DataFrame with 'close' column
        
        Returns:
            Signal object with buy/sell/hold indication
        """
        if not self.validate_data(data):
            return Signal(SignalType.HOLD, confidence=0.0, reason="Invalid data")
        
        if len(data) < self.period + 1:
            return Signal(SignalType.HOLD, confidence=0.0, reason="Insufficient data")
        
        close = data["close"]
        middle, upper, lower = self._calculate_bands(close)
        
        if len(upper) < 1 or pd.isna(upper.iloc[-1]) or pd.isna(lower.iloc[-1]):
            return Signal(SignalType.HOLD, confidence=0.0, reason="Bollinger Bands calculation incomplete")
        
        current_price = close.iloc[-1]
        current_upper = upper.iloc[-1]
        current_lower = lower.iloc[-1]
        current_middle = middle.iloc[-1]
        
        bandwidth = (current_upper - current_lower) / current_middle if current_middle > 0 else 0
        
        if current_price < current_lower:
            distance = (current_lower - current_price) / current_lower
            confidence = min(0.5 + distance * 5, 1.0)
            return Signal(
                SignalType.BUY,
                confidence=confidence,
                reason=f"Price ({current_price:.2f}) below lower band ({current_lower:.2f})",
                metadata={
                    "price": current_price,
                    "upper": current_upper,
                    "lower": current_lower,
                    "middle": current_middle,
                    "bandwidth": bandwidth,
                }
            )
        
        if current_price > current_upper:
            distance = (current_price - current_upper) / current_upper
            confidence = min(0.5 + distance * 5, 1.0)
            return Signal(
                SignalType.SELL,
                confidence=confidence,
                reason=f"Price ({current_price:.2f}) above upper band ({current_upper:.2f})",
                metadata={
                    "price": current_price,
                    "upper": current_upper,
                    "lower": current_lower,
                    "middle": current_middle,
                    "bandwidth": bandwidth,
                }
            )
        
        position = (current_price - current_lower) / (current_upper - current_lower) if current_upper > current_lower else 0.5
        
        return Signal(
            SignalType.HOLD,
            confidence=0.5,
            reason=f"Price within bands, position: {position:.2%}",
            metadata={
                "price": current_price,
                "upper": current_upper,
                "lower": current_lower,
                "middle": current_middle,
                "bandwidth": bandwidth,
                "position": position,
            }
        )
    
    def get_name(self) -> str:
        return "Bollinger Bands Strategy"
    
    def get_params(self) -> Dict[str, Any]:
        return {
            "period": self.period,
            "num_std": self.num_std,
        }
    
    def get_required_data_points(self) -> int:
        return self.period + 2
