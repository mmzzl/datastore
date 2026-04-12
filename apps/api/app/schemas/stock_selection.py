from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class StockPoolType(str, Enum):
    """Stock pool type enumeration."""

    HS300 = "hs300"  # 沪深300
    ZZ500 = "zz500"  # 中证500
    ALL = "all"  # 全市场


class SelectionStatus(str, Enum):
    """Selection task status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class StockIndicator(BaseModel):
    """Technical indicators for a stock."""

    ma5: Optional[float] = None
    ma10: Optional[float] = None
    ma20: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    boll_upper: Optional[float] = None
    boll_mid: Optional[float] = None
    boll_lower: Optional[float] = None
    volume_ratio: Optional[float] = None
    turnover_rate: Optional[float] = None


class StockAIAnalysis(BaseModel):
    """AI analysis result for a single stock."""

    code: str
    name: str
    sector: str  # 所属板块(简化名称)
    sector_features: str = ""  # 板块特征描述
    risk_factors: List[str] = Field(default_factory=list)  # 风险因素
    operation_suggestion: str = ""  # 操作建议
    brief_analysis: str = ""  # 技术面简要分析


class SelectionStockResult(BaseModel):
    """Result for a single stock in selection."""

    code: str
    name: str
    score: float = Field(..., ge=0, le=100)  # 综合评分 (0-100)
    signal_type: str  # BUY/SELL/HOLD
    signal_strength: str  # 强/中/弱
    confidence: float = Field(..., ge=0, le=1)  # 策略置信度 (0-1)
    indicators: StockIndicator
    industry: str = ""  # 所属行业
    ai_analysis: Optional[StockAIAnalysis] = None


class MarketTrendData(BaseModel):
    """Market trend analysis data."""

    total_stocks: int = 0
    analyzed_stocks: int = 0
    macd_golden_cross_count: int = 0
    macd_golden_cross_ratio: float = 0.0
    ma_golden_cross_count: int = 0
    ma_golden_cross_ratio: float = 0.0
    full_bullish_alignment_count: int = 0
    full_bullish_alignment_ratio: float = 0.0
    partial_bullish_alignment_count: int = 0
    partial_bullish_alignment_ratio: float = 0.0
    selected_macd_golden_cross: int = 0
    selected_bullish_alignment: int = 0
    rsi_oversold_count: int = 0  # RSI <<  30
    rsi_overbought_count: int = 0  # RSI > 70
    rsi_neutral_count: int = 0  # 30 <= RSI <= 70
    trend_direction: str = "震荡"  # 看多/看空/震荡
    trend_strength: str = "中"  # 强/中/弱


class SelectionAIResult(BaseModel):
    """AI analysis result for selection task."""

    stock_analyses: List[StockAIAnalysis] = Field(default_factory=list)
    summary: str = ""  # 整体总结
    sector_overview: str = ""  # 板块整体特征
    market_risk: str = ""  # 市场风险提示


class FiltrationLogEntry(BaseModel):
    """Record of why a stock was filtered out."""

    code: str
    reason: str  # e.g., "INSUFFICIENT_DATA", "STRATEGY_MISMATCH"
    detail: str
    timestamp: datetime = Field(default_factory=datetime.now)


class StockSelectionTask(BaseModel):
    """Stock selection task model."""

    id: str
    strategy_type: str
    strategy_params: Dict[str, Any] = Field(default_factory=dict)
    plugin_id: Optional[str] = None
    stock_pool: StockPoolType = StockPoolType.HS300
    status: SelectionStatus = SelectionStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    results: List[SelectionStockResult] = Field(default_factory=list)
    filtration_logs: List[FiltrationLogEntry] = Field(default_factory=list)
    ai_result: Optional[SelectionAIResult] = None
    market_trend: Optional[MarketTrendData] = None
    error: Optional[str] = None
    total_stocks: int = 0
    selected_count: int = 0
