import schedule
import time
import threading
import multiprocessing
import logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from ..utils.config import load_config, save_progress, load_progress

# 创建logger实例
logger = logging.getLogger(__name__)


def run_spider(sort_end, req_trace, sort_start):
    """在子进程中运行爬虫"""
    try:
        logger.info(f"子进程启动爬虫... 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        # 导入需要的类（在子进程中需要重新导入）
        from ..spider.eastmoney_spider import EastMoneyNewsSpider
        # 创建CrawlerProcess实例
        process = CrawlerProcess(get_project_settings())
        # 启动爬虫
        process.crawl(EastMoneyNewsSpider, 
                      sort_end=sort_end,
                      req_trace=req_trace,
                      sort_start=sort_start)
        logger.debug(f"sort_end={sort_end}, req_trace={req_trace}, sort_start={sort_start}")
        # 启动进程
        process.start()
        logger.info(f"子进程爬虫执行完成: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        logger.error(f"子进程运行爬虫失败: {e}")
        import traceback
        traceback.print_exc()

class NewsScheduler:
    def __init__(self):
        self.config = load_config()
        self.interval = self.config['spider']['interval']
        self.running = False

    def start_crawler(self):
        """启动爬虫"""
        try:
            logger.info(f"开始启动爬虫... 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            # 加载历史进度
            progress = load_progress()
            sort_end = progress.get('sort_end', '')
            req_trace = progress.get('req_trace', '')
            sort_start = progress.get('sort_start', '')
            logger.info(f"加载历史进度: sort_end='{sort_end}', req_trace='{req_trace}', sort_start='{sort_start}'")
            
            # 在新的子进程中运行爬虫
            logger.info("创建子进程运行爬虫...")
            p = multiprocessing.Process(target=run_spider, 
                                      args=(sort_end, req_trace, sort_start))
            p.start()
            logger.info(f"子进程已启动，PID: {p.pid}")
            
            # 等待子进程完成
            p.join()
            logger.info(f"子进程已完成，返回码: {p.exitcode}")
            
            # 爬虫完成后，重新加载进度，确认进度已更新
            updated_progress = load_progress()
            logger.info(f"爬虫执行完成，最新进度: sort_end='{updated_progress.get('sort_end', '')}', req_trace='{updated_progress.get('req_trace', '')}'")
            logger.info(f"等待{self.interval}秒后再次执行")
            
        except Exception as e:
            logger.error(f"启动爬虫失败: {e}")
            import traceback
            traceback.print_exc()
    
    def job(self):
        """定时任务"""
        logger.info(f"\n======================================")
        logger.info(f"定时任务被触发！当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"开始执行爬虫任务...")
        try:
            self.start_crawler()
            logger.info(f"定时任务执行完成: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logger.error(f"定时任务执行失败: {e}")
        logger.info(f"======================================\n")
    
    def start(self):
        """启动调度器"""
        # 设置定时任务
        job = schedule.every(self.interval).seconds.do(self.job)
        logger.info(f"已设置定时任务，每{self.interval}秒执行一次")
        logger.debug(f"定时任务详情: {job}")
        
        # 立即执行一次
        logger.info("立即执行第一次任务")
        self.job()
        
        # 启动调度线程
        self.running = True
        def run_schedule():
            logger.info(f"调度线程已启动，当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            while self.running:
                schedule.run_pending()
                time.sleep(1)
            logger.info("调度线程已停止")
        
        thread = threading.Thread(target=run_schedule)
        thread.daemon = False  # 改为非守护线程，确保它能正常运行
        thread.start()
        
        logger.info(f"调度器已启动，每{self.interval}秒执行一次")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        logger.info("调度器已停止")
