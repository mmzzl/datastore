import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, Query
from app.auth import get_current_user
from app.core.auth import get_storage

logger = logging.getLogger(__name__)

router = APIRouter()

DEDUP_WINDOW_HOURS = 24


def _make_dedup_key(signal: Dict[str, Any]) -> str:
    code = signal.get("code", "") or signal.get("symbol", "")
    signal_type = signal.get("signal", "")
    alert_type = signal.get("alert_type", "")
    raw = f"{code}|{signal_type}|{alert_type}"
    return hashlib.sha256(raw.encode()).hexdigest()


def add_signal(signal: Dict[str, Any]):
    try:
        storage = get_storage()
        ts = signal.get("timestamp")
        if not ts:
            signal["timestamp"] = datetime.now()
        elif isinstance(ts, str):
            try:
                signal["timestamp"] = datetime.fromisoformat(ts)
            except ValueError:
                signal["timestamp"] = datetime.now()
        if not signal.get("code") and signal.get("symbol"):
            signal["code"] = signal["symbol"]
        if not signal.get("symbol") and signal.get("code"):
            signal["symbol"] = signal["code"]
        if not signal.get("message") and signal.get("reasons"):
            signal["message"] = "; ".join(signal["reasons"][:2])
        dedup_key = _make_dedup_key(signal)
        signal["dedup_key"] = dedup_key
        cutoff = datetime.now() - timedelta(hours=DEDUP_WINDOW_HOURS)
        collection = storage.market_signals_collection
        existing = collection.find_one({"dedup_key": dedup_key, "timestamp": {"$gte": cutoff}})
        if existing:
            logger.info(f"Signal deduped: {dedup_key}")
            return str(existing["_id"])
        return storage.save_market_signal(signal)
    except Exception as e:
        logger.error(f"Failed to add signal: {e}")
        raise


@router.get("/signals/latest")
def latest_signals(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    signal_type: Optional[str] = Query(default=None, description="Filter by signal type (buy/sell/hold)"),
    code: Optional[str] = Query(default=None, description="Filter by stock code"),
    days: int = Query(default=7, ge=1, le=365, description="Look back days"),
    current_user: str = Depends(get_current_user),
):
    try:
        storage = get_storage()
        collection = storage.market_signals_collection
        query: Dict[str, Any] = {}
        if signal_type:
            query["signal"] = signal_type
        if code:
            query["code"] = code
        if days:
            since = datetime.now() - timedelta(days=days)
            query["timestamp"] = {"$gte": since}
        total = collection.count_documents(query)
        skip = (page - 1) * page_size
        cursor = collection.find(query).sort("timestamp", -1).skip(skip).limit(page_size)
        items = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if isinstance(doc.get("timestamp"), datetime):
                doc["timestamp"] = doc["timestamp"].isoformat()
            items.append(doc)
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    except Exception as e:
        logger.error(f"Failed to fetch latest signals: {e}")
        return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.post("/signals")
def push_signal(signal: Dict[str, Any], current_user: str = Depends(get_current_user)):
    try:
        storage = get_storage()
        signal_id = storage.save_market_signal(signal)
        return {"ok": True, "id": signal_id}
    except Exception as e:
        logger.error(f"Failed to push manual signal: {e}")
        return {"ok": False, "detail": str(e)}
