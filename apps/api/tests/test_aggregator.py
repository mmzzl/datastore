import pytest
from datetime import datetime
from app.monitor.analysis.aggregator import AlertAggregator
from app.monitor.models.alert_signal import SignalType


class TestAlertAggregator:
    def test_aggregate_high_score_buy(self):
        agg = AlertAggregator(strategy_type="all")
        signals = [
            {
                "code": "600000",
                "name": "浦发银行",
                "signal": "buy",
                "confidence": 0.8,
                "priority": "high",
                "alert_type": "technical",
                "reasons": ["RSI低于30"],
                "price": 9.5,
                "volume_ratio": 2.0,
                "technical_data": {"rsi": 25.0},
            }
        ]
        result = agg.aggregate(signals)
        assert len(result) == 1
        assert result[0].signal == SignalType.BUY

    def test_aggregate_low_score_sell(self):
        agg = AlertAggregator(strategy_type="all")
        signals = [
            {
                "code": "600000",
                "name": "浦发银行",
                "signal": "sell",
                "confidence": 0.15,
                "priority": "medium",
                "alert_type": "technical",
                "reasons": [],
                "price": 9.5,
                "volume_ratio": 0.5,
                "technical_data": {"rsi": 80.0},
            }
        ]
        result = agg.aggregate(signals)
        assert len(result) == 1
        assert result[0].signal == SignalType.SELL

    def test_aggregate_dedup(self):
        agg = AlertAggregator(strategy_type="all")
        signals = [
            {
                "code": "600000",
                "name": "浦发银行",
                "signal": "buy",
                "confidence": 0.8,
                "priority": "high",
                "alert_type": "technical",
                "reasons": [],
                "price": 9.5,
                "volume_ratio": 0.0,
                "technical_data": {},
            }
        ]
        result1 = agg.aggregate(signals)
        assert len(result1) == 1
        result2 = agg.aggregate(signals)
        assert len(result2) == 0

    def test_aggregate_priority_order(self):
        agg = AlertAggregator(strategy_type="all")
        signals = [
            {
                "code": "B",
                "name": "",
                "signal": "buy",
                "confidence": 0.5,
                "priority": "low",
                "alert_type": "technical",
                "reasons": [],
                "price": 0.0,
                "volume_ratio": 0.0,
                "technical_data": {},
            },
            {
                "code": "A",
                "name": "",
                "signal": "buy",
                "confidence": 0.5,
                "priority": "critical",
                "alert_type": "price",
                "reasons": [],
                "price": 0.0,
                "volume_ratio": 0.0,
                "technical_data": {},
            },
            {
                "code": "C",
                "name": "",
                "signal": "buy",
                "confidence": 0.5,
                "priority": "high",
                "alert_type": "volume",
                "reasons": [],
                "price": 0.0,
                "volume_ratio": 0.0,
                "technical_data": {},
            },
        ]
        result = agg.aggregate(signals)
        assert len(result) == 3
        assert result[0].code == "A"
        assert result[1].code == "C"
        assert result[2].code == "B"

    def test_aggregate_empty(self):
        agg = AlertAggregator()
        assert agg.aggregate([]) == []

    def test_strategy_weights_intraday(self):
        agg = AlertAggregator(strategy_type="intraday")
        assert agg.weights["volume"] == 0.25
        assert agg.weights["technical"] == 0.30

    def test_strategy_weights_event(self):
        agg = AlertAggregator(strategy_type="event")
        assert agg.weights["event"] == 0.40
        assert agg.weights["correlation"] == 0.30
