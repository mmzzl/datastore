import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from app.core.auth import AuthenticatedUser, require_permission, get_current_user
from pydantic import BaseModel

from app.data_source import DataSourceManager

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_data_manager() -> DataSourceManager:
    """获取 DataSourceManager 单例，如果 MongoDB adapter 未初始化则尝试重新初始化"""
    global _data_manager, _adapter_ok
    if _data_manager is None:
        _data_manager = DataSourceManager()
        _adapter_ok = False
    if not _adapter_ok:
        adapter = _data_manager.get_adapter("mongodb")
        if adapter and adapter.storage:
            _adapter_ok = True
        else:
            try:
                adapter._init_storage()
                if adapter and adapter.storage:
                    _adapter_ok = True
                    logger.info("MongoDB adapter re-initialized successfully")
            except Exception as e:
                logger.warning(f"MongoDB adapter re-init failed: {e}")
    return _data_manager


_data_manager = None
_adapter_ok = False


class HoldingInput(BaseModel):
    code: str
    name: Optional[str] = None
    quantity: float
    average_cost: float

    def validate_quantity(self):
        if self.quantity <= 0:
            raise ValueError("买入数量必须大于0")


class SellInput(BaseModel):
    quantity: float
    price: float


class ExitRuleInput(BaseModel):
    exit_strategy: str = "tiered"
    stop_loss: float = 0.05
    profit_target: float = 0.10
    trailing_stop_pct: float = 0.03
    tier_profits: Optional[List[float]] = None
    tier_sell_pcts: Optional[List[float]] = None


@router.get("/holdings/{user_id}")
def get_holdings(
    user_id: str,
    page: int = 1,
    page_size: int = 10,
    current_user: AuthenticatedUser = Depends(require_permission("holdings:view")),
):
    if current_user.user_id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此持仓"
        )
    try:
        adapter = _get_data_manager().get_adapter("mongodb")
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


@router.get("/holdings/{user_id}/history")
def get_holdings_history(
    user_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("holdings:view"))
):
    if current_user.user_id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此持仓"
        )
    try:
        adapter = _get_data_manager().get_adapter("mongodb")
        if adapter and hasattr(adapter, "get_holdings_history"):
            return adapter.get_holdings_history(user_id) or []
        return []
    except Exception as e:
        logger.error(f"获取持仓历史失败: {e}")
        return []


@router.post("/holdings/{user_id}")
def upsert_holding(
    user_id: str,
    item: HoldingInput,
    current_user: AuthenticatedUser = Depends(require_permission("holdings:edit"))
):
    """买入持仓 — 只接受正数量，手动添加"""
    if current_user.user_id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此持仓"
        )
    # if item.quantity <= 0:
    #     raise HTTPException(status_code=400, detail="买入数量必须大于0，请使用卖出接口")

    adapter = _get_data_manager().get_adapter("mongodb")
    if not adapter:
        return {"holding_id": None, "success": False}

    holding_id = adapter.upsert_holding(
        user_id, item.code, item.quantity, item.average_cost
    )

    return {
        "holding_id": holding_id,
        "success": holding_id is not None,
        "type": "buy",
        "code": item.code,
        "quantity": item.quantity,
    }


@router.post("/holdings/{user_id}/{code}/sell")
def sell_holding(
    user_id: str,
    code: str,
    body: SellInput,
    current_user: AuthenticatedUser = Depends(require_permission("holdings:edit"))
):
    """卖出持仓 — 独立端点"""
    if current_user.user_id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此持仓"
        )
    if body.quantity <= 0:
        raise HTTPException(status_code=400, detail="卖出数量必须大于0")

    adapter = _get_data_manager().get_adapter("mongodb")
    if not adapter:
        raise HTTPException(status_code=500, detail="MongoDB adapter not available")

    holding_id = adapter.sell_holding(user_id, code, body.quantity, body.price)
    if holding_id is None:
        raise HTTPException(status_code=400, detail="卖出失败，持仓可能不存在")

    return {
        "holding_id": holding_id,
        "success": True,
        "type": "sell",
        "code": code,
        "quantity": body.quantity,
    }


@router.delete("/holdings/{user_id}/{code}")
def remove_holding(
    user_id: str,
    code: str,
    current_user: AuthenticatedUser = Depends(require_permission("holdings:edit"))
):
    if current_user.user_id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此持仓"
        )
    adapter = _get_data_manager().get_adapter("mongodb")
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
    current_user: AuthenticatedUser = Depends(require_permission("holdings:view")),
):
    if current_user.user_id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问")
    adapter = _get_data_manager().get_adapter("mongodb")
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
    current_user: AuthenticatedUser = Depends(require_permission("holdings:view")),
):
    if current_user.user_id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问")
    adapter = _get_data_manager().get_adapter("mongodb")
    if not adapter:
        raise HTTPException(status_code=500, detail="MongoDB adapter not available")
    return adapter.calculate_realized_pnl(user_id, code)


@router.delete("/transactions/{user_id}/{transaction_id}")
def delete_transaction(
    user_id: str,
    transaction_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("holdings:edit")),
):
    if current_user.user_id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问")
    adapter = _get_data_manager().get_adapter("mongodb")
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


DEFAULT_TIER_PROFITS = [0.03, 0.05, 0.08, 0.10]
DEFAULT_TIER_SELL_PCTS = [0.25, 0.25, 0.25, 0.25]


def _build_exit_rules_text(exit_rule: dict) -> list:
    strategy = exit_rule.get("exit_strategy", "fixed")
    stop_loss = exit_rule.get("stop_loss", 0.05)
    trailing_pct = exit_rule.get("trailing_stop_pct", 0.03)
    lines = [f"亏损 ≥{stop_loss*100:.0f}% → 止损卖出全部"]

    if strategy == "tiered":
        profits = exit_rule.get("tier_profits", DEFAULT_TIER_PROFITS)
        sell_pcts = exit_rule.get("tier_sell_pcts", DEFAULT_TIER_SELL_PCTS)
        for i, p in enumerate(profits):
            pct = sell_pcts[i] if i < len(sell_pcts) else 25
            lines.append(f"盈利 ≥{p*100:.0f}% → 卖出 {pct*100:.0f}%")
        lines.append(f"全部触发后启用 {trailing_pct*100:.0f}% 回撤追踪止损")
    elif strategy == "trailing":
        profit_target = exit_rule.get("profit_target", 0.10)
        lines.append(f"盈利 ≥{profit_target*100:.0f}% → 启用 {trailing_pct*100:.0f}% 回撤追踪止损")
    else:
        profit_target = exit_rule.get("profit_target", 0.10)
        lines.append(f"盈利 ≥{profit_target*100:.0f}% → 卖出全部")

    return lines


@router.get("/holdings/{user_id}/{code}/exit-rule")
def get_exit_rule(
    user_id: str,
    code: str,
    current_user: AuthenticatedUser = Depends(require_permission("holdings:view")),
):
    if current_user.user_id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问")

    adapter = _get_data_manager().get_adapter("mongodb")
    if not adapter or not adapter.storage:
        raise HTTPException(status_code=500, detail="MongoDB adapter not available")

    coll = adapter.storage.db.get_collection("holdings")
    holding = coll.find_one({"user_id": user_id, "code": code, "quantity": {"$gt": 0}})
    if not holding:
        raise HTTPException(status_code=404, detail="未找到该持仓")

    cost_price = holding.get("average_cost", 0)
    exit_rule = holding.get("exit_rule", {
        "exit_strategy": "tiered",
        "stop_loss": 0.05,
        "profit_target": 0.10,
        "trailing_stop_pct": 0.03,
        "tier_profits": DEFAULT_TIER_PROFITS,
        "tier_sell_pcts": DEFAULT_TIER_SELL_PCTS,
    })
    highest_price = holding.get("highest_price", cost_price)

    dm = _get_data_manager()
    current_price = cost_price
    try:
        rt = dm.get_realtime_data(code)
        if isinstance(rt, dict):
            current_price = float(rt.get("price") or rt.get("close") or cost_price)
    except Exception:
        pass

    if current_price > highest_price:
        highest_price = current_price
        coll.update_one(
            {"_id": holding["_id"]},
            {"$set": {"highest_price": highest_price}},
        )

    profit_pct = ((current_price - cost_price) / cost_price * 100) if cost_price > 0 else 0
    stop_loss_price = cost_price * (1 - exit_rule.get("stop_loss", 0.05))
    trailing_stop_price = highest_price * (1 - exit_rule.get("trailing_stop_pct", 0.03))

    # Build tier rules with triggered status
    tier_rules = []
    if exit_rule.get("exit_strategy") == "tiered":
        profits = exit_rule.get("tier_profits", DEFAULT_TIER_PROFITS)
        sell_pcts = exit_rule.get("tier_sell_pcts", DEFAULT_TIER_SELL_PCTS)
        tier_triggered = holding.get("tier_triggered", [])
        for i, p in enumerate(profits):
            pct = sell_pcts[i] if i < len(sell_pcts) else 0.25
            triggered = i < len(tier_triggered) and bool(tier_triggered[i])
            tier_rules.append({
                "profit_pct": p * 100,
                "sell_pct": pct * 100,
                "triggered": triggered,
            })

    return {
        "code": code,
        "name": holding.get("name", code),
        "cost_price": cost_price,
        "current_price": current_price,
        "profit_pct": round(profit_pct, 2),
        "highest_price": highest_price,
        "exit_strategy": exit_rule.get("exit_strategy", "tiered"),
        "stop_loss": exit_rule.get("stop_loss", 0.05),
        "profit_target": exit_rule.get("profit_target", 0.10),
        "trailing_stop_pct": exit_rule.get("trailing_stop_pct", 0.03),
        "tier_profits": exit_rule.get("tier_profits", DEFAULT_TIER_PROFITS),
        "tier_sell_pcts": exit_rule.get("tier_sell_pcts", DEFAULT_TIER_SELL_PCTS),
        "stop_loss_price": round(stop_loss_price, 3),
        "trailing_stop_price": round(trailing_stop_price, 3),
        "tier_rules": tier_rules,
        "exit_rules_text": _build_exit_rules_text(exit_rule),
    }


@router.put("/holdings/{user_id}/{code}/exit-rule")
def set_exit_rule(
    user_id: str,
    code: str,
    body: ExitRuleInput,
    current_user: AuthenticatedUser = Depends(require_permission("holdings:edit")),
):
    if current_user.user_id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问")

    adapter = _get_data_manager().get_adapter("mongodb")
    if not adapter or not adapter.storage:
        raise HTTPException(status_code=500, detail="MongoDB adapter not available")

    coll = adapter.storage.db.get_collection("holdings")
    holding = coll.find_one({"user_id": user_id, "code": code, "quantity": {"$gt": 0}})
    if not holding:
        raise HTTPException(status_code=404, detail="未找到该持仓")

    tier_profits = body.tier_profits or DEFAULT_TIER_PROFITS
    tier_sell_pcts = body.tier_sell_pcts or DEFAULT_TIER_SELL_PCTS

    exit_rule = {
        "exit_strategy": body.exit_strategy,
        "stop_loss": body.stop_loss,
        "profit_target": body.profit_target,
        "trailing_stop_pct": body.trailing_stop_pct,
        "tier_profits": tier_profits,
        "tier_sell_pcts": tier_sell_pcts,
    }

    cost_price = holding.get("average_cost", 0)
    highest_price = holding.get("highest_price", cost_price)

    update = {"$set": {"exit_rule": exit_rule}}
    if not holding.get("highest_price"):
        update["$set"]["highest_price"] = cost_price

    coll.update_one({"_id": holding["_id"]}, update)

    return {"success": True, "exit_rule": exit_rule}


class PortfolioRequest(BaseModel):
    price_fetcher_endpoint: Optional[str] = None


@router.get("/portfolio/{user_id}")
def portfolio(
    user_id: str,
    _req: Optional[PortfolioRequest] = None,
    current_user: AuthenticatedUser = Depends(require_permission("holdings:view")),
):
    dm = _get_data_manager()

    def price_fetcher(code: str) -> float:
        data = dm.get_realtime_data(code)
        if isinstance(data, dict):
            return float(data.get("price", 0.0) or 0.0)
        return 0.0

    if current_user.user_id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此持仓"
        )

    summary = dm.get_portfolio_summary(user_id, price_fetcher)

    mongodb_adapter = dm.get_adapter("mongodb")
    if mongodb_adapter:
        pnl_data = mongodb_adapter.calculate_realized_pnl(user_id)
        summary["realized_pnl"] = pnl_data.get("realized_pnl", 0.0)
        summary["total_sell_value"] = pnl_data.get("total_sell_value", 0.0)

    return summary
