import scrapy
import logging
import requests
import re
import time
from datetime import datetime
from ..utils.config import load_config
from ..storage.mongo_storage import MongoStorage

logger = logging.getLogger(__name__)


class EastMoneyCapitalFlowSpider(scrapy.Spider):
    name = 'eastmoney_capital_flow'
    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'RETRY_TIMES': 3,
        'DOWNLOAD_TIMEOUT': 60,
    }
    
    def __init__(self, *args, **kwargs):
        super(EastMoneyCapitalFlowSpider, self).__init__(*args, **kwargs)
        self.config = load_config()
        self.storage = MongoStorage()
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.processed_count = 0
        self.error_count = 0
    
    def start_requests(self):
        """开始请求资金流向数据"""
        logger.info(f"开始获取资金流向数据，日期: {self.today}")
        
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        headers = {
            'Host': 'push2.eastmoney.com',
            'Referer': 'https://data.eastmoney.com/zjlx/detail.html',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 先获取总数
        params = {
            'cb': f'jQuery112305365419743416425_{int(time.time() * 1000)}',
            'fid': 'f62',
            'po': '1',
            'pz': '20',
            'pn': '1',
            'np': '1',
            'fltt': '2',
            'invt': '2',
            'ut': '8dec03ba335b81bf4ebdf7b29ec27d15',
            'fs': 'm:0+t:6+f:!2,m:0+t:13+f:!2,m:0+t:80+f:!2,m:1+t:2+f:!2,m:1+t:23+f:!2,m:0+t:7+f:!2,m:1+t:3+f:!2',
            'fields': 'f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124,f1,f13'
        }
        
        # 手动构建带参数的 URL
        import urllib.parse
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        
        # 使用 requests 获取总数
        try:
            response = requests.get(full_url, headers=headers, timeout=30)
            text = response.text
            # 移除 jQuery 回调函数
            text = re.sub(r'^jQuery\d+_\d+\(', '', text)
            text = re.sub(r'\);$', '', text)
            
            import json
            data = json.loads(text)
            
            if data.get('rc') != 0:
                logger.error(f"获取资金流向数据失败: {data}")
                return
            
            total = data.get('data', {}).get('total', 0)
            logger.info(f"资金流向数据总数: {total}")
            
            if total == 0:
                logger.info("没有资金流向数据")
                return
            
            # 计算需要多少页
            page_size = 100
            total_pages = (total + page_size - 1) // page_size
            logger.info(f"需要获取 {total_pages} 页数据")
            
            # 用 for 循环获取所有页的数据
            for page in range(1, total_pages + 1):
                callback_name = f'jQuery112305365419743416425_{int(time.time() * 1000)}'
                params = {
                    'cb': callback_name,
                    'fid': 'f62',
                    'po': '1',
                    'pz': str(page_size),  # pz 表示每页的记录数（limit）
                    'pn': str(page),  # pn 表示页数
                    'np': '1',
                    'fltt': '2',
                    'invt': '2',
                    'ut': '8dec03ba335b81bf4ebdf7b29ec27d15',
                    'fs': 'm:0+t:6+f:!2,m:0+t:13+f:!2,m:0+t:80+f:!2,m:1+t:2+f:!2,m:1+t:23+f:!2,m:0+t:7+f:!2,m:1+t:3+f:!2',
                    'fields': 'f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124,f1,f13'
                }
                
                query_string = urllib.parse.urlencode(params)
                full_url = f"{url}?{query_string}"
                yield scrapy.Request(
                    url=full_url,
                    headers=headers,
                    callback=self.parse,
                    dont_filter=True,
                    meta={'page': page, 'total_pages': total_pages}
                )
                
                logger.info(f"已生成第 {page}/{total_pages} 页请求")
                
                # 添加延时，避免请求太快
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"获取资金流向总数失败: {e}")
            import traceback
            traceback.print_exc()
    
    def parse(self, response):
        """解析资金流向数据"""
        try:
            text = response.text
            # 移除 jQuery 回调函数
            text = re.sub(r'^jQuery\d+_\d+\(', '', text)
            text = re.sub(r'\);$', '', text)
            
            import json
            data = json.loads(text)
            
            if data.get('rc') != 0:
                logger.error(f"获取资金流向数据失败: {data}")
                return
            
            stock_list = data.get('data', {}).get('diff', [])
            logger.info(f"获取到 {len(stock_list)} 只股票的资金流向数据")
            
            for stock in stock_list:
                self._process_stock(stock)
            
            logger.info(f"资金流向数据处理完成: 处理 {self.processed_count} 只, 错误 {self.error_count} 只")
            
        except Exception as e:
            logger.error(f"解析资金流向数据失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
    
    def _process_stock(self, stock):
        """处理单只股票的资金流向数据"""
        try:
            # 转换股票代码格式
            f12 = stock.get('f12', '')
            f13 = stock.get('f13', '')
            
            # f13 为 1 表示沪市，0 表示深市
            if f13 == 1:
                code = f'sh.{f12}'
            else:
                code = f'sz.{f12}'
            
            # 构建资金流向数据
            capital_flow_data = {
                'code': code,
                'name': stock.get('f14', ''),
                'date': self.today,
                'latest_price': stock.get('f2'),
                'change_pct': stock.get('f3'),
                'main_net_inflow': stock.get('f62'),
                'main_net_inflow_pct': stock.get('f184'),
                'super_large_net_inflow': stock.get('f66'),
                'super_large_net_inflow_pct': stock.get('f69'),
                'large_net_inflow': stock.get('f72'),
                'large_net_inflow_pct': stock.get('f75'),
                'medium_net_inflow': stock.get('f78'),
                'medium_net_inflow_pct': stock.get('f81'),
                'small_net_inflow': stock.get('f84'),
                'small_net_inflow_pct': stock.get('f87'),
                'f204': stock.get('f204'),
                'f205': stock.get('f205'),
                'f124': stock.get('f124'),
                'f1': stock.get('f1'),
                'f13': stock.get('f13'),
                'crawl_time': datetime.now()
            }
            
            # 保存到数据库
            self.storage.save_capital_flow(capital_flow_data)
            self.processed_count += 1
            
            if self.processed_count % 100 == 0:
                logger.info(f"已处理 {self.processed_count} 只股票")
            
        except Exception as e:
            logger.error(f"处理股票资金流向失败: {stock}: {e}")
            self.error_count += 1
    
    def closed(self, reason):
        logger.info(f"资金流向爬虫关闭: {reason}, 处理 {self.processed_count} 只, 错误 {self.error_count} 只")
        self.storage.close()
