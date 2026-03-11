from pymongo import MongoClient
import logging
from ..utils.config import load_config
from datetime import datetime

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
        self.kline_collection = self.db[config['mongodb'].get('kline_collection', 'stock_kline')]
        
        self.collection.create_index('code', unique=True)
        self.kline_collection.create_index([('code', 1), ('date', 1)], unique=True)
    
    def save_news(self, news_item):
        """保存新闻到mongodb"""
        try:
            result = self.collection.insert_one(news_item)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"保存新闻失败: {e}")
            return None
    
    def save_kline(self, code, klines, name=''):
        """保存K线数据到mongodb（去重）"""
        inserted_count = 0
        skipped_count = 0
        for kline in klines:
            parts = kline.split(',')
            if len(parts) >= 8:
                date = parts[0]
                try:
                    kline_data = {
                        'code': code,
                        'date': date,
                        'open': float(parts[1]) if parts[1] and parts[1] != '-' else None,
                        'close': float(parts[2]) if parts[2] and parts[2] != '-' else None,
                        'high': float(parts[3]) if parts[3] and parts[3] != '-' else None,
                        'low': float(parts[4]) if parts[4] and parts[4] != '-' else None,
                        'volume': float(parts[5]) if parts[5] and parts[5] != '-' else None,
                        'amount': float(parts[6]) if parts[6] and parts[6] != '-' else None,
                        'amplitude': float(parts[7]) if parts[7] and parts[7] != '-' else None,
                        'pct_chg': float(parts[8]) if len(parts) > 8 and parts[8] and parts[8] != '-' else None,
                        'turnover': float(parts[9]) if len(parts) > 9 and parts[9] and parts[9] != '-' else None,
                        'name': name,
                        'crawl_time': datetime.now()
                        
                    }
                    self.kline_collection.update_one(
                        {'code': code, 'date': date},
                        {'$set': kline_data},
                        upsert=True
                    )
                    inserted_count += 1
                except Exception as e:
                    logger.error(f"保存K线数据失败: {code} - {date}: {e}")
                    skipped_count += 1
        logger.info(f"K线数据保存完成: {code}, 新增: {inserted_count}, 跳过: {skipped_count}")
        return inserted_count, skipped_count
    
    def get_latest_kline_date(self, code):
        """获取指定股票最新K线日期"""
        try:
            result = self.kline_collection.find_one(
                {'code': code},
                sort=[('date', -1)]
            )
            return result.get('date') if result else None
        except Exception as e:
            logger.error(f"获取最新K线日期失败: {e}")
            return None
    
    def get_kline(self, code, start_date=None, end_date=None):
        """获取K线数据"""
        try:
            query = {'code': code}
            if start_date:
                query['date'] = {'$gte': start_date}
            if end_date:
                if 'date' in query:
                    query['date']['$lte'] = end_date
                else:
                    query['date'] = {'$lte': end_date}
            
            cursor = self.kline_collection.find(query).sort('date', 1)
            return list(cursor)
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            return []
    
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
            logger.info(f"检查重复: 数据库={self.db.name}, 集合={self.collection.name}, code={news_code}")
            result = self.collection.find_one({'code': news_code})
            logger.info(f"检查重复: {news_code}, 结果: {result is not None}, 详细结果: {result}")
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
