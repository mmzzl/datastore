import pytest
from datetime import datetime
from app.monitor.alert_orchestrator import AlertOrchestrator
from app.monitor.analysis.aggregator import AlertAggregator
from app.monitor.models.alert_signal import SignalType


class TestEndToEnd:
    def test_orchestrator_initialization(self):
        orchestrator = AlertOrchestrator(
            interval_sec=5,
            watchlist=[{"code": "SH600000", "name": "测试"}],
            strategy_type="all",
        )
        assert orchestrator.interval_sec == 5
        assert len(orchestrator.watchlist) == 1
        assert orchestrator.aggregator is not None

    def test_orchestrator_has_all_watchers(self):
        orchestrator = AlertOrchestrator()
        assert orchestrator.breadth_watcher is not None
        assert orchestrator.correlated_watcher is not None
        assert orchestrator.stock_watcher is not None
        assert orchestrator.news_watcher is not None
        assert orchestrator.minute_watcher is not None

    def test_aggregator_with_real_strategy_weights(self):
        for strategy in ["intraday", "swing", "event", "all"]:
            agg = AlertAggregator(strategy_type=strategy)
            total_weight = sum(agg.weights.values())
            assert abs(total_weight - 1.0) < 0.001, (
                f"Strategy {strategy} weights sum to {total_weight}"
            )

    def test_signal_flow_through_aggregator(self):
        agg = AlertAggregator(strategy_type="intraday")
        signals = [
            {
                "code": "600000",
                "name": "测试",
                "signal": "buy",
                "confidence": 0.7,
                "priority": "high",
                "alert_type": "technical",
                "reasons": ["RSI<30"],
                "price": 10.0,
                "volume_ratio": 2.0,
                "technical_data": {"rsi": 25.0},
            }
        ]
        result = agg.aggregate(signals)
        assert len(result) == 1
        assert result[0].signal == SignalType.BUY
        assert result[0].priority == "high"
        assert result[0].target_price == 10.5
        assert result[0].stop_loss == 9.5

    def test_critical_overrides_other_signals(self):
        agg = AlertAggregator(strategy_type="all")
        signals = [
            {
                "code": "600000",
                "name": "",
                "signal": "hold",
                "confidence": 0.5,
                "priority": "low",
                "alert_type": "technical",
                "reasons": [],
                "price": 10.0,
                "volume_ratio": 0.0,
                "technical_data": {"rsi": 50.0},
            }
        ]
        result = agg.aggregate(signals)
        assert len(result) == 1
        assert result[0].signal == SignalType.HOLD
