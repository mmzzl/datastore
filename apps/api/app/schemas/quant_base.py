from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class SignalType(str, Enum):
    """Standardized signal types for quant strategies."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    NEUTRAL = "NEUTRAL"


class SignalModel(BaseModel):
    """Strongly typed signal output from a strategy."""

    code: str
    signal_type: SignalType
    confidence: float = Field(..., ge=0, le=1)
    score: float
    indicators: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class KLineData(BaseModel):
    """Strongly typed K-line candle."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    turnover: Optional[float] = None


class KLineSet(BaseModel):
    """A collection of K-lines for a specific stock."""

    code: str
    data: List[KLineData]
    start_date: datetime
    end_date: datetime
    is_complete: bool = True
    gap_count: int = 0
