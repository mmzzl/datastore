import scrapy
import json
import logging
import random
import time
from datetime import datetime, timedelta
from urllib.parse import urlencode
from ..utils.config import load_config
from ..storage.mongo_storage import MongoStorage
from .baostock_stock_codes import load_stock_codes

logger = logging.getLogger(__name__)


class EastMoneyKlineSpider(scrapy.Spider):
    name = 'eastmoney_kline'
    
    def __init__(self, *args, **kwargs):
        super(EastMoneyKlineSpider, self).__init__(*args, **kwargs)
        self.config = load_config()
        self.base_url = self.config['api']['kline_url']
        self.kline_params = self.config['api']['kline_params']
        self.storage = MongoStorage()
        self.today = datetime.now().strftime('%Y%m%d')
        self.processed_count = 0
        self.skip_count = 0
        self.error_count = 0
        kline_config = self.config.get('kline_spider', {})
        self.batch_size = kline_config.get('batch_size', 50)
        self.batch_delay = kline_config.get('batch_delay', 10)
        self.default_days = kline_config.get('default_days', 60)
        
        # 获取 User-Agent 列表
        spider_config = self.config.get('spider', {})
        self.user_agents = spider_config.get('user_agents', [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ])
        
    def start_requests(self):
        df = load_stock_codes()
        if df.empty:
            logger.error("没有股票代码，退出")
            return
        
        logger.info(f"开始处理 {len(df)} 只股票，每批 {self.batch_size} 只")
        
        total = len(df)
        for i in range(0, total, self.batch_size):
            batch = df.iloc[i:min(i+self.batch_size, total)]
            logger.info(f"处理第 {i//self.batch_size + 1} 批股票 ({i+1}-{min(i+self.batch_size, total)})")
            for _, row in batch.iterrows():
                code = str(row['code'])
                stock_code = code.split('.')[1]
                market = 1 if code.startswith('sh') else 0
                
                secid = f"{market}.{stock_code}"
                
                latest_date = self.storage.get_latest_kline_date(secid)
                
                if latest_date:
                    if latest_date >= self.today:
                        logger.info(f"跳过 {secid}: 已采集到最新日期 {latest_date}")
                        self.skip_count += 1
                        continue
                    beg = latest_date
                    end_date = self.today
                else:
                    # 没有历史数据时，只获取默认天数前的数据
                    beg = (datetime.now() - timedelta(days=self.default_days)).strftime('%Y%m%d')
                    end_date = self.today
                params = {
                    'secid': secid,
                    'klt': self.kline_params['klt'],
                    'fqt': self.kline_params['fqt'],
                    'lmt': self.kline_params['lmt'],
                    'end': end_date,
                    'beg': beg,
                    'fields1': self.kline_params['fields1'],
                    'fields2': self.kline_params['fields2']
                }
                
                url = f"{self.base_url}?{urlencode(params)}"
                
                # 随机选择 User-Agent
                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Host': 'push2his.eastmoney.com',
                    'Referer': f'https://quote.eastmoney.com/{code.replace(".", "")}.html',
                }
                
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_kline,
                    meta={'secid': secid, 'stock_code': stock_code},
                    headers=headers,
                    dont_filter=True,
                    errback=self.errback
                )
            time.sleep(0.5)
            # 每批处理完后延迟1秒，避免请求过快
    def errback(self, failure):
        secid = failure.request.meta.get('secid', 'unknown')
        self.error_count += 1
        
        error_type = failure.type.__name__
        error_value = str(failure.value)
        logger.warning(f"请求失败 {secid}: {error_type} - {error_value}")
    
    def parse_kline(self, response):
        secid = response.meta['secid']
        stock_code = response.meta['stock_code']
        
        try:
            data = json.loads(response.text)
            
            if data.get('rc') == 0 and 'data' in data:
                kline_data = data['data']
                klines = kline_data.get('klines', [])
                name = kline_data.get('name', '')
                if klines:
                    inserted, skipped = self.storage.save_kline(secid, klines, name)
                    self.processed_count += 1
                    logger.info(f"成功采集 {secid}: {len(klines)} 条数据")
                else:
                    logger.debug(f"无K线数据 {secid}")
                    self.skip_count += 1
            else:
                logger.warning(f"API返回错误 {secid}: {data.get('msg', '')}")
                self.error_count += 1
                
        except Exception as e:
            logger.error(f"解析K线数据失败 {secid}: {e}")
            self.error_count += 1
        
        if (self.processed_count + self.skip_count + self.error_count) % 50 == 0:
            logger.info(f"进度: 已处理 {self.processed_count} 只, 跳过 {self.skip_count} 只, 错误 {self.error_count} 只")
    
    def closed(self, reason):
        logger.info(f"爬虫关闭: {reason}, 共处理 {self.processed_count} 只股票, 跳过 {self.skip_count} 只, 错误 {self.error_count} 只")
        self.storage.close()

