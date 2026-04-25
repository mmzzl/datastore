"""
Qlib API Endpoints

Provides REST API endpoints for:
- Model training
- Model management
- Stock selection
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.core.config import settings
from app.core.auth import AuthenticatedUser, require_permission
from app.qlib import QlibTrainer, ModelManager, QlibPredictor
from app.qlib.top_stocks_manager import TopStocksManager
from app.qlib.config import CSI_300_STOCKS, get_csi300_instruments, QlibConfig
from app.qlib.bin_converter import QlibBinConverter
from app.experiment.tracker import ExperimentTracker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/qlib", tags=["qlib"])

_trainer: Optional[QlibTrainer] = None
_model_manager: Optional[ModelManager] = None
_predictor: Optional[QlibPredictor] = None
_tracker: Optional[ExperimentTracker] = None
_top_stocks_manager: Optional[TopStocksManager] = None
_sync_tasks: Dict[str, Dict[str, Any]] = {}


def get_trainer() -> QlibTrainer:
    """Get or create QlibTrainer instance."""
    global _trainer
    if _trainer is None:
        _trainer = QlibTrainer(
            model_dir="./models",
            min_sharpe_ratio=1.5,
        )
    return _trainer


def get_model_manager() -> ModelManager:
    """Get or create ModelManager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager


def get_predictor() -> QlibPredictor:
    """Get or create QlibPredictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = QlibPredictor()
    return _predictor


def get_tracker() -> ExperimentTracker:
    global _tracker
    if _tracker is None:
        _tracker = ExperimentTracker()
    return _tracker


def get_top_stocks_manager() -> TopStocksManager:
    global _top_stocks_manager
    if _top_stocks_manager is None:
        _top_stocks_manager = TopStocksManager()
    return _top_stocks_manager


class TrainRequest(BaseModel):
    """Training request model."""
    instruments: Optional[List[str]] = Field(
        default=None,
        description="List of stock codes. If not provided, uses CSI 300"
    )
    start_time: str = Field(
        default="2015-01-01",
        description="Start date for training data"
    )
    end_time: str = Field(
        default="2026-01-01",
        description="End date for training data"
    )
    model_type: str = Field(
        default="lgbm",
        description="Model type (lgbm, mlp)"
    )
    factor_type: str = Field(
        default="alpha158",
        description="Factor type (alpha158, alpha360)"
    )


class TrainResponse(BaseModel):
    """Training response model."""
    task_id: str
    status: str
    message: str


class TrainStatusResponse(BaseModel):
    """Training status response model."""
    task_id: str
    status: str
    progress: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    model_id: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None
    error: Optional[str] = None


class ModelResponse(BaseModel):
    """Model response model."""
    model_id: str
    version: int
    created_at: datetime
    status: str
    metrics: Dict[str, float]
    config: Dict[str, Any]


class SelectionRequest(BaseModel):
    """Stock selection request model."""
    model_id: Optional[str] = Field(
        default=None,
        description="Model ID to use. If not provided, uses latest approved model"
    )
    date: Optional[str] = Field(
        default=None,
        description="Selection date. If not provided, uses latest available date"
    )
    topk: int = Field(
        default=50,
        ge=1,
        le=300,
        description="Number of stocks to select"
    )
    strategy: Optional[str] = Field(
        default=None,
        description="Optional strategy type for filtering (e.g., 'plugin')"
    )
    plugin_id: Optional[str] = Field(
        default=None,
        description="Plugin ID if strategy is 'plugin'"
    )


class SelectionResult(BaseModel):
    """Single stock selection result."""
    rank: int
    code: str
    name: Optional[str] = None
    score: float


class SelectionResponse(BaseModel):
    """Stock selection response model."""
    model_id: str
    date: str
    results: List[SelectionResult]
    generated_at: datetime


@router.post("/train", response_model=TrainResponse)
async def start_training(
    request: TrainRequest,
    background_tasks: BackgroundTasks,
    trainer: QlibTrainer = Depends(get_trainer),
):
    """
    Start a model training task.

    Training runs in background. Use the returned task_id to poll for status.
    """
    instruments = request.instruments or get_csi300_instruments()

    config = {
        "instruments": instruments,
        "start_time": request.start_time,
        "end_time": request.end_time,
        "model_type": request.model_type,
        "factor_type": request.factor_type,
    }

    try:
        task_id = trainer.start_training(config)

        logger.info(f"Training started: task_id={task_id}")

        return TrainResponse(
            task_id=task_id,
            status="pending",
            message="Training task started successfully",
        )

    except Exception as e:
        logger.error(f"Failed to start training: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start training: {str(e)}"
        )


@router.get("/train/{task_id}", response_model=TrainStatusResponse)
async def get_training_status(
    task_id: str,
    trainer: QlibTrainer = Depends(get_trainer),
):
    """
    Get training task status.

    Returns current progress, status, and results if completed.
    """
    status = trainer.get_status(task_id)

    if "error" in status and status.get("error") == "Task not found":
        raise HTTPException(status_code=404, detail="Training task not found")

    return TrainStatusResponse(
        task_id=task_id,
        status=status.get("status", "unknown"),
        progress=status.get("progress", 0),
        started_at=status.get("started_at"),
        completed_at=status.get("completed_at"),
        model_id=status.get("model_id"),
        metrics=status.get("metrics"),
        error=status.get("error"),
    )


@router.get("/models", response_model=List[ModelResponse])
async def list_models(
    limit: int = 50,
    skip: int = 0,
    status: Optional[str] = None,
    model_manager: ModelManager = Depends(get_model_manager),
):
    """
    List all trained models.

    Supports pagination and filtering by status.
    """
    try:
        models = model_manager.list_models(
            limit=limit,
            skip=skip,
            status=status,
        )

        return [
            ModelResponse(
                model_id=m.get("model_id", ""),
                version=m.get("version", 0),
                created_at=m.get("created_at", datetime.now()),
                status=m.get("status", "unknown"),
                metrics=m.get("metrics", {}),
                config=m.get("config", {}),
            )
            for m in models
        ]

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list models: {str(e)}"
        )


@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    model_manager: ModelManager = Depends(get_model_manager),
):
    """
    Get model details by ID.
    """
    metadata = model_manager.get_model_metadata(model_id)

    if metadata is None:
        raise HTTPException(status_code=404, detail="Model not found")

    return ModelResponse(
        model_id=metadata.get("model_id", ""),
        version=metadata.get("version", 0),
        created_at=metadata.get("created_at", datetime.now()),
        status=metadata.get("status", "unknown"),
        metrics=metadata.get("metrics", {}),
        config=metadata.get("config", {}),
    )


@router.put("/models/{model_id}/status")
async def update_model_status(
    model_id: str,
    status: str,
    model_manager: ModelManager = Depends(get_model_manager),
):
    """
    Update model status.

    Valid statuses: approved, rejected, pending
    """
    valid_statuses = ["approved", "rejected", "pending", "deleted"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Valid values: {valid_statuses}"
        )

    success = model_manager.update_model_status(model_id, status)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Model not found or update failed"
        )

    return {"message": f"Model status updated to {status}"}


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: str,
    model_manager: ModelManager = Depends(get_model_manager),
):
    """
    Delete a model (soft delete).
    """
    success = model_manager.delete_model(model_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Model not found"
        )

    return {"message": "Model deleted successfully"}


@router.post("/select", response_model=SelectionResponse)
async def select_stocks(
    request: SelectionRequest,
    predictor: QlibPredictor = Depends(get_predictor),
    model_manager: ModelManager = Depends(get_model_manager),
    current_user: AuthenticatedUser = Depends(require_permission("selection:run")),
):
    """
    Run stock selection using a trained model.

    Returns top-k stocks ranked by prediction score.
    """
    model_id = request.model_id

    if model_id is None:
        latest_model = model_manager.get_latest_model(status="approved")
        if latest_model is None:
            raise HTTPException(
                status_code=404,
                detail="No approved model found. Please train a model first."
            )
        model_id = latest_model.get("model_id")

    else:
        metadata = model_manager.get_model_metadata(model_id)
        if metadata is None:
            raise HTTPException(status_code=404, detail="Model not found")

    try:
        results = predictor.predict(
            model_id=model_id,
            topk=request.topk,
            date=request.date,
        )

        if request.strategy == "plugin" and request.plugin_id:
            from app.backtest.strategies.factory import StrategyFactory
            try:
                strategy = StrategyFactory.create("plugin", plugin_id=request.plugin_id)
                logger.info(f"Applied plugin strategy filter: {request.plugin_id}")
            except Exception as e:
                logger.warning(f"Failed to apply plugin strategy: {e}")

        selection_results = [
            SelectionResult(
                rank=i + 1,
                code=r.get("code", ""),
                name=r.get("name"),
                score=r.get("score", 0.0),
            )
            for i, r in enumerate(results)
        ]

        logger.info(f"Selection completed: model={model_id}, count={len(results)}, user={current_user.user_id}")

        return SelectionResponse(
            model_id=model_id,
            date=request.date or datetime.now().strftime("%Y-%m-%d"),
            results=selection_results,
            generated_at=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Stock selection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Stock selection failed: {str(e)}"
        )


@router.get("/instruments/csi300")
async def get_csi300():
    """
    Get CSI 300 stock list.

    Returns list of stock codes in CSI 300 index.
    """
    return {
        "instruments": get_csi300_instruments(),
        "count": len(CSI_300_STOCKS),
    }


@router.get("/experiments", response_model=ExperimentListResponse)
async def list_experiments(
    page: int = 1,
    page_size: int = 20,
    tag: Optional[str] = None,
    status: Optional[str] = None,
    tracker: ExperimentTracker = Depends(get_tracker),
):
    try:
        results, total = tracker.list_experiments(
            tag=tag, status=status, page=page, page_size=page_size
        )
        items = [
            ExperimentItem(
                experiment_id=r.get("experiment_id", ""),
                tag=r.get("tag"),
                config=r.get("config", {}),
                training_metrics=r.get("training_metrics"),
                backtest_result=r.get("backtest_result"),
                model_id=r.get("model_id"),
                status=r.get("status", "unknown"),
                created_at=r.get("created_at"),
                error=r.get("error"),
            )
            for r in results
        ]
        return ExperimentListResponse(
            items=items, total=total, page=page, page_size=page_size
        )
    except Exception as e:
        logger.error(f"Failed to list experiments: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list experiments: {str(e)}")


@router.get("/experiments/compare")
async def compare_experiments(
    ids: str,
    tracker: ExperimentTracker = Depends(get_tracker),
):
    experiment_ids = [i.strip() for i in ids.split(",") if i.strip()]
    if not experiment_ids:
        raise HTTPException(status_code=400, detail="At least one experiment ID required")
    try:
        comparison = tracker.compare(experiment_ids)
        return comparison
    except Exception as e:
        logger.error(f"Failed to compare experiments: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare experiments: {str(e)}")


@router.get("/best-model", response_model=BestModelResponse)
async def get_best_model(
    tracker: ExperimentTracker = Depends(get_tracker),
):
    try:
        best = tracker.get_best("backtest_result.sharpe_ratio")
        if best is None:
            raise HTTPException(status_code=404, detail="No completed experiment found")
        return BestModelResponse(
            experiment_id=best.get("experiment_id", ""),
            model_id=best.get("model_id"),
            tag=best.get("tag"),
            config=best.get("config", {}),
            training_metrics=best.get("training_metrics"),
            backtest_result=best.get("backtest_result"),
            status=best.get("status", "unknown"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get best model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get best model: {str(e)}")


@router.get("/top-stocks", response_model=List[TopStocksDayResponse])
async def get_top_stocks(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    model_id: Optional[str] = None,
    mgr: TopStocksManager = Depends(get_top_stocks_manager),
):
    try:
        if start_date is None and end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = end_date

        results = mgr.get_top_stocks(
            start_date=start_date,
            end_date=end_date,
            model_id=model_id,
        )

        return [
            TopStocksDayResponse(
                date=r.get("date", ""),
                model_id=r.get("model_id", ""),
                model_type=r.get("model_type", ""),
                factor=r.get("factor", ""),
                stocks=[TopStockItem(**s) for s in r.get("stocks", [])],
                created_at=r.get("created_at"),
            )
            for r in results
        ]
    except Exception as e:
        logger.error(f"Failed to get top stocks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get top stocks: {str(e)}")


@router.post("/top-stocks/refresh")
async def refresh_top_stocks(
    tracker: ExperimentTracker = Depends(get_tracker),
    predictor: QlibPredictor = Depends(get_predictor),
    mgr: TopStocksManager = Depends(get_top_stocks_manager),
):
    try:
        best = tracker.get_best("backtest_result.sharpe_ratio")
        if best is None:
            raise HTTPException(status_code=404, detail="No completed experiment found")

        model_id = best.get("model_id")
        if not model_id:
            raise HTTPException(status_code=400, detail="Best experiment has no model_id")

        config = best.get("config", {})
        today = datetime.now().strftime("%Y-%m-%d")

        predictions = predictor.predict(
            model_id=model_id,
            topk=10,
            date=today,
        )

        stocks = [
            {"rank": p.get("rank", i + 1), "code": p.get("code", ""), "name": p.get("name", ""), "score": p.get("score", 0.0)}
            for i, p in enumerate(predictions[:10])
        ]

        mgr.save_top_stocks(
            date=today,
            model_id=model_id,
            model_type=config.get("model_type", "lgbm"),
            factor=config.get("factor_type", "alpha158"),
            stocks=stocks,
        )

        return {"message": "Top stocks refreshed", "date": today, "model_id": model_id, "count": len(stocks)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh top stocks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh top stocks: {str(e)}")


class ExperimentItem(BaseModel):
    experiment_id: str
    tag: Optional[str] = None
    config: Dict[str, Any]
    training_metrics: Optional[Dict[str, Any]] = None
    backtest_result: Optional[Dict[str, Any]] = None
    model_id: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    error: Optional[str] = None


class ExperimentListResponse(BaseModel):
    items: List[ExperimentItem]
    total: int
    page: int
    page_size: int


class BestModelResponse(BaseModel):
    experiment_id: str
    model_id: Optional[str] = None
    tag: Optional[str] = None
    config: Dict[str, Any]
    training_metrics: Optional[Dict[str, Any]] = None
    backtest_result: Optional[Dict[str, Any]] = None
    status: str


class TopStockItem(BaseModel):
    rank: int
    code: str
    name: Optional[str] = None
    score: float


class TopStocksDayResponse(BaseModel):
    date: str
    model_id: str
    model_type: str
    factor: str
    stocks: List[TopStockItem]
    created_at: Optional[datetime] = None


class SyncRequest(BaseModel):
    mode: str = Field(
        default="incremental",
        description="Sync mode: 'incremental' or 'full'",
    )


class SyncResponse(BaseModel):
    task_id: str
    status: str
    message: str


class SyncStatusResponse(BaseModel):
    task_id: str
    status: str
    mode: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/sync", response_model=SyncResponse)
async def start_qlib_sync(
    request: SyncRequest,
    current_user: AuthenticatedUser = Depends(require_permission("qlib:sync")),
):
    """Start a Qlib data sync task (incremental or full)."""
    import threading
    import uuid

    if request.mode not in ("incremental", "full"):
        raise HTTPException(status_code=400, detail="mode must be 'incremental' or 'full'")

    task_id = f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    _sync_tasks[task_id] = {
        "status": "pending",
        "mode": request.mode,
        "started_at": datetime.now(),
        "completed_at": None,
        "result": None,
        "error": None,
    }

    def _run_sync(tid: str, mode: str):
        try:
            _sync_tasks[tid]["status"] = "running"

            from app.storage.mongo_client import MongoStorage
            storage = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_database,
                username=settings.mongodb_username,
                password=settings.mongodb_password,
            )
            storage.connect()

            converter = QlibBinConverter(
                target_dir=QlibConfig.provider_uri,
                storage=storage,
            )

            if mode == "full":
                result = converter.full_convert()
            else:
                result = converter.incremental_sync()

            _sync_tasks[tid]["status"] = "completed"
            _sync_tasks[tid]["result"] = result
            _sync_tasks[tid]["completed_at"] = datetime.now()

            logger.info(f"Qlib sync task {tid} completed: {result}")

        except Exception as e:
            logger.error(f"Qlib sync task {tid} failed: {e}")
            _sync_tasks[tid]["status"] = "failed"
            _sync_tasks[tid]["error"] = str(e)
            _sync_tasks[tid]["completed_at"] = datetime.now()

        finally:
            try:
                storage.close()
            except Exception:
                pass

    thread = threading.Thread(target=_run_sync, args=(task_id, request.mode), daemon=True)
    thread.start()

    return SyncResponse(
        task_id=task_id,
        status="pending",
        message=f"Qlib data sync started in {request.mode} mode",
    )


@router.get("/sync/status", response_model=List[SyncStatusResponse])
async def list_sync_tasks():
    """List all Qlib data sync tasks."""
    return [
        SyncStatusResponse(
            task_id=tid,
            status=task["status"],
            mode=task["mode"],
            started_at=task.get("started_at"),
            completed_at=task.get("completed_at"),
            result=task.get("result"),
            error=task.get("error"),
        )
        for tid, task in sorted(_sync_tasks.items(), key=lambda x: x[1].get("started_at", datetime.min), reverse=True)
    ]


@router.get("/sync/{task_id}", response_model=SyncStatusResponse)
async def get_sync_status(task_id: str):
    """Get status of a specific Qlib data sync task."""
    if task_id not in _sync_tasks:
        raise HTTPException(status_code=404, detail="Sync task not found")

    task = _sync_tasks[task_id]
    return SyncStatusResponse(
        task_id=task_id,
        status=task["status"],
        mode=task["mode"],
        started_at=task.get("started_at"),
        completed_at=task.get("completed_at"),
        result=task.get("result"),
        error=task.get("error"),
    )
