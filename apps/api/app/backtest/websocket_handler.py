"""
WebSocket Handler for Backtest Progress Streaming.

Provides real-time progress updates during backtest execution.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Set
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

from .async_engine import AsyncBacktestEngine, BacktestStatus

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket connections for backtest streaming.

    Supports multiple concurrent clients and handles disconnections gracefully.

    Example:
        >>> manager = ConnectionManager()
        >>> await manager.connect(websocket, task_id)
        >>> await manager.broadcast(task_id, message)
    """

    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, task_id: str) -> None:
        """
        Accept and register a WebSocket connection.

        Args:
            websocket: WebSocket connection
            task_id: Backtest task identifier
        """
        await websocket.accept()

        async with self._lock:
            if task_id not in self._connections:
                self._connections[task_id] = set()
            self._connections[task_id].add(websocket)

        logger.info(f"WebSocket connected for task {task_id}")

    async def disconnect(self, websocket: WebSocket, task_id: str) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
            task_id: Backtest task identifier
        """
        async with self._lock:
            if task_id in self._connections:
                self._connections[task_id].discard(websocket)
                if not self._connections[task_id]:
                    del self._connections[task_id]

        logger.info(f"WebSocket disconnected for task {task_id}")

    async def send_message(self, websocket: WebSocket, message: dict) -> bool:
        """
        Send a JSON message to a specific WebSocket.

        Args:
            websocket: Target WebSocket
            message: Message dictionary

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.warning(f"Failed to send message: {e}")
            return False

    async def broadcast(self, task_id: str, message: dict) -> None:
        """
        Broadcast a message to all connections for a task.

        Args:
            task_id: Backtest task identifier
            message: Message dictionary to broadcast
        """
        async with self._lock:
            connections = self._connections.get(task_id, set()).copy()

        dead_connections = []

        for websocket in connections:
            if not await self.send_message(websocket, message):
                dead_connections.append(websocket)

        for ws in dead_connections:
            await self.disconnect(ws, task_id)

    async def send_progress(
        self,
        task_id: str,
        current: int,
        total: int,
        portfolio_value: float,
        return_pct: float,
        drawdown: float,
    ) -> None:
        """
        Send progress update message.

        Args:
            task_id: Backtest task identifier
            current: Current data point index
            total: Total data points
            portfolio_value: Current portfolio value
            return_pct: Current return percentage
            drawdown: Current drawdown
        """
        message = {
            "type": "progress",
            "current": current,
            "total": total,
            "portfolio_value": portfolio_value,
            "return_pct": return_pct,
            "drawdown": drawdown,
        }
        await self.broadcast(task_id, message)

    async def send_completed(
        self,
        task_id: str,
        metrics: dict,
    ) -> None:
        """
        Send completion message with final metrics.

        Args:
            task_id: Backtest task identifier
            metrics: Final backtest metrics
        """
        message = {
            "type": "completed",
            "metrics": metrics,
        }
        await self.broadcast(task_id, message)

    async def send_error(self, task_id: str, error_message: str) -> None:
        """
        Send error message.

        Args:
            task_id: Backtest task identifier
            error_message: Error description
        """
        message = {
            "type": "error",
            "message": error_message,
        }
        await self.broadcast(task_id, message)


manager = ConnectionManager()


async def websocket_backtest_endpoint(
    websocket: WebSocket,
    task_id: str,
    engine: AsyncBacktestEngine,
) -> None:
    """
    WebSocket endpoint for backtest progress streaming.

    Handles connection lifecycle and streams progress updates.

    Args:
        websocket: WebSocket connection
        task_id: Backtest task identifier
        engine: Backtest engine instance

    Protocol:
    1. Server acknowledges connection
    2. Streams progress every 10 data points
    3. Sends completion message when done
    4. Sends error message on failure
    """
    await manager.connect(websocket, task_id)

    try:
        await manager.send_message(websocket, {"type": "connected", "task_id": task_id})

        last_progress_count = -1
        initial_capital = 100000.0
        start_time = time.time()
        MAX_WAIT_SECONDS = 3600

        while True:
            if time.time() - start_time > MAX_WAIT_SECONDS:
                await manager.send_error(task_id, "Backtest timeout (max 1 hour)")
                break

            status = await engine.get_status(task_id)

            if not status or "error" in status:
                await manager.send_error(task_id, "Task not found")
                break

            task_status = status.get("status")

            if task_status == BacktestStatus.COMPLETED.value:
                result = await engine.get_result(task_id)
                if result and result.get("metrics"):
                    await manager.send_completed(task_id, result["metrics"])
                else:
                    await manager.send_completed(task_id, {})
                break

            if task_status == BacktestStatus.FAILED.value:
                error_msg = status.get("error", "Unknown error")
                await manager.send_error(task_id, error_msg)
                break

            if task_status == BacktestStatus.CANCELLED.value:
                await manager.send_error(task_id, "Backtest was cancelled")
                break

        if task_status == BacktestStatus.RUNNING.value:
            result = engine.get_task_result(task_id)
            if result:
                    config = result.config
                    initial_capital = config.get("initial_capital", 100000.0)

                    portfolio_values = result.portfolio_values or []
                    current_count = len(portfolio_values)

                    if current_count > 0 and current_count != last_progress_count:
                        if current_count % engine.PROGRESS_UPDATE_INTERVAL == 0:
                            last_progress_count = current_count

                            total_data_points = status.get("total_data_points", 0)
                            if total_data_points == 0:
                                grouped_count = 1
                            else:
                                grouped_count = total_data_points

                            current_portfolio_value = portfolio_values[-1]
                            return_pct = (current_portfolio_value - initial_capital) / initial_capital * 100

                            peak = max(portfolio_values) if portfolio_values else initial_capital
                            drawdown = (peak - current_portfolio_value) / peak * 100 if peak > 0 else 0

                            progress_data = {
                                "type": "progress",
                                "current": current_count,
                                "total": grouped_count,
                                "portfolio_value": current_portfolio_value,
                                "return_pct": return_pct,
                                "drawdown": drawdown,
                            }
                            await manager.send_message(websocket, progress_data)

            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from task {task_id}")

    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
        await manager.send_error(task_id, str(e))

    finally:
        await manager.disconnect(websocket, task_id)


def get_connection_manager() -> ConnectionManager:
    """
    Get the global connection manager instance.

    Returns:
        ConnectionManager singleton
    """
    return manager
