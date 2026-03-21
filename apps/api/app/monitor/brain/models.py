from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class BrainDecision(BaseModel):
    """大脑决策模型"""
    code: str = Field(..., description="股票代码")
    action: str = Field(..., description="操作类型: buy/sell/hold")
    confidence: float = Field(..., description="置信度 0-1")
    target_price: float = Field(..., description="目标价格")
    entry_price: float = Field(..., description="建议入场价格")
    stop_loss: float = Field(..., description="止损价格")
    reasons: List[str] = Field(default_factory=list, description="决策原因")
    timestamp: datetime = Field(default_factory=datetime.now, description="决策时间")

class UnhookStrategy(BaseModel):
    """解套策略模型"""
    code: str = Field(..., description="股票代码")
    current_price: float = Field(..., description="当前价格")
    cost_price: float = Field(..., description="持仓成本")
    suggestion: str = Field(..., description="策略建议")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细操作")
    expected_recovery_time: str = Field(default="未知", description="预计解套时间")
    timestamp: datetime = Field(default_factory=datetime.now, description="策略生成时间")
