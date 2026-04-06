"""
Double Moving Average Cross Strategy

Classic trend-following strategy using two moving averages.
- Buy when fast MA crosses above slow MA (Golden Cross)
- Sell when fast MA crosses below slow MA (Death Cross)
"""

from typing import Dict, Any
import pandas as pd
import numpy as np

from app.backtest.strategies.base import BaseStrategy, Signal, SignalType


class DoubleMAStrategy(BaseStrategy):
    """
    Double Moving Average Crossover Strategy.

    A classic trend-following strategy that generates signals based on
    the crossover of two moving averages.

    Parameters:
        fast_period: Period for fast moving average (default: 5)
        slow_period: Period for slow moving average (default: 20)
        ma_type: Type of moving average - 'sma' or 'ema' (default: 'sma')
    """

    def __init__(
        self,
        fast_period: int = 5,
        slow_period: int = 20,
        ma_type: str = "sma"
    ):
        """
        Initialize Double MA Strategy.

        Args:
            fast_period: Fast MA period
            slow_period: Slow MA period
            ma_type: Moving average type ('sma' or 'ema')

        Raises:
            ValueError: If fast_period >= slow_period or invalid ma_type
        """
        if fast_period >= slow_period:
            raise ValueError(
                f"fast_period ({fast_period}) must be less than slow_period ({slow_period})"
            )

        if ma_type not in ("sma", "ema"):
            raise ValueError(f"ma_type must be 'sma' or 'ema', got '{ma_type}'")

        self.fast_period = fast_period
        self.slow_period = slow_period
        self.ma_type = ma_type

    def _calculate_ma(self, series: pd.Series, period: int) -> pd.Series:
        """
        Calculate moving average based on ma_type.

        Args:
            series: Price series
            period: MA period

        Returns:
            Moving average series
        """
        if self.ma_type == "ema":
            return series.ewm(span=period, adjust=False).mean()
        else:
            return series.rolling(window=period).mean()

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

        min_required = self.slow_period + 2
        if len(data) < min_required:
            return Signal(
                SignalType.HOLD,
                confidence=0.0,
                reason=f"Insufficient data: need {min_required}, got {len(data)}"
            )

        close = data["close"]

        fast_ma = self._calculate_ma(close, self.fast_period)
        slow_ma = self._calculate_ma(close, self.slow_period)

        # Check if we have valid MA values
        if pd.isna(fast_ma.iloc[-1]) or pd.isna(slow_ma.iloc[-1]):
            return Signal(SignalType.HOLD, confidence=0.0, reason="MA calculation incomplete")

        if pd.isna(fast_ma.iloc[-2]) or pd.isna(slow_ma.iloc[-2]):
            return Signal(SignalType.HOLD, confidence=0.0, reason="MA calculation incomplete")

        fast_current = fast_ma.iloc[-1]
        fast_previous = fast_ma.iloc[-2]
        slow_current = slow_ma.iloc[-1]
        slow_previous = slow_ma.iloc[-2]

        # Golden Cross: Fast MA crosses above Slow MA
        if fast_previous <= slow_previous and fast_current > slow_current:
            # Calculate confidence based on the distance between MAs
            distance = abs(fast_current - slow_current) / slow_current
            confidence = min(0.5 + distance * 10, 1.0)

            return Signal(
                SignalType.BUY,
                confidence=confidence,
                reason=f"Golden Cross: {self.ma_type.upper()}({self.fast_period}) crossed above {self.ma_type.upper()}({self.slow_period})",
                metadata={
                    "fast_ma": round(float(fast_current), 4),
                    "slow_ma": round(float(slow_current), 4),
                    "distance_pct": round(float(distance * 100), 2),
                    "signal_type": "golden_cross"
                }
            )

        # Death Cross: Fast MA crosses below Slow MA
        if fast_previous >= slow_previous and fast_current < slow_current:
            distance = abs(fast_current - slow_current) / slow_current
            confidence = min(0.5 + distance * 10, 1.0)

            return Signal(
                SignalType.SELL,
                confidence=confidence,
                reason=f"Death Cross: {self.ma_type.upper()}({self.fast_period}) crossed below {self.ma_type.upper()}({self.slow_period})",
                metadata={
                    "fast_ma": round(float(fast_current), 4),
                    "slow_ma": round(float(slow_current), 4),
                    "distance_pct": round(float(distance * 100), 2),
                    "signal_type": "death_cross"
                }
            )

        # No crossover - determine trend direction
        trend = "up" if fast_current > slow_current else "down"

        return Signal(
            SignalType.HOLD,
            confidence=0.5,
            reason=f"No crossover. Trend: {trend}",
            metadata={
                "fast_ma": round(float(fast_current), 4),
                "slow_ma": round(float(slow_current), 4),
                "trend": trend
            }
        )

    def get_name(self) -> str:
        """Return strategy name."""
        ma_name = "EMA" if self.ma_type == "ema" else "SMA"
        return f"Double {ma_name} Cross ({self.fast_period}/{self.slow_period})"

    def get_params(self) -> Dict[str, Any]:
        """Return strategy parameters."""
        return {
            "fast_period": self.fast_period,
            "slow_period": self.slow_period,
            "ma_type": self.ma_type,
        }

    def get_required_data_points(self) -> int:
        """Return minimum data points needed."""
        return self.slow_period + 2
