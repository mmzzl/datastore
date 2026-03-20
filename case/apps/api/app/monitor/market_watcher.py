import logging
import threading
import time
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Callable

from app.data_source import DataSourceManager
from app.monitor.brain.analyzer import BrainAnalyzer
from app.monitor.analysis.technical import TechnicalAnalyzer


class MarketWatcher:
    """市场盯盘模块：对 watchlist 中的股票进行实时信号监控并产出交易信号"""

    def __init__(
        self,
        data_manager: Optional[DataSourceManager] = None,
        interval_sec: int = 60,
        watchlist: Optional[List[Dict[str, Any]]] = None,
        days: int = 5,
        report_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.data_manager = data_manager or DataSourceManager()
        self.brain = BrainAnalyzer()
        self._ta = TechnicalAnalyzer()
        self.interval_sec = max(1, int(interval_sec))
        self.watchlist = watchlist or self._default_watchlist()
        self.days = int(days)
        self.report_callback = report_callback
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._logger = logging.getLogger(__name__)

        # 简单状态记录，便于外部查看盯盘状态
        self.signals_log: List[Dict[str, Any]] = []

    def _default_watchlist(self) -> List[Dict[str, Any]]:
        # 默认示例；请替换为实际需要盯盘的股票列表，代码格式可以是 SH600000 或 600000
        return [
            {"code": "SH600000", "name": "浦发银行"},
            {"code": "SH600519", "name": "贵州茅台"},
        ]

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._logger.info("MarketWatcher started")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._logger.info("MarketWatcher stopped")

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception as e:
                self._logger.error(f"MarketWatcher run error: {e}")
            time.sleep(self.interval_sec)

    def run_once(self):
        for item in self.watchlist:
            code_val = item.get("code")
            if not isinstance(code_val, str) or not code_val:
                continue
            code = code_val
            rt = self.data_manager.get_realtime_data(code)
            current_price = 0.0
            if isinstance(rt, dict):
                current_price = (
                    rt.get("price") or rt.get("最新价") or rt.get("close") or 0.0
                )
            cap_flow = self.data_manager.get_capital_flow(code, days=self.days)

            # gather technical data and compute scores
            technical_data = self._gather_technical_data(str(code))
            tech_score = self._calculate_tech_score(technical_data)
            cap_score = self._calculate_capital_score(cap_flow)
            sentiment_score = 0.5
            total_score = (
                (tech_score * 0.5) + (cap_score * 0.3) + (sentiment_score * 0.2)
            )

            action, reasons = self._determine_action_and_reasons(
                total_score, technical_data, cap_flow, current_price
            )
            target_price, entry_price, stop_loss = self._price_targets(current_price)

            signal = {
                "timestamp": int(time.time()),
                "code": code,
                "action": action,
                "confidence": total_score,
                "target_price": target_price,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "reasons": reasons,
                "price": current_price,
                "capital_flow": cap_flow,
            }

            self.signals_log.append(signal)
            if self.report_callback:
                try:
                    self.report_callback(signal)
                except Exception:
                    pass

            if action in ("buy", "sell"):
                self._logger.info(
                    f"MarketWatcher signal: {signal['code']} -> {signal['action']} @ {signal['target_price']}"
                )

    # 简单回测入口（骨架实现，便于扩展）
    def backtest(self, historical: List[Dict[str, Any]]):
        """对市场观测逻辑进行回测，historical 为历史行情记录列表"""
        self._logger.info("Starting market watcher backtest (skeleton)")
        # 这里给出一个最小实现：对历史数据逐条触发信号计算，但不执行真实交易
        for bar in historical:
            code_val = bar.get("code")
            if not isinstance(code_val, str) or not code_val:
                continue
            code = code_val
            price = bar.get("price", 0.0)
            technical_data = self._gather_technical_data(str(code))
            tech_score = self._calculate_tech_score(technical_data)
            cap_flow = self.data_manager.get_capital_flow(code, days=self.days)
            cap_score = self._calculate_capital_score(cap_flow)
            total_score = (tech_score * 0.5) + (cap_score * 0.3) + (0.5 * 0.2)
            action, reasons = self._determine_action_and_reasons(
                total_score, technical_data, cap_flow, price
            )
            self._logger.debug(
                f"Backtest {code} at {price}: action={action}, score={total_score}"
            )
        self._logger.info("Backtest finished")

    def _gather_technical_data(self, code: str) -> Dict[str, Any]:
        # 尝试获取最近一段时间的 K 线数据，用 TechnicalAnalyzer 计算指标
        try:
            from datetime import date, timedelta

            end_date = date.today()
            start_date = end_date - timedelta(days=60)
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            klines = self.data_manager.get_kline(
                code, start_str, end_str, frequency="d", adjust_flag="3"
            )
            closes = [k.close for k in klines]
            highs = [k.high for k in klines]
            lows = [k.low for k in klines]
            if closes:
                tech = self._ta.analyze_stock(
                    {"close": closes, "high": highs, "low": lows}
                )
                return tech
        except Exception:
            pass
        return {
            "rsi": 50.0,
            "macd": {"macd": 0.0, "signal": 0.0, "histogram": 0.0},
            "kdj": {"k": 50.0, "d": 50.0, "j": 50.0},
            "bollinger": {"upper": 0.0, "middle": 0.0, "lower": 0.0},
        }

    def _calculate_tech_score(self, technical_data: Dict[str, Any]) -> float:
        try:
            rsi = technical_data.get("rsi", 50.0)
            scores = []
            if rsi < 30:
                scores.append(0.8)
            elif rsi > 70:
                scores.append(0.2)
            else:
                scores.append(0.5)
            macd = technical_data.get("macd", {})
            macd_value = macd.get("macd", 0.0)
            signal_value = macd.get("signal", 0.0)
            histogram = macd.get("histogram", 0.0)
            if macd_value > signal_value and histogram > 0:
                scores.append(0.7)
            elif macd_value < signal_value and histogram < 0:
                scores.append(0.3)
            else:
                scores.append(0.5)
            kdj = technical_data.get("kdj", {})
            k_value = kdj.get("k", 50.0)
            if k_value < 20:
                scores.append(0.8)
            elif k_value > 80:
                scores.append(0.2)
            else:
                scores.append(0.5)
            return sum(scores) / len(scores) if scores else 0.5
        except Exception:
            return 0.5

    def _calculate_capital_score(self, cap_flow: List[Dict[str, Any]]) -> float:
        try:
            net_vals = [d.get("net_inflow", 0) for d in cap_flow] if cap_flow else []
            avg = sum(net_vals) / len(net_vals) if net_vals else 0
            if avg > 0:
                return min(0.8, avg / 1000000)
            else:
                return max(0.2, 1 - abs(avg) / 1000000)
        except Exception:
            return 0.5

    def _determine_action_and_reasons(
        self,
        total_score: float,
        technical_data: Dict[str, Any],
        cap_flow: List[Dict[str, Any]],
        current_price: float,
    ):
        rsi = technical_data.get("rsi", 50.0)
        action = "hold"
        if total_score > 0.7 or rsi < 25:
            action = "buy"
        elif total_score < 0.3 or rsi > 75:
            action = "sell"
        reasons = []
        if rsi < 30:
            reasons.append(f"RSI低于30，可能反弹")
        if rsi > 70:
            reasons.append(f"RSI高于70，可能回撤")
        macd = technical_data.get("macd", {})
        if macd.get("macd", 0) > macd.get("signal", 0):
            reasons.append("MACD金叉")
        else:
            reasons.append("MACD死叉")
        if cap_flow:
            avg_net = sum([d.get("net_inflow", 0) for d in cap_flow]) / len(cap_flow)
            if avg_net > 0:
                reasons.append("市场资金净流入")
            else:
                reasons.append("市场资金净流出")
        reasons.append(f"总分: {total_score:.3f}")
        return action, reasons

    def _price_targets(self, current_price: float):
        target = current_price * 1.05
        entry = current_price * 0.95
        stop = current_price * 0.9
        return target, entry, stop


__all__ = ["MarketWatcher"]
