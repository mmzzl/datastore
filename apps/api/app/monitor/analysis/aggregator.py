from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.monitor.models.alert_signal import AlertSignal, SignalType
from app.monitor.models.alert_rule import AlertRule, AlertPriority


class AlertAggregator:
    STRATEGY_WEIGHTS = {
        "intraday": {
            "technical": 0.30,
            "volume": 0.25,
            "sentiment": 0.25,
            "correlation": 0.10,
            "event": 0.10,
        },
        "swing": {
            "technical": 0.20,
            "volume": 0.15,
            "sentiment": 0.20,
            "correlation": 0.20,
            "event": 0.25,
        },
        "event": {
            "technical": 0.10,
            "volume": 0.10,
            "sentiment": 0.10,
            "correlation": 0.30,
            "event": 0.40,
        },
        "all": {
            "technical": 0.25,
            "volume": 0.20,
            "sentiment": 0.20,
            "correlation": 0.15,
            "event": 0.20,
        },
    }

    def __init__(self, strategy_type: str = "all"):
        self.strategy_type = strategy_type
        self.weights = self.STRATEGY_WEIGHTS.get(
            strategy_type, self.STRATEGY_WEIGHTS["all"]
        )
        self._logger = logging.getLogger(__name__)
        self._signal_cache: Dict[str, datetime] = {}
        self._dedup_window = 300

    def aggregate(self, signals: List[Dict[str, Any]]) -> List[AlertSignal]:
        if not signals:
            return []

        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for sig in signals:
            key = f"{sig.get('code', '')}_{sig.get('alert_type', '')}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(sig)

        results = []
        now = datetime.now()

        for key, group in grouped.items():
            if key in self._signal_cache:
                last_time = self._signal_cache[key]
                if (now - last_time).total_seconds() < self._dedup_window:
                    if not any(s.get("priority") == "critical" for s in group):
                        continue

            best = max(group, key=lambda x: x.get("confidence", 0.0))

            total_score = self._calculate_weighted_score(best)

            action = self._determine_action(total_score, best)

            price = best.get("price", 0.0)
            target_price = price * 1.05 if price > 0 else 0.0
            stop_loss = price * 0.95 if price > 0 else 0.0

            alert_signal = AlertSignal(
                timestamp=now,
                code=best.get("code", ""),
                name=best.get("name", ""),
                signal=action,
                confidence=total_score,
                priority=best.get("priority", "medium"),
                reasons=best.get("reasons", []),
                technical_data=best.get("technical_data", {}),
                market_breadth=best.get("market_breadth"),
                correlated_assets=best.get("correlated_assets"),
                price=price,
                volume_ratio=best.get("volume_ratio", 0.0),
                alert_type=best.get("alert_type", "technical"),
                strategy_type=best.get("strategy_type", "all"),
                action_price=best.get("action_price", price),
                target_price=target_price,
                stop_loss=stop_loss,
            )

            results.append(alert_signal)
            self._signal_cache[key] = now

        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        results.sort(key=lambda x: priority_order.get(x.priority, 4))

        return results

    def _calculate_weighted_score(self, signal: Dict[str, Any]) -> float:
        alert_type = signal.get("alert_type", "technical")
        base_confidence = signal.get("confidence", 0.5)
        weight = self.weights.get(alert_type, 0.2)

        priority_boost = {"critical": 0.15, "high": 0.1, "medium": 0.05, "low": 0.0}
        boost = priority_boost.get(signal.get("priority", "low"), 0.0)

        return min(1.0, base_confidence * (1 + weight - 0.2) + boost)

    def _determine_action(
        self, total_score: float, signal: Dict[str, Any]
    ) -> SignalType:
        rsi = signal.get("technical_data", {}).get("rsi", 50.0)
        priority = signal.get("priority", "medium")

        if priority == "critical":
            sig = signal.get("signal", "hold")
            if sig in ("buy", "sell"):
                return SignalType(sig)

        if total_score > 0.75 or rsi < 25:
            return SignalType.BUY
        elif total_score < 0.25 or rsi > 75:
            return SignalType.SELL
        else:
            return SignalType.HOLD
