import logging
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timedelta

from ..interface import IDataSource
from ..models import StockKLine, StockInfo
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
        if not self.storage:
            return []

        try:
            kline_data = self.storage.get_kline(
                code=code, start_date=start_date, end_date=end_date, limit=1000
            )

            data_list = []
            for item in kline_data:
                kline = StockKLine(
                    code=item.get("code", code),
                    date=item.get("date", ""),
                    open=float(item.get("open", 0)),
                    high=float(item.get("high", 0)),
                    low=float(item.get("low", 0)),
                    close=float(item.get("close", 0)),
                    volume=int(item.get("volume", 0)),
                    amount=float(item.get("amount", 0)),
                    turnover_rate=float(item.get("turnover", 0))
                    if item.get("turnover")
                    else None,
                    change_pct=float(item.get("pct_chg", 0))
                    if item.get("pct_chg")
                    else None,
                )
                data_list.append(kline)

            return data_list

        except Exception as e:
            logger.error(f"获取MongoDB K线数据失败: {e}")
            return []

    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        # MongoDB通常存储K线数据，股票基本信息可以从其他数据源获取
        # 这里返回基本信息
        return StockInfo(
            code=code, name=code, exchange=code[:2] if "." in code else "SH"
        )

    def get_stock_list(self) -> List[StockInfo]:
        """从K线数据中提取股票列表"""
        if not self.storage:
            return []

        try:
            # 获取所有股票的最新数据
            kline_data = self.storage.get_all_klines(limit=10000)

            # 去重获取股票列表
            stock_dict = {}
            for item in kline_data:
                code = item.get("code")
                if code and code not in stock_dict:
                    stock_dict[code] = StockInfo(
                        code=code,
                        name=item.get("name", code),
                        exchange=code[:2] if "." in code else "SH",
                    )

            return list(stock_dict.values())

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

    # --------------- 持仓相关扩展 ---------------
    def get_holdings(self, user_id: str) -> List[Dict[str, Any]]:
        """获取某用户的持仓列表"""
        if not self.storage or not getattr(self.storage, "holdings_collection", None):
            return []
        try:
            cursor = self.storage.holdings_collection.find({"user_id": user_id})
            results = []
            for doc in cursor:
                doc["_id"] = str(doc.get("_id"))
                results.append(doc)
            return results
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            return []

    def upsert_holding(
        self, user_id: str, code: str, quantity: float, average_cost: float
    ) -> Optional[str]:
        """如果已有则更新，否则插入；成本按加权平均更新"""
        if not self.storage or not getattr(self.storage, "holdings_collection", None):
            return None
        try:
            now = __import__("datetime").datetime.now()
            coll = self.storage.holdings_collection
            existing = coll.find_one({"user_id": user_id, "code": code})
            if existing:
                old_qty = existing.get("quantity", 0.0)
                old_cost = existing.get("average_cost", 0.0)
                new_qty = old_qty + quantity
                if new_qty <= 0:
                    coll.delete_one({"_id": existing.get("_id")})
                    return None
                new_avg = (
                    ((old_qty * old_cost) + (quantity * average_cost)) / new_qty
                    if new_qty > 0
                    else 0.0
                )
                coll.update_one(
                    {"_id": existing.get("_id")},
                    {
                        "$set": {
                            "quantity": new_qty,
                            "average_cost": new_avg,
                            "updated_at": now,
                        }
                    },
                )
                return str(existing.get("_id"))
            else:
                doc = {
                    "user_id": user_id,
                    "code": code,
                    "quantity": float(quantity),
                    "average_cost": float(average_cost),
                    "created_at": now,
                    "updated_at": now,
                }
                res = coll.insert_one(doc)
                return str(res.inserted_id)
        except Exception as e:
            logger.error(f"Upsert 持仓失败: {e}")
            return None

    def remove_holding(self, user_id: str, code: str) -> int:
        """移除某用户的某一持仓"""
        if not self.storage or not getattr(self.storage, "holdings_collection", None):
            return 0
        try:
            result = self.storage.holdings_collection.delete_one(
                {"user_id": user_id, "code": code}
            )
            return result.deleted_count
        except Exception as e:
            logger.error(f"移除持仓失败: {e}")
            return 0

    def get_portfolio_summary(
        self, user_id: str, price_fetcher: Optional[Callable[[str], float]] = None
    ) -> Dict[str, Any]:
        """计算用户持仓总成本、市场价值与未实现盈亏。price_fetcher 用于获取最新价格"""
        holdings = self.get_holdings(user_id)
        total_cost = 0.0
        market_value = None
        unrealized_pnl = None
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
                except Exception:
                    market_value = None
                    unrealized_pnl = None
        return {
            "user_id": user_id,
            "holdings_count": len(holdings),
            "total_cost": total_cost,
            "market_value": market_value,
            "unrealized_pnl": unrealized_pnl,
            "holdings": holdings,
        }

    def close(self):
        """关闭MongoDB连接"""
        if self.storage:
            self.storage.close()
            logger.info("MongoDB连接已关闭")
