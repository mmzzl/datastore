import logging
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.data_source import DataSourceManager

logger = logging.getLogger(__name__)

router = APIRouter()

_data_manager = DataSourceManager()


class HoldingInput(BaseModel):
    code: str
    quantity: float
    average_cost: float


@router.get("/holdings/{user_id}")
def get_holdings(user_id: str):
    try:
        return _data_manager.get_holdings(user_id) or []
    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        return []


@router.post("/holdings/{user_id}")
def upsert_holding(user_id: str, item: HoldingInput):
    # 使用数据源管理器直接操作底层适配器的持仓能力
    adapter = _data_manager.get_adapter("mongodb")
    if not adapter:
        return {"holding_id": None}
    holding_id = adapter.upsert_holding(
        user_id=user_id,
        code=item.code,
        quantity=item.quantity,
        average_cost=item.average_cost,
    )
    return {"holding_id": holding_id}


@router.delete("/holdings/{user_id}/{code}")
def remove_holding(user_id: str, code: str):
    adapter = _data_manager.get_adapter("mongodb")
    count = adapter.remove_holding(user_id, code) if adapter else 0
    return {"deleted": count}


class PortfolioRequest(BaseModel):
    price_fetcher_endpoint: Optional[str] = None


@router.get("/portfolio/{user_id}")
def portfolio(user_id: str, _req: PortfolioRequest = None):
    # price_fetcher is left as an extension point; here we use a simple price fetcher via realtime data API
    def price_fetcher(code: str) -> float:
        data = _data_manager.get_realtime_data(code)
        if isinstance(data, dict):
            return float(data.get("price", 0.0) or 0.0)
        return 0.0

    return _data_manager.get_portfolio_summary(user_id, price_fetcher)
