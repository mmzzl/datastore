"""异步 MongoDB 存储层 — 基于 motor，供 API endpoints 使用"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from bson.objectid import ObjectId
import logging

logger = logging.getLogger(__name__)


def _serialize_datetime(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return None


class AsyncMongoStorage:
    def __init__(
        self,
        host: str,
        port: int,
        db_name: str,
        username: str = None,
        password: str = None,
    ):
        self.host = host
        self.port = port
        self.db_name = db_name
        self.username = username
        self.password = password
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self._is_shared = False

    async def connect(self):
        if self.username and self.password:
            encoded_password = quote_plus(self.password)
            uri = f"mongodb://{self.username}:{encoded_password}@{self.host}:{self.port}"
        else:
            uri = f"mongodb://{self.host}:{self.port}"

        self.client = AsyncIOMotorClient(
            uri,
            maxPoolSize=20,
            minPoolSize=2,
            maxIdleTimeMS=60000,
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=30000,
            retryWrites=True,
            retryReads=True,
        )
        self.db = self.client[self.db_name]
        await self._ensure_indexes()
        # 验证连接
        await self.client.admin.command("ping")
        logger.info(f"AsyncMongoDB connected: {self.host}:{self.port}/{self.db_name}")

    async def _ensure_indexes(self):
        try:
            await self.db["users"].create_index("username", unique=True)
            await self.db["users"].create_index("email", unique=True, sparse=True)
            await self.db["users"].create_index("role_id")
            await self.db["users"].create_index("status")
            await self.db["roles"].create_index("role_id", unique=True)
            await self.db["watch_list"].create_index("symbol", unique=True)
            await self.db["market_signals"].create_index(
                [("symbol", ASCENDING), ("timestamp", DESCENDING)]
            )
        except Exception as e:
            logger.warning(f"Create indexes skipped: {e}")

    def close(self):
        if self._is_shared:
            return
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
            self.db = None

    def _col(self, name):
        return self.db[name]

    # ==================== 用户 ====================

    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        return await self._col("users").find_one({"username": username})

    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        if ObjectId.is_valid(user_id):
            return await self._col("users").find_one({"_id": ObjectId(user_id)})
        return await self._col("users").find_one({"username": user_id})

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        cursor = self._col("users").find().skip(skip).limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["created_at"] = _serialize_datetime(doc.get("created_at"))
            doc["updated_at"] = _serialize_datetime(doc.get("updated_at"))
            doc["last_login"] = _serialize_datetime(doc.get("last_login"))
            results.append(doc)
        return results

    async def save_user(self, user_data: Dict) -> str:
        result = await self._col("users").insert_one(user_data)
        return str(result.inserted_id)

    async def update_user(self, user_id: str, update_data: Dict) -> bool:
        update_data["updated_at"] = datetime.now()
        if ObjectId.is_valid(user_id):
            result = await self._col("users").update_one(
                {"_id": ObjectId(user_id)}, {"$set": update_data}
            )
        else:
            result = await self._col("users").update_one(
                {"username": user_id}, {"$set": update_data}
            )
        return result.modified_count > 0

    async def delete_user(self, user_id: str) -> bool:
        if ObjectId.is_valid(user_id):
            result = await self._col("users").delete_one({"_id": ObjectId(user_id)})
        else:
            result = await self._col("users").delete_one({"username": user_id})
        return result.deleted_count > 0

    async def update_user_login(self, user_id: str) -> bool:
        result = await self._col("users").update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {"last_login": datetime.now(), "updated_at": datetime.now()},
                "$inc": {"login_count": 1},
            },
        )
        return result.modified_count > 0

    # ==================== 角色 ====================

    async def get_role_by_id(self, role_id: str) -> Optional[Dict]:
        return await self._col("roles").find_one({"role_id": role_id})

    async def get_all_roles(self) -> List[Dict]:
        cursor = self._col("roles").find()
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["created_at"] = _serialize_datetime(doc.get("created_at"))
            doc["updated_at"] = _serialize_datetime(doc.get("updated_at"))
            results.append(doc)
        return results

    async def save_role(self, role_data: Dict) -> str:
        role_data["created_at"] = datetime.now()
        role_data["updated_at"] = datetime.now()
        result = await self._col("roles").insert_one(role_data)
        return str(result.inserted_id)

    async def update_role(self, role_id: str, update_data: Dict) -> bool:
        update_data["updated_at"] = datetime.now()
        result = await self._col("roles").update_one(
            {"role_id": role_id}, {"$set": update_data}
        )
        return result.modified_count > 0

    async def delete_role(self, role_id: str) -> bool:
        result = await self._col("roles").delete_one({"role_id": role_id})
        return result.deleted_count > 0

    # ==================== K 线 ====================

    async def get_kline(
        self, code: str, start_date: str = None, end_date: str = None, limit: int = 100
    ) -> List[Dict]:
        query = {"code": code}
        if start_date:
            query["date"] = {"$gte": start_date}
        if end_date:
            if "date" in query:
                query["date"]["$lte"] = end_date
            else:
                query["date"] = {"$lte": end_date}
        cursor = self._col("stock_kline").find(query).sort("date", DESCENDING).limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["crawl_time"] = _serialize_datetime(doc.get("crawl_time"))
            results.append(doc)
        return results

    async def get_kline_by_name(
        self, name: str, start_date: str = None, end_date: str = None, limit: int = 100
    ) -> List[Dict]:
        query = {"name": name}
        if start_date:
            query["date"] = {"$gte": start_date}
        if end_date:
            if "date" in query:
                query["date"]["$lte"] = end_date
            else:
                query["date"] = {"$lte": end_date}
        cursor = self._col("stock_kline").find(query).sort("date", DESCENDING).limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["crawl_time"] = _serialize_datetime(doc.get("crawl_time"))
            results.append(doc)
        return results

    async def get_kline_by_date(self, code: str, date: str) -> Optional[Dict]:
        doc = await self._col("stock_kline").find_one({"code": code, "date": date})
        if doc:
            doc["_id"] = str(doc["_id"])
            doc["crawl_time"] = _serialize_datetime(doc.get("crawl_time"))
        return doc

    async def get_all_kline_by_date(
        self, date: str, limit: int = 5000, deduplicate: bool = True
    ) -> List[Dict]:
        if deduplicate:
            pipeline = [
                {"$match": {"date": date}},
                {"$sort": {"crawl_time": -1}},
                {"$group": {"_id": "$code", "doc": {"$first": "$$ROOT"}}},
                {"$replaceRoot": {"newRoot": "$doc"}},
                {"$limit": limit},
            ]
            cursor = self._col("stock_kline").aggregate(pipeline)
        else:
            cursor = self._col("stock_kline").find({"date": date}).limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["crawl_time"] = _serialize_datetime(doc.get("crawl_time"))
            results.append(doc)
        return results

    async def get_all_klines(
        self, start_date: str = None, end_date: str = None, limit: int = None
    ) -> List[Dict]:
        query = {}
        if start_date:
            query["date"] = {"$gte": start_date}
        if end_date:
            if "date" in query:
                query["date"]["$lte"] = end_date
            else:
                query["date"] = {"$lte": end_date}
        cursor = self._col("stock_kline").find(query).sort("date", DESCENDING)
        if limit:
            cursor = cursor.limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["crawl_time"] = _serialize_datetime(doc.get("crawl_time"))
            results.append(doc)
        return results

    # ==================== 盘后数据 ====================

    async def save(self, data: Any) -> Optional[str]:
        save_data = {"created_at": datetime.now(), "data": data}
        result = await self._col("after_market").update_one(
            {"date": save_data["created_at"]}, {"$set": save_data}, upsert=True
        )
        if result.upserted_id:
            return str(result.upserted_id)
        return str(result.modified_count)

    async def load(self, date_str: Optional[str] = None) -> Optional[Dict]:
        if not date_str:
            start_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_date = start_date + timedelta(days=1)
        else:
            start_date = datetime.strptime(date_str, "%Y-%m-%d")
            end_date = start_date + timedelta(days=1)
        doc = await self._col("after_market").find_one(
            {"created_at": {"$gte": start_date, "$lt": end_date}},
            sort=[("created_at", DESCENDING)],
        )
        if doc:
            return doc.get("data")
        return None

    async def get_by_date(self, date: str) -> Optional[Dict]:
        return await self._col("after_market").find_one({"date": date})

    async def get_all(self, limit: int = 50) -> List[Dict]:
        cursor = self._col("after_market").find().sort("date", DESCENDING).limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["created_at"] = _serialize_datetime(doc.get("created_at"))
            results.append(doc)
        return results

    async def delete(self, date: str) -> int:
        result = await self._col("after_market").delete_one({"date": date})
        return result.deleted_count

    # ==================== 策略插件 ====================

    async def save_strategy_plugin(self, plugin_data: Dict) -> str:
        plugin_data["created_at"] = datetime.now()
        plugin_data["updated_at"] = datetime.now()
        result = await self._col("strategy_plugins").insert_one(plugin_data)
        return str(result.inserted_id)

    async def get_strategy_plugin(self, plugin_id: str) -> Optional[Dict]:
        return await self._col("strategy_plugins").find_one(
            {"_id": ObjectId(plugin_id)}
        )

    async def get_all_strategy_plugins(self) -> List[Dict]:
        cursor = self._col("strategy_plugins").find()
        results = []
        async for doc in cursor:
            results.append(doc)
        return results

    async def delete_strategy_plugin(self, plugin_id: str) -> bool:
        result = await self._col("strategy_plugins").delete_one(
            {"_id": ObjectId(plugin_id)}
        )
        return result.deleted_count > 0

    # ==================== 资金流 ====================

    async def get_capital_flow(
        self, name: str, start_date: str = None, end_date: str = None, limit: int = 10
    ) -> List[Dict]:
        query = {"name": name}
        if start_date:
            query["date"] = {"$gte": start_date}
        if end_date:
            if "date" in query:
                query["date"]["$lte"] = end_date
            else:
                query["date"] = {"$lte": end_date}
        cursor = self._col("capital_flow").find(query).sort("date", DESCENDING).limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["crawl_time"] = _serialize_datetime(doc.get("crawl_time"))
            results.append(doc)
        return results

    # ==================== 新闻 ====================

    async def save_news_stocks(self, stocks: List[Dict]) -> Optional[str]:
        today = datetime.now().strftime("%Y-%m-%d")
        await self._col("news_stocks").delete_many({"date": today})
        save_data = {"date": today, "created_at": datetime.now(), "stocks": stocks}
        result = await self._col("news_stocks").insert_one(save_data)
        return str(result.inserted_id)

    async def get_news_stocks(self, date: str = None) -> List[Dict]:
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        doc = await self._col("news_stocks").find_one({"date": date})
        if doc:
            return doc.get("stocks", [])
        return []

    # ==================== 监控股票池 ====================

    async def save_monitor_stocks(self, stocks: List[Dict]) -> Optional[str]:
        await self._col("monitor_stocks").delete_many({})
        save_data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "created_at": datetime.now(),
            "stocks": stocks,
        }
        result = await self._col("monitor_stocks").insert_one(save_data)
        return str(result.inserted_id)

    async def get_monitor_stocks(self) -> List[Dict]:
        doc = await self._col("monitor_stocks").find_one(sort=[("created_at", DESCENDING)])
        if doc:
            return doc.get("stocks", [])
        return []

    async def remove_monitor_stock(self, stock_code: str) -> int:
        doc = await self._col("monitor_stocks").find_one(sort=[("created_at", DESCENDING)])
        if not doc:
            return 0
        stocks = doc.get("stocks", [])
        filtered = [s for s in stocks if s.get("code") != stock_code]
        if len(filtered) != len(stocks):
            save_data = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "created_at": datetime.now(),
                "stocks": filtered,
            }
            await self._col("monitor_stocks").delete_many({})
            await self._col("monitor_stocks").insert_one(save_data)
            return 1
        return 0

    # ==================== 看板 & 信号 ====================

    async def add_to_watch_list(self, symbol: str, source: str, ttl_days: int) -> None:
        expiry_date = datetime.now() + timedelta(days=ttl_days)
        await self._col("watch_list").update_one(
            {"symbol": symbol},
            {
                "$set": {
                    "symbol": symbol,
                    "source": source,
                    "expiry_date": expiry_date,
                    "updated_at": datetime.now(),
                }
            },
            upsert=True,
        )

    async def get_watch_list(self) -> List[str]:
        cursor = self._col("watch_list").find(
            {"expiry_date": {"$gte": datetime.now()}}
        )
        return [doc["symbol"] async for doc in cursor]

    async def save_market_signal(self, signal_data: Dict) -> str:
        signal_data["timestamp"] = signal_data.get("timestamp", datetime.now())
        result = await self._col("market_signals").insert_one(signal_data)
        return str(result.inserted_id)

    async def get_recent_signals(self, limit: int = 10) -> List[Dict]:
        cursor = self._col("market_signals").find().sort("timestamp", DESCENDING).limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["timestamp"] = _serialize_datetime(doc.get("timestamp"))
            results.append(doc)
        return results

    # ==================== 统计 ====================

    async def get_collection_stats(self) -> Dict[str, Any]:
        stats = {}
        for name in ["stock_kline", "after_market", "capital_flow", "users", "roles"]:
            try:
                count = await self._col(name).count_documents({})
                stats[name] = {"count": count}
            except Exception:
                stats[name] = {"count": 0}
        return stats


# --- 全局共享异步单例 ---

_async_storage: Optional[AsyncMongoStorage] = None


async def get_async_storage() -> AsyncMongoStorage:
    """获取全局共享的 AsyncMongoStorage 单例，API endpoints 使用"""
    global _async_storage
    if _async_storage is None:
        from app.core.config import settings
        _async_storage = AsyncMongoStorage(
            host=settings.mongodb_host,
            port=settings.mongodb_port,
            db_name=settings.mongodb_database,
            username=settings.mongodb_username,
            password=settings.mongodb_password,
        )
        _async_storage._is_shared = True
        await _async_storage.connect()
    return _async_storage
