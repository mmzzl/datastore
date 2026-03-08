#!/usr/bin/env python3
"""
独立的K线爬虫运行脚本
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

# 锁文件路径
KLINE_LOCK_FILE = os.path.join(project_root, 'data', 'kline_running.lock')


def unlock_kline():
    """解锁K线爬虫"""
    if os.path.exists(KLINE_LOCK_FILE):
        try:
            os.remove(KLINE_LOCK_FILE)
            logger.info("K线爬虫锁文件已删除")
        except Exception as e:
            logger.error(f"删除锁文件失败: {e}")


def run_kline_spider():
    """运行K线爬虫"""
    # 注册清理函数
    atexit.register(unlock_kline)
    
    try:
        logger.info("独立进程启动K线爬虫")
        
        # 延迟导入爬虫类
        from internal.spider.akshare_kline_spider import AkshareKlineSpider
        
        # 获取Scrapy设置
        settings = get_project_settings()
        
        # 禁用py_mini_racer的自动清理
        settings.set('PY_MINI_RACER_NO_CLEANUP', True)
        
        # 创建并启动CrawlerProcess
        process = CrawlerProcess(settings)
        process.crawl(AkshareKlineSpider)
        
        logger.info("开始执行K线爬虫")
        process.start()
        logger.info("K线爬虫执行完成")
        
    except Exception as e:
        logger.error(f"K线爬虫执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    logger.info("K线爬虫脚本启动")
    
    run_kline_spider()
    
    logger.info("K线爬虫脚本退出")
