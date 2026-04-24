import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.notify.dedup_filter import NotificationDedupFilter


@pytest.fixture
def mock_collection():
    coll = MagicMock()
    coll.create_index = MagicMock()
    coll.find_one = MagicMock(return_value=None)
    coll.insert_one = MagicMock()
    return coll


@pytest.fixture
def filter_instance(mock_collection):
    with patch("app.notify.dedup_filter.MongoStorage") as MockStorage:
        storage = MockStorage.return_value
        storage.db = {"notification_log": mock_collection}
        storage.connect = MagicMock()
        storage.close = MagicMock()
        f = NotificationDedupFilter()
        f._collection = mock_collection
        return f


class TestNoStockCodeFilter:
    def test_empty_code_filtered(self, filter_instance):
        ok, signal = filter_instance.should_send("", "buy", ["RSI oversold"])
        assert ok is False
        assert signal == "no_stock_code"

    def test_market_code_filtered(self, filter_instance):
        ok, signal = filter_instance.should_send("MARKET", "buy", ["政策利好"])
        assert ok is False
        assert signal == "no_stock_code"

    def test_whitespace_code_filtered(self, filter_instance):
        ok, signal = filter_instance.should_send("  ", "buy", ["test"])
        assert ok is False
        assert signal == "no_stock_code"

    def test_none_code_filtered(self, filter_instance):
        ok, signal = filter_instance.should_send(None, "buy", ["test"])
        assert ok is False
        assert signal == "no_stock_code"

    def test_valid_code_passes(self, filter_instance):
        ok, signal = filter_instance.should_send("SH600519", "buy", ["test"])
        assert ok is True


class TestDelistedStockFilter:
    def test_delisted_buy_converted_to_sell(self, filter_instance):
        ok, signal = filter_instance.should_send(
            "SH600519", "buy", ["新闻命中关键词「退市」"]
        )
        assert ok is True
        assert signal == "sell"

    def test_delisted_sell_stays_sell(self, filter_instance):
        ok, signal = filter_instance.should_send(
            "SH600519", "sell", ["新闻命中关键词「退市」"]
        )
        assert ok is True
        assert signal == "sell"

    def test_delisted_keyword_terminate(self, filter_instance):
        ok, signal = filter_instance.should_send(
            "SH600519", "buy", ["公司将被终止上市"]
        )
        assert ok is True
        assert signal == "sell"

    def test_delisted_keyword_delist(self, filter_instance):
        ok, signal = filter_instance.should_send(
            "SH600519", "buy", ["面临摘牌风险"]
        )
        assert ok is True
        assert signal == "sell"

    def test_non_delisted_buy_stays_buy(self, filter_instance):
        ok, signal = filter_instance.should_send(
            "SH600519", "buy", ["业绩预增"]
        )
        assert ok is True
        assert signal == "buy"


class TestSameDayDedup:
    def test_first_send_passes(self, filter_instance, mock_collection):
        mock_collection.find_one.return_value = None
        ok, signal = filter_instance.should_send("SH600519", "buy", ["RSI oversold"])
        assert ok is True
        assert signal == "buy"

    def test_duplicate_blocked(self, filter_instance, mock_collection):
        today = datetime.now().strftime("%Y-%m-%d")
        mock_collection.find_one.return_value = {"date": today, "dedup_key": "some_key"}
        ok, signal = filter_instance.should_send("SH600519", "buy", ["RSI oversold"])
        assert ok is False
        assert signal == "duplicate"

    def test_different_reasons_not_blocked(self, filter_instance, mock_collection):
        mock_collection.find_one.return_value = None
        ok, signal = filter_instance.should_send("SH600519", "buy", ["MACD golden cross"])
        assert ok is True

    def test_record_sent_inserts_doc(self, filter_instance, mock_collection):
        filter_instance.record_sent("SH600519", "buy", ["RSI oversold"])
        assert mock_collection.insert_one.called
        doc = mock_collection.insert_one.call_args[0][0]
        assert doc["date"] == datetime.now().strftime("%Y-%m-%d")
        assert doc["code"] == "SH600519"
        assert doc["signal"] == "buy"

    def test_hold_signal_not_filtered_by_dedup(self, filter_instance, mock_collection):
        ok, signal = filter_instance.should_send("SH600519", "hold", ["test"])
        assert ok is True
        assert signal == "hold"


class TestDedupKeyGeneration:
    def test_same_inputs_same_key(self, filter_instance):
        key1 = filter_instance._make_dedup_key("SH600519", "buy", ["RSI"])
        key2 = filter_instance._make_dedup_key("SH600519", "buy", ["RSI"])
        assert key1 == key2

    def test_different_reasons_different_key(self, filter_instance):
        key1 = filter_instance._make_dedup_key("SH600519", "buy", ["RSI"])
        key2 = filter_instance._make_dedup_key("SH600519", "buy", ["MACD"])
        assert key1 != key2

    def test_reasons_order_invariant(self, filter_instance):
        key1 = filter_instance._make_dedup_key("SH600519", "buy", ["RSI", "MACD"])
        key2 = filter_instance._make_dedup_key("SH600519", "buy", ["MACD", "RSI"])
        assert key1 == key2


class TestPriorityNotifierIntegration:
    def test_no_code_signal_skipped(self):
        from app.monitor.models.alert_signal import AlertSignal, SignalType
        from app.monitor.notification.priority_notifier import PriorityNotifier

        notifier = PriorityNotifier(dingtalk_client=None)
        sig = AlertSignal(
            timestamp=datetime.now(),
            code="",
            name="",
            signal=SignalType.BUY,
            confidence=0.8,
            priority="high",
            reasons=["test"],
        )
        with patch.object(notifier, "dedup_filter") as mock_filter:
            mock_filter.should_send.return_value = (False, "no_stock_code")
            mock_filter.record_sent = MagicMock()
            notifier._send_high = MagicMock()
            notifier.send(sig)
            notifier._send_high.assert_not_called()

    def test_duplicate_signal_skipped(self):
        from app.monitor.models.alert_signal import AlertSignal, SignalType
        from app.monitor.notification.priority_notifier import PriorityNotifier

        notifier = PriorityNotifier(dingtalk_client=None)
        sig = AlertSignal(
            timestamp=datetime.now(),
            code="SH600519",
            name="贵州茅台",
            signal=SignalType.BUY,
            confidence=0.8,
            priority="high",
            reasons=["RSI oversold"],
        )
        with patch.object(notifier, "dedup_filter") as mock_filter:
            mock_filter.should_send.return_value = (False, "duplicate")
            mock_filter.record_sent = MagicMock()
            notifier._send_high = MagicMock()
            notifier.send(sig)
            notifier._send_high.assert_not_called()

    def test_delisted_buy_converted_and_sent(self):
        from app.monitor.models.alert_signal import AlertSignal, SignalType
        from app.monitor.notification.priority_notifier import PriorityNotifier

        notifier = PriorityNotifier(dingtalk_client=None)
        sig = AlertSignal(
            timestamp=datetime.now(),
            code="SH600519",
            name="贵州茅台",
            signal=SignalType.BUY,
            confidence=0.8,
            priority="high",
            reasons=["新闻命中关键词「退市」"],
        )
        with patch.object(notifier, "dedup_filter") as mock_filter:
            mock_filter.should_send.return_value = (True, "sell")
            mock_filter.record_sent = MagicMock()
            dingtalk = MagicMock()
            notifier._dingtalk = dingtalk
            notifier.send(sig)
            assert mock_filter.record_sent.called
