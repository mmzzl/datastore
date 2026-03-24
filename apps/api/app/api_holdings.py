import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from app.auth import create_token, get_current_user, verify_token
from pydantic import BaseModel

from app.data_source import DataSourceManager

logger = logging.getLogger(__name__)

router = APIRouter()

_data_manager = DataSourceManager()


class HoldingInput(BaseModel):
    code: str
    name: Optional[str] = None
    quantity: float
    average_cost: float


@router.get("/holdings/{user_id}")
def get_holdings(
    user_id: str,
    page: int = 1,
    page_size: int = 10,
    current_user: str = Depends(get_current_user),
):
    if current_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此持仓"
        )
    try:
        adapter = _data_manager.get_adapter("mongodb")
        if adapter and hasattr(adapter, "get_holdings"):
            return adapter.get_holdings(user_id, page, page_size)
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
        }
    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
        }
    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
        }


@router.get("/holdings/{user_id}/history")
def get_holdings_history(user_id: str, current_user: str = Depends(get_current_user)):
    """获取用户的持仓历史，包括已卖出的"""
    if current_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此持仓"
        )
    try:
        adapter = _data_manager.get_adapter("mongodb")
        if adapter and hasattr(adapter, "get_holdings_history"):
            return adapter.get_holdings_history(user_id) or []
        return []
    except Exception as e:
        logger.error(f"获取持仓历史失败: {e}")
        return []


@router.post("/holdings/{user_id}")
def upsert_holding(
    user_id: str, item: HoldingInput, current_user: str = Depends(get_current_user)
):
    if current_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此持仓"
        )
    adapter = _data_manager.get_adapter("mongodb")
    if not adapter:
        return {"holding_id": None, "success": False}

    holding_id = adapter.upsert_holding(
        user_id, item.code, item.quantity, item.average_cost
    )

    return {
        "holding_id": holding_id,
        "success": holding_id is not None,
        "type": "buy" if item.quantity > 0 else "sell",
        "code": item.code,
        "quantity": abs(item.quantity),
    }


@router.delete("/holdings/{user_id}/{code}")
def remove_holding(
    user_id: str, code: str, current_user: str = Depends(get_current_user)
):
    if current_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此持仓"
        )
    adapter = _data_manager.get_adapter("mongodb")
    if not adapter:
        raise HTTPException(status_code=500, detail="MongoDB adapter not available")
    count = adapter.remove_holding(user_id, code)
    if count == 0:
        raise HTTPException(status_code=404, detail="持仓不存在或删除失败")
    return {"deleted": count, "code": code}


@router.get("/transactions/{user_id}")
def get_transactions(
    user_id: str,
    code: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    current_user: str = Depends(get_current_user),
):
    if current_user != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问")
    adapter = _data_manager.get_adapter("mongodb")
    if not adapter:
        raise HTTPException(status_code=500, detail="MongoDB adapter not available")
    result = adapter.get_transactions(user_id, code, page, page_size)
    if isinstance(result, dict) and "items" in result:
        return result
    return {
        "items": result or [],
        "total": len(result) if result else 0,
        "page": page,
        "page_size": page_size,
        "total_pages": 0,
    }


@router.get("/pnl/{user_id}")
def get_realized_pnl(
    user_id: str,
    code: Optional[str] = None,
    current_user: str = Depends(get_current_user),
):
    if current_user != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问")
    adapter = _data_manager.get_adapter("mongodb")
    if not adapter:
        raise HTTPException(status_code=500, detail="MongoDB adapter not available")
    return adapter.calculate_realized_pnl(user_id, code)


@router.delete("/transactions/{user_id}/{transaction_id}")
def delete_transaction(
    user_id: str,
    transaction_id: str,
    current_user: str = Depends(get_current_user),
):
    if current_user != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问")
    adapter = _data_manager.get_adapter("mongodb")
    if not adapter:
        raise HTTPException(status_code=500, detail="MongoDB adapter not available")
    try:
        from bson import ObjectId

        coll = adapter.storage.db.get_collection("transactions")
        result = coll.delete_one({"_id": ObjectId(transaction_id), "user_id": user_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="交易记录不存在")
        return {"deleted": True, "transaction_id": transaction_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除交易记录失败: {e}")
        raise HTTPException(status_code=500, detail="删除失败")


class PortfolioRequest(BaseModel):
    price_fetcher_endpoint: Optional[str] = None


@router.get("/portfolio/{user_id}")
def portfolio(
    user_id: str,
    _req: Optional[PortfolioRequest] = None,
    current_user: str = Depends(get_current_user),
):
    # price_fetcher is left as an extension point; here we use a simple price fetcher via realtime data API
    def price_fetcher(code: str) -> float:
        data = _data_manager.get_realtime_data(code)
        if isinstance(data, dict):
            return float(data.get("price", 0.0) or 0.0)
        return 0.0

    # 访问控制：确保当前用户对该账户有权限
    if current_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此持仓"
        )

    summary = _data_manager.get_portfolio_summary(user_id, price_fetcher)

    mongodb_adapter = _data_manager.get_adapter("mongodb")
    if mongodb_adapter:
        pnl_data = mongodb_adapter.calculate_realized_pnl(user_id)
        summary["realized_pnl"] = pnl_data.get("realized_pnl", 0.0)
        summary["total_sell_value"] = pnl_data.get("total_sell_value", 0.0)

    return summary
