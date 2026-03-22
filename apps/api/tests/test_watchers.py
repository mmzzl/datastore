import pytest
from app.monitor.watchers.base import BaseWatcher
from app.monitor.watchers.breadth import MarketBreadthWatcher
from app.monitor.watchers.correlated import CorrelatedAssetWatcher
from app.monitor.watchers.stock_alert import StockAlertWatcher
from app.monitor.watchers.news_event import NewsEventWatcher
from app.monitor.watchers.minute_kline import MinuteKlineWatcher


class TestMarketBreadthWatcher:
    def test_evaluate_high_ratio_buy(self):
        watcher = MarketBreadthWatcher(data_manager=None)
        data = {
            "advance_decline_ratio": 3.0,
            "north_bound_flow": 10000.0,
            "sector_rankings": [],
        }
        signals = watcher.evaluate(data)
        assert len(signals) == 1
        assert signals[0]["signal"] == "buy"
        assert signals[0]["priority"] == "high"

    def test_evaluate_low_ratio_sell(self):
        watcher = MarketBreadthWatcher(data_manager=None)
        data = {
            "advance_decline_ratio": 0.3,
            "north_bound_flow": 0.0,
            "sector_rankings": [],
        }
        signals = watcher.evaluate(data)
        assert len(signals) == 1
        assert signals[0]["signal"] == "sell"


class TestCorrelatedAssetWatcher:
    def test_evaluate_a50_up(self):
        watcher = CorrelatedAssetWatcher(data_manager=None)
        data = {"a50_change_pct": 1.5, "usdcnh": 7.2, "dxy": 104.0}
        signals = watcher.evaluate(data)
        assert len(signals) == 1
        assert signals[0]["code"] == "A50"
        assert signals[0]["signal"] == "buy"


class TestStockAlertWatcher:
    def test_stop_loss_trigger(self):
        watcher = StockAlertWatcher(data_manager=None)
        signals = watcher.evaluate_single(
            code="600000",
            name="浦发银行",
            realtime_data={"price": 8.0, "volume_ratio": 1.0, "change_pct": -2.0},
            technical_data={"rsi": 50.0, "macd": {}, "kdj": {}, "bollinger": {}},
            capital_flow=[],
            watchlist=[
                {"code": "600000", "hold": True, "cost_price": 10.0, "stop_loss": 0.1}
            ],
        )
        assert len(signals) == 1
        assert signals[0]["signal"] == "sell"
        assert signals[0]["priority"] == "critical"
        assert "止损" in signals[0]["reasons"][0]

    def test_buy_signal_oversold(self):
        watcher = StockAlertWatcher(data_manager=None)
        signals = watcher.evaluate_single(
            code="600000",
            name="浦发银行",
            realtime_data={"price": 8.0, "volume_ratio": 1.0, "change_pct": 0.5},
            technical_data={
                "rsi": 25.0,
                "macd": {"histogram": 0.1, "macd": 0.2, "signal": 0.1},
                "kdj": {},
                "bollinger": {},
            },
            capital_flow=[],
            watchlist=[{"code": "600000", "hold": False}],
        )
        assert any(s["signal"] == "buy" for s in signals)


class TestNewsEventWatcher:
    def test_keyword_matching(self):
        watcher = NewsEventWatcher(
            data_manager=None,
            keyword_rules={"黑天鹅": ["地震", "疫情"], "政策": ["降准", "加息"]},
        )
        data = {
            "news": [{"title": "疫情爆发导致股市暴跌", "content": "", "time": ""}],
            "timestamp": None,
        }
        signals = watcher.evaluate(data)
        assert len(signals) == 1
        assert signals[0]["signal"] == "sell"
        assert signals[0]["priority"] == "critical"


class TestMinuteKlineWatcher:
    def test_breakout_signal(self):
        watcher = MinuteKlineWatcher(data_manager=None, frequency="5")
        assert watcher.evaluate({}) == []
