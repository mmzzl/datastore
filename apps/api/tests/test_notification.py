import pytest
from datetime import datetime
from app.monitor.notification.priority_notifier import PriorityNotifier
from app.monitor.models.alert_signal import AlertSignal, SignalType


class TestPriorityNotifier:
    def test_dedup_within_window(self):
        notifier = PriorityNotifier(dingtalk_client=None)
        sig = AlertSignal(
            timestamp=datetime.now(),
            code="600000",
            name="浦发银行",
            signal=SignalType.BUY,
            confidence=0.8,
            priority="high",
            reasons=["测试"],
            price=9.5,
        )

        notifier.send(sig)
        notifier.send(sig)

        key = "600000_technical"
        assert key in notifier._sent_history

    def test_critical_tracks_repeat(self):
        notifier = PriorityNotifier(dingtalk_client=None)
        sig = AlertSignal(
            timestamp=datetime.now(),
            code="600000",
            name="浦发银行",
            signal=SignalType.SELL,
            confidence=0.95,
            priority="critical",
            reasons=["止损触发"],
            price=8.0,
            alert_type="price",
        )

        notifier.send(sig)
        notifier.send(sig)

        key = "600000_price"
        assert key in notifier._repeat_history

    def test_low_priority_no_dingtalk(self, caplog):
        notifier = PriorityNotifier(dingtalk_client=None)
        sig = AlertSignal(
            timestamp=datetime.now(),
            code="600000",
            name="浦发银行",
            signal=SignalType.HOLD,
            confidence=0.5,
            priority="low",
            reasons=["缩量整理"],
            price=9.5,
        )

        with caplog.at_level("DEBUG"):
            notifier.send(sig)
        assert "LOW" in caplog.text

    def test_send_with_mock_dingtalk(self):
        class MockDingTalk:
            def __init__(self):
                self.sent = []

            def send(self, msg, at_all=False):
                self.sent.append((msg[:50], at_all))

        mock = MockDingTalk()
        notifier = PriorityNotifier(dingtalk_client=mock)

        sig = AlertSignal(
            timestamp=datetime.now(),
            code="600000",
            name="浦发银行",
            signal=SignalType.BUY,
            confidence=0.8,
            priority="high",
            reasons=["RSI低于30"],
            price=9.5,
        )

        notifier.send(sig)
        assert len(mock.sent) == 1
