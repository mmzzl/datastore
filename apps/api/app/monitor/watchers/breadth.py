from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import BaseWatcher


class MarketBreadthWatcher(BaseWatcher):
    def collect(self) -> Optional[Dict[str, Any]]:
        try:
            result = self.data_manager.get_market_breadth()
            if result is None:
                return None
            return {
                "timestamp": result.timestamp,
                "advance_count": result.advance_count,
                "decline_count": result.decline_count,
                "advance_decline_ratio": result.advance_decline_ratio,
                "sector_rankings": result.sector_rankings,
                "north_bound_flow": result.north_bound_flow,
                "vix": result.vix,
            }
        except Exception as e:
            self._logger.error(f"MarketBreadthWatcher collect error: {e}")
            return None

    def evaluate(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        signals = []
        ratio = data.get("advance_decline_ratio", 1.0)
        north_flow = data.get("north_bound_flow", 0.0)
        sector_rankings = data.get("sector_rankings", [])

        if ratio > 2.0:
            signals.append(
                {
                    "code": "MARKET",
                    "name": "市场整体",
                    "signal": "buy",
                    "confidence": min(0.9, (ratio - 2.0) / 2.0 + 0.7),
                    "priority": "high",
                    "reasons": [f"上涨家数远超下跌家数（涨跌比={ratio:.2f}）"],
                    "alert_type": "breadth",
                    "strategy_type": "all",
                    "price": 0.0,
                    "volume_ratio": ratio,
                    "market_breadth": data,
                }
            )
        elif ratio < 0.5:
            signals.append(
                {
                    "code": "MARKET",
                    "name": "市场整体",
                    "signal": "sell",
                    "confidence": min(0.9, (0.5 - ratio) / 0.5 + 0.7),
                    "priority": "high",
                    "reasons": [f"下跌家数远超上涨家数（涨跌比={ratio:.2f}）"],
                    "alert_type": "breadth",
                    "strategy_type": "all",
                    "price": 0.0,
                    "volume_ratio": ratio,
                    "market_breadth": data,
                }
            )

        if north_flow > 50000:
            signals.append(
                {
                    "code": "NORTHBOUND",
                    "name": "北向资金",
                    "signal": "buy",
                    "confidence": min(0.85, north_flow / 200000),
                    "priority": "medium",
                    "reasons": [f"北向资金大幅净流入 {north_flow:.0f} 万元"],
                    "alert_type": "breadth",
                    "strategy_type": "swing",
                    "price": 0.0,
                    "volume_ratio": 0.0,
                    "market_breadth": data,
                }
            )
        elif north_flow < -50000:
            signals.append(
                {
                    "code": "NORTHBOUND",
                    "name": "北向资金",
                    "signal": "sell",
                    "confidence": min(0.85, abs(north_flow) / 200000),
                    "priority": "medium",
                    "reasons": [f"北向资金大幅净流出 {north_flow:.0f} 万元"],
                    "alert_type": "breadth",
                    "strategy_type": "swing",
                    "price": 0.0,
                    "volume_ratio": 0.0,
                    "market_breadth": data,
                }
            )

        for sector in sector_rankings[:3]:
            change_pct = sector.get("change_pct", 0.0)
            if change_pct > 3.0:
                signals.append(
                    {
                        "code": f"SECTOR_{sector['name']}",
                        "name": f"板块: {sector['name']}",
                        "signal": "buy",
                        "confidence": min(0.8, change_pct / 10),
                        "priority": "medium",
                        "reasons": [f"板块 {sector['name']} 大涨 {change_pct:.2f}%"],
                        "alert_type": "breadth",
                        "strategy_type": "event",
                        "price": 0.0,
                        "volume_ratio": change_pct,
                        "market_breadth": data,
                    }
                )
            elif change_pct < -3.0:
                signals.append(
                    {
                        "code": f"SECTOR_{sector['name']}",
                        "name": f"板块: {sector['name']}",
                        "signal": "sell",
                        "confidence": min(0.8, abs(change_pct) / 10),
                        "priority": "medium",
                        "reasons": [f"板块 {sector['name']} 大跌 {change_pct:.2f}%"],
                        "alert_type": "breadth",
                        "strategy_type": "event",
                        "price": 0.0,
                        "volume_ratio": change_pct,
                        "market_breadth": data,
                    }
                )

        return signals
