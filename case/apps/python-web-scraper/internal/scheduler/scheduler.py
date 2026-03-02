import schedule
import time
import threading
import multiprocessing
import logging
import os
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from ..utils.config import load_config, save_progress, load_progress

logger = logging.getLogger(__name__)

KLINE_LOCK_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'kline_running.lock')


def run_spider(sort_end, req_trace, sort_start):
    """在子进程中运行新闻爬虫"""
    try:
        logger.info(f"子进程启动新闻爬虫... 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        from ..spider.eastmoney_spider import EastMoneyNewsSpider
        process = CrawlerProcess(get_project_settings())
        process.crawl(EastMoneyNewsSpider, 
                      sort_end=sort_end,
                      req_trace=req_trace,
                      sort_start=sort_start)
        logger.debug(f"sort_end={sort_end}, req_trace={req_trace}, sort_start={sort_start}")
        process.start()
        logger.info(f"子进程新闻爬虫执行完成: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        logger.error(f"子进程运行新闻爬虫失败: {e}")
        import traceback
        traceback.print_exc()


def run_kline_spider():
    """在子进程中运行K线爬虫"""
    import atexit
    atexit.register(unlock_kline)
    try:
        logger.info(f"子进程启动K线爬虫... 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        from ..spider.eastmoney_kline_spider import EastMoneyKlineSpider
        process = CrawlerProcess(get_project_settings())
        process.crawl(EastMoneyKlineSpider)
        process.start()
        logger.info(f"子进程K线爬虫执行完成: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        logger.error(f"子进程运行K线爬虫失败: {e}")
        import traceback
        traceback.print_exc()


def is_kline_locked():
    """检查K线爬虫是否正在运行"""
    if os.path.exists(KLINE_LOCK_FILE):
        try:
            with open(KLINE_LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
                try:
                    os.kill(pid, 0)
                    return True
                except OSError:
                    unlock_kline()
                    return False
        except:
            return False
    return False


def lock_kline():
    """锁定K线爬虫"""
    os.makedirs(os.path.dirname(KLINE_LOCK_FILE), exist_ok=True)
    with open(KLINE_LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))


def unlock_kline():
    """解锁K线爬虫"""
    if os.path.exists(KLINE_LOCK_FILE):
        try:
            os.remove(KLINE_LOCK_FILE)
        except:
            pass


class NewsScheduler:
    def __init__(self):
        self.config = load_config()
        self.interval = self.config['spider']['interval']
        self.running = False
        self.kline_enabled = self.config.get('kline_spider', {}).get('enabled', True)
        self.kline_run_time = self.config.get('kline_spider', {}).get('run_time', '15:30').strip()

    def start_crawler(self):
        """启动新闻爬虫"""
        try:
            logger.info(f"开始启动新闻爬虫... 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            progress = load_progress()
            sort_end = progress.get('sort_end', '')
            req_trace = progress.get('req_trace', '')
            sort_start = progress.get('sort_start', '')
            logger.info(f"加载历史进度: sort_end='{sort_end}', req_trace='{req_trace}', sort_start='{sort_start}'")
            
            p = multiprocessing.Process(target=run_spider, 
                                      args=(sort_end, req_trace, sort_start))
            p.start()
            logger.info(f"子进程已启动，PID: {p.pid}")
            
            p.join()
            logger.info(f"子进程已完成，返回码: {p.exitcode}")
            
            updated_progress = load_progress()
            logger.info(f"爬虫执行完成，最新进度: sort_end='{updated_progress.get('sort_end', '')}', req_trace='{updated_progress.get('req_trace', '')}'")
            logger.info(f"等待{self.interval}秒后再次执行")
            
        except Exception as e:
            logger.error(f"启动爬虫失败: {e}")
            import traceback
            traceback.print_exc()
    
    def start_kline_crawler(self):
        """启动K线爬虫"""
        if is_kline_locked():
            logger.warning("K线爬虫正在运行中，跳过本次任务")
            return
        
        try:
            logger.info(f"开始启动K线爬虫... 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            lock_kline()
            p = multiprocessing.Process(target=run_kline_spider)
            p.start()
            logger.info(f"K线爬虫子进程已启动，PID: {p.pid}")
            p.join()
            logger.info(f"K线爬虫子进程已完成，返回码: {p.exitcode}")
        except Exception as e:
            logger.error(f"启动K线爬虫失败: {e}")
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
        job = schedule.every(self.interval).seconds.do(self.job)
        logger.info(f"已设置定时任务，每{self.interval}秒执行一次")
        logger.debug(f"定时任务详情: {job}")
        
        if self.kline_enabled:
            kline_time = self.kline_run_time.strip()
            try:
                kline_job = schedule.every().day.at(kline_time).do(self.start_kline_crawler)
                logger.info(f"已设置K线爬虫定时任务，每天{kline_time}执行一次")
            except Exception as e:
                logger.warning(f"K线爬虫定时任务设置失败: {e}，将使用默认时间15:30")
                kline_job = schedule.every().day.at("15:30").do(self.start_kline_crawler)
        else:
            logger.info("K线爬虫已禁用")
        
        logger.info("立即执行第一次任务")
        self.job()
        
        self.running = True
        def run_schedule():
            logger.info(f"调度线程已启动，当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            while self.running:
                schedule.run_pending()
                time.sleep(1)
            logger.info("调度线程已停止")
        
        thread = threading.Thread(target=run_schedule)
        thread.daemon = False
        thread.start()
        
        kline_status = f"每天{self.kline_run_time}" if self.kline_enabled else "已禁用"
        logger.info(f"调度器已启动，新闻爬虫每{self.interval}秒执行一次，K线爬虫{kline_status}执行一次")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        logger.info("调度器已停止")
