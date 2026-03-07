from pymongo import MongoClient
from pymongo.errors import PyMongoError
from typing import Optional, List, Dict, Any
from datetime import datetime
from urllib.parse import quote_plus
import logging

logger = logging.getLogger(__name__)


class MongoStorage:
    def __init__(self, host: str, port: int, db_name: str, username: str = None, password: str = None):
        self.host = host
        self.port = port
        self.db_name = db_name
        self.username = username
        self.password = password
        self.client = None
        self.db = None
        self.collection = None
        self.kline_collection = None

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
            self.client.admin.command('ping')
            logger.info(f"MongoDB connected: {self.host}:{self.port}/{self.db_name}")
        except PyMongoError as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise

    def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    def save(self, data: Dict[str, Any]) -> Optional[str]:
        if self.collection is None:
            self.connect()
        
        data['created_at'] = datetime.now()
        
        try:
            result = self.collection.update_one(
                {"date": data.get("date")},
                {"$set": data},
                upsert=True
            )
            if result.upserted_id:
                return str(result.upserted_id)
            return str(result.modified_count)
        except PyMongoError as e:
            logger.error(f"MongoDB save failed: {e}")
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
                doc['_id'] = str(doc['_id'])
                if doc.get('created_at'):
                    doc['created_at'] = doc['created_at'].isoformat()
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

    def get_kline(self, code: str, start_date: str = None, end_date: str = None, limit: int = 100) -> List[Dict]:
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
                doc['_id'] = str(doc['_id'])
                if doc.get('crawl_time'):
                    doc['crawl_time'] = doc['crawl_time'].isoformat()
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
                doc['_id'] = str(doc['_id'])
                if doc.get('crawl_time'):
                    doc['crawl_time'] = doc['crawl_time'].isoformat()
            return doc
        except PyMongoError as e:
            logger.error(f"MongoDB kline query failed: {e}")
            raise

    def get_all_kline_by_date(self, date: str, limit: int = 5000) -> List[Dict]:
        if self.kline_collection is None:
            self.connect()
        
        try:
            cursor = self.kline_collection.find({"date": date}).limit(limit)
            results = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                if doc.get('crawl_time'):
                    doc['crawl_time'] = doc['crawl_time'].isoformat()
                results.append(doc)
            return results
        except PyMongoError as e:
            logger.error(f"MongoDB kline query failed: {e}")
            raise

    def get_all_klines(self, start_date: str = None, end_date: str = None, limit: int = None) -> List[Dict]:
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
                doc['_id'] = str(doc['_id'])
                if doc.get('crawl_time'):
                    doc['crawl_time'] = doc['crawl_time'].isoformat()
                results.append(doc)
            return results
        except PyMongoError as e:
            logger.error(f"MongoDB kline query failed: {e}")
            raise
