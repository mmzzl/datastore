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
from app.qlib.config import CSI_300_STOCKS, get_csi300_instruments

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/qlib", tags=["qlib"])

_trainer: Optional[QlibTrainer] = None
_model_manager: Optional[ModelManager] = None
_predictor: Optional[QlibPredictor] = None


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
