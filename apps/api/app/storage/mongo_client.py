from pymongo import MongoClient
from pymongo.errors import PyMongoError
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import logging

logger = logging.getLogger(__name__)


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
        # 新增 holdings 集合
        self.holdings_collection = None

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
            # holdings 集合
            self.holdings_collection = self.db["holdings"]
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
        # Always create a new dictionary to avoid modifying the input
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
        """
        根据日期字符串加载数据

        参数:
            date_str: 日期字符串，格式为 YYYY-MM-DD

        返回:
            数据字典，如果未找到返回None
        """
        if self.collection is None:
            self.connect()

        try:
            # 查询指定日期的数据
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

    def get_all(self, limit: int = 50) -> List[Dict]:
        if self.collection is None:
            self.connect()

        try:
            cursor = self.collection.find().sort("date", -1).limit(limit)
            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                if doc.get("created_at"):
                    doc["created_at"] = doc["created_at"].isoformat()
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
        """根据股票名称获取K线数据"""
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
                if doc.get("crawl_time"):
                    doc["crawl_time"] = doc["crawl_time"].isoformat()
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
                if doc.get("crawl_time"):
                    doc["crawl_time"] = doc["crawl_time"].isoformat()
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
                if doc.get("crawl_time"):
                    doc["crawl_time"] = doc["crawl_time"].isoformat()
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
                if doc.get("crawl_time"):
                    doc["crawl_time"] = doc["crawl_time"].isoformat()
                results.append(doc)
            return results
        except PyMongoError as e:
            logger.error(f"MongoDB kline query failed: {e}")
            raise

    def get_all_klines(
        self, start_date: str = None, end_date: str = None, limit: int = None
    ) -> List[Dict]:
        """获取所有股票的 K 线数据"""
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
                if doc.get("crawl_time"):
                    doc["crawl_time"] = doc["crawl_time"].isoformat()
                results.append(doc)
            return results
        except PyMongoError as e:
            logger.error(f"MongoDB kline query failed: {e}")
            raise

    def get_capital_flow(
        self, name: str, start_date: str = None, end_date: str = None, limit: int = 10
    ) -> List[Dict]:
        """获取资金流向数据"""
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
                if doc.get("crawl_time"):
                    doc["crawl_time"] = doc["crawl_time"].isoformat()
                results.append(doc)
            return results
        except PyMongoError as e:
            logger.error(f"MongoDB capital flow query failed: {e}")
            raise

    def save_news_stocks(self, stocks: List[Dict]) -> Optional[str]:
        """
        保存新闻分析后的股票到单独的collection

        参数:
            stocks: 股票列表，每个股票包含code、name等信息

        返回:
            保存结果的ID或修改计数
        """
        if self.news_stocks_collection is None:
            self.connect()

        try:
            # 先删除当天的记录
            today = datetime.now().strftime("%Y-%m-%d")
            self.news_stocks_collection.delete_many({"date": today})

            # 保存新记录
            save_data = {"date": today, "created_at": datetime.now(), "stocks": stocks}

            result = self.news_stocks_collection.insert_one(save_data)
            logger.info(f"保存新闻分析股票成功，共 {len(stocks)} 只股票")
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"保存新闻分析股票失败: {e}")
            raise

    def get_news_stocks(self, date: str = None) -> List[Dict]:
        """
        获取新闻分析后的股票

        参数:
            date: 日期字符串，格式为 YYYY-MM-DD，默认今天

        返回:
            股票列表
        """
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
        """
        保存监控股票池

        参数:
            stocks: 股票列表，每个股票包含code、name等信息

        返回:
            保存结果的ID
        """
        if self.monitor_stocks_collection is None:
            self.connect()

        try:
            # 先删除所有记录
            self.monitor_stocks_collection.delete_many({})

            # 保存新记录
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
        """
        获取监控股票池

        返回:
            股票列表
        """
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
        """
        从监控股票池中移除股票

        参数:
            stock_code: 股票代码

        返回:
            操作结果
        """
        if self.monitor_stocks_collection is None:
            self.connect()

        try:
            # 获取当前监控股票池
            doc = self.monitor_stocks_collection.find_one(sort=[("created_at", -1)])
            if not doc:
                return 0

            # 过滤掉要移除的股票
            stocks = doc.get("stocks", [])
            filtered_stocks = [
                stock for stock in stocks if stock.get("code") != stock_code
            ]

            # 保存更新后的股票池
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
