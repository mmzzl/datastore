import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.monitor.models.alert_signal import AlertSignal, SignalType
from app.monitor.models.notification_config import (
    NotificationPayload,
    NotificationLevel,
)


class PriorityNotifier:
    def __init__(self, dingtalk_client=None):
        self._dingtalk = dingtalk_client
        self._logger = logging.getLogger(__name__)
        self._sent_history: Dict[str, datetime] = {}
        self._repeat_history: Dict[str, datetime] = {}

    def send(self, alert_signal: AlertSignal):
        priority = alert_signal.priority

        signal_value = alert_signal.signal.value if hasattr(alert_signal.signal, 'value') else str(alert_signal.signal)

        payload = NotificationPayload(
            title=self._get_title(alert_signal),
            body="\n".join(alert_signal.reasons),
            level=priority,
            code=alert_signal.code,
            signal=signal_value,
            confidence=alert_signal.confidence,
            price=alert_signal.price,
            reasons=alert_signal.reasons,
            action_price=alert_signal.action_price,
            target_price=alert_signal.target_price,
            stop_loss=alert_signal.stop_loss,
        )

        if priority == "critical":
            self._send_critical(payload, alert_signal)
        elif priority == "high":
            self._send_high(payload, alert_signal)
        elif priority == "medium":
            self._send_medium(payload, alert_signal)
        else:
            self._send_low(payload, alert_signal)

    def _get_title(self, sig: AlertSignal) -> str:
        signal_val = sig.signal.value if hasattr(sig.signal, 'value') else str(sig.signal)
        action = (
            "买入"
            if signal_val == "buy"
            else ("卖出" if signal_val == "sell" else "观望")
        )
        return f"{sig.name} {action}信号"

    def _should_send(self, key: str) -> bool:
        now = datetime.now()
        if key in self._sent_history:
            last = self._sent_history[key]
            if (now - last).total_seconds() < 300:
                return False
        self._sent_history[key] = now
        return True

    def _send_critical(self, payload: NotificationPayload, sig: AlertSignal):
        key = f"{sig.code}_{sig.alert_type}"

        if key in self._repeat_history:
            last = self._repeat_history[key]
            if (datetime.now() - last).total_seconds() < 30:
                return

        self._repeat_history[key] = datetime.now()

        if self._dingtalk:
            md = payload.to_dingtalk_markdown()
            self._dingtalk.send(md, at_all=True)
        self._logger.warning(f"[CRITICAL] {payload.title}: {payload.body}")

    def _send_high(self, payload: NotificationPayload, sig: AlertSignal):
        key = f"{sig.code}_{sig.alert_type}"
        if not self._should_send(key):
            return

        if self._dingtalk:
            md = payload.to_dingtalk_markdown()
            self._dingtalk.send(md)
        self._logger.info(f"[HIGH] {payload.title}")

    def _send_medium(self, payload: NotificationPayload, sig: AlertSignal):
        key = f"{sig.code}_{sig.alert_type}"
        if not self._should_send(key):
            return

        if self._dingtalk:
            md = payload.to_dingtalk_markdown()
            self._dingtalk.send(md)
        self._logger.info(f"[MEDIUM] {payload.title}")

    def _send_low(self, payload: NotificationPayload, sig: AlertSignal):
        self._logger.debug(f"[LOW] {payload.title}: {payload.body}")
