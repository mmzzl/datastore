#!/usr/bin/env python3
"""
独立的新闻爬虫运行脚本
用于避免Python 3.12多进程环境下的atexit问题
"""

# 重要：必须在最开始就修复threading和atexit状态
import sys
import os

# 重新初始化threading模块，避免Python 3.12的atexit问题
import threading
if hasattr(threading, '_exithandlers'):
    threading._exithandlers = []
    threading._shutdown = False

# 重新初始化atexit模块
import atexit
atexit._exithandlers = []

# 添加项目路径到sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)


def run_news_spider(sort_end, req_trace, sort_start):
    """运行新闻爬虫"""
    try:
        logger.info("独立进程启动新闻爬虫")
        
        # 延迟导入爬虫类
        from internal.spider.eastmoney_spider import EastMoneyNewsSpider
        
        # 获取Scrapy设置
        settings = get_project_settings()
        
        # 禁用py_mini_racer的自动清理
        settings.set('PY_MINI_RACER_NO_CLEANUP', True)
        
        # 创建并启动CrawlerProcess
        process = CrawlerProcess(settings)
        process.crawl(EastMoneyNewsSpider, 
                      sort_end=sort_end,
                      req_trace=req_trace,
                      sort_start=sort_start)
        
        logger.info("开始执行新闻爬虫")
        process.start()
        logger.info("新闻爬虫执行完成")
        
    except Exception as e:
        logger.error(f"新闻爬虫执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python run_news_spider.py <sort_end> <req_trace> <sort_start>")
        sys.exit(1)
    
    sort_end = sys.argv[1]
    req_trace = sys.argv[2]
    sort_start = sys.argv[3]
    
    logger.info(f"参数: sort_end={sort_end}, req_trace={req_trace}, sort_start={sort_start}")
    
    run_news_spider(sort_end, req_trace, sort_start)
