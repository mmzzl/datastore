"""
Stock Selection Data Models

Defines data models for strategy-based stock selection feature.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class StockPoolType(str, Enum):
    """Stock pool type enumeration."""
    HS300 = "hs300"  # 沪深300
    ZZ500 = "zz500"  # 中证500
    ALL = "all"      # 全市场


class SelectionStatus(str, Enum):
    """Selection task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class StockIndicator:
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ma5": self.ma5,
            "ma10": self.ma10,
            "ma20": self.ma20,
            "rsi": self.rsi,
            "macd": self.macd,
            "macd_signal": self.macd_signal,
            "macd_hist": self.macd_hist,
            "boll_upper": self.boll_upper,
            "boll_mid": self.boll_mid,
            "boll_lower": self.boll_lower,
            "volume_ratio": self.volume_ratio,
            "turnover_rate": self.turnover_rate,
        }


@dataclass
class StockAIAnalysis:
    """AI analysis result for a single stock."""
    code: str
    name: str
    sector: str  # 所属板块(简化名称)
    sector_features: str = ""  # 板块特征描述
    risk_factors: List[str] = field(default_factory=list)  # 风险因素
    operation_suggestion: str = ""  # 操作建议
    brief_analysis: str = ""  # 技术面简要分析

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "code": self.code,
            "name": self.name,
            "sector": self.sector,
            "sector_features": self.sector_features,
            "risk_factors": self.risk_factors,
            "operation_suggestion": self.operation_suggestion,
            "brief_analysis": self.brief_analysis,
        }


@dataclass
class SelectionStockResult:
    """Result for a single stock in selection."""
    code: str
    name: str
    score: float  # 综合评分 (0-100)
    signal_type: str  # BUY/SELL/HOLD
    signal_strength: str  # 强/中/弱
    confidence: float  # 策略置信度 (0-1)
    indicators: StockIndicator
    industry: str = ""  # 所属行业
    ai_analysis: Optional[StockAIAnalysis] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "code": self.code,
            "name": self.name,
            "score": self.score,
            "signal_type": self.signal_type,
            "signal_strength": self.signal_strength,
            "confidence": self.confidence,
            "indicators": self.indicators.to_dict() if self.indicators else {},
            "industry": self.industry,
            "ai_analysis": self.ai_analysis.to_dict() if self.ai_analysis else None,
        }


@dataclass
class MarketTrendData:
    """Market trend analysis data."""
    # 基础统计
    total_stocks: int = 0
    analyzed_stocks: int = 0

    # 金叉统计
    macd_golden_cross_count: int = 0
    macd_golden_cross_ratio: float = 0.0
    ma_golden_cross_count: int = 0
    ma_golden_cross_ratio: float = 0.0

    # 多头排列统计
    full_bullish_alignment_count: int = 0
    full_bullish_alignment_ratio: float = 0.0
    partial_bullish_alignment_count: int = 0
    partial_bullish_alignment_ratio: float = 0.0

    # 选出股票中的统计
    selected_macd_golden_cross: int = 0
    selected_bullish_alignment: int = 0

    # RSI分布
    rsi_oversold_count: int = 0  # RSI < 30
    rsi_overbought_count: int = 0  # RSI > 70
    rsi_neutral_count: int = 0  # 30 <= RSI <= 70

    # 综合判断
    trend_direction: str = "震荡"  # 看多/看空/震荡
    trend_strength: str = "中"  # 强/中/弱

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_stocks": self.total_stocks,
            "analyzed_stocks": self.analyzed_stocks,
            "macd_golden_cross_count": self.macd_golden_cross_count,
            "macd_golden_cross_ratio": self.macd_golden_cross_ratio,
            "ma_golden_cross_count": self.ma_golden_cross_count,
            "ma_golden_cross_ratio": self.ma_golden_cross_ratio,
            "full_bullish_alignment_count": self.full_bullish_alignment_count,
            "full_bullish_alignment_ratio": self.full_bullish_alignment_ratio,
            "partial_bullish_alignment_count": self.partial_bullish_alignment_count,
            "partial_bullish_alignment_ratio": self.partial_bullish_alignment_ratio,
            "selected_macd_golden_cross": self.selected_macd_golden_cross,
            "selected_bullish_alignment": self.selected_bullish_alignment,
            "rsi_oversold_count": self.rsi_oversold_count,
            "rsi_overbought_count": self.rsi_overbought_count,
            "rsi_neutral_count": self.rsi_neutral_count,
            "trend_direction": self.trend_direction,
            "trend_strength": self.trend_strength,
        }


@dataclass
class SelectionAIResult:
    """AI analysis result for selection task."""
    stock_analyses: List[StockAIAnalysis] = field(default_factory=list)
    summary: str = ""  # 整体总结
    sector_overview: str = ""  # 板块整体特征
    market_risk: str = ""  # 市场风险提示

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stock_analyses": [a.to_dict() for a in self.stock_analyses],
            "summary": self.summary,
            "sector_overview": self.sector_overview,
            "market_risk": self.market_risk,
        }


@dataclass
class StockSelectionTask:
    """Stock selection task model."""
    id: str
    strategy_type: str
    strategy_params: Dict[str, Any] = field(default_factory=dict)
    plugin_id: Optional[str] = None
    stock_pool: StockPoolType = StockPoolType.HS300
    status: SelectionStatus = SelectionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    results: List[SelectionStockResult] = field(default_factory=list)
    ai_result: Optional[SelectionAIResult] = None
    market_trend: Optional[MarketTrendData] = None
    error: Optional[str] = None

    # 统计信息
    total_stocks: int = 0
    selected_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        return {
            "task_id": self.id,
            "strategy_type": self.strategy_type,
            "strategy_params": self.strategy_params,
            "plugin_id": self.plugin_id,
            "stock_pool": self.stock_pool.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "results": [r.to_dict() for r in self.results],
            "ai_result": self.ai_result.to_dict() if self.ai_result else None,
            "market_trend": self.market_trend.to_dict() if self.market_trend else None,
            "error": self.error,
            "total_stocks": self.total_stocks,
            "selected_count": self.selected_count,
        }
