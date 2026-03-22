from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime


class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class AlertSignal:
    timestamp: datetime
    code: str
    name: str
    signal: SignalType
    confidence: float
    priority: str
    reasons: List[str] = field(default_factory=list)
    technical_data: Dict[str, Any] = field(default_factory=dict)
    market_breadth: Optional[Dict[str, Any]] = None
    correlated_assets: Optional[Dict[str, Any]] = None
    price: float = 0.0
    volume_ratio: float = 0.0
    alert_type: str = "technical"
    strategy_type: str = "all"
    action_price: float = 0.0
    target_price: float = 0.0
    stop_loss: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "code": self.code,
            "name": self.name,
            "signal": self.signal.value,
            "confidence": round(self.confidence, 4),
            "priority": self.priority,
            "reasons": self.reasons,
            "technical_data": self.technical_data,
            "market_breadth": self.market_breadth,
            "correlated_assets": self.correlated_assets,
            "price": self.price,
            "volume_ratio": self.volume_ratio,
            "alert_type": self.alert_type,
            "strategy_type": self.strategy_type,
            "action_price": self.action_price,
            "target_price": self.target_price,
            "stop_loss": self.stop_loss,
        }
