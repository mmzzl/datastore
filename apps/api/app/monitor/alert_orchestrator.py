import logging
import threading
import time
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Callable

from app.data_source import DataSourceManager
from app.monitor.market_signals import add_signal
from app.monitor.analysis.aggregator import AlertAggregator
from app.monitor.watchers import (
    MarketBreadthWatcher,
    CorrelatedAssetWatcher,
    StockAlertWatcher,
    NewsEventWatcher,
    MinuteKlineWatcher,
)
from app.monitor.models.alert_signal import AlertSignal, SignalType
from app.monitor.models.alert_rule import AlertPriority


class AlertOrchestrator:
    def __init__(
        self,
        data_manager: Optional[DataSourceManager] = None,
        interval_sec: int = 60,
        watchlist: Optional[List[Dict[str, Any]]] = None,
        strategy_type: str = "all",
        news_keywords: Optional[Dict[str, List[str]]] = None,
        report_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.data_manager = data_manager or DataSourceManager()
        self.interval_sec = max(1, int(interval_sec))
        self.watchlist = watchlist or self._default_watchlist()
        self.strategy_type = strategy_type
        self.report_callback = report_callback
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._logger = logging.getLogger(__name__)

        self.breadth_watcher = MarketBreadthWatcher(self.data_manager)
        self.correlated_watcher = CorrelatedAssetWatcher(self.data_manager)
        self.stock_watcher = StockAlertWatcher(self.data_manager)
        self.news_watcher = NewsEventWatcher(
            self.data_manager, news_keywords or self._default_keywords()
        )
        self.minute_watcher = MinuteKlineWatcher(self.data_manager, frequency="5")

        self.aggregator = AlertAggregator(strategy_type=strategy_type)

        self.signals_log: List[Dict[str, Any]] = []

    def _default_watchlist(self) -> List[Dict[str, Any]]:
        return [
            {"code": "SH600000", "name": "浦发银行"},
            {"code": "SH600519", "name": "贵州茅台"},
        ]

    def _default_keywords(self) -> Dict[str, List[str]]:
        return {
            "政策": ["降准", "加息", "LPR", "监管"],
            "利好": ["业绩预增", "订单", "合作", "重组"],
            "利空": ["业绩预减", "减持", "诉讼"],
            "黑天鹅": ["疫情", "地震", "制裁", "断供"],
        }

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._logger.info("AlertOrchestrator started")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._logger.info("AlertOrchestrator stopped")

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception as e:
                self._logger.error(f"AlertOrchestrator run error: {e}")
            time.sleep(self.interval_sec)

    def run_once(self):
        all_signals: List[Dict[str, Any]] = []

        try:
            breadth_signals = self.breadth_watcher.run_once()
            all_signals.extend(breadth_signals)
        except Exception as e:
            self._logger.error(f"BreadthWatcher error: {e}")

        try:
            correlated_signals = self.correlated_watcher.run_once()
            all_signals.extend(correlated_signals)
        except Exception as e:
            self._logger.error(f"CorrelatedAssetWatcher error: {e}")

        try:
            news_signals = self.news_watcher.run_once()
            all_signals.extend(news_signals)
        except Exception as e:
            self._logger.error(f"NewsEventWatcher error: {e}")

        for item in self.watchlist:
            code = item.get("code")
            name = item.get("name", code)
            if not code:
                continue

            try:
                rt = self.data_manager.get_realtime_data(code)
                if not rt:
                    continue

                technical = self._gather_technical_data(code)

                capital_flow = self.data_manager.get_capital_flow(code, days=5)

                minute_signals = []
                if self.strategy_type in ("intraday", "all"):
                    minute_signals = self.minute_watcher.evaluate_single(
                        code, name, frequency="5", days=2
                    )

                stock_signals = self.stock_watcher.evaluate_single(
                    code, name, rt, technical, capital_flow, self.watchlist
                )

                all_signals.extend(stock_signals)
                all_signals.extend(minute_signals)

            except Exception as e:
                self._logger.error(f"StockWatcher error for {code}: {e}")

        aggregated = self.aggregator.aggregate(all_signals)

        for alert_signal in aggregated:
            self._emit_signal(alert_signal)

    def _gather_technical_data(self, code: str) -> Dict[str, Any]:
        try:
            end = date.today()
            start = end - timedelta(days=60)
            klines = self.data_manager.get_kline(
                code,
                start.strftime("%Y-%m-%d"),
                end.strftime("%Y-%m-%d"),
                frequency="d",
                adjust_flag="3",
            )
            if not klines:
                return {}
            closes = [k.close for k in klines]
            highs = [k.high for k in klines]
            lows = [k.low for k in klines]

            from app.monitor.analysis.technical import TechnicalAnalyzer

            ta = TechnicalAnalyzer()
            return ta.analyze_stock({"close": closes, "high": highs, "low": lows})
        except Exception:
            return {}

    def _emit_signal(self, alert_signal: AlertSignal):
        sig_dict = alert_signal.to_dict()

        try:
            add_signal(sig_dict)
        except Exception:
            pass

        self.signals_log.append(sig_dict)

        if self.report_callback:
            try:
                self.report_callback(sig_dict)
            except Exception:
                pass

        if alert_signal.signal != SignalType.HOLD:
            self._logger.info(
                f"Alert: [{alert_signal.priority.upper()}] {alert_signal.code} -> {alert_signal.signal.value} "
                f"(confidence={alert_signal.confidence:.2f}) @ {alert_signal.price}"
            )

    def backtest(self, historical: List[Dict[str, Any]]):
        self._logger.info("AlertOrchestrator backtest (skeleton)")
        pass


__all__ = ["AlertOrchestrator"]
