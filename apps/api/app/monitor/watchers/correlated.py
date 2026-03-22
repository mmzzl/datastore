from typing import List, Dict, Any, Optional
from .base import BaseWatcher


class CorrelatedAssetWatcher(BaseWatcher):
    A50_SPIKE_THRESHOLD = 1.0
    USDCNH_SPIKE_THRESHOLD = 0.5
    DXY_SPIKE_THRESHOLD = 0.3

    def collect(self) -> Optional[Dict[str, Any]]:
        try:
            result = self.data_manager.get_correlated_assets()
            if result is None:
                return None
            return {
                "timestamp": result.timestamp,
                "a50_future": result.a50_future,
                "a50_change_pct": result.a50_change_pct,
                "usdcnh": result.usdcnh,
                "dxy": result.dxy,
            }
        except Exception as e:
            self._logger.error(f"CorrelatedAssetWatcher collect error: {e}")
            return None

    def evaluate(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        signals = []
        a50_change = abs(data.get("a50_change_pct", 0.0))

        if data.get("a50_change_pct", 0) > self.A50_SPIKE_THRESHOLD:
            signals.append(
                {
                    "code": "A50",
                    "name": "富时A50",
                    "signal": "buy",
                    "confidence": min(0.8, a50_change / 3),
                    "priority": "medium",
                    "reasons": [f"A50期货上涨 {data['a50_change_pct']:.2f}%"],
                    "alert_type": "breadth",
                    "strategy_type": "all",
                    "price": data.get("a50_future", 0.0),
                    "volume_ratio": a50_change,
                    "correlated_assets": data,
                }
            )
        elif data.get("a50_change_pct", 0) < -self.A50_SPIKE_THRESHOLD:
            signals.append(
                {
                    "code": "A50",
                    "name": "富时A50",
                    "signal": "sell",
                    "confidence": min(0.8, a50_change / 3),
                    "priority": "medium",
                    "reasons": [f"A50期货下跌 {data['a50_change_pct']:.2f}%"],
                    "alert_type": "breadth",
                    "strategy_type": "all",
                    "price": data.get("a50_future", 0.0),
                    "volume_ratio": a50_change,
                    "correlated_assets": data,
                }
            )

        usdcnh = data.get("usdcnh", 7.25)
        if usdcnh > 7.3:
            signals.append(
                {
                    "code": "USDCNH",
                    "name": "离岸人民币",
                    "signal": "sell",
                    "confidence": min(0.7, (usdcnh - 7.3) * 2),
                    "priority": "low",
                    "reasons": [
                        f"离岸人民币突破7.3（当前{usdcnh:.4f}），人民币贬值压力"
                    ],
                    "alert_type": "breadth",
                    "strategy_type": "swing",
                    "price": usdcnh,
                    "volume_ratio": 0.0,
                    "correlated_assets": data,
                }
            )

        return signals
