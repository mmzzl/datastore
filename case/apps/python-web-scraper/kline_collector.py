#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K 线数据采集脚本
使用 requests 替代 Scrapy 实现 K 线数据采集
"""

import json
import logging
import random
import time
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode
from internal.utils.config import load_config
from internal.storage.mongo_storage import MongoStorage
from internal.spider.baostock_stock_codes import load_stock_codes
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KlineCollector:
    def __init__(self):
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
        
        # 获取 User-Agent 列表
        spider_config = self.config.get('spider', {})
        self.user_agents = spider_config.get('user_agents', [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ])
        
        # 创建会话并配置重试策略
        self.session = self._create_session()
    
    def _create_session(self):
        """创建配置了重试策略的会话"""
        session = requests.Session()
        
        # 禁用自动重试，手动控制重试逻辑
        retry_strategy = Retry(
            total=0,
            connect=0,
            read=0,
            redirect=0,
            status=0
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=5,
            pool_maxsize=10
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_headers(self):
        """生成随机的请求头"""
        user_agent = random.choice(self.user_agents)
        
        headers = {
            'User-Agent': user_agent,
            'Host': 'push2his.eastmoney.com',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://quote.eastmoney.com/',
            'Origin': 'https://quote.eastmoney.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        
        return headers
    
    def run(self):
        """运行采集任务"""
        logger.info("开始 K 线数据采集任务")
        
        try:
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
                    self._process_stock(secid, stock_code)
                
                # 每批处理完后延迟5秒，避免请求过快
                time.sleep(5)
                
            logger.info(f"采集任务完成: 共处理 {self.processed_count} 只股票, 跳过 {self.skip_count} 只, 错误 {self.error_count} 只")
            
        except Exception as e:
            logger.error(f"采集任务失败: {e}")
        finally:
            self.storage.close()
            if hasattr(self, 'session'):
                self.session.close()
    
    def _process_stock(self, secid, stock_code):
        """处理单个股票"""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                latest_date = self.storage.get_latest_kline_date(secid)
                if not latest_date:
                    latest_date = self.today
                else:
                    latest_date = datetime.strptime(latest_date, "%Y-%m-%d").strftime("%Y%m%d")
                if latest_date:
                    if latest_date >= self.today:
                        logger.info(f"跳过 {secid}: 已采集到最新日期 {latest_date}")
                        self.skip_count += 1
                        return
                    
                    end_date = self.today
                    beg = latest_date
                    if end_date == beg:
                        beg = (datetime.strptime(beg, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
                else:
                    # 没有历史数据时，只获取一周前的数据
                    beg = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
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
                
                # 使用会话和完整的请求头
                headers = self._get_headers()
                
                # 发送请求，增加超时时间
                response = self.session.get(url, headers=headers, timeout=90, verify=False)
                response.raise_for_status()
                
                # 解析数据
                data = response.json()
                
                if data.get('rc') == 0 and 'data' in data:
                    kline_data = data['data']
                    klines = kline_data.get('klines', [])
                    
                    if klines:
                        inserted, skipped = self.storage.save_kline(secid, klines)
                        self.processed_count += 1
                        logger.info(f"成功采集 {secid}: {len(klines)} 条数据")
                    else:
                        logger.debug(f"无K线数据 {secid}")
                        self.skip_count += 1
                else:
                    logger.warning(f"API返回错误 {secid}: {data.get('msg', '')}")
                    self.error_count += 1
                
                # 成功后退出重试循环
                break
                
            except requests.exceptions.ConnectionError as e:
                retry_count += 1
                logger.warning(f"连接错误 {secid} (重试 {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    # 指数退避：3秒、6秒、12秒、24秒、48秒
                    sleep_time = 3 * (2 ** (retry_count - 1))
                    logger.info(f"等待 {sleep_time} 秒后重试...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"处理股票失败 {secid}: 达到最大重试次数")
                    self.error_count += 1
                    
            except requests.exceptions.Timeout as e:
                retry_count += 1
                logger.warning(f"超时错误 {secid} (重试 {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    sleep_time = 3 * (2 ** (retry_count - 1))
                    logger.info(f"等待 {sleep_time} 秒后重试...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"处理股票失败 {secid}: 达到最大重试次数")
                    self.error_count += 1
                    
            except Exception as e:
                logger.error(f"处理股票失败 {secid}: {e}")
                self.error_count += 1
                break
        
        # 控制请求频率，每个请求之间延迟2-4秒
        time.sleep(random.uniform(2.0, 4.0))
        
        # 每50只股票打印一次进度
        if (self.processed_count + self.skip_count + self.error_count) % 50 == 0:
            logger.info(f"进度: 已处理 {self.processed_count} 只, 跳过 {self.skip_count} 只, 错误 {self.error_count} 只")


if __name__ == '__main__':
    collector = KlineCollector()
    collector.run()
