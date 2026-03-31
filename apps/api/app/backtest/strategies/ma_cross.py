"""
Moving Average Cross Strategy

Generates buy/sell signals based on MA crossovers.
"""

import logging
from typing import Dict, Any
import pandas as pd
import numpy as np

from .base import BaseStrategy, Signal, SignalType

logger = logging.getLogger(__name__)


class MACrossStrategy(BaseStrategy):
    """
    Moving Average Crossover Strategy.
    
    Buy when fast MA crosses above slow MA.
    Sell when fast MA crosses below slow MA.
    
    Parameters:
        fast_period: Period for fast moving average (default: 5)
        slow_period: Period for slow moving average (default: 20)
    """
    
    def __init__(self, fast_period: int = 5, slow_period: int = 20):
        """
        Initialize MA Cross Strategy.
        
        Args:
            fast_period: Fast MA period
            slow_period: Slow MA period
        """
        if fast_period >= slow_period:
            raise ValueError(f"fast_period ({fast_period}) must be less than slow_period ({slow_period})")
        
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def generate_signals(self, data: pd.DataFrame) -> Signal:
        """
        Generate trading signal based on MA crossover.
        
        Args:
            data: DataFrame with 'close' column
        
        Returns:
            Signal object with buy/sell/hold indication
        """
        if not self.validate_data(data):
            return Signal(SignalType.HOLD, confidence=0.0, reason="Invalid data")
        
        if len(data) < self.slow_period + 1:
            return Signal(SignalType.HOLD, confidence=0.0, reason="Insufficient data")
        
        close = data["close"]
        
        fast_ma = close.rolling(window=self.fast_period).mean()
        slow_ma = close.rolling(window=self.slow_period).mean()
        
        if len(fast_ma) < 2 or pd.isna(fast_ma.iloc[-1]) or pd.isna(slow_ma.iloc[-1]):
            return Signal(SignalType.HOLD, confidence=0.0, reason="MA calculation incomplete")
        
        fast_current = fast_ma.iloc[-1]
        fast_previous = fast_ma.iloc[-2]
        slow_current = slow_ma.iloc[-1]
        slow_previous = slow_ma.iloc[-2]
        
        if pd.isna(fast_previous) or pd.isna(slow_previous):
            return Signal(SignalType.HOLD, confidence=0.0, reason="MA calculation incomplete")
        
        if fast_previous <= slow_previous and fast_current > slow_current:
            distance = abs(fast_current - slow_current) / slow_current
            confidence = min(0.5 + distance * 10, 1.0)
            return Signal(
                SignalType.BUY,
                confidence=confidence,
                reason=f"Fast MA ({self.fast_period}) crossed above Slow MA ({self.slow_period})",
                metadata={"fast_ma": fast_current, "slow_ma": slow_current}
            )
        
        if fast_previous >= slow_previous and fast_current < slow_current:
            distance = abs(fast_current - slow_current) / slow_current
            confidence = min(0.5 + distance * 10, 1.0)
            return Signal(
                SignalType.SELL,
                confidence=confidence,
                reason=f"Fast MA ({self.fast_period}) crossed below Slow MA ({self.slow_period})",
                metadata={"fast_ma": fast_current, "slow_ma": slow_current}
            )
        
        return Signal(
            SignalType.HOLD,
            confidence=0.5,
            reason="No crossover detected",
            metadata={"fast_ma": fast_current, "slow_ma": slow_current}
        )
    
    def get_name(self) -> str:
        return "MA Cross Strategy"
    
    def get_params(self) -> Dict[str, Any]:
        return {
            "fast_period": self.fast_period,
            "slow_period": self.slow_period,
        }
    
    def get_required_data_points(self) -> int:
        return self.slow_period + 2
