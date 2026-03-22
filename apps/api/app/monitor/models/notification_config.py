from dataclasses import dataclass
from enum import Enum
from typing import List


class NotificationLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class NotificationPayload:
    title: str
    body: str
    level: NotificationLevel
    code: str
    signal: str
    confidence: float
    price: float
    reasons: list
    action_price: float
    target_price: float
    stop_loss: float

    def to_dingtalk_markdown(self) -> str:
        emoji = (
            "🔴"
            if self.level == "critical"
            else (
                "🟠"
                if self.level == "high"
                else ("🟡" if self.level == "medium" else "⚪")
            )
        )
        return (
            f"### {emoji} [{self.level.upper()}] {self.title}\n\n"
            f"**股票**: {self.name} ({self.code})\n\n"
            f"**当前价格**: {self.price:.2f}\n\n"
            f"**信号**: {self.signal.upper()}\n\n"
            f"**置信度**: {self.confidence * 100:.1f}%\n\n"
            f"**理由**:\n"
            + "\n".join([f"- {r}" for r in self.reasons])
            + f"\n\n**建议操作**: {'立即执行' if self.level in ('critical', 'high') else '观察'}"
        )

    @property
    def name(self) -> str:
        return self.title.replace("信号", "").replace("预警", "")
