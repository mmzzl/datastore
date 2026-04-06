import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from app.auth import get_current_user

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


def init_test_signals() -> None:
    """Initialize test signals for development."""
    if _signals:
        logger.info(f"Signals already initialized with {len(_signals)} items")
        return

    test_signals = [
        {
            "type": "breakout",
            "symbol": "SH600519",
            "name": "贵州茅台",
            "signal": "price_breakout_up",
            "price": 1850.50,
            "volume": 152300,
            "message": "股价突破20日高点，成交量放大",
            "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
        },
        {
            "type": "volume",
            "symbol": "SH000001",
            "name": "上证指数",
            "signal": "volume_surge",
            "price": 3250.80,
            "volume": 425000000,
            "message": "成交量较前一日放大50%",
            "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
        },
        {
            "type": "ma",
            "symbol": "SH601318",
            "name": "中国平安",
            "signal": "ma_golden_cross",
            "price": 52.30,
            "volume": 89500,
            "message": "MA5上穿MA20，形成金叉",
            "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
        },
        {
            "type": "rsi",
            "symbol": "SZ000858",
            "name": "五粮液",
            "signal": "rsi_oversold",
            "price": 148.20,
            "volume": 42300,
            "message": "RSI(14)进入超卖区域(<30)",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "type": "macd",
            "symbol": "SH600036",
            "name": "招商银行",
            "signal": "macd_cross_up",
            "price": 38.50,
            "volume": 67800,
            "message": "MACD金叉，DIF上穿DEA",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
        },
        {
            "type": "breakout",
            "symbol": "SZ002594",
            "name": "比亚迪",
            "signal": "price_breakout_down",
            "price": 268.90,
            "volume": 125600,
            "message": "股价跌破20日低点",
            "timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),
        },
        {
            "type": "volume",
            "symbol": "SH688111",
            "name": "金山办公",
            "signal": "volume_surge",
            "price": 285.60,
            "volume": 23400,
            "message": "成交量异常放大",
            "timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
        },
        {
            "type": "ma",
            "symbol": "SH600900",
            "name": "长江电力",
            "signal": "ma_death_cross",
            "price": 24.80,
            "volume": 34500,
            "message": "MA5下穿MA20，形成死叉",
            "timestamp": (datetime.now() - timedelta(hours=5)).isoformat(),
        },
    ]

    for signal in test_signals:
        add_signal(signal)

    logger.info(f"Initialized {len(_signals)} test signals")


@router.on_event("startup")
async def startup_event():
    """Initialize test signals on startup."""
    init_test_signals()


@router.get("/signals/latest")
def latest_signals(n: int = 10, current_user: str = Depends(get_current_user)):
    return get_latest_signals(n)


@router.post("/signals")
def push_signal(signal: Dict[str, Any], current_user: str = Depends(get_current_user)):
    add_signal(signal)
    return {"ok": True, "count": len(_signals)}
