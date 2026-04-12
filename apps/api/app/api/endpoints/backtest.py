"""Backtest API Endpoints

Provides REST and WebSocket endpoints for backtest management.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket
from pydantic import BaseModel, Field, field_validator
from pydantic import BaseModel, Field, field_validator

from app.backtest.websocket_handler import (
    websocket_backtest_endpoint,
    get_connection_manager,
)
from app.backtest.async_engine import AsyncBacktestEngine
from app.backtest.strategies.factory import StrategyFactory
from app.core.config import settings
from app.core.auth import AuthenticatedUser, require_permission
import os
import zipfile
import importlib
import shutil
from fastapi import UploadFile, File

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backtest", tags=["backtest"])

VALID_STRATEGY_TYPES = ["ma_cross", "rsi", "bollinger", "macd", "qlib_model", "plugin"]


class BacktestRunRequest(BaseModel):
    """Request model for running a backtest."""

    strategy: str = Field(..., description="Strategy type")
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Strategy parameters"
    )
    start_date: str = Field(..., description="Backtest start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Backtest end date (YYYY-MM-DD)")
    initial_capital: float = Field(
        default=100000.0, gt=0, description="Initial capital"
    )
    instruments: List[str] = Field(
        default_factory=list, description="List of stock codes"
    )
    plugin_id: Optional[str] = Field(
        default=None, description="Plugin ID for plugin strategy"
    )

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
    current_user: AuthenticatedUser = Depends(require_permission("backtest:run")),
):
    """
    Start a new backtest task.

    Creates a backtest task and returns task_id for WebSocket connection
    to receive real-time progress updates.

    Supported strategies: ma_cross, rsi, bollinger, macd, qlib_model, plugin
    """
    strategy_params = request.params.copy()

    if request.strategy.lower() == "plugin":
        if not request.plugin_id:
            raise HTTPException(
                status_code=400, detail="plugin_id is required for plugin strategy"
            )
        strategy_params["plugin_id"] = request.plugin_id

    config = {
        "strategy": request.strategy,
        "params": strategy_params,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "initial_capital": request.initial_capital,
        "instruments": request.instruments,
    }

    try:
        task_id = await engine.run_backtest(config)
        logger.info(
            f"Backtest started: task_id={task_id}, strategy={request.strategy}, user={current_user.user_id}"
        )

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
        raise HTTPException(
            status_code=500, detail=f"Failed to start backtest: {str(e)}"
        )


@router.get("/results", response_model=BacktestResultsResponse)
async def get_backtest_results(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: AuthenticatedUser = Depends(require_permission("backtest:view")),
):
    storage = get_storage()
    try:
        collection = storage.db["backtest_results"]
        skip = (page - 1) * page_size

        total = await asyncio.to_thread(collection.count_documents, {})

        docs = await asyncio.to_thread(
            lambda: list(
                collection.find({}).sort("created_at", -1).skip(skip).limit(page_size)
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

            items.append(
                BacktestResultItem(
                    task_id=doc.get("task_id", ""),
                    strategy=strategy,
                    date_range=date_range,
                    key_metrics=key_metrics,
                )
            )

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


# Plugin management endpoints


class StrategyPluginResponse(BaseModel):
    """Response model for strategy plugin."""

    id: str
    name: str
    description: str
    module_name: str
    class_name: str
    path: str
    author: str = ""
    version: str = "1.0.0"
    tags: list = []
    parameters: dict = {}
    created_at: str
    updated_at: str


class StrategyPluginsResponse(BaseModel):
    """Response model for paginated strategy plugins."""

    items: List[StrategyPluginResponse]
    total: int


@router.post("/plugins/upload")
async def upload_strategy_plugin(
    file: UploadFile = File(...),
):
    """
    Upload a strategy plugin.

    Uploads a zip file containing strategy implementation.
    """
    # Create uploads directory if it doesn't exist
    uploads_dir = "uploads"
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    # Save uploaded file
    file_path = os.path.join(uploads_dir, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Extract zip file
        extract_dir = os.path.join(uploads_dir, "temp")
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir)

        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # Find the main strategy module
        strategy_modules = []
        for root, dirs, files in os.walk(extract_dir):
            if "__init__.py" in files and "strategy.py" in files:
                module_name = os.path.basename(root)
                strategy_modules.append((module_name, root))

        if not strategy_modules:
            raise HTTPException(
                status_code=400, detail="No valid strategy module found in zip file"
            )

        # Use the first strategy module found
        module_name, module_path = strategy_modules[0]

        # Create plugins directory if it doesn't exist
        plugins_dir = os.path.join("app", "backtest", "strategies", "plugins")
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)

        # Move the module to plugins directory
        target_path = os.path.join(plugins_dir, module_name)
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
        shutil.move(module_path, target_path)

        # Add __init__.py to plugins directory if it doesn't exist
        plugins_init = os.path.join(plugins_dir, "__init__.py")
        if not os.path.exists(plugins_init):
            with open(plugins_init, "w") as f:
                f.write("# Plugins directory\n")

        # Dynamically import the strategy module
        try:
            module = importlib.import_module(
                f"app.backtest.strategies.plugins.{module_name}"
            )
            # Find the strategy class
            strategy_class = None
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and hasattr(obj, "PLUGIN_METADATA"):
                    strategy_class = obj
                    break

            if not strategy_class:
                raise HTTPException(
                    status_code=400, detail="No valid strategy class found in module"
                )

            # Extract metadata
            metadata = getattr(strategy_class, "PLUGIN_METADATA", {})

            # Save to MongoDB
            storage = get_storage()
            try:
                plugin_data = {
                    "name": metadata.get("name", module_name),
                    "description": metadata.get("description", ""),
                    "module_name": module_name,
                    "class_name": strategy_class.__name__,
                    "path": f"plugins/{module_name}",
                    "author": metadata.get("author", ""),
                    "version": metadata.get("version", "1.0.0"),
                    "tags": metadata.get("tags", []),
                    "parameters": metadata.get("parameters", {}),
                }

                plugin_id = storage.save_strategy_plugin(plugin_data)

                return {
                    "id": plugin_id,
                    "message": "Strategy plugin uploaded successfully",
                    "plugin": plugin_data,
                }
            finally:
                storage.close()

        except Exception as e:
            # Clean up
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            raise HTTPException(
                status_code=400, detail=f"Failed to load strategy module: {str(e)}"
            )

    finally:
        # Clean up temporary files
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)


@router.get("/plugins", response_model=StrategyPluginsResponse)
async def get_strategy_plugins():
    """
    Get all strategy plugins.
    """
    storage = get_storage()
    try:
        plugins = storage.get_all_strategy_plugins()

        items = []
        for plugin in plugins:
            items.append(
                StrategyPluginResponse(
                    id=str(plugin["_id"]),
                    name=plugin.get("name", ""),
                    description=plugin.get("description", ""),
                    module_name=plugin.get("module_name", ""),
                    class_name=plugin.get("class_name", ""),
                    path=plugin.get("path", ""),
                    author=plugin.get("author", ""),
                    version=plugin.get("version", "1.0.0"),
                    tags=plugin.get("tags", []),
                    parameters=plugin.get("parameters", {}),
                    created_at=plugin.get("created_at", "").isoformat()
                    if hasattr(plugin.get("created_at"), "isoformat")
                    else "",
                    updated_at=plugin.get("updated_at", "").isoformat()
                    if hasattr(plugin.get("updated_at"), "isoformat")
                    else "",
                )
            )

        return StrategyPluginsResponse(items=items, total=len(items))
    finally:
        storage.close()


@router.delete("/plugins/{plugin_id}")
async def delete_strategy_plugin(
    plugin_id: str,
):
    """
    Delete a strategy plugin.
    """
    storage = get_storage()
    try:
        # Get plugin info first
        plugin = storage.get_strategy_plugin(plugin_id)
        if not plugin:
            raise HTTPException(status_code=404, detail="Plugin not found")

        # Delete from file system
        module_name = plugin.get("module_name")
        if module_name:
            plugin_path = os.path.join(
                "app", "backtest", "strategies", "plugins", module_name
            )
            if os.path.exists(plugin_path):
                shutil.rmtree(plugin_path)

        # Delete from MongoDB
        deleted = storage.delete_strategy_plugin(plugin_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Failed to delete plugin")

        return {"message": "Strategy plugin deleted successfully"}
    finally:
        storage.close()


@router.get("/plugins/{plugin_id}", response_model=StrategyPluginResponse)
async def get_strategy_plugin(
    plugin_id: str,
):
    """
    Get a strategy plugin by ID.
    """
    storage = get_storage()
    try:
        plugin = storage.get_strategy_plugin(plugin_id)
        if not plugin:
            raise HTTPException(status_code=404, detail="Plugin not found")

        return StrategyPluginResponse(
            id=str(plugin["_id"]),
            name=plugin.get("name", ""),
            description=plugin.get("description", ""),
            module_name=plugin.get("module_name", ""),
            class_name=plugin.get("class_name", ""),
            path=plugin.get("path", ""),
            author=plugin.get("author", ""),
            version=plugin.get("version", "1.0.0"),
            tags=plugin.get("tags", []),
            parameters=plugin.get("parameters", {}),
            created_at=plugin.get("created_at", "").isoformat()
            if hasattr(plugin.get("created_at"), "isoformat")
            else "",
            updated_at=plugin.get("updated_at", "").isoformat()
            if hasattr(plugin.get("updated_at"), "isoformat")
            else "",
        )
    finally:
        storage.close()
