from pymongo import MongoClient
from pymongo.errors import PyMongoError
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from bson.objectid import ObjectId
import logging

logger = logging.getLogger(__name__)


def _serialize_datetime(value: Any) -> Optional[str]:
    """Serialize a datetime object to ISO format string."""
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return None


class MongoStorage:
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
        self.client = None
        self.db = None
        self.collection = None
        self.kline_collection = None
        self.capital_flow_collection = None
        self.news_stocks_collection = None
        self.monitor_stocks_collection = None
        self.holdings_collection = None
        self.settings_collection = None
        self.strategy_plugins_collection = None
        self.users_collection = None
        self.roles_collection = None

    def connect(self):
        try:
            if self.username and self.password:
                encoded_password = quote_plus(self.password)
                connection_string = f"mongodb://{self.username}:{encoded_password}@{self.host}:{self.port}"
                self.client = MongoClient(connection_string)
            else:
                self.client = MongoClient(self.host, self.port)
            self.db = self.client[self.db_name]
            self.collection = self.db["after_market"]
            self.kline_collection = self.db["stock_kline"]
            self.capital_flow_collection = self.db["capital_flow"]
            self.news_stocks_collection = self.db["news_stocks"]
            self.monitor_stocks_collection = self.db["monitor_stocks"]
            self.holdings_collection = self.db["holdings"]
            self.settings_collection = self.db["settings"]
            self.strategy_plugins_collection = self.db["strategy_plugins"]
            self.users_collection = self.db["users"]
            self.roles_collection = self.db["roles"]
            self.watch_list_collection = self.db["watch_list"]
            self.market_signals_collection = self.db["market_signals"]
            self._create_user_indexes()
            self._create_role_indexes()
            self._create_signal_indexes()
            self.client.admin.command("ping")
            logger.info(f"MongoDB connected: {self.host}:{self.port}/{self.db_name}")
        except PyMongoError as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise

    def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    def save(self, data: Any) -> Optional[str]:
        if self.collection is None:
            self.connect()
        save_data = {}
        save_data["created_at"] = datetime.now()
        save_data["data"] = data

        try:
            result = self.collection.update_one(
                {"date": save_data.get("created_at")}, {"$set": save_data}, upsert=True
            )
            if result.upserted_id:
                return str(result.upserted_id)
            return str(result.modified_count)
        except PyMongoError as e:
            logger.error(f"MongoDB save failed: {e}")
            raise

    def load(self, date_str: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if self.collection is None:
            self.connect()

        try:
            if not date_str:
                start_date = datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                end_date = start_date + timedelta(days=1)
            else:
                start_date = datetime.strptime(date_str, "%Y-%m-%d")
                end_date = start_date + timedelta(days=1)

            doc = self.collection.find_one(
                {"created_at": {"$gte": start_date, "$lt": end_date}},
                sort=[("created_at", -1)],
            )

            if doc:
                return doc.get("data")
            return None
        except PyMongoError as e:
            logger.error(f"MongoDB load failed: {e}")
            raise

    def get_by_date(self, date: str) -> Optional[Dict]:
        if self.collection is None:
            self.connect()

        try:
            return self.collection.find_one({"date": date})
        except PyMongoError as e:
            logger.error(f"MongoDB query failed: {e}")
            raise

    def save_strategy_plugin(self, plugin_data: Dict[str, Any]) -> str:
        if self.strategy_plugins_collection is None:
            self.connect()

        try:
            plugin_data["created_at"] = datetime.now()
            plugin_data["updated_at"] = datetime.now()

            result = self.strategy_plugins_collection.insert_one(plugin_data)
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Save strategy plugin failed: {e}")
            raise

    def get_strategy_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        if self.strategy_plugins_collection is None:
            self.connect()

        try:
            return self.strategy_plugins_collection.find_one(
                {"_id": ObjectId(plugin_id)}
            )
        except PyMongoError as e:
            logger.error(f"Get strategy plugin failed: {e}")
            raise

    def get_all_strategy_plugins(self) -> List[Dict[str, Any]]:
        if self.strategy_plugins_collection is None:
            self.connect()

        try:
            return list(self.strategy_plugins_collection.find())
        except PyMongoError as e:
            logger.error(f"Get all strategy plugins failed: {e}")
            raise

    def delete_strategy_plugin(self, plugin_id: str) -> bool:
        if self.strategy_plugins_collection is None:
            self.connect()

        try:
            result = self.strategy_plugins_collection.delete_one(
                {"_id": ObjectId(plugin_id)}
            )
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Delete strategy plugin failed: {e}")
            raise

    def get_all(self, limit: int = 50) -> List[Dict]:
        if self.collection is None:
            self.connect()

        try:
            cursor = self.collection.find().sort("date", -1).limit(limit)
            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                doc["created_at"] = _serialize_datetime(doc.get("created_at"))
                results.append(doc)
            return results
        except PyMongoError as e:
            logger.error(f"MongoDB query failed: {e}")
            raise

    def delete(self, date: str) -> int:
        if self.collection is None:
            self.connect()

        try:
            result = self.collection.delete_one({"date": date})
            return result.deleted_count
        except PyMongoError as e:
            logger.error(f"MongoDB delete failed: {e}")
            raise

    def get_kline_by_name(
        self, name: str, start_date: str = None, end_date: str = None, limit: int = 100
    ) -> List[Dict]:
        if self.kline_collection is None:
            self.connect()

        try:
            query = {"name": name}
            if start_date:
                query["date"] = {"$gte": start_date}
            if end_date:
                if "date" in query:
                    query["date"]["$lte"] = end_date
                else:
                    query["date"] = {"$lte": end_date}

            cursor = self.kline_collection.find(query).sort("date", -1).limit(limit)
            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                doc["crawl_time"] = _serialize_datetime(doc.get("crawl_time"))
                results.append(doc)
            return results
        except PyMongoError as e:
            logger.error(f"MongoDB kline by name query failed: {e}")
            raise

    def get_kline(
        self, code: str, start_date: str = None, end_date: str = None, limit: int = 100
    ) -> List[Dict]:
        if self.kline_collection is None:
            self.connect()

        try:
            query = {"code": code}
            if start_date:
                query["date"] = {"$gte": start_date}
            if end_date:
                if "date" in query:
                    query["date"]["$lte"] = end_date
                else:
                    query["date"] = {"$lte": end_date}

            cursor = self.kline_collection.find(query).sort("date", -1).limit(limit)
            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                doc["crawl_time"] = _serialize_datetime(doc.get("crawl_time"))
                results.append(doc)
            return results
        except PyMongoError as e:
            logger.error(f"MongoDB kline query failed: {e}")
            raise

    def get_kline_by_date(self, code: str, date: str) -> Optional[Dict]:
        if self.kline_collection is None:
            self.connect()

        try:
            doc = self.kline_collection.find_one({"code": code, "date": date})
            if doc:
                doc["_id"] = str(doc["_id"])
                doc["crawl_time"] = _serialize_datetime(doc.get("crawl_time"))
            return doc
        except PyMongoError as e:
            logger.error(f"MongoDB kline query failed: {e}")
            raise

    def get_all_kline_by_date(
        self, date: str, limit: int = 5000, deduplicate: bool = True
    ) -> List[Dict]:
        if self.kline_collection is None:
            self.connect()

        try:
            if deduplicate:
                pipeline = [
                    {"$match": {"date": date}},
                    {"$sort": {"crawl_time": -1}},
                    {"$group": {"_id": "$code", "doc": {"$first": "$$ROOT"}}},
                    {"$replaceRoot": {"newRoot": "$doc"}},
                    {"$limit": limit},
                ]
                cursor = self.kline_collection.aggregate(pipeline)
            else:
                cursor = self.kline_collection.find({"date": date}).limit(limit)

            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                doc["crawl_time"] = _serialize_datetime(doc.get("crawl_time"))
                results.append(doc)
            return results
        except PyMongoError as e:
            logger.error(f"MongoDB kline query failed: {e}")
            raise

    def get_all_klines(
        self, start_date: str = None, end_date: str = None, limit: int = None
    ) -> List[Dict]:
        if self.kline_collection is None:
            self.connect()

        try:
            query = {}
            if start_date:
                query["date"] = {"$gte": start_date}
            if end_date:
                if "date" in query:
                    query["date"]["$lte"] = end_date
                else:
                    query["date"] = {"$lte": end_date}

            cursor = self.kline_collection.find(query).sort("date", -1)
            if limit:
                cursor = cursor.limit(limit)

            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                doc["crawl_time"] = _serialize_datetime(doc.get("crawl_time"))
                results.append(doc)
            return results
        except PyMongoError as e:
            logger.error(f"MongoDB kline query failed: {e}")
            raise

    def get_capital_flow(
        self, name: str, start_date: str = None, end_date: str = None, limit: int = 10
    ) -> List[Dict]:
        if self.capital_flow_collection is None:
            self.connect()

        try:
            query = {"name": name}
            if start_date:
                query["date"] = {"$gte": start_date}
            if end_date:
                if "date" in query:
                    query["date"]["$lte"] = end_date
                else:
                    query["date"] = {"$lte": end_date}

            cursor = (
                self.capital_flow_collection.find(query).sort("date", -1).limit(limit)
            )
            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                doc["crawl_time"] = _serialize_datetime(doc.get("crawl_time"))
                results.append(doc)
            return results
        except PyMongoError as e:
            logger.error(f"MongoDB capital flow query failed: {e}")
            raise

    def save_news_stocks(self, stocks: List[Dict]) -> Optional[str]:
        if self.news_stocks_collection is None:
            self.connect()

        try:
            today = datetime.now().strftime("%Y-%m-%d")
            self.news_stocks_collection.delete_many({"date": today})

            save_data = {"date": today, "created_at": datetime.now(), "stocks": stocks}

            result = self.news_stocks_collection.insert_one(save_data)
            logger.info(f"保存新闻分析股票成功，共 {len(stocks)} 只股票")
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"保存新闻分析股票失败: {e}")
            raise

    def get_news_stocks(self, date: str = None) -> List[Dict]:
        if self.news_stocks_collection is None:
            self.connect()

        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")

            doc = self.news_stocks_collection.find_one({"date": date})
            if doc:
                return doc.get("stocks", [])
            return []
        except PyMongoError as e:
            logger.error(f"获取新闻分析股票失败: {e}")
            raise

    def save_monitor_stocks(self, stocks: List[Dict]) -> Optional[str]:
        if self.monitor_stocks_collection is None:
            self.connect()

        try:
            self.monitor_stocks_collection.delete_many({})

            save_data = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "created_at": datetime.now(),
                "stocks": stocks,
            }

            result = self.monitor_stocks_collection.insert_one(save_data)
            logger.info(f"保存监控股票池成功，共 {len(stocks)} 只股票")
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"保存监控股票池失败: {e}")
            raise

    def get_monitor_stocks(self) -> List[Dict]:
        if self.monitor_stocks_collection is None:
            self.connect()

        try:
            doc = self.monitor_stocks_collection.find_one(sort=[("created_at", -1)])
            if doc:
                return doc.get("stocks", [])
            return []
        except PyMongoError as e:
            logger.error(f"获取监控股票池失败: {e}")
            raise

    def remove_monitor_stock(self, stock_code: str) -> int:
        if self.monitor_stocks_collection is None:
            self.connect()

        try:
            doc = self.monitor_stocks_collection.find_one(sort=[("created_at", -1)])
            if not doc:
                return 0

            stocks = doc.get("stocks", [])
            filtered_stocks = [
                stock for stock in stocks if stock.get("code") != stock_code
            ]

            if len(filtered_stocks) != len(stocks):
                save_data = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "created_at": datetime.now(),
                    "stocks": filtered_stocks,
                }
                self.monitor_stocks_collection.delete_many({})
                self.monitor_stocks_collection.insert_one(save_data)
                logger.info(f"从监控股票池移除股票: {stock_code}")
                return 1
            return 0
        except PyMongoError as e:
            logger.error(f"移除监控股票失败: {e}")
            raise

    def _create_user_indexes(self):
        if self.users_collection is None:
            return
        try:
            self.users_collection.create_index("username", unique=True)
            self.users_collection.create_index("email", unique=True, sparse=True)
            self.users_collection.create_index("role_id")
            self.users_collection.create_index("status")
            logger.info("Users collection indexes created")
        except PyMongoError as e:
            logger.error(f"Create users indexes failed: {e}")

    def _create_role_indexes(self):
        if self.roles_collection is None:
            return
        try:
            self.roles_collection.create_index("role_id", unique=True)
            logger.info("Roles collection indexes created")
        except PyMongoError as e:
            logger.error(f"Create roles indexes failed: {e}")
            raise

    def _create_signal_indexes(self):
        if self.watch_list_collection is None or self.market_signals_collection is None:
            return
        try:
            self.watch_list_collection.create_index("symbol", unique=True)
            self.market_signals_collection.create_index([("symbol", 1), ("timestamp", -1)])
            logger.info("Signal and Watchlist indexes created")
        except PyMongoError as e:
            logger.error(f"Create signal indexes failed: {e}")
            raise


    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        if self.users_collection is None:
            self.connect()

        try:
            return self.users_collection.find_one({"username": username})
        except PyMongoError as e:
            logger.error(f"Get user by username failed: {e}")
            raise

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        if self.users_collection is None:
            self.connect()

        try:
            if ObjectId.is_valid(user_id):
                return self.users_collection.find_one({"_id": ObjectId(user_id)})
            return self.users_collection.find_one({"username": user_id})
        except PyMongoError as e:
            logger.error(f"Get user by id failed: {e}")
            raise

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        if self.users_collection is None:
            self.connect()

        try:
            cursor = self.users_collection.find().skip(skip).limit(limit)
            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                doc["created_at"] = _serialize_datetime(doc.get("created_at"))
                doc["updated_at"] = _serialize_datetime(doc.get("updated_at"))
                doc["last_login"] = _serialize_datetime(doc.get("last_login"))
                results.append(doc)
            return results
        except PyMongoError as e:
            logger.error(f"Get all users failed: {e}")
            raise

    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        if self.users_collection is None:
            self.connect()

        try:
            update_data["updated_at"] = datetime.now()
            if ObjectId.is_valid(user_id):
                result = self.users_collection.update_one(
                    {"_id": ObjectId(user_id)}, {"$set": update_data}
                )
            else:
                result = self.users_collection.update_one(
                    {"username": user_id}, {"$set": update_data}
                )
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Update user failed: {e}")
            raise

    def delete_user(self, user_id: str) -> bool:
        if self.users_collection is None:
            self.connect()

        try:
            if ObjectId.is_valid(user_id):
                result = self.users_collection.delete_one({"_id": ObjectId(user_id)})
            else:
                result = self.users_collection.delete_one({"username": user_id})
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Delete user failed: {e}")
            raise

    def update_user_login(self, user_id: str) -> bool:
        if self.users_collection is None:
            self.connect()

        try:
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "last_login": datetime.now(),
                        "updated_at": datetime.now(),
                    },
                    "$inc": {"login_count": 1},
                },
            )
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Update user login failed: {e}")
            raise

    def save_role(self, role_data: Dict[str, Any]) -> str:
        if self.roles_collection is None:
            self.connect()

        try:
            role_data["created_at"] = datetime.now()
            role_data["updated_at"] = datetime.now()
            result = self.roles_collection.insert_one(role_data)
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Save role failed: {e}")
            raise

    def get_role_by_id(self, role_id: str) -> Optional[Dict[str, Any]]:
        if self.roles_collection is None:
            self.connect()

        try:
            return self.roles_collection.find_one({"role_id": role_id})
        except PyMongoError as e:
            logger.error(f"Get role by id failed: {e}")
            raise

    def get_all_roles(self) -> List[Dict[str, Any]]:
        if self.roles_collection is None:
            self.connect()

        try:
            cursor = self.roles_collection.find()
            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                doc["created_at"] = _serialize_datetime(doc.get("created_at"))
                doc["updated_at"] = _serialize_datetime(doc.get("updated_at"))
                results.append(doc)
            return results
        except PyMongoError as e:
            logger.error(f"Get all roles failed: {e}")
            raise

    def update_role(self, role_id: str, update_data: Dict[str, Any]) -> bool:
        if self.roles_collection is None:
            self.connect()

        try:
            update_data["updated_at"] = datetime.now()
            result = self.roles_collection.update_one(
                {"role_id": role_id}, {"$set": update_data}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Update role failed: {e}")
            raise

    def delete_role(self, role_id: str) -> bool:
        if self.roles_collection is None:
            self.connect()
        try:
            result = self.roles_collection.delete_one({"role_id": role_id})
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Delete role failed: {e}")
            raise

    def add_to_watch_list(self, symbol: str, source: str, ttl_days: int) -> None:
        if self.watch_list_collection is None:
            self.connect()
        expiry_date = datetime.now() + timedelta(days=ttl_days)
        self.watch_list_collection.update_one(
            {"symbol": symbol},
            {"$set": {"symbol": symbol, "source": source, "expiry_date": expiry_date, "updated_at": datetime.now()}},
            upsert=True
        )

    def get_watch_list(self) -> List[str]:
        if self.watch_list_collection is None:
            self.connect()
        # Filter out expired stocks
        cursor = self.watch_list_collection.find({"expiry_date": {"$gte": datetime.now()}})
        return [doc["symbol"] for doc in cursor]

    def save_market_signal(self, signal_data: Dict[str, Any]) -> str:
        if self.market_signals_collection is None:
            self.connect()
        signal_data["timestamp"] = signal_data.get("timestamp", datetime.now())
        result = self.market_signals_collection.insert_one(signal_data)
        return str(result.inserted_id)

    def get_recent_signals(self, limit: int = 10) -> List[Dict]:
        if self.market_signals_collection is None:
            self.connect()
        cursor = self.market_signals_collection.find().sort("timestamp", -1).limit(limit)
        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["timestamp"] = _serialize_datetime(doc.get("timestamp"))
            results.append(doc)
        return results

