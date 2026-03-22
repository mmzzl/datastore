from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime


class AlertType(str, Enum):
    PRICE = "price"
    VOLUME = "volume"
    TECHNICAL = "technical"
    NEWS = "news"
    BREADTH = "breadth"


class StrategyType(str, Enum):
    INTRADAY = "intraday"
    SWING = "swing"
    EVENT = "event"
    ALL = "all"


class AlertPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertOperator(str, Enum):
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    EQ = "=="
    CROSS_UP = "cross_up"
    CROSS_DOWN = "cross_down"
    IN_RANGE = "in_range"


@dataclass
class AlertCondition:
    operator: AlertOperator
    value: float
    reference: str
    period: int = 14


@dataclass
class NotifyConfig:
    dingtalk: bool = True
    dashboard: bool = True
    repeat_interval: int = 30
    at_all: bool = False


@dataclass
class AlertRule:
    id: str = ""
    code: str = ""
    name: str = ""
    alert_type: AlertType = AlertType.PRICE
    condition: Optional[AlertCondition] = None
    strategy_type: StrategyType = StrategyType.ALL
    priority: AlertPriority = AlertPriority.MEDIUM
    notification: NotifyConfig = field(default_factory=NotifyConfig)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "alert_type": self.alert_type.value,
            "condition": {
                "operator": self.condition.operator.value if self.condition else None,
                "value": self.condition.value if self.condition else None,
                "reference": self.condition.reference if self.condition else None,
                "period": self.condition.period if self.condition else None,
            }
            if self.condition
            else None,
            "strategy_type": self.strategy_type.value,
            "priority": self.priority.value,
            "notification": {
                "dingtalk": self.notification.dingtalk,
                "dashboard": self.notification.dashboard,
                "repeat_interval": self.notification.repeat_interval,
                "at_all": self.notification.at_all,
            },
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlertRule":
        condition = None
        if data.get("condition"):
            cond_data = data["condition"]
            condition = AlertCondition(
                operator=AlertOperator(cond_data.get("operator", ">")),
                value=float(cond_data.get("value", 0)),
                reference=cond_data.get("reference", "price"),
                period=int(cond_data.get("period", 14)),
            )
        notify_data = data.get("notification", {})
        return cls(
            id=data.get("id", ""),
            code=data.get("code", ""),
            name=data.get("name", ""),
            alert_type=AlertType(data.get("alert_type", "price")),
            condition=condition,
            strategy_type=StrategyType(data.get("strategy_type", "all")),
            priority=AlertPriority(data.get("priority", "medium")),
            notification=NotifyConfig(
                dingtalk=notify_data.get("dingtalk", True),
                dashboard=notify_data.get("dashboard", True),
                repeat_interval=notify_data.get("repeat_interval", 30),
                at_all=notify_data.get("at_all", False),
            ),
            enabled=data.get("enabled", True),
        )
