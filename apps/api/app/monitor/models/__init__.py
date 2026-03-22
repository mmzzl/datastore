from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from .alert_rule import (
    AlertRule,
    AlertType,
    AlertCondition,
    AlertPriority,
    AlertOperator,
    StrategyType,
    NotifyConfig,
)
from .alert_signal import AlertSignal, SignalType
from .notification_config import NotificationPayload, NotificationLevel


class StockConfig(BaseModel):
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    hold: bool = Field(False, description="是否持仓")
    buy_threshold: float = Field(0.05, description="买入阈值")
    sell_threshold: float = Field(0.03, description="卖出阈值")
    cost_price: float = Field(0.0, description="持仓成本价")
    profit_target: float = Field(0.1, description="盈利目标")
    stop_loss: float = Field(0.05, description="止损线")
    rsi_buy_level: int = Field(30, description="RSI买入水平")
    rsi_sell_level: int = Field(70, description="RSI卖出水平")
    k_buy_level: int = Field(20, description="KDJ K值买入水平")
    k_sell_level: int = Field(80, description="KDJ K值卖出水平")


class IndicatorConfig(BaseModel):
    rsi: Dict[str, Any] = Field(
        default_factory=lambda: {"period": 14, "buy_level": 30, "sell_level": 70}
    )
    macd: Dict[str, Any] = Field(
        default_factory=lambda: {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9,
        }
    )
    kdj: Dict[str, Any] = Field(
        default_factory=lambda: {"period": 9, "k_buy_level": 20, "k_sell_level": 80}
    )
    bollinger: Dict[str, Any] = Field(
        default_factory=lambda: {"period": 20, "num_std": 2.0}
    )


class MonitorConfig(BaseModel):
    enabled: bool = Field(True, description="是否启用")
    interval: int = Field(300, description="监控间隔（秒）")
    stocks: List[StockConfig] = Field(default_factory=list, description="监控股票列表")
    indicators: IndicatorConfig = Field(
        default_factory=IndicatorConfig, description="指标配置"
    )


class RSI(BaseModel):
    value: float = Field(..., description="RSI值")
    period: int = Field(14, description="计算周期")


class MACD(BaseModel):
    macd: float = Field(..., description="MACD值")
    signal: float = Field(..., description="信号线值")
    histogram: float = Field(..., description="柱状图值")


class KDJ(BaseModel):
    k: float = Field(..., description="K值")
    d: float = Field(..., description="D值")
    j: float = Field(..., description="J值")


class BollingerBands(BaseModel):
    upper: float = Field(..., description="上轨")
    middle: float = Field(..., description="中轨")
    lower: float = Field(..., description="下轨")


class TechnicalData(BaseModel):
    rsi: RSI = Field(default_factory=lambda: RSI(value=50.0))
    macd: MACD = Field(
        default_factory=lambda: MACD(macd=0.0, signal=0.0, histogram=0.0)
    )
    kdj: KDJ = Field(default_factory=lambda: KDJ(k=50.0, d=50.0, j=50.0))
    bollinger: BollingerBands = Field(
        default_factory=lambda: BollingerBands(upper=0.0, middle=0.0, lower=0.0)
    )


class Signal(BaseModel):
    signal: str = Field(..., description="信号类型：buy, sell, hold")
    strength: int = Field(..., description="信号强度")
    strength_percentage: float = Field(..., description="信号强度百分比")
    reasons: List[str] = Field(default_factory=list, description="信号原因")
    suggestion: str = Field(..., description="操作建议")


class StockData(BaseModel):
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    current_price: float = Field(..., description="当前价格")
    high_price: float = Field(..., description="最高价")
    low_price: float = Field(..., description="最低价")
    open_price: float = Field(..., description="开盘价")
    close_price: float = Field(..., description="收盘价")
    change: float = Field(..., description="涨跌额")
    change_pct: float = Field(..., description="涨跌幅")
    volume: int = Field(..., description="成交量")
    amount: float = Field(..., description="成交额")


class MonitorResult(BaseModel):
    stock: StockData = Field(..., description="股票数据")
    technical_data: TechnicalData = Field(..., description="技术指标数据")
    signal: Signal = Field(..., description="信号")
    timestamp: datetime = Field(default_factory=datetime.now, description="监控时间")


class MonitorNotification(BaseModel):
    type: str = Field(..., description="通知类型：buy, sell")
    stock: StockData = Field(..., description="股票数据")
    signal: Signal = Field(..., description="信号")
    message: str = Field(..., description="通知消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="通知时间")


class MonitorHistory(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    timestamp: datetime = Field(default_factory=datetime.now, description="监控时间")
    signal: str = Field(..., description="信号类型")
    signal_strength: int = Field(..., description="信号强度")
    price: float = Field(..., description="股票价格")
    technical_data: Dict[str, Any] = Field(
        default_factory=dict, description="技术指标数据"
    )
    reasons: List[str] = Field(default_factory=list, description="信号原因")


__all__ = [
    "AlertRule",
    "AlertType",
    "AlertCondition",
    "AlertPriority",
    "AlertOperator",
    "StrategyType",
    "NotifyConfig",
    "AlertSignal",
    "SignalType",
    "NotificationPayload",
    "NotificationLevel",
    "StockData",
    "TechnicalData",
    "Signal",
    "MonitorResult",
    "MonitorNotification",
    "RSI",
    "MACD",
    "KDJ",
    "BollingerBands",
    "StockConfig",
    "IndicatorConfig",
    "MonitorConfig",
    "MonitorHistory",
]
