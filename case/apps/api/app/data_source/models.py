from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DataSourceType(Enum):
    """数据源类型"""
    BAOSTOCK = "baostock"
    AKSHARE = "akshare"
    MONGODB = "mongodb"
    CUSTOM = "custom"

class StockKLine(BaseModel):
    """统一K线数据模型"""
    code: str = Field(..., description="股票代码")
    date: str = Field(..., description="日期 YYYY-MM-DD")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: int = Field(..., description="成交量")
    amount: float = Field(..., description="成交额")
    turnover_rate: Optional[float] = Field(None, description="换手率")
    change_pct: Optional[float] = Field(None, description="涨跌幅")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "sh.600000",
                "date": "2026-03-17",
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": 1000000,
                "amount": 10000000.0
            }
        }

class StockInfo(BaseModel):
    """统一股票信息模型"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    exchange: str = Field(..., description="交易所 SH/SZ")
    industry: Optional[str] = Field(None, description="行业")
    market_value: Optional[float] = Field(None, description="市值")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "sh.600000",
                "name": "浦发银行",
                "exchange": "SH"
            }
        }

class DataSourceConfig(BaseModel):
    """数据源配置模型"""
    provider: str = Field(..., description="数据源提供商")
    name: str = Field(..., description="数据源名称")
    enabled: bool = Field(True, description="是否启用")
    priority: int = Field(1, description="优先级，数字越小优先级越高")
    config: Dict[str, Any] = Field(default_factory=dict, description=" provider-specific配置")
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "baostock",
                "name": "Baostock免费数据源",
                "enabled": True,
                "priority": 1
            }
        }
