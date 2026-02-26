from pymongo import MongoClient
from pymongo.collection import Collection
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
    
    def connect(self):
        """连接MongoDB"""
        try:
            logger.info(f"尝试连接MongoDB: {settings.mongodb_host}:{settings.mongodb_port},{settings.mongodb_username}, {settings.mongodb_password}")
            self.client = MongoClient(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                username=settings.mongodb_username,
                password=settings.mongodb_password
            )
            self.db = self.client[settings.mongodb_database]
            self.collection = self.db[settings.mongodb_collection]
            logger.info(f"MongoDB连接成功: {settings.mongodb_host}:{settings.mongodb_port}/{settings.mongodb_database}")
            return True
        except Exception as e:
            logger.error(f"MongoDB连接失败: {e}")
            return False
    
    def close(self):
        """关闭MongoDB连接"""
        if self.client:
            self.client.close()
            logger.info("MongoDB连接已关闭")
    
    def get_collection(self) -> Collection:
        """获取集合"""
        if self.collection is None:
            self.connect()
        return self.collection

# 创建全局MongoDB实例
mongodb = MongoDB()

# 初始化连接
mongodb.connect()
