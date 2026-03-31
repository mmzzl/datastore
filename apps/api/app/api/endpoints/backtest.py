"""Backtest API Endpoints

Provides REST and WebSocket endpoints for backtest management.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket
from pydantic import BaseModel, Field, field_validator

from app.backtest.websocket_handler import websocket_backtest_endpoint, get_connection_manager
from app.backtest.async_engine import AsyncBacktestEngine
from app.backtest.strategies.factory import StrategyFactory
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["backtest"])

VALID_STRATEGY_TYPES = ["ma_cross", "rsi", "bollinger", "macd", "qlib_model"]


class BacktestRunRequest(BaseModel):
    """Request model for running a backtest."""
    strategy: str = Field(..., description="Strategy type")
    params: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
    start_date: str = Field(..., description="Backtest start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Backtest end date (YYYY-MM-DD)")
    initial_capital: float = Field(default=100000.0, gt=0, description="Initial capital")
    instruments: List[str] = Field(default_factory=list, description="List of stock codes")

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, v: str) -> str:
        if v.lower() not in VALID_STRATEGY_TYPES:
            raise ValueError(f"Invalid strategy. Supported: {VALID_STRATEGY_TYPES}")
        return v.lower()

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: str, info) -> str:
        start_date = info.data.get("start_date")
        if start_date and v <= start_date:
            raise ValueError("end_date must be greater than start_date")
        return v


class BacktestRunResponse(BaseModel):
    """Response model for backtest run."""
    task_id: str
    status: str
    message: str


class BacktestResultItem(BaseModel):
    """Model for backtest result list item."""
    task_id: str
    strategy: str
    date_range: str
    key_metrics: Dict[str, Any]


class BacktestResultsResponse(BaseModel):
    """Response model for paginated backtest results."""
    items: List[BacktestResultItem]
    total: int
    page: int
    page_size: int


def get_storage():
    """Get MongoDB storage instance."""
    from app.storage import MongoStorage
    storage = MongoStorage(
        host=settings.mongodb_host,
        port=settings.mongodb_port,
        db_name=settings.mongodb_database,
        username=settings.mongodb_username,
        password=settings.mongodb_password,
    )
    storage.connect()
    return storage


def get_backtest_engine(request: Request) -> AsyncBacktestEngine:
    """Get or create AsyncBacktestEngine instance using app.state."""
    if not hasattr(request.app.state, "backtest_engine"):
        request.app.state.backtest_engine = AsyncBacktestEngine()
    return request.app.state.backtest_engine


@router.post("/run", response_model=BacktestRunResponse)
async def run_backtest(
    request: BacktestRunRequest,
    engine: AsyncBacktestEngine = Depends(get_backtest_engine),
):
    """
    Start a new backtest task.

    Creates a backtest task and returns task_id for WebSocket connection
    to receive real-time progress updates.

    Supported strategies: ma_cross, rsi, bollinger, macd, qlib_model
    """
    config = {
        "strategy": request.strategy,
        "params": request.params,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "initial_capital": request.initial_capital,
        "instruments": request.instruments,
    }

    try:
        task_id = await engine.run_backtest(config)
        logger.info(f"Backtest started: task_id={task_id}, strategy={request.strategy}")

        return BacktestRunResponse(
            task_id=task_id,
            status="pending",
            message="Backtest task started successfully",
        )

    except ValueError as e:
        logger.error(f"Invalid backtest config: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to start backtest: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start backtest: {str(e)}")


@router.get("/results", response_model=BacktestResultsResponse)
async def get_backtest_results(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
):
    storage = get_storage()
    try:
        collection = storage.db["backtest_results"]
        skip = (page - 1) * page_size

        total = await asyncio.to_thread(collection.count_documents, {})

        docs = await asyncio.to_thread(
            lambda: list(
                collection.find({})
                .sort("created_at", -1)
                .skip(skip)
                .limit(page_size)
            )
        )

        items = []
        for doc in docs:
            strategy = doc.get("strategy", "")
            start_date = doc.get("start_date", "")
            end_date = doc.get("end_date", "")
            date_range = f"{start_date} ~ {end_date}" if start_date and end_date else ""

            metrics = doc.get("metrics", {})
            key_metrics = {
                "total_return": metrics.get("total_return"),
                "annual_return": metrics.get("annual_return"),
                "sharpe_ratio": metrics.get("sharpe_ratio"),
                "max_drawdown": metrics.get("max_drawdown"),
                "win_rate": metrics.get("win_rate"),
                "total_trades": len(doc.get("trades", [])),
            }

            items.append(BacktestResultItem(
                task_id=doc.get("task_id", ""),
                strategy=strategy,
                date_range=date_range,
                key_metrics=key_metrics,
            ))

        return BacktestResultsResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"Failed to get backtest results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")

    finally:
        storage.close()


async def save_backtest_result(result: Dict[str, Any]) -> None:
    storage = get_storage()
    try:
        collection = storage.db["backtest_results"]

        doc = {
            "task_id": result.get("task_id"),
            "strategy": result.get("config", {}).get("strategy"),
            "params": result.get("config", {}).get("params", {}),
            "start_date": result.get("config", {}).get("start_date"),
            "end_date": result.get("config", {}).get("end_date"),
            "initial_capital": result.get("config", {}).get("initial_capital"),
            "final_value": result.get("portfolio_values", [0])[-1] if result.get("portfolio_values") else 0,
            "metrics": result.get("metrics", {}),
            "trades": result.get("trades", []),
            "created_at": datetime.now(),
        }

        await asyncio.to_thread(collection.insert_one, doc)
        logger.info(f"Saved backtest result: task_id={doc.get('task_id')}")

    except Exception as e:
        logger.error(f"Failed to save backtest result: {e}")

    finally:
        storage.close()


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
