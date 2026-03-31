"""
MACD Strategy

Generates buy/sell signals based on MACD indicator.
"""

import logging
from typing import Dict, Any
import pandas as pd
import numpy as np

from .base import BaseStrategy, Signal, SignalType

logger = logging.getLogger(__name__)


class MACDStrategy(BaseStrategy):
    """
    MACD (Moving Average Convergence Divergence) Strategy.
    
    Buy when MACD line crosses above signal line.
    Sell when MACD line crosses below signal line.
    
    Parameters:
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line period (default: 9)
    """
    
    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ):
        """
        Initialize MACD Strategy.
        
        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
        """
        if fast_period >= slow_period:
            raise ValueError(f"fast_period ({fast_period}) must be less than slow_period ({slow_period})")
        
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
    
    def _calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average.
        
        Args:
            data: Price series
            period: EMA period
        
        Returns:
            EMA series
        """
        return data.ewm(span=period, adjust=False).mean()
    
    def _calculate_macd(
        self,
        close: pd.Series,
    ) -> tuple:
        """
        Calculate MACD indicator.
        
        Args:
            close: Close price series
        
        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        fast_ema = self._calculate_ema(close, self.fast_period)
        slow_ema = self._calculate_ema(close, self.slow_period)
        
        macd_line = fast_ema - slow_ema
        signal_line = self._calculate_ema(macd_line, self.signal_period)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def generate_signals(self, data: pd.DataFrame) -> Signal:
        """
        Generate trading signal based on MACD.
        
        Args:
            data: DataFrame with 'close' column
        
        Returns:
            Signal object with buy/sell/hold indication
        """
        if not self.validate_data(data):
            return Signal(SignalType.HOLD, confidence=0.0, reason="Invalid data")
        
        min_data_points = self.slow_period + self.signal_period + 2
        if len(data) < min_data_points:
            return Signal(SignalType.HOLD, confidence=0.0, reason="Insufficient data")
        
        close = data["close"]
        macd_line, signal_line, histogram = self._calculate_macd(close)
        
        if len(macd_line) < 2:
            return Signal(SignalType.HOLD, confidence=0.0, reason="MACD calculation incomplete")
        
        macd_current = macd_line.iloc[-1]
        macd_previous = macd_line.iloc[-2]
        signal_current = signal_line.iloc[-1]
        signal_previous = signal_line.iloc[-2]
        hist_current = histogram.iloc[-1]
        
        if pd.isna(macd_current) or pd.isna(signal_current):
            return Signal(SignalType.HOLD, confidence=0.0, reason="MACD calculation incomplete")
        
        if pd.isna(macd_previous) or pd.isna(signal_previous):
            return Signal(
                SignalType.HOLD,
                confidence=0.5,
                reason="MACD values available but previous values are NaN",
                metadata={"macd": macd_current, "signal": signal_current, "histogram": hist_current}
            )
        
        if macd_previous <= signal_previous and macd_current > signal_current:
            distance = abs(hist_current) / abs(signal_current) if signal_current != 0 else 0
            confidence = min(0.5 + distance, 1.0)
            return Signal(
                SignalType.BUY,
                confidence=confidence,
                reason=f"MACD ({macd_current:.4f}) crossed above signal ({signal_current:.4f})",
                metadata={
                    "macd": macd_current,
                    "signal": signal_current,
                    "histogram": hist_current,
                }
            )
        
        if macd_previous >= signal_previous and macd_current < signal_current:
            distance = abs(hist_current) / abs(signal_current) if signal_current != 0 else 0
            confidence = min(0.5 + distance, 1.0)
            return Signal(
                SignalType.SELL,
                confidence=confidence,
                reason=f"MACD ({macd_current:.4f}) crossed below signal ({signal_current:.4f})",
                metadata={
                    "macd": macd_current,
                    "signal": signal_current,
                    "histogram": hist_current,
                }
            )
        
        return Signal(
            SignalType.HOLD,
            confidence=0.5,
            reason="No MACD crossover detected",
            metadata={
                "macd": macd_current,
                "signal": signal_current,
                "histogram": hist_current,
            }
        )
    
    def get_name(self) -> str:
        return "MACD Strategy"
    
    def get_params(self) -> Dict[str, Any]:
        return {
            "fast_period": self.fast_period,
            "slow_period": self.slow_period,
            "signal_period": self.signal_period,
        }
    
    def get_required_data_points(self) -> int:
        return self.slow_period + self.signal_period + 2
