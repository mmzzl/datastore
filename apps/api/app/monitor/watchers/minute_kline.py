from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .base import BaseWatcher


class MinuteKlineWatcher(BaseWatcher):
    def __init__(self, data_manager=None, frequency: str = "5"):
        super().__init__(data_manager)
        self.frequency = frequency
        self._cache: Dict[str, List[Dict[str, Any]]] = {}

    def collect(self) -> Optional[Dict[str, Any]]:
        return None

    def evaluate_single(
        self,
        code: str,
        name: str,
        frequency: str = None,
        days: int = 3,
    ) -> List[Dict[str, Any]]:
        signals = []
        freq = frequency or self.frequency

        try:
            klines = self.data_manager.get_minute_kline(code, freq, days)
            if not klines:
                return signals

            closes = [k.close for k in klines]
            highs = [k.high for k in klines]
            lows = [k.low for k in klines]
            volumes = [k.volume for k in klines]

            if len(closes) < 20:
                return signals

            current_price = closes[-1]

            import numpy as np

            ma20 = np.mean(closes[-20:])
            std20 = np.std(closes[-20:])
            upper = ma20 + 2 * std20
            lower = ma20 - 2 * std20

            prev_high = max(highs[-6:-1])
            prev_low = min(lows[-6:-1])

            if current_price > prev_high and current_price > ma20:
                signals.append(
                    {
                        "code": code,
                        "name": name,
                        "signal": "buy",
                        "confidence": 0.7,
                        "priority": "medium",
                        "reasons": [
                            f"{freq}分钟K线突破前高({prev_high:.2f})，价格={current_price:.2f}"
                        ],
                        "alert_type": "technical",
                        "strategy_type": "intraday",
                        "price": current_price,
                        "volume_ratio": 0.0,
                        "technical_data": {
                            "ma20": ma20,
                            "upper": upper,
                            "lower": lower,
                        },
                    }
                )
            elif current_price < prev_low and current_price < ma20:
                signals.append(
                    {
                        "code": code,
                        "name": name,
                        "signal": "sell",
                        "confidence": 0.7,
                        "priority": "medium",
                        "reasons": [
                            f"{freq}分钟K线跌破前低({prev_low:.2f})，价格={current_price:.2f}"
                        ],
                        "alert_type": "technical",
                        "strategy_type": "intraday",
                        "price": current_price,
                        "volume_ratio": 0.0,
                        "technical_data": {
                            "ma20": ma20,
                            "upper": upper,
                            "lower": lower,
                        },
                    }
                )

            avg_vol_5 = sum(volumes[-5:]) / 5
            current_vol = volumes[-1]
            if (
                current_vol < avg_vol_5 * 0.5
                and abs(closes[-1] - closes[-2]) / closes[-2] < 0.005
            ):
                signals.append(
                    {
                        "code": code,
                        "name": name,
                        "signal": "hold",
                        "confidence": 0.5,
                        "priority": "low",
                        "reasons": [
                            f"缩量整理（量为5日均量的{current_vol / avg_vol_5 * 100:.0f}%），等待方向选择"
                        ],
                        "alert_type": "volume",
                        "strategy_type": "intraday",
                        "price": current_price,
                        "volume_ratio": current_vol / avg_vol_5
                        if avg_vol_5 > 0
                        else 0.0,
                        "technical_data": {},
                    }
                )

        except Exception as e:
            self._logger.error(
                f"MinuteKlineWatcher evaluate_single error for {code}: {e}"
            )

        return signals

    def evaluate(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []
