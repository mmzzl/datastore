import pytest
from datetime import datetime
from app.monitor.models.alert_rule import (
    AlertRule,
    AlertType,
    AlertCondition,
    AlertPriority,
    AlertOperator,
    StrategyType,
    NotifyConfig,
)
from app.monitor.models.alert_signal import AlertSignal, SignalType
from app.monitor.models.notification_config import NotificationPayload


class TestAlertRule:
    def test_alert_rule_serialization(self):
        rule = AlertRule(
            code="600000",
            name="浦发银行",
            alert_type=AlertType.PRICE,
            condition=AlertCondition(
                operator=AlertOperator.GT,
                value=10.0,
                reference="price",
            ),
            priority=AlertPriority.HIGH,
        )
        data = rule.to_dict()
        assert data["code"] == "600000"
        assert data["alert_type"] == "price"
        assert data["condition"]["operator"] == ">"

    def test_alert_rule_deserialization(self):
        data = {
            "code": "600000",
            "alert_type": "volume",
            "condition": {
                "operator": "cross_up",
                "value": 1.5,
                "reference": "volume_ratio",
                "period": 5,
            },
            "priority": "critical",
            "notification": {
                "dingtalk": True,
                "dashboard": True,
                "repeat_interval": 30,
                "at_all": True,
            },
        }
        rule = AlertRule.from_dict(data)
        assert rule.code == "600000"
        assert rule.alert_type == AlertType.VOLUME
        assert rule.condition.operator == AlertOperator.CROSS_UP
        assert rule.priority == AlertPriority.CRITICAL
        assert rule.notification.at_all is True

    def test_notify_config_defaults(self):
        cfg = NotifyConfig()
        assert cfg.repeat_interval == 30
        assert cfg.at_all is False


class TestAlertSignal:
    def test_alert_signal_to_dict(self):
        signal = AlertSignal(
            timestamp=datetime.now(),
            code="600000",
            name="浦发银行",
            signal=SignalType.BUY,
            confidence=0.75,
            priority="high",
            reasons=["RSI低于30", "MACD金叉"],
            price=9.5,
            volume_ratio=2.0,
            alert_type="technical",
            strategy_type="intraday",
        )
        data = signal.to_dict()
        assert data["code"] == "600000"
        assert data["signal"] == "buy"
        assert data["confidence"] == 0.75
        assert len(data["reasons"]) == 2


class TestNotificationPayload:
    def test_dingtalk_markdown_critical(self):
        payload = NotificationPayload(
            title="止损预警",
            body="止损触发",
            level="critical",
            code="600000",
            signal="sell",
            confidence=0.9,
            price=8.5,
            reasons=["触及止损线"],
            action_price=8.8,
            target_price=10.0,
            stop_loss=8.8,
        )
        md = payload.to_dingtalk_markdown()
        assert "🔴" in md
        assert "[CRITICAL]" in md
        assert "止损预警" in md
