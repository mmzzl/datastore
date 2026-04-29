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

        ok, resolved = self._check_delisting(signal, reasons)
        if not ok:
            logger.info(f"Notification filtered: delisting detected for {code}")
            return False, "delisting_filtered"
        signal = resolved

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

    def _check_delisting(self, signal: str, reasons: List[str]) -> Tuple[bool, str]:
        for reason in reasons:
            for keyword in DELISTING_KEYWORDS:
                if keyword in reason:
                    logger.info(
                        f"Delisting keyword '{keyword}' detected, suppressing notification"
                    )
                    return False, "hold"
        return True, signal

    def check_price_zero(self, code: str, price: float) -> bool:
        """Return True if stock should be suppressed due to zero price."""
        if price is not None and price <= 0:
            logger.info(f"Notification filtered: price is {price} for {code}")
            return True
        return False

    def _make_dedup_key(self, code: str, signal: str, reasons: List[str]) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        raw = f"{today}|{code}|{signal}"
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
