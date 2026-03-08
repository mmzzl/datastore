#!/usr/bin/env python
"""
独立的K线爬虫运行脚本
用于避免Python 3.12多进程环境下的atexit问题
"""

import sys
import os

# 添加项目路径到sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import logging

logger = logging.getLogger(__name__)

# 锁文件路径
KLINE_LOCK_FILE = os.path.join(project_root, 'data', 'kline_running.lock')


def unlock_kline():
    """解锁K线爬虫"""
    if os.path.exists(KLINE_LOCK_FILE):
        try:
            os.remove(KLINE_LOCK_FILE)
        except:
            pass


def run_kline_spider():
    """运行K线爬虫"""
    import atexit
    atexit.register(unlock_kline)
    
    try:
        logger.info(f"独立进程启动K线爬虫... 当前时间")
        
        from internal.spider.akshare_kline_spider import AkshareKlineSpider
        
        settings = get_project_settings()
        settings.set('PY_MINI_RACER_NO_CLEANUP', True)
        
        process = CrawlerProcess(settings)
        process.crawl(AkshareKlineSpider)
        
        logger.info(f"开始执行K线爬虫")
        process.start()
        logger.info(f"K线爬虫执行完成")
        
    except Exception as e:
        logger.error(f"K线爬虫执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    run_kline_spider()
