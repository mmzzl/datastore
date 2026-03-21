from attr import dataclass
import scrapy
import json
import time
import random
import logging
import datetime
from urllib.parse import urlencode
from ..utils.config import load_config, save_progress
from ..storage.mongo_storage import MongoStorage

# 创建logger实例
logger = logging.getLogger(__name__)

class EastMoneyNewsSpider(scrapy.Spider):
    name = 'eastmoney_news'
    
    def __init__(self, sort_end='', req_trace='', sort_start='', *args, **kwargs):
        super(EastMoneyNewsSpider, self).__init__(*args, **kwargs)
        self.config = load_config()
        self.base_url = self.config['api']['base_url']
        self.ischange = False
        self.storage = MongoStorage()
        self.news_list_endpoint = self.config['api']['news_list_endpoint']
        self.news_count_endpoint = self.config['api']['news_count_endpoint']
        self.default_params = self.config['api']['default_params']
        # 使用传递的参数，如果没有则使用当前时间戳
        self.req_trace = req_trace if req_trace else str(int(time.time() * 1000))
        self.sort_end = sort_end
        self.sort_start = sort_start
        logger.info(f"爬虫初始化: sort_end='{self.sort_end}', req_trace='{self.req_trace}'")
    
    def start_requests(self):
        # 每次都使用当前时间戳作为req_trace，确保API返回最新的结果
        current_req_trace = str(int(time.time() * 1000))
        
        # 先检查是否有新新闻
        count_url = f"{self.base_url}{self.news_count_endpoint}"
        # 使用历史的sort_end作为sortStart参数，这样API就能返回从上一次sortEnd之后的新新闻
        count_params = {
            **self.default_params,
            'sortStart': self.sort_start,
            'req_trace': current_req_trace,
            '_': current_req_trace,
            'callback': f'jQuery{random.randint(1000000000000000, 9999999999999999)}'
        }
        # 构建带参数的URL
        full_count_url = f"{count_url}?{urlencode(count_params)}"
        logger.info(f"COUNT_URL: {full_count_url}")
        yield scrapy.Request(
            url=full_count_url,
            method='GET',
            callback=self.parse_count,
            meta={'req_trace': current_req_trace, 'sort_end': self.sort_end}
        )
    
    def parse_count(self, response):
        count = self._parse_count_response(response)
        meta = response.meta
        
        # 检查是否需要获取历史数据
        # 首先检查是否有新新闻
        if count != 0:
            # 有新新闻，使用空sortEnd获取最新数据
            sort_end = ''
            self.ischange = True
            logger.info(f"有新新闻({count}条)，使用空sort_end")
            
            # 请求新闻列表
            news_url = f"{self.base_url}{self.news_list_endpoint}"
            news_params = {
                **self.default_params,
                'sortEnd': sort_end,
                'req_trace': meta['req_trace'],
                '_': meta['req_trace'],
                'callback': f'jQuery{random.randint(1000000000000000, 9999999999999999)}'
            }
            # 构建带参数的URL
            full_news_url = f"{news_url}?{urlencode(news_params)}"
            yield scrapy.Request(
                url=full_news_url,
                method='GET',
                callback=self.parse,
                meta=meta
            )
        else:
            # 没有新新闻，检查是否需要获取历史数据
            # 检查是否已经有一个月前的数据
            # 尝试从数据库获取最早的新闻时间
            try:
                # 从数据库获取最早的新闻
                oldest_news = self.storage.collection.find_one(sort=[("showTime", 1)])
                if oldest_news:
                    oldest_time = oldest_news.get('showTime', '')
                    if oldest_time:
                        # 解析showTime为datetime对象
                        news_date = datetime.datetime.strptime(oldest_time, '%Y-%m-%d %H:%M:%S')
                        # 计算当前时间和新闻时间的差值
                        now = datetime.datetime.now()
                        delta = now - news_date
                        # 如果差值超过30天，不再获取历史数据
                        if delta.days > 30:
                            logger.info(f"新闻数据已超过30天，停止获取历史数据: {oldest_time}")
                            # 使用当前时间戳作为sort_end，确保下次只获取最新数据
                            sort_end = str(int(time.time() * 1000))
                            req_trace = int(time.time() * 1000)
                            # 保存进度到文件
                            progress_data = {
                                'sort_end': sort_end,
                                'req_trace': req_trace,
                                'sort_start': self.sort_start
                            }
                            save_progress(progress_data)
                            logger.info(f"进度已保存: sort_end='{sort_end}', req_trace='{req_trace}', sort_start='{self.sort_start}'")
                            # 直接返回，不再请求新闻列表API
                            return
                        else:
                            # 否则，继续获取历史数据
                            sort_end = meta.get('sort_end', '')
                            if self.storage.query_sort_end(sort_end):
                                # 历史数据已存在，使用sortEnd获取历史数据, 避免重复请求
                                sort_end = self.storage.get_sort_end()
                            logger.info(f"没有新新闻，使用历史sort_end: {sort_end}")
                            self.ischange = False
                            
                            # 请求新闻列表
                            news_url = f"{self.base_url}{self.news_list_endpoint}"
                            news_params = {
                                **self.default_params,
                                'sortEnd': sort_end,
                                'req_trace': meta['req_trace'],
                                '_': meta['req_trace'],
                                'callback': f'jQuery{random.randint(1000000000000000, 9999999999999999)}'
                            }
                            # 构建带参数的URL
                            full_news_url = f"{news_url}?{urlencode(news_params)}"
                            yield scrapy.Request(
                                url=full_news_url,
                                method='GET',
                                callback=self.parse,
                                meta=meta
                            )
                    else:
                        # 没有showTime，继续获取历史数据
                        sort_end = meta.get('sort_end', '')
                        if self.storage.query_sort_end(sort_end):
                            # 历史数据已存在，使用sortEnd获取历史数据, 避免重复请求
                            sort_end = self.storage.get_sort_end()
                        logger.info(f"没有新新闻，使用历史sort_end: {sort_end}")
                        self.ischange = False
                        
                        # 请求新闻列表
                        news_url = f"{self.base_url}{self.news_list_endpoint}"
                        news_params = {
                            **self.default_params,
                            'sortEnd': sort_end,
                            'req_trace': meta['req_trace'],
                            '_': meta['req_trace'],
                            'callback': f'jQuery{random.randint(1000000000000000, 9999999999999999)}'
                        }
                        # 构建带参数的URL
                        full_news_url = f"{news_url}?{urlencode(news_params)}"
                        yield scrapy.Request(
                            url=full_news_url,
                            method='GET',
                            callback=self.parse,
                            meta=meta
                        )
                else:
                    # 数据库中没有新闻，继续获取历史数据
                    sort_end = meta.get('sort_end', '')
                    if self.storage.query_sort_end(sort_end):
                        # 历史数据已存在，使用sortEnd获取历史数据, 避免重复请求
                        sort_end = self.storage.get_sort_end()
                    logger.info(f"没有新新闻，使用历史sort_end: {sort_end}")
                    self.ischange = False
                    
                    # 请求新闻列表
                    news_url = f"{self.base_url}{self.news_list_endpoint}"
                    news_params = {
                        **self.default_params,
                        'sortEnd': sort_end,
                        'req_trace': meta['req_trace'],
                        '_': meta['req_trace'],
                        'callback': f'jQuery{random.randint(1000000000000000, 9999999999999999)}'
                    }
                    # 构建带参数的URL
                    full_news_url = f"{news_url}?{urlencode(news_params)}"
                    yield scrapy.Request(
                        url=full_news_url,
                        method='GET',
                        callback=self.parse,
                        meta=meta
                    )
            except Exception as e:
                logger.error(f"检查历史数据时间失败: {e}")
                # 出错时，继续获取历史数据
                sort_end = meta.get('sort_end', '')
                if self.storage.query_sort_end(sort_end):
                    # 历史数据已存在，使用sortEnd获取历史数据, 避免重复请求
                    sort_end = self.storage.get_sort_end()
                logger.info(f"没有新新闻，使用历史sort_end: {sort_end}")
                self.ischange = False
                
                # 请求新闻列表
                news_url = f"{self.base_url}{self.news_list_endpoint}"
                news_params = {
                    **self.default_params,
                    'sortEnd': sort_end,
                    'req_trace': meta['req_trace'],
                    '_': meta['req_trace'],
                    'callback': f'jQuery{random.randint(1000000000000000, 9999999999999999)}'
                }
                # 构建带参数的URL
                full_news_url = f"{news_url}?{urlencode(news_params)}"
                yield scrapy.Request(
                    url=full_news_url,
                    method='GET',
                    callback=self.parse,
                    meta=meta
                )
    
    def parse(self, response):
        data = self._parse_jsonp(response.text)
        meta = response.meta
        req_trace = int(time.time() * 1000)
        news_list = []
        sort_end = ''
        
        if data.get('code') == '1' and 'data' in data:
            news_list = data['data'].get('fastNewsList', [])
            if news_list:
                sort_end = news_list[-1].get('realSort', '')
                if self.ischange:
                    self.sort_start = news_list[0].get('realSort', '')
                
                # 检查新闻的showTime是否是一个月前的数据
                first_news_time = news_list[0].get('showTime', '')
                if first_news_time:
                    # 解析showTime为datetime对象
                    try:
                        news_date = datetime.datetime.strptime(first_news_time, '%Y-%m-%d %H:%M:%S')
                        # 计算当前时间和新闻时间的差值
                        now = datetime.datetime.now()
                        delta = now - news_date
                        # 如果差值超过30天，记录日志并设置标志
                        if delta.days > 30:
                            logger.info(f"新闻数据已超过30天，停止获取历史数据: {first_news_time}")
                            # 保存进度时使用当前时间戳，确保下次只获取最新数据
                            sort_end = str(int(time.time() * 1000))
                    except Exception as e:
                        logger.error(f"解析showTime失败: {e}")
            else:
                logger.info(f"API返回空新闻列表")
                # 使用当前时间戳作为sort_end，确保下次只获取最新数据
                sort_end = str(int(time.time() * 1000))
        else:
            logger.error(f"API响应数据: {data}")
            logger.error(f"API响应失败")
            # 使用当前时间戳作为sort_end，确保下次只获取最新数据
            sort_end = str(int(time.time() * 1000))

        
        # 提取新闻项
       
        for news in news_list:
            yield {
                'code': news.get('code'),
                'title': news.get('title'),
                'summary': news.get('summary'),
                'showTime': news.get('showTime'),
                'stockList': news.get('stockList', []),
                'image': news.get('image', []),
                'pinglun_Num': news.get('pinglun_Num'),
                'share': news.get('share'),
                'realSort': news.get('realSort'),
                'titleColor': news.get('titleColor'),
                'crawlTime': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        
        # 优先使用API返回的sortEnd值
        # 如果API返回的sortEnd值与当前保存的sort_end相同，说明API可能返回固定值
        # 这种情况下，我们使用当前时间戳作为新的sort_end，确保下次能获取到最新的新闻数据
        
        
        # 保存进度到文件
        progress_data = {
            'sort_end': sort_end,
            'req_trace': req_trace,
            'sort_start': self.sort_start
        }
        save_progress(progress_data)
        logger.info(f"进度已保存: sort_end='{sort_end}', req_trace='{req_trace}', sort_start='{self.sort_start}'")
    
    def _parse_jsonp(self, jsonp_str):
        """解析JSONP格式的响应"""
        # 移除jQuery回调包装
        start = jsonp_str.find('(')
        end = jsonp_str.rfind(')')
        if start != -1 and end != -1:
            json_str = jsonp_str[start+1:end]
            return json.loads(json_str)
        return {}
    
    def _parse_count_response(self, response):
        """解析新闻计数响应"""
        data = self._parse_jsonp(response.text)
        logger.debug(f"新闻计数：{data}")
        if data.get('code') == '1':
            return data['data'].get('count', 0)
        return 0
