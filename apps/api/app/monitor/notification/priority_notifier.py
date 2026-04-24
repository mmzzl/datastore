import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.monitor.models.alert_signal import AlertSignal, SignalType
from app.monitor.models.notification_config import (
    NotificationPayload,
    NotificationLevel,
)
from app.notify.dedup_filter import NotificationDedupFilter


class PriorityNotifier:
    def __init__(self, dingtalk_client=None):
        self._dingtalk = dingtalk_client
        self._logger = logging.getLogger(__name__)
        self._sent_history: Dict[str, datetime] = {}
        self._repeat_history: Dict[str, datetime] = {}
        self.dedup_filter = NotificationDedupFilter()

    def send(self, alert_signal: AlertSignal):
        signal_value = alert_signal.signal.value if hasattr(alert_signal.signal, 'value') else str(alert_signal.signal)

        ok, resolved_signal = self.dedup_filter.should_send(
            alert_signal.code, signal_value, alert_signal.reasons
        )
        if not ok:
            self._logger.info(f"Notification filtered: {alert_signal.code} -> {resolved_signal}")
            return

        if resolved_signal != signal_value:
            alert_signal = AlertSignal(
                timestamp=alert_signal.timestamp,
                code=alert_signal.code,
                name=alert_signal.name,
                signal=SignalType(resolved_signal),
                confidence=alert_signal.confidence,
                priority=alert_signal.priority,
                reasons=alert_signal.reasons,
                technical_data=alert_signal.technical_data,
                market_breadth=alert_signal.market_breadth,
                correlated_assets=alert_signal.correlated_assets,
                price=alert_signal.price,
                volume_ratio=alert_signal.volume_ratio,
                alert_type=alert_signal.alert_type,
                strategy_type=alert_signal.strategy_type,
                action_price=alert_signal.action_price,
                target_price=alert_signal.target_price,
                stop_loss=alert_signal.stop_loss,
            )
            signal_value = resolved_signal

        self.dedup_filter.record_sent(alert_signal.code, signal_value, alert_signal.reasons)

        priority = alert_signal.priority

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
            stop_loss=alert_signal.stop_price if hasattr(alert_signal, 'stop_price') else alert_signal.stop_loss,
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
