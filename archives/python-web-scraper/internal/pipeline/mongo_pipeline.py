from scrapy.exceptions import DropItem
import logging
from ..storage.mongo_storage import MongoStorage

# 创建logger实例
logger = logging.getLogger(__name__)

class MongoPipeline:
    def __init__(self):
        self.storage = MongoStorage()
    
    def process_item(self, item, spider):
        """处理采集到的新闻项"""
        # 检查是否重复
        if self.storage.check_duplicate(item.get('code')):
            raise DropItem(f"重复的新闻: {item.get('code')}")
        
        # 保存到mongodb
        logger.info(f"保存新闻到mongodb: {item.get('code')}")
        self.storage.save_news(dict(item))
        return item
    
    def close_spider(self, spider):
        """关闭爬虫时关闭存储连接"""
        self.storage.close()
