import logging
from typing import List, Dict, Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory store for signals (simple in-process cache). This can be replaced by a DB later.
_signals: List[Dict[str, Any]] = []


def add_signal(signal: Dict[str, Any]) -> None:
    _signals.append(signal)


def get_latest_signals(n: int = 10) -> List[Dict[str, Any]]:
    if not _signals:
        return []
    return _signals[-n:]


@router.get("/signals/latest")
def latest_signals(n: int = 10):
    return get_latest_signals(n)


@router.post("/signals")
def push_signal(signal: Dict[str, Any]):
    add_signal(signal)
    return {"ok": True, "count": len(_signals)}
