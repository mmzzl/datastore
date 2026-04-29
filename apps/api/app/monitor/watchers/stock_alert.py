from typing import List, Dict, Any, Optional
from .base import BaseWatcher


class StockAlertWatcher(BaseWatcher):
    def collect(self) -> Optional[Dict[str, Any]]:
        return None

    def evaluate_single(
        self,
        code: str,
        name: str,
        realtime_data: Dict[str, Any],
        technical_data: Dict[str, Any],
        capital_flow: List[Dict[str, Any]],
        watchlist: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        signals = []
        current_price = realtime_data.get("price") or realtime_data.get("close") or 0.0
        volume_ratio = realtime_data.get("volume_ratio", 0.0)
        change_pct = realtime_data.get("change_pct", 0.0)

        if not current_price:
            return signals

        stock_config = next((s for s in watchlist if s.get("code") == code), {})
        is_holding = stock_config.get("hold", False)
        cost_price = stock_config.get("cost_price", 0.0)
        stop_loss = stock_config.get("stop_loss", 0.05)
        profit_target = stock_config.get("profit_target", 0.1)

        if is_holding and cost_price > 0:
            loss_pct = (cost_price - current_price) / cost_price
            if loss_pct >= stop_loss:
                signals.append(
                    {
                        "code": code,
                        "name": name,
                        "signal": "sell",
                        "confidence": 0.95,
                        "priority": "critical",
                        "reasons": [
                            f"触及止损线（亏损{loss_pct * 100:.1f}%，止损线{stop_loss * 100:.1f}%）"
                        ],
                        "alert_type": "price",
                        "strategy_type": "all",
                        "price": current_price,
                        "volume_ratio": volume_ratio,
                        "stop_loss": cost_price * (1 - stop_loss),
                        "technical_data": technical_data,
                    }
                )
                return signals

            profit_pct = (current_price - cost_price) / cost_price
            exit_strategy = stock_config.get("exit_strategy", "fixed")
            highest_price = stock_config.get("highest_price", current_price)

            # 阶梯止盈
            if exit_strategy == "tiered":
                tier_profits = stock_config.get("tier_profits", [0.03, 0.05, 0.08, 0.10])
                tier_sell_pcts = stock_config.get("tier_sell_pcts", [0.25, 0.25, 0.25, 0.25])
                for i, threshold in enumerate(tier_profits):
                    if profit_pct >= threshold:
                        sell_pct = tier_sell_pcts[i] if i < len(tier_sell_pcts) else 0.25
                        signals.append(
                            {
                                "code": code,
                                "name": name,
                                "signal": "sell",
                                "confidence": 0.9,
                                "priority": "high",
                                "reasons": [
                                    f"阶梯止盈：盈利{profit_pct*100:.1f}% ≥ {threshold*100:.0f}%，卖出{sell_pct*100:.0f}%"
                                ],
                                "alert_type": "price",
                                "strategy_type": "tiered",
                                "price": current_price,
                                "sell_pct": sell_pct,
                                "tier_index": i,
                                "volume_ratio": volume_ratio,
                                "technical_data": technical_data,
                            }
                        )
                        return signals

            # 追踪止损
            if exit_strategy == "trailing" and highest_price > cost_price:
                trailing_stop_pct = stock_config.get("trailing_stop_pct", 0.03)
                trailing_stop_price = highest_price * (1 - trailing_stop_pct)
                if current_price <= trailing_stop_price:
                    signals.append(
                        {
                            "code": code,
                            "name": name,
                            "signal": "sell",
                            "confidence": 0.92,
                            "priority": "critical",
                            "reasons": [
                                f"追踪止损：从最高价{highest_price:.2f}回撤超过{trailing_stop_pct*100:.0f}%"
                            ],
                            "alert_type": "price",
                            "strategy_type": "trailing",
                            "price": current_price,
                            "volume_ratio": volume_ratio,
                            "technical_data": technical_data,
                        }
                    )
                    return signals

            # 固定止盈（兜底）
            if profit_pct >= profit_target:
                signals.append(
                    {
                        "code": code,
                        "name": name,
                        "signal": "sell",
                        "confidence": 0.9,
                        "priority": "critical",
                        "reasons": [
                            f"达到止盈目标（盈利{profit_pct * 100:.1f}%，目标{profit_target * 100:.1f}%）"
                        ],
                        "alert_type": "price",
                        "strategy_type": "all",
                        "price": current_price,
                        "volume_ratio": volume_ratio,
                        "profit_target": cost_price * (1 + profit_target),
                        "technical_data": technical_data,
                    }
                )
                return signals

        if volume_ratio > 2.0:
            direction = (
                "buy" if change_pct > 0 else ("sell" if change_pct < 0 else "hold")
            )
            if direction != "hold":
                signals.append(
                    {
                        "code": code,
                        "name": name,
                        "signal": direction,
                        "confidence": min(0.8, (volume_ratio - 2.0) / 3 + 0.6),
                        "priority": "high",
                        "reasons": [
                            f"量比突放 {volume_ratio:.1f}倍，{'放量上涨' if direction == 'buy' else '放量下跌'}"
                        ],
                        "alert_type": "volume",
                        "strategy_type": "intraday",
                        "price": current_price,
                        "volume_ratio": volume_ratio,
                        "technical_data": technical_data,
                    }
                )

        rsi = technical_data.get("rsi", 50.0)
        macd = technical_data.get("macd", {})
        kdj = technical_data.get("kdj", {})
        bollinger = technical_data.get("bollinger", {})

        if not is_holding:
            reasons = []
            strength = 0.0

            if rsi < 30:
                reasons.append(f"RSI超卖({rsi:.1f})")
                strength += 0.3
            if macd.get("histogram", 0) > 0 and macd.get("macd", 0) > macd.get(
                "signal", 0
            ):
                reasons.append("MACD金叉")
                strength += 0.25
            if kdj.get("k", 50) < 20:
                reasons.append(f"KDJ超卖(K={kdj.get('k', 50):.1f})")
                strength += 0.2
            if bollinger.get("lower", 0) and current_price <= bollinger["lower"]:
                reasons.append("价格触及布林带下轨")
                strength += 0.25

            if strength >= 0.4:
                signals.append(
                    {
                        "code": code,
                        "name": name,
                        "signal": "buy",
                        "confidence": min(0.85, strength + 0.3),
                        "priority": "high" if rsi < 25 else "medium",
                        "reasons": reasons,
                        "alert_type": "technical",
                        "strategy_type": "swing",
                        "price": current_price,
                        "volume_ratio": volume_ratio,
                        "technical_data": technical_data,
                    }
                )
        else:
            reasons = []
            strength = 0.0

            if rsi > 70:
                reasons.append(f"RSI超买({rsi:.1f})")
                strength += 0.3
            if macd.get("histogram", 0) < 0 and macd.get("macd", 0) < macd.get(
                "signal", 0
            ):
                reasons.append("MACD死叉")
                strength += 0.25
            if kdj.get("k", 50) > 80:
                reasons.append(f"KDJ超买(K={kdj.get('k', 50):.1f})")
                strength += 0.2
            if bollinger.get("upper", 0) and current_price >= bollinger["upper"]:
                reasons.append("价格触及布林带上轨")
                strength += 0.25

            if strength >= 0.4:
                signals.append(
                    {
                        "code": code,
                        "name": name,
                        "signal": "sell",
                        "confidence": min(0.85, strength + 0.3),
                        "priority": "high" if rsi > 75 else "medium",
                        "reasons": reasons,
                        "alert_type": "technical",
                        "strategy_type": "swing",
                        "price": current_price,
                        "volume_ratio": volume_ratio,
                        "technical_data": technical_data,
                    }
                )

        return signals

    def evaluate(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []
