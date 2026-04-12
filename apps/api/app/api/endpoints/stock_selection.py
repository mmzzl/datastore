"""
Stock Selection API Endpoints

REST API for strategy-based stock selection.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...core.auth import AuthenticatedUser, require_permission, get_storage
from ...schemas.stock_selection import (
    StockPoolType,
    SelectionStatus,
    SelectionStockResult,
    StockAIAnalysis,
    MarketTrendData,
    FiltrationLogEntry,
)
from ...stock_selection.engine import get_selection_engine, StockSelectionEngine
from ...stock_selection.stock_pool import StockPoolService
from ...storage import MongoStorage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stock-selection", tags=["策略选股"])


# Request/Response Models


class RunSelectionRequest(BaseModel):
    """Request to start selection task."""

    strategy_type: str = Field(
        ..., description="策略类型: ma_cross/rsi/bollinger/macd/plugin"
    )
    strategy_params: Dict[str, Any] = Field(
        default_factory=dict, description="策略参数"
    )
    stock_pool: str = Field(default="hs300", description="股票池: hs300/zz500/all")
    plugin_id: Optional[str] = Field(default=None, description="插件ID(使用插件策略时)")


class RunSelectionResponse(BaseModel):
    """Response for selection task start."""

    task_id: str
    status: str
    message: str


class StockResultItem(BaseModel):
    """Single stock result item."""

    code: str
    name: str
    score: float
    signal_type: str
    signal_strength: str
    confidence: float
    industry: str
    indicators: Dict[str, Any]
    ai_analysis: Optional[Dict[str, Any]] = None


class MarketTrendItem(BaseModel):
    """Market trend data item."""

    total_stocks: int
    macd_golden_cross_count: int
    macd_golden_cross_ratio: float
    ma_golden_cross_count: int
    ma_golden_cross_ratio: float
    full_bullish_alignment_count: int
    full_bullish_alignment_ratio: float
    trend_direction: str
    trend_strength: str
    rsi_oversold_count: int
    rsi_overbought_count: int
    rsi_neutral_count: int


class FiltrationLogItem(BaseModel):
    """Single filtration log entry."""

    code: str
    reason: str
    detail: str
    timestamp: str


class SelectionResultResponse(BaseModel):
    """Response for selection result."""

    id: str
    task_id: str
    strategy_type: str
    stock_pool: str
    status: str
    created_at: str
    completed_at: Optional[str]
    total_stocks: int
    selected_count: int
    results: List[StockResultItem]
    filtration_logs: List[FiltrationLogItem] = Field(default_factory=list)
    market_trend: Optional[MarketTrendItem]
    ai_summary: Optional[str]
    sector_overview: Optional[str]
    market_risk: Optional[str]
    error: Optional[str]


class HistoryItem(BaseModel):
    """History item."""

    id: str
    task_id: str
    strategy_type: str
    stock_pool: str
    created_at: str
    selected_count: int
    status: str


class HistoryResponse(BaseModel):
    """Response for history query."""

    items: List[HistoryItem]
    total: int
    page: int
    page_size: int


class StockPoolItem(BaseModel):
    """Stock pool info item."""

    id: str
    name: str
    count: int
    description: str


class StockPoolsResponse(BaseModel):
    """Response for stock pools list."""

    pools: List[StockPoolItem]


class RunSelectionResponse(BaseModel):
    """Response for selection task start."""

    task_id: str
    status: str
    message: str


class StockResultItem(BaseModel):
    """Single stock result item."""

    code: str
    name: str
    score: float
    signal_type: str
    signal_strength: str
    confidence: float
    industry: str
    indicators: Dict[str, Any]
    ai_analysis: Optional[Dict[str, Any]] = None


class MarketTrendItem(BaseModel):
    """Market trend data item."""

    total_stocks: int
    macd_golden_cross_count: int
    macd_golden_cross_ratio: float
    ma_golden_cross_count: int
    ma_golden_cross_ratio: float
    full_bullish_alignment_count: int
    full_bullish_alignment_ratio: float
    trend_direction: str
    trend_strength: str
    rsi_oversold_count: int
    rsi_overbought_count: int
    rsi_neutral_count: int


class FiltrationLogItem(BaseModel):
    """Single filtration log entry."""

    code: str
    reason: str
    detail: str
    timestamp: str


class SelectionResultResponse(BaseModel):
    """Response for selection result."""

    id: str
    task_id: str
    strategy_type: str
    stock_pool: str
    status: str
    created_at: str
    completed_at: Optional[str]
    total_stocks: int
    selected_count: int
    results: List[StockResultItem]
    filtration_logs: List[FiltrationLogItem] = Field(default_factory=list)
    market_trend: Optional[MarketTrendItem]
    ai_summary: Optional[str]
    sector_overview: Optional[str]
    market_risk: Optional[str]
    error: Optional[str]


class HistoryItem(BaseModel):
    """History item."""

    id: str
    task_id: str
    strategy_type: str
    stock_pool: str
    created_at: str
    selected_count: int
    status: str


class HistoryResponse(BaseModel):
    """Response for history query."""

    items: List[HistoryItem]
    total: int
    page: int
    page_size: int


class StockPoolItem(BaseModel):
    """Stock pool info item."""

    id: str
    name: str
    count: int
    description: str


class StockPoolsResponse(BaseModel):
    """Response for stock pools list."""

    pools: List[StockPoolItem]


# Helper functions


def _get_stock_pool_service() -> StockPoolService:
    """Get StockPoolService instance."""
    return StockPoolService()


# API Endpoints


@router.post("/run", response_model=RunSelectionResponse)
async def run_selection(
    request: RunSelectionRequest,
    current_user: AuthenticatedUser = Depends(require_permission("selection:run")),
):
    """
    Start a new selection task.

    Requires permission: selection:run
    """
    # Validate strategy type
    valid_types = ["ma_cross", "rsi", "bollinger", "macd", "plugin"]
    if request.strategy_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy type: {request.strategy_type}. Valid types: {valid_types}",
        )

    # Validate stock pool
    valid_pools = ["hs300", "zz500", "all"]
    if request.stock_pool not in valid_pools:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stock pool: {request.stock_pool}. Valid pools: {valid_pools}",
        )

    # Plugin strategy requires plugin_id
    if request.strategy_type == "plugin" and not request.plugin_id:
        raise HTTPException(
            status_code=400, detail="Plugin strategy requires plugin_id parameter"
        )

    try:
        engine = get_selection_engine()
        task_id = await engine.run_selection(
            strategy_type=request.strategy_type,
            strategy_params=request.strategy_params,
            stock_pool=StockPoolType(request.stock_pool),
            plugin_id=request.plugin_id,
        )

        logger.info(f"User {current_user.username} started selection task {task_id}")

        return RunSelectionResponse(
            task_id=task_id,
            status="pending",
            message="Selection task started successfully",
        )

    except Exception as e:
        import traceback

        logger.error(f"Failed to start selection: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# Place specific paths BEFORE {task_id} to avoid path conflicts
@router.get("/pools", response_model=StockPoolsResponse)
async def get_stock_pools(
    current_user: AuthenticatedUser = Depends(require_permission("selection:view")),
):
    """
    Get available stock pools.

    Requires permission: selection:view
    """
    pool_service = _get_stock_pool_service()

    pools = [
        StockPoolItem(
            id="hs300",
            name="沪深300",
            count=len(pool_service.get_codes("hs300")),
            description="沪深两市市值最大的300只股票",
        ),
        StockPoolItem(
            id="zz500",
            name="中证500",
            count=len(pool_service.get_codes("zz500")),
            description="沪深两市中盘代表性500只股票",
        ),
        StockPoolItem(
            id="all",
            name="全部A股",
            count=len(pool_service.get_codes("all")),
            description="沪深两市的全部A股",
        ),
    ]

    return StockPoolsResponse(pools=pools)


@router.get("/history", response_model=HistoryResponse)
async def get_selection_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(None, description="Filter by status"),
    stock_pool: Optional[str] = Query(None, description="Filter by stock pool"),
    current_user: AuthenticatedUser = Depends(require_permission("selection:view")),
):
    """
    Get selection history with pagination.

    Requires permission: selection:view
    """
    engine = get_selection_engine()

    filters = {}
    if status:
        filters["status"] = status
    if stock_pool:
        filters["stock_pool"] = stock_pool

    from datetime import datetime

    def _format_datetime(value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    history = engine.get_history(page=page, page_size=page_size, filters=filters)

    items = []
    for item in history.get("items", []):
        items.append(
            HistoryItem(
                id=item.get("id", ""),
                task_id=item.get("task_id", ""),
                strategy_type=item.get("strategy_type", ""),
                stock_pool=item.get("stock_pool", ""),
                created_at=_format_datetime(item.get("created_at")),
                selected_count=item.get("selected_count", 0),
                status=item.get("status", ""),
            )
        )

    return HistoryResponse(
        items=items,
        total=history.get("total", 0),
        page=page,
        page_size=page_size,
    )


# Keep {task_id} at the END to avoid conflicting with specific paths
@router.get("/{task_id}", response_model=SelectionResultResponse)
async def get_selection_result(
    task_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("selection:view")),
):
    """
    Get selection result by task ID.

    Requires permission: selection:view
    """
    logger.warning(f"get_selection_result called for task_id={task_id}")

    engine = get_selection_engine()
    logger.warning(f"Engine storage db_name: {engine.storage.db_name}")

    task = engine.get_task(task_id)
    logger.warning(f"get_task result: {task}")

    if not task:
        raise HTTPException(status_code=404, detail="Selection task not found")

    # Build response
    results = [
        SelectionStockResult(
            code=r.code,
            name=r.name,
            score=r.score,
            signal_type=r.signal_type,
            signal_strength=r.signal_strength,
            confidence=r.confidence,
            industry=r.industry,
            indicators=r.indicators,
            ai_analysis=next(
                (
                    StockAIAnalysis(
                        code=a.code,
                        name=a.name,
                        sector=a.sector,
                        sector_features=a.sector_features,
                        risk_factors=a.risk_factors,
                        operation_suggestion=a.operation_suggestion,
                        brief_analysis=a.brief_analysis,
                    )
                    for a in (task.ai_result.stock_analyses if task.ai_result else [])
                    if a.code == r.code
                ),
                None,
            ),
        )
        for r in task.results
    ]

    # Market trend
    market_trend = task.market_trend if task.market_trend else None

    # Filtration logs
    filtration_logs = [
        FiltrationLogEntry(
            code=log.code,
            reason=log.reason,
            detail=log.detail,
            timestamp=log.timestamp,
        )
        for log in task.filtration_logs
    ]

    return SelectionResultResponse(
        id=task.id,
        task_id=task.id,
        strategy_type=task.strategy_type,
        stock_pool=task.stock_pool.value,
        status=task.status.value,
        created_at=task.created_at.isoformat() if task.created_at else "",
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        total_stocks=task.total_stocks,
        selected_count=task.selected_count,
        results=results,
        filtration_logs=filtration_logs,
        market_trend=market_trend,
        ai_summary=task.ai_result.summary if task.ai_result else None,
        sector_overview=task.ai_result.sector_overview if task.ai_result else None,
        market_risk=task.ai_result.market_risk if task.ai_result else None,
        error=task.error,
    )


@router.get("/history", response_model=HistoryResponse)
async def get_selection_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(None, description="Filter by status"),
    stock_pool: Optional[str] = Query(None, description="Filter by stock pool"),
    current_user: AuthenticatedUser = Depends(require_permission("selection:view")),
):
    """
    Get selection history with pagination.

    Requires permission: selection:view
    """
    engine = get_selection_engine()

    filters = {}
    if status:
        filters["status"] = status
    if stock_pool:
        filters["stock_pool"] = stock_pool

    from datetime import datetime

    def _format_datetime(value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    history = engine.get_history(page=page, page_size=page_size, filters=filters)

    items = []
    for item in history.get("items", []):
        items.append(
            HistoryItem(
                id=item.get("id", ""),
                task_id=item.get("task_id", ""),
                strategy_type=item.get("strategy_type", ""),
                stock_pool=item.get("stock_pool", ""),
                created_at=_format_datetime(item.get("created_at")),
                selected_count=item.get("selected_count", 0),
                status=item.get("status", ""),
            )
        )

    return HistoryResponse(
        items=items,
        total=history.get("total", 0),
        page=page,
        page_size=page_size,
    )


@router.get("/pools", response_model=StockPoolsResponse)
async def get_stock_pools(
    current_user: AuthenticatedUser = Depends(require_permission("selection:view")),
):
    """
    Get available stock pools.

    Requires permission: selection:view
    """
    pool_service = _get_stock_pool_service()

    pools = [
        StockPoolItem(
            id="hs300",
            name="沪深300",
            count=len(pool_service.get_codes("hs300")),
            description="沪深两市市值最大的300只股票",
        ),
        StockPoolItem(
            id="zz500",
            name="中证500",
            count=len(pool_service.get_codes("zz500")),
            description="沪深两市中盘代表性500只股票",
        ),
        StockPoolItem(
            id="all",
            name="全市场",
            count=len(pool_service.get_codes("all")),
            description="沪深300+中证500 (排除ST)",
        ),
    ]

    return StockPoolsResponse(pools=pools)
