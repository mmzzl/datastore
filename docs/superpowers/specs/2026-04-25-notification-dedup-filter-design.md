# Notification Dedup Filter Design

## Problem

The market monitoring system sends duplicate DingTalk notifications for the same stock/signal within a day, sends buy signals for delisted stocks, and sends notifications that contain no stock code.

Current dedup is in-memory only (5-min window in `AlertAggregator`, `PriorityNotifier`, `NewsEventWatcher`), lost on process restart, and does not cover `StockMonitor` at all.

## Requirements

1. **Same-day dedup**: Identical message (same stock + signal type + reasons) not re-pushed within the same day. Reset next day.
2. **Delisted stock filter**: If the news mentions delisting ("退市", "终止上市", "摘牌"), do not send a buy signal — convert to sell.
3. **No-stock-code filter**: If the signal has no meaningful stock code (empty, "MARKET", etc.), skip notification.

## Design

### Core Component: `NotificationDedupFilter`

New file: `app/notify/dedup_filter.py`

MongoDB collection: `notification_log`

#### Document Schema

```json
{
  "date": "2026-04-25",
  "dedup_key": "sha256_hex",
  "code": "SH600519",
  "signal": "buy",
  "reasons_hash": "sha256_hex",
  "sent_at": "2026-04-25T10:30:00"
}
```

- `dedup_key` = SHA256(`date` + `code` + `signal` + `reasons_hash`)
- `reasons_hash` = SHA256(sorted `reasons` strings joined with `|`)
- TTL index on `sent_at` with 48h expiry (allows next-day reset plus buffer)

#### `should_send(code, signal, reasons) -> (bool, str)`

Returns `(True, signal)` if the notification should be sent, `(False, reason)` if it should be skipped.

Logic order:
1. **No-stock-code check**: If `code` is empty, `"MARKET"`, or whitespace-only → return `(False, "no_stock_code")`
2. **Delisted stock check**: If any reason contains delisting keyword AND signal is "buy" → mutate signal to "sell"
3. **Same-day dedup check**: Compute `dedup_key`, query `{date: today, dedup_key: key}`. If found → return `(False, "duplicate")`

After a successful send, caller calls `record_sent(code, signal, reasons)` to log the notification.

#### Delisting Keywords

`["退市", "终止上市", "摘牌"]`

### Integration Points

#### 1. `PriorityNotifier.send()` (alert_orchestrator path)

Before calling `self._dingtalk.send()`, call `dedup_filter.should_send()`. If filtered, skip and log. If delisted, update signal before sending. After successful send, call `record_sent()`.

#### 2. `StockMonitor.send_notification()` (stock_monitor path)

Before calling `self.dingtalk_notifier.send()`, extract code/signal/reasons from `MonitorNotification`, call `dedup_filter.should_send()`. Same filter logic.

#### 3. DailyScanner / IntradayMonitor

These do not send DingTalk notifications directly (they only write to MongoDB `watch_list` / `market_signals`). No changes needed.

### MongoDB Indexes

- Unique compound index: `{date: 1, dedup_key: 1}`
- TTL index: `{sent_at: 1}` with expireAfterSeconds=172800 (48h)

### Dependencies

- `app.storage.mongo_client.MongoStorage` for DB access
- `app.core.config.settings` for connection parameters (same as existing `news_event.py` pattern)
- `hashlib` for SHA256 (stdlib)
