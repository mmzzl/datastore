# Notification Dedup Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a MongoDB-backed notification dedup filter that prevents same-day duplicate pushes, blocks buy signals for delisted stocks, and skips notifications with no stock code.

**Architecture:** A `NotificationDedupFilter` class in `app/notify/dedup_filter.py` queries/inserts a `notification_log` MongoDB collection. All DingTalk send paths call `should_send()` before sending and `record_sent()` after.

**Tech Stack:** Python 3.12, MongoDB (pymongo), hashlib (stdlib)

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `apps/api/app/notify/dedup_filter.py` | Core filter: dedup, delist, no-code checks |
| Create | `apps/api/tests/notify/test_dedup_filter.py` | Unit tests for filter logic |
| Modify | `apps/api/app/notify/__init__.py` | Export `NotificationDedupFilter` |
| Modify | `apps/api/app/monitor/notification/priority_notifier.py` | Call filter before DingTalk send |
| Modify | `apps/api/app/monitor/stock_monitor.py` | Call filter before DingTalk send |

---

### Task 1: Create NotificationDedupFilter

**Files:**
- Create: `apps/api/app/notify/dedup_filter.py`
- Test: `apps/api/tests/notify/test_dedup_filter.py`

- [ ] **Step 1: Write the failing tests**

Create `apps/api/tests/notify/test_dedup_filter.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `py -3.12 -m pytest apps/api/tests/notify/test_dedup_filter.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.notify.dedup_filter'`

- [ ] **Step 3: Implement NotificationDedupFilter**

Create `apps/api/app/notify/dedup_filter.py`:

```python
import hashlib
import logging
from datetime import datetime
from typing import List, Optional, Tuple

from app.storage.mongo_client import MongoStorage
from app.core.config import settings

logger = logging.getLogger(__name__)

DELISTING_KEYWORDS = ["退市", "终止上市", "摘牌"]
NO_CODE_VALUES = {"", "MARKET", "NONE"}


class NotificationDedupFilter:
    def __init__(self):
        self._storage: Optional[MongoStorage] = None
        self._collection = None

    def _ensure_connection(self):
        if self._collection is not None:
            return
        self._storage = MongoStorage(
            host=settings.mongodb_host,
            port=settings.mongodb_port,
            db_name=settings.mongodb_database,
            username=settings.mongodb_username,
            password=settings.mongodb_password,
        )
        self._storage.connect()
        self._collection = self._storage.db["notification_log"]
        self._collection.create_index(
            [("date", 1), ("dedup_key", 1)], unique=True
        )
        self._collection.create_index(
            [("sent_at", 1)], expireAfterSeconds=172800
        )

    def should_send(
        self, code: Optional[str], signal: str, reasons: List[str]
    ) -> Tuple[bool, str]:
        self._ensure_connection()

        if not code or code.strip() == "" or code.strip().upper() in NO_CODE_VALUES:
            logger.info(f"Notification filtered: no stock code (code={code!r})")
            return False, "no_stock_code"

        signal = self._check_delisting(signal, reasons)

        if signal == "hold":
            return True, signal

        today = datetime.now().strftime("%Y-%m-%d")
        dedup_key = self._make_dedup_key(code, signal, reasons)

        existing = self._collection.find_one(
            {"date": today, "dedup_key": dedup_key}
        )
        if existing:
            logger.info(
                f"Notification filtered: duplicate (code={code}, signal={signal})"
            )
            return False, "duplicate"

        return True, signal

    def record_sent(self, code: str, signal: str, reasons: List[str]):
        self._ensure_connection()

        today = datetime.now().strftime("%Y-%m-%d")
        dedup_key = self._make_dedup_key(code, signal, reasons)
        reasons_hash = self._make_reasons_hash(reasons)

        try:
            self._collection.insert_one({
                "date": today,
                "dedup_key": dedup_key,
                "code": code,
                "signal": signal,
                "reasons_hash": reasons_hash,
                "sent_at": datetime.now(),
            })
        except Exception as e:
            logger.error(f"Failed to record notification: {e}")

    def _check_delisting(self, signal: str, reasons: List[str]) -> str:
        if signal != "buy":
            return signal
        for reason in reasons:
            for keyword in DELISTING_KEYWORDS:
                if keyword in reason:
                    logger.info(
                        f"Delisting detected ('{keyword}'), converting buy -> sell"
                    )
                    return "sell"
        return signal

    def _make_dedup_key(self, code: str, signal: str, reasons: List[str]) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        reasons_hash = self._make_reasons_hash(reasons)
        raw = f"{today}|{code}|{signal}|{reasons_hash}"
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def _make_reasons_hash(reasons: List[str]) -> str:
        sorted_reasons = "|".join(sorted(reasons))
        return hashlib.sha256(sorted_reasons.encode()).hexdigest()

    def close(self):
        if self._storage:
            try:
                self._storage.close()
            except Exception:
                pass
            self._storage = None
            self._collection = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -3.12 -m pytest apps/api/tests/notify/test_dedup_filter.py -v`

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/notify/dedup_filter.py apps/api/tests/notify/test_dedup_filter.py
git commit -m "feat: add NotificationDedupFilter with same-day dedup, delist check, no-code filter"
```

---

### Task 2: Export NotificationDedupFilter from notify package

**Files:**
- Modify: `apps/api/app/notify/__init__.py`

- [ ] **Step 1: Update __init__.py**

Read current `apps/api/app/notify/__init__.py`, then add the export:

Add `from app.notify.dedup_filter import NotificationDedupFilter` to the imports and add it to `__all__` if present, or just add the import line.

- [ ] **Step 2: Verify import works**

Run: `py -3.12 -c "from app.notify.dedup_filter import NotificationDedupFilter; print('OK')"`

Workdir: `D:\datastore\apps\api`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add apps/api/app/notify/__init__.py
git commit -m "feat: export NotificationDedupFilter from notify package"
```

---

### Task 3: Integrate filter into PriorityNotifier

**Files:**
- Modify: `apps/api/app/monitor/notification/priority_notifier.py`

- [ ] **Step 1: Write failing test for PriorityNotifier integration**

Add to `apps/api/tests/notify/test_dedup_filter.py`:

```python
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
            notifier.send(sig)
            notifier._send_high.assert_not_called()

    def test_delisted_buy_converted(self):
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `py -3.12 -m pytest apps/api/tests/notify/test_dedup_filter.py::TestPriorityNotifierIntegration -v`

Expected: FAIL (PriorityNotifier doesn't use dedup_filter yet)

- [ ] **Step 3: Modify PriorityNotifier.send()**

In `apps/api/app/monitor/notification/priority_notifier.py`, modify the `send()` method and add `dedup_filter` initialization:

Add import at top:
```python
from app.notify.dedup_filter import NotificationDedupFilter
```

In `__init__`, add:
```python
self.dedup_filter = NotificationDedupFilter()
```

In `send()`, add filter check at the very beginning of the method, before the payload creation:
```python
def send(self, alert_signal: AlertSignal):
    signal_value = alert_signal.signal.value if hasattr(alert_signal.signal, 'value') else str(alert_signal.signal)
    ok, resolved_signal = self.dedup_filter.should_send(
        alert_signal.code, signal_value, alert_signal.reasons
    )
    if not ok:
        self._logger.info(f"Notification filtered: {alert_signal.code} -> {resolved_signal}")
        return

    if resolved_signal != signal_value:
        alert_signal = AlertSignal(
            timestamp=alert_signal.timestamp,
            code=alert_signal.code,
            name=alert_signal.name,
            signal=SignalType(resolved_signal),
            confidence=alert_signal.confidence,
            priority=alert_signal.priority,
            reasons=alert_signal.reasons,
            technical_data=alert_signal.technical_data,
            market_breadth=alert_signal.market_breadth,
            correlated_assets=alert_signal.correlated_assets,
            price=alert_signal.price,
            volume_ratio=alert_signal.volume_ratio,
            alert_type=alert_signal.alert_type,
            strategy_type=alert_signal.strategy_type,
            action_price=alert_signal.action_price,
            target_price=alert_signal.target_price,
            stop_loss=alert_signal.stop_loss,
        )
        signal_value = resolved_signal

    self.dedup_filter.record_sent(alert_signal.code, signal_value, alert_signal.reasons)

    # ... rest of original send() logic (payload creation, priority dispatch) ...
```

The full modified `send()` method should be:

```python
def send(self, alert_signal: AlertSignal):
    signal_value = alert_signal.signal.value if hasattr(alert_signal.signal, 'value') else str(alert_signal.signal)

    ok, resolved_signal = self.dedup_filter.should_send(
        alert_signal.code, signal_value, alert_signal.reasons
    )
    if not ok:
        self._logger.info(f"Notification filtered: {alert_signal.code} -> {resolved_signal}")
        return

    if resolved_signal != signal_value:
        alert_signal = AlertSignal(
            timestamp=alert_signal.timestamp,
            code=alert_signal.code,
            name=alert_signal.name,
            signal=SignalType(resolved_signal),
            confidence=alert_signal.confidence,
            priority=alert_signal.priority,
            reasons=alert_signal.reasons,
            technical_data=alert_signal.technical_data,
            market_breadth=alert_signal.market_breadth,
            correlated_assets=alert_signal.correlated_assets,
            price=alert_signal.price,
            volume_ratio=alert_signal.volume_ratio,
            alert_type=alert_signal.alert_type,
            strategy_type=alert_signal.strategy_type,
            action_price=alert_signal.action_price,
            target_price=alert_signal.target_price,
            stop_loss=alert_signal.stop_loss,
        )
        signal_value = resolved_signal

    self.dedup_filter.record_sent(alert_signal.code, signal_value, alert_signal.reasons)

    priority = alert_signal.priority

    payload = NotificationPayload(
        title=self._get_title(alert_signal),
        body="\n".join(alert_signal.reasons),
        level=priority,
        code=alert_signal.code,
        signal=signal_value,
        confidence=alert_signal.confidence,
        price=alert_signal.price,
        reasons=alert_signal.reasons,
        action_price=alert_signal.action_price,
        target_price=alert_signal.target_price,
        stop_loss=alert_signal.stop_loss,
    )

    if priority == "critical":
        self._send_critical(payload, alert_signal)
    elif priority == "high":
        self._send_high(payload, alert_signal)
    elif priority == "medium":
        self._send_medium(payload, alert_signal)
    else:
        self._send_low(payload, alert_signal)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -3.12 -m pytest apps/api/tests/notify/test_dedup_filter.py -v`

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/monitor/notification/priority_notifier.py apps/api/tests/notify/test_dedup_filter.py
git commit -m "feat: integrate NotificationDedupFilter into PriorityNotifier"
```

---

### Task 4: Integrate filter into StockMonitor

**Files:**
- Modify: `apps/api/app/monitor/stock_monitor.py`

- [ ] **Step 1: Modify StockMonitor.send_notification()**

In `apps/api/app/monitor/stock_monitor.py`, add import at top:
```python
from app.notify.dedup_filter import NotificationDedupFilter
```

In `StockMonitor.__init__()`, add:
```python
self.dedup_filter = NotificationDedupFilter()
```

Modify `send_notification()` method (currently lines 421-432):

```python
def send_notification(self, notification: MonitorNotification):
    try:
        signal_value = notification.type
        reasons = [r for r in notification.signal.reasons] if notification.signal else []

        ok, resolved_signal = self.dedup_filter.should_send(
            notification.stock.code, signal_value, reasons
        )
        if not ok:
            logger.info(f"Notification filtered: {notification.stock.code} -> {resolved_signal}")
            return

        self.dedup_filter.record_sent(notification.stock.code, resolved_signal, reasons)

        self.dingtalk_notifier.send(notification.message)
        logger.info(f"Notification sent for {notification.stock.code}: {notification.type}")
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
```

- [ ] **Step 2: Verify syntax**

Run: `py -3.12 -c "from app.monitor.stock_monitor import StockMonitor; print('OK')"`

Workdir: `D:\datastore\apps\api`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add apps/api/app/monitor/stock_monitor.py
git commit -m "feat: integrate NotificationDedupFilter into StockMonitor"
```

---

### Task 5: End-to-end verification

**Files:** None (manual verification)

- [ ] **Step 1: Run all dedup filter tests**

Run: `py -3.12 -m pytest apps/api/tests/notify/test_dedup_filter.py -v`

Expected: All tests PASS

- [ ] **Step 2: Run full test suite**

Run: `py -3.12 -m pytest apps/api/tests/ -v --timeout=60`

Expected: All tests PASS

- [ ] **Step 3: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix: address issues found during verification"
```
