"""
Base Strategy Abstract Class

Provides the foundation for all trading strategies.
"""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
import pandas as pd


class SignalType(Enum):
    """Signal types for trading decisions."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class Signal:
    """
    Trading signal with confidence level.
    
    Attributes:
        signal_type: Type of signal (BUY, SELL, HOLD)
        confidence: Confidence level between 0 and 1
        reason: Optional reason for the signal
        metadata: Optional additional metadata
    """
    signal_type: SignalType
    confidence: float = 0.5
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.
    
    All strategies must implement:
    - generate_signals: Analyze data and produce trading signals
    - get_name: Return strategy name
    - get_params: Return strategy parameters
    """
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> Signal:
        """
        Generate trading signals from market data.
        
        Args:
            data: DataFrame with OHLCV data (columns: open, high, low, close, volume)
        
        Returns:
            Signal object with type and confidence
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Return the strategy name.
        
        Returns:
            Strategy name string
        """
        pass
    
    @abstractmethod
    def get_params(self) -> Dict[str, Any]:
        """
        Return strategy parameters.
        
        Returns:
            Dictionary of parameter names and values
        """
        pass
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate that data has required columns.
        
        Args:
            data: DataFrame to validate
        
        Returns:
            True if data is valid, False otherwise
        """
        required_columns = ["close"]
        return all(col in data.columns for col in required_columns)
    
    def get_required_data_points(self) -> int:
        """Return minimum number of data points needed.

        Returns:
            Minimum data points required for this strategy
        """
        return 1

    @property
    def is_portfolio_strategy(self) -> bool:
        """Whether this strategy selects stocks at portfolio level (not per-stock)."""
        return False
