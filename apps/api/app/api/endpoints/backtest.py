"""Backtest API Endpoints

Provides WebSocket endpoint for backtest progress streaming.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Request
import logging

from app.backtest.websocket_handler import websocket_backtest_endpoint, get_connection_manager
from app.backtest.async_engine import AsyncBacktestEngine

logger = logging.getLogger(__name__)
router = APIRouter(tags=["backtest"])


def get_backtest_engine(request: Request) -> AsyncBacktestEngine:
    """Get or create AsyncBacktestEngine instance using app.state."""
    if not hasattr(request.app.state, "backtest_engine"):
        request.app.state.backtest_engine = AsyncBacktestEngine()
    return request.app.state.backtest_engine


@router.websocket("/ws/backtest/{task_id}")
async def backtest_websocket(
    websocket: WebSocket,
    task_id: str,
    engine: AsyncBacktestEngine = Depends(get_backtest_engine),
):
    """WebSocket endpoint for backtest progress streaming.

    Streams real-time progress updates during backtest execution.

    Protocol:
    - Server sends {"type": "connected", "task_id": "..."} on connect
    - Server streams progress every 10 data points processed
    - Server sends {"type": "completed", "metrics": {...}} on completion
    - Server sends {"type": "error", "message": "..."} on failure
    """
    await websocket_backtest_endpoint(websocket, task_id, engine)
