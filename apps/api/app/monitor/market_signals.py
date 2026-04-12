import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from app.auth import get_current_user
from app.storage.mongo_client import MongoStorage

logger = logging.getLogger(__name__)

router = APIRouter()
storage = MongoStorage(
    host="localhost", port=27017, db_name="datastore"
)  # This will be overridden by app settings in actual usage


def add_signal(signal: Dict[str, Any]):
    """
    Saves a market signal to the database.
    """
    try:
        return storage.save_market_signal(signal)
    except Exception as e:
        logger.error(f"Failed to add signal: {e}")
        raise


@router.get("/signals/latest")
def latest_signals(n: int = 10, current_user: str = Depends(get_current_user)):
    """
    Get the latest generated market signals from MongoDB.
    """
    try:
        return storage.get_recent_signals(limit=n)
    except Exception as e:
        logger.error(f"Failed to fetch latest signals: {e}")
        return []


@router.post("/signals")
def push_signal(signal: Dict[str, Any], current_user: str = Depends(get_current_user)):
    """
    Manually push a signal to the system.
    """
    try:
        signal_id = storage.save_market_signal(signal)
        return {"ok": True, "id": signal_id}
    except Exception as e:
        logger.error(f"Failed to push manual signal: {e}")
        return {"ok": False, "detail": str(e)}
