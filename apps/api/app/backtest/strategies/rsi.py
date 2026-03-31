"""
RSI Strategy

Generates buy/sell signals based on Relative Strength Index.
"""

import logging
from typing import Dict, Any
import pandas as pd
import numpy as np

from .base import BaseStrategy, Signal, SignalType

logger = logging.getLogger(__name__)


class RSIStrategy(BaseStrategy):
    """
    RSI (Relative Strength Index) Strategy.
    
    Buy when RSI < oversold threshold.
    Sell when RSI > overbought threshold.
    
    Parameters:
        period: RSI calculation period (default: 14)
        oversold: Oversold threshold (default: 30)
        overbought: Overbought threshold (default: 70)
    """
    
    def __init__(
        self,
        period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
    ):
        """
        Initialize RSI Strategy.
        
        Args:
            period: RSI period
            oversold: Oversold threshold
            overbought: Overbought threshold
        """
        if oversold >= overbought:
            raise ValueError(f"oversold ({oversold}) must be less than overbought ({overbought})")
        
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def _calculate_rsi(self, close: pd.Series) -> pd.Series:
        """
        Calculate RSI indicator.
        
        Args:
            close: Close price series
        
        Returns:
            RSI series
        """
        delta = close.diff()
        
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        
        avg_gain = gain.rolling(window=self.period, min_periods=self.period).mean()
        avg_loss = loss.rolling(window=self.period, min_periods=self.period).mean()
        
        rs = avg_gain / avg_loss.replace(0, np.inf)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        
        rsi = rsi.replace([np.inf, -np.inf], np.nan)
        
        return rsi
    
    def generate_signals(self, data: pd.DataFrame) -> Signal:
        """
        Generate trading signal based on RSI.
        
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
        rsi = self._calculate_rsi(close)
        
        if len(rsi) < 1 or pd.isna(rsi.iloc[-1]):
            return Signal(SignalType.HOLD, confidence=0.0, reason="RSI calculation incomplete")
        
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < self.oversold:
            distance = (self.oversold - current_rsi) / self.oversold
            confidence = min(0.5 + distance, 1.0)
            return Signal(
                SignalType.BUY,
                confidence=confidence,
                reason=f"RSI ({current_rsi:.2f}) below oversold threshold ({self.oversold})",
                metadata={"rsi": current_rsi}
            )
        
        if current_rsi > self.overbought:
            distance = (current_rsi - self.overbought) / (100 - self.overbought)
            confidence = min(0.5 + distance, 1.0)
            return Signal(
                SignalType.SELL,
                confidence=confidence,
                reason=f"RSI ({current_rsi:.2f}) above overbought threshold ({self.overbought})",
                metadata={"rsi": current_rsi}
            )
        
        return Signal(
            SignalType.HOLD,
            confidence=0.5,
            reason=f"RSI ({current_rsi:.2f}) in neutral zone",
            metadata={"rsi": current_rsi}
        )
    
    def get_name(self) -> str:
        return "RSI Strategy"
    
    def get_params(self) -> Dict[str, Any]:
        return {
            "period": self.period,
            "oversold": self.oversold,
            "overbought": self.overbought,
        }
    
    def get_required_data_points(self) -> int:
        return self.period + 2
