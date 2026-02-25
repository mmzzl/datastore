from pymongo import MongoClient
import logging
from ..utils.config import load_config

# 创建logger实例
logger = logging.getLogger(__name__)

class MongoStorage:
    def __init__(self):
        config = load_config()
        self.client = MongoClient(
            host=config['mongodb']['host'],
            port=config['mongodb']['port'],
            username=config['mongodb']['username'],
            password=config['mongodb']['password'],
        )
        self.db = self.client[config['mongodb']['db']]
        self.collection = self.db[config['mongodb']['collection']]
        # 创建唯一索引，确保新闻code不重复
        self.collection.create_index('code', unique=True)
    
    def save_news(self, news_item):
        """保存新闻到mongodb"""
        try:
            result = self.collection.insert_one(news_item)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"保存新闻失败: {e}")
            return None
    
    def get_sort_end(self):
        """获取当前排序最大值"""
        try:
            result = self.collection.find_one(
                sort=[("showTime", 1)]
            )
            return result.get('realSort') if result else ''
        except Exception as e:
            logger.error(f"获取排序最大值失败: {e}")
            return None
    
    def query_sort_end(self, sort_end=''):
        """查询排序最大值"""
        try:
            result = self.collection.find_one(
                {'realSort': sort_end}
            )
            logger.info(f"查询排序最大值: {sort_end}, 结果: {result}")
            return True if result else False

        except Exception as e:
            logger.error(f"查询排序最大值失败: {e}")
            return None
    
    def check_duplicate(self, news_code):
        """检查新闻是否已存在"""
        try:
            # 打印集合名称和数据库名称，确认连接是否正确
            logger.info(f"检查重复: 数据库={self.db.name}, 集合={self.collection.name}, code={news_code}")
            # 尝试查询
            result = self.collection.find_one({'code': news_code})
            logger.info(f"检查重复: {news_code}, 结果: {result is not None}, 详细结果: {result}")
            # 尝试计数，确认集合中是否有数据
            count = self.collection.count_documents({})
            logger.info(f"集合中总文档数: {count}")
            return result is not None
        except Exception as e:
            logger.error(f"检查重复失败: {e}")
            return False
    
    def close(self):
        """关闭mongodb连接"""
        if self.client:
            self.client.close()
