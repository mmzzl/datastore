import logging
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timedelta

from ..interface import IDataSource
from ..models import StockKLine, StockInfo, MarketBreadth, CorrelatedAssets
from ...storage.mongo_client import MongoStorage
from ...core.config import settings

logger = logging.getLogger(__name__)


class MongoDBAdapter(IDataSource):
    """MongoDB数据源适配器"""

    def __init__(self):
        self._name = "MongoDB"
        self._provider = "mongodb"
        self.storage = None
        self._init_storage()

    def _init_storage(self):
        """初始化存储连接"""
        try:
            self.storage = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_database,
                username=settings.mongodb_username,
                password=settings.mongodb_password,
            )
            self.storage.connect()
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB: {e}")
            self.storage = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def provider(self) -> str:
        return self._provider

    def get_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d",
        adjust_flag: str = "3",
    ) -> List[StockKLine]:
        """从MongoDB获取K线数据"""
        if not self.storage:
            return []
        try:
            coll = getattr(self.storage, "kline_collection", None)
            if coll is None:
                return []
            query = {
                "code": code,
                "date": {"$gte": start_date, "$lte": end_date},
            }
            cursor = coll.find(query).sort("date", 1)
            results = []
            for doc in cursor:
                results.append(
                    StockKLine(
                        code=doc.get("code"),
                        date=doc.get("date"),
                        open=float(doc.get("open", 0)),
                        high=float(doc.get("high", 0)),
                        low=float(doc.get("low", 0)),
                        close=float(doc.get("close", 0)),
                        volume=int(doc.get("volume", 0)),
                        amount=float(doc.get("amount", 0)) if doc.get("amount") else 0,
                    )
                )
            return results
        except Exception as e:
            logger.error(f"获取K线失败: {e}")
            return []

    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        """从MongoDB获取股票信息"""
        if not self.storage:
            return None
        try:
            coll = getattr(self.storage, "stock_info_collection", None)
            if coll is None:
                return None
            doc = coll.find_one({"code": code})
            if doc:
                return StockInfo(
                    code=doc.get("code"),
                    name=doc.get("name"),
                    exchange=doc.get("exchange", code[:2]),
                )
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
        return None

    def get_stock_list(self) -> List[StockInfo]:
        """从MongoDB获取股票列表"""
        if not self.storage:
            return []
        try:
            coll = getattr(self.storage, "stock_info_collection", None)
            if coll is None:
                return []
            cursor = coll.find({})
            results = []
            for doc in cursor:
                results.append(
                    StockInfo(
                        code=doc.get("code"),
                        name=doc.get("name"),
                        exchange=doc.get("exchange", doc.get("code", "")[:2]),
                    )
                )
            return results
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []

    def get_realtime_data(self, code: str) -> Dict[str, Any]:
        """MongoDB不提供实时数据"""
        return {}

    def get_capital_flow(self, code: str, days: int = 5) -> List[Dict[str, Any]]:
        """从MongoDB获取资金流向数据"""
        if not self.storage:
            return []
        return []

    # --------------- 持仓相关扩展 ---------------
    def get_holdings(
        self, user_id: str, page: int = 1, page_size: int = 10
    ) -> Dict[str, Any]:
        """获取某用户的持仓列表（只返回数量大于0的），支持分页"""
        if not self.storage:
            logger.warning("Storage is None in get_holdings")
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
            }
        try:
            coll = getattr(self.storage, "holdings_collection", None)
            if coll is None:
                logger.warning("holdings_collection is None")
                return {
                    "items": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                }

            query = {"user_id": user_id, "quantity": {"$gt": 0}}
            total = coll.count_documents(query)
            logger.info(f"get_holdings query: user_id={user_id}, total={total}")
            skip = (page - 1) * page_size
            cursor = coll.find(query).skip(skip).limit(page_size)

            results = []
            for doc in cursor:
                doc["_id"] = str(doc.get("_id"))
                results.append(doc)

            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            logger.info(f"get_holdings returning {len(results)} items, total={total}")
            return {
                "items": results,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
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

    def get_holdings_history(self, user_id: str) -> List[Dict[str, Any]]:
        """获取某用户的所有持仓历史，包括已卖出的"""
        if not self.storage:
            return []
        try:
            coll = getattr(self.storage, "holdings_collection", None)
            if coll is None:
                return []
            cursor = coll.find({"user_id": user_id}).sort("updated_at", -1)
            results = []
            for doc in cursor:
                doc["_id"] = str(doc.get("_id"))
                results.append(doc)
            return results
        except Exception as e:
            logger.error(f"获取持仓历史失败: {e}")
            return []

    def upsert_holding(
        self, user_id: str, code: str, quantity: float, price: float
    ) -> Optional[str]:
        """买入/卖出持仓处理，使用移动平均成本法（东方财富算法）"""
        if not self.storage:
            return None
        try:
            tx_type = "buy" if quantity > 0 else "sell"
            self.add_transaction(user_id, code, quantity, price, tx_type)

            transactions = self.get_transactions(user_id, code).get("items", [])

            # 计算各项数据
            total_buy_amount = sum(
                t["quantity"] * t["price"] for t in transactions if t["type"] == "buy"
            )
            total_buy_qty = sum(
                t["quantity"] for t in transactions if t["type"] == "buy"
            )
            total_sell_qty = sum(
                t["quantity"] for t in transactions if t["type"] == "sell"
            )
            total_sell_amount = sum(
                t["quantity"] * t["price"] for t in transactions if t["type"] == "sell"
            )
            current_qty = total_buy_qty - total_sell_qty

            coll = getattr(self.storage, "holdings_collection", None)
            if coll is None:
                return None

            now = __import__("datetime").datetime.now()
            existing = coll.find_one({"user_id": user_id, "code": code})

            # 计算成本
            avg_cost = 0.0
            if current_qty > 0:
                if tx_type == "sell":
                    # 卖出时：成本价 = (总买入金额 − 卖出金额) ÷ 剩余股数
                    avg_cost = (total_buy_amount - total_sell_amount) / current_qty
                else:
                    # 买入时：加权平均
                    if existing:
                        old_qty = existing.get("quantity", 0)
                        old_cost = existing.get("average_cost", 0)
                        avg_cost = (old_qty * old_cost + quantity * price) / (
                            old_qty + quantity
                        )
                    else:
                        avg_cost = price
            else:
                avg_cost = 0.0

            if existing:
                coll.update_one(
                    {"_id": existing.get("_id")},
                    {
                        "$set": {
                            "quantity": current_qty,
                            "average_cost": avg_cost,
                            "updated_at": now,
                        }
                    },
                )
                return str(existing.get("_id"))
            else:
                doc = {
                    "user_id": user_id,
                    "code": code,
                    "quantity": current_qty,
                    "average_cost": avg_cost,
                    "created_at": now,
                    "updated_at": now,
                }
                res = coll.insert_one(doc)
                return str(res.inserted_id)
        except Exception as e:
            logger.error(f"Upsert 持仓失败: {e}")
            return None

    def sell_holding(
        self, user_id: str, code: str, quantity: float, price: float
    ) -> Optional[str]:
        """卖出持仓，记录卖出交易并更新持仓数量和成本"""
        if not self.storage or quantity <= 0:
            return None
        try:
            self.add_transaction(user_id, code, quantity, price, "sell")

            transactions = self.get_transactions(user_id, code).get("items", [])

            total_buy_qty = sum(
                t["quantity"] for t in transactions if t["type"] == "buy"
            )
            total_sell_qty = sum(
                t["quantity"] for t in transactions if t["type"] == "sell"
            )
            current_qty = total_buy_qty - total_sell_qty

            total_buy_amount = sum(
                t["quantity"] * t["price"] for t in transactions if t["type"] == "buy"
            )
            total_sell_amount = sum(
                t["quantity"] * t["price"] for t in transactions if t["type"] == "sell"
            )
            avg_cost = 0.0
            if current_qty > 0:
                avg_cost = (total_buy_amount - total_sell_amount) / current_qty

            coll = getattr(self.storage, "holdings_collection", None)
            if coll is None:
                return None

            now = __import__("datetime").datetime.now()
            existing = coll.find_one({"user_id": user_id, "code": code})

            if existing:
                coll.update_one(
                    {"_id": existing.get("_id")},
                    {
                        "$set": {
                            "quantity": current_qty,
                            "average_cost": avg_cost,
                            "updated_at": now,
                        }
                    },
                )
                return str(existing.get("_id"))
            return None
        except Exception as e:
            logger.error(f"卖出持仓失败: {e}")
            return None

    def remove_holding(self, user_id: str, code: str) -> int:
        """移除某用户的某一持仓"""
        if not self.storage:
            return 0
        try:
            coll = getattr(self.storage, "holdings_collection", None)
            if coll is None:
                return 0
            result = coll.delete_one({"user_id": user_id, "code": code})
            return result.deleted_count
        except Exception as e:
            logger.error(f"移除持仓失败: {e}")
            return 0

    def set_holdings(self, user_id: str, holdings: List[Dict[str, Any]]) -> List[str]:
        """已禁用 — 持仓只能通过手动买入添加"""
        raise RuntimeError("批量设定持仓已禁用，请通过买入接口手动添加")

    def get_market_breadth(self) -> Optional[MarketBreadth]:
        return None

    def get_correlated_assets(self) -> Optional[CorrelatedAssets]:
        return None

    def get_minute_kline(
        self, code: str, frequency: str = "5", days: int = 5
    ) -> List[StockKLine]:
        return []

    def get_portfolio_summary(
        self, user_id: str, price_fetcher: Optional[Callable[[str], float]] = None
    ) -> Dict[str, Any]:
        """计算用户持仓总成本、市场价值与未实现盈亏。price_fetcher 用于获取最新价格"""
        result = self.get_holdings(user_id, page=1, page_size=100)
        holdings = result.get("items", []) if isinstance(result, dict) else []
        logger.info(
            f"get_portfolio_summary: user_id={user_id}, holdings_count={len(holdings)}"
        )
        total_cost = 0.0
        market_value = None
        unrealized_pnl = None
        profit = 0.0
        profit_rate = 0.0
        if holdings:
            total_cost = sum(
                h.get("quantity", 0.0) * h.get("average_cost", 0.0) for h in holdings
            )
            if price_fetcher:
                try:
                    market_value = sum(
                        h.get("quantity", 0.0) * price_fetcher(h.get("code"))
                        for h in holdings
                    )
                    unrealized_pnl = (market_value or 0.0) - total_cost
                    profit = unrealized_pnl
                    profit_rate = profit / total_cost if total_cost > 0 else 0.0
                except Exception:
                    market_value = None
                    unrealized_pnl = None
        return {
            "user_id": user_id,
            "holdings_count": len(holdings),
            "total_cost": total_cost,
            "market_value": market_value,
            "unrealized_pnl": unrealized_pnl,
            "profit": profit,
            "profit_rate": profit_rate,
            "holdings": holdings,
        }

    def close(self):
        """关闭MongoDB连接"""
        if self.storage:
            self.storage.close()
            logger.info("MongoDB连接已关闭")

    def get_settings(self, user_id: str) -> Dict[str, Any]:
        """获取用户设置，若无则返回默认设置"""
        if not self.storage:
            return {"watchlist": [], "interval_sec": 60, "days": 5, "cache_ttl": 60}
        try:
            coll = getattr(self.storage, "settings_collection", None)
            if coll is None:
                return {"watchlist": [], "interval_sec": 60, "days": 5, "cache_ttl": 60}
            doc = coll.find_one({"user_id": user_id})
            if doc:
                return {
                    "watchlist": doc.get("watchlist", []),
                    "interval_sec": doc.get("interval_sec", 60),
                    "days": doc.get("days", 5),
                    "cache_ttl": doc.get("cache_ttl", 60),
                }
        except Exception as e:
            logger.error(f"获取设置失败: {e}")
        return {"watchlist": [], "interval_sec": 60, "days": 5, "cache_ttl": 60}

    def set_settings(self, user_id: str, settings: Dict[str, Any]) -> None:
        """保存用户设置"""
        if not self.storage:
            raise RuntimeError("MongoDB storage not available")
        try:
            coll = getattr(self.storage, "settings_collection", None)
            if coll is None:
                raise RuntimeError("settings_collection not available")
            doc = {
                "user_id": user_id,
                **settings,
                "updated_at": __import__("datetime").datetime.now(),
            }
            coll.update_one({"user_id": user_id}, {"$set": doc}, upsert=True)
        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"设置 Settings 失败: {e}")
            raise RuntimeError(f"保存设置失败: {e}")

    def add_transaction(
        self,
        user_id: str,
        code: str,
        quantity: float,
        price: float,
        transaction_type: str,
    ) -> Optional[str]:
        """添加交易记录（buy/sell）"""
        if not self.storage:
            return None
        try:
            coll = self.storage.db.get_collection("transactions")
            now = __import__("datetime").datetime.now()
            doc = {
                "user_id": user_id,
                "code": code,
                "quantity": abs(quantity),
                "price": float(price),
                "type": transaction_type,
                "created_at": now,
            }
            res = coll.insert_one(doc)
            return str(res.inserted_id)
        except Exception as e:
            logger.error(f"添加交易记录失败: {e}")
            return None

    def get_transactions(
        self,
        user_id: str,
        code: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        """获取交易历史，支持分页"""
        if not self.storage:
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
            }
        try:
            coll = self.storage.db.get_collection("transactions")
            query = {"user_id": user_id}
            if code:
                query["code"] = code
            total = coll.count_documents(query)
            skip = (page - 1) * page_size
            cursor = coll.find(query).sort("created_at", 1).skip(skip).limit(page_size)
            results = []
            for doc in cursor:
                doc["_id"] = str(doc.get("_id"))
                results.append(doc)
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            return {
                "items": results,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }
        except Exception as e:
            logger.error(f"获取交易历史失败: {e}")
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
            }

    def calculate_realized_pnl(
        self, user_id: str, code: Optional[str] = None
    ) -> Dict[str, float]:
        """计算已实现盈亏（按股票代码分别移动平均法，与东方财富一致）"""
        if not self.storage:
            return {
                "realized_pnl": 0.0,
                "total_sell_value": 0.0,
                "total_sell_cost": 0.0,
            }
        try:
            transactions = self.get_transactions(user_id, code, page=1, page_size=1000).get("items", [])
            total_sell_value = 0.0
            total_sell_cost = 0.0

            per_stock: Dict[str, Dict[str, float]] = {}

            for tx in sorted(transactions, key=lambda x: x["created_at"]):
                tx_code = tx.get("code", "")
                if tx_code not in per_stock:
                    per_stock[tx_code] = {"qty": 0, "cost": 0.0}
                stock = per_stock[tx_code]

                if tx["type"] == "buy":
                    buy_qty = tx["quantity"]
                    buy_price = tx["price"]
                    if stock["qty"] > 0:
                        stock["cost"] = (
                            stock["qty"] * stock["cost"] + buy_qty * buy_price
                        ) / (stock["qty"] + buy_qty)
                    else:
                        stock["cost"] = buy_price
                    stock["qty"] += buy_qty
                else:
                    sell_qty = tx["quantity"]
                    sell_price = tx["price"]
                    total_sell_value += sell_qty * sell_price
                    total_sell_cost += sell_qty * stock["cost"]
                    stock["qty"] -= sell_qty

            realized_pnl = total_sell_value - total_sell_cost
            return {
                "realized_pnl": realized_pnl,
                "total_sell_value": total_sell_value,
                "total_sell_cost": total_sell_cost,
            }
        except Exception as e:
            logger.error(f"计算已实现盈亏失败: {e}")
            return {
                "realized_pnl": 0.0,
                "total_sell_value": 0.0,
                "total_sell_cost": 0.0,
            }
        try:
            transactions = self.get_transactions(user_id, code).get("items", [])
            total_sell_value = 0.0
            total_sell_cost = 0.0

            # 按时间顺序计算移动平均成本
            running_qty = 0
            running_cost = 0.0

            for tx in sorted(transactions, key=lambda x: x["created_at"]):
                if tx["type"] == "buy":
                    buy_qty = tx["quantity"]
                    buy_price = tx["price"]
                    if running_qty > 0:
                        running_cost = (
                            running_qty * running_cost + buy_qty * buy_price
                        ) / (running_qty + buy_qty)
                    else:
                        running_cost = buy_price
                    running_qty += buy_qty
                else:  # sell
                    sell_qty = tx["quantity"]
                    sell_price = tx["price"]
                    total_sell_value += sell_qty * sell_price
                    total_sell_cost += sell_qty * running_cost
                    running_qty -= sell_qty

            realized_pnl = total_sell_value - total_sell_cost
            return {
                "realized_pnl": realized_pnl,
                "total_sell_value": total_sell_value,
                "total_sell_cost": total_sell_cost,
            }
        except Exception as e:
            logger.error(f"计算已实现盈亏失败: {e}")
            return {
                "realized_pnl": 0.0,
                "total_sell_value": 0.0,
                "total_sell_cost": 0.0,
            }
        try:
            transactions = self.get_transactions(user_id, code)
            total_sell_value = 0.0
            total_sell_cost = 0.0

            # 模拟交易过程，按时间顺序计算
            running_qty = 0  # 当前持股数
            running_cost = 0.0  # 当前持股成本

            for tx in sorted(transactions, key=lambda x: x["created_at"]):
                if tx["type"] == "buy":
                    buy_qty = tx["quantity"]
                    buy_price = tx["price"]
                    if running_qty > 0:
                        # 移动平均：新的加权平均成本
                        running_cost = (
                            running_qty * running_cost + buy_qty * buy_price
                        ) / (running_qty + buy_qty)
                    else:
                        running_cost = buy_price
                    running_qty += buy_qty
                else:  # sell
                    sell_qty = tx["quantity"]
                    sell_price = tx["price"]
                    total_sell_value += sell_qty * sell_price
                    # 已实现盈亏 = 卖出数量 × (卖出价格 - 卖出时的持仓成本)
                    total_sell_cost += sell_qty * running_cost
                    running_qty -= sell_qty

            realized_pnl = total_sell_value - total_sell_cost
            return {
                "realized_pnl": realized_pnl,
                "total_sell_value": total_sell_value,
                "total_sell_cost": total_sell_cost,
            }
        except Exception as e:
            logger.error(f"计算已实现盈亏失败: {e}")
            return {
                "realized_pnl": 0.0,
                "total_sell_value": 0.0,
                "total_sell_cost": 0.0,
            }
