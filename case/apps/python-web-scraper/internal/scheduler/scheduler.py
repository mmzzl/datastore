import schedule
import time
import threading
import multiprocessing
import logging
import os
import baostock as bs
from datetime import datetime, timedelta
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from ..utils.config import load_config, save_progress, load_progress

logger = logging.getLogger(__name__)

KLINE_LOCK_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'kline_running.lock')


def is_trading_day(date=None):
    """判断指定日期是否为交易日"""
    if date is None:
        date = datetime.now()
    else:
        date = datetime.strptime(date, '%Y-%m-%d') if isinstance(date, str) else date
    
    try:
        # 登录 baostock
        lg = bs.login()
        if lg.error_code != '0':
            logger.error(f"baostock login failed: {lg.error_msg}")
            return False
        
        # 获取交易日历
        end_date = date.strftime("%Y-%m-%d")
        start_date = (date - timedelta(days=7)).strftime("%Y-%m-%d")
        
        rs = bs.query_trade_dates(start_date=start_date, end_date=end_date)
        bs.logout()
        
        if rs.error_code == '0' and len(rs.data) > 0:
            # 检查日期是否在交易日历中
            for trade_date in rs.data:
                if trade_date[0] == end_date:
                    logger.info(f"{end_date} 是交易日")
                    return True
            logger.info(f"{end_date} 不是交易日")
            return False
        else:
            logger.error(f"获取交易日历失败: {rs.error_msg}")
            return False
    except Exception as e:
        logger.error(f"判断交易日失败: {e}")
        return False


def run_spider(sort_end, req_trace, sort_start):
    """在子进程中运行新闻爬虫"""
    # 必须在函数开始就设置所有环境变量，在任何导入之前
    import sys
    import importlib
    
    # 设置环境变量，避免各种库的atexit注册问题
    os.environ['PY_MINI_RACER_NO_CLEANUP'] = '1'
    
    # 修复Python 3.12的concurrent.futures问题
    # 需要重新初始化threading模块的atexit状态
    import threading
    if hasattr(threading, '_exithandlers'):
        threading._exithandlers = []
    
    try:
        logger.info(f"子进程启动新闻爬虫... 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 延迟导入，避免在主进程中加载
        from ..spider.eastmoney_spider import EastMoneyNewsSpider
        
        # 获取Scrapy设置
        settings = get_project_settings()
        
        # 禁用py_mini_racer的自动清理
        settings.set('PY_MINI_RACER_NO_CLEANUP', True)
        
        # 设置Scrapy不使用线程池执行器
        settings.set('REACTOR_THREADPOOL_MAXSIZE', 0)
        
        process = CrawlerProcess(settings)
        process.crawl(EastMoneyNewsSpider, 
                      sort_end=sort_end,
                      req_trace=req_trace,
                      sort_start=sort_start)
        logger.debug(f"sort_end={sort_end}, req_trace={req_trace}, sort_start={sort_start}")
        
        # 启动爬虫
        process.start()
        
        logger.info(f"子进程新闻爬虫执行完成: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        logger.error(f"子进程运行新闻爬虫失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保进程清理
        try:
            import gc
            gc.collect()
        except:
            pass


def run_kline_spider():
    """在子进程中运行K线爬虫"""
    # 必须在函数开始就设置所有环境变量，在任何导入之前
    import sys
    import importlib
    import atexit
    
    # 设置环境变量，避免各种库的atexit注册问题
    os.environ['PY_MINI_RACER_NO_CLEANUP'] = '1'
    
    # 修复Python 3.12的concurrent.futures问题
    # 需要重新初始化threading模块的atexit状态
    import threading
    if hasattr(threading, '_exithandlers'):
        threading._exithandlers = []
    
    # 注册清理函数
    atexit.register(unlock_kline)
    
    try:
        logger.info(f"子进程启动K线爬虫... 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 延迟导入，避免在主进程中加载
        from ..spider.akshare_kline_spider import AkshareKlineSpider
        
        # 获取Scrapy设置
        settings = get_project_settings()
        
        # 禁用py_mini_racer的自动清理
        settings.set('PY_MINI_RACER_NO_CLEANUP', True)
        
        # 设置Scrapy不使用线程池执行器
        settings.set('REACTOR_THREADPOOL_MAXSIZE', 0)
        
        process = CrawlerProcess(settings)
        process.crawl(AkshareKlineSpider)
        process.start()
        
        logger.info(f"子进程K线爬虫执行完成: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        logger.error(f"子进程运行K线爬虫失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保进程清理
        try:
            import gc
            gc.collect()
        except:
            pass


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
        self.kline_enabled = self.config.get('akshare_kline', {}).get('enabled', True)
        self.kline_run_time = self.config.get('akshare_kline', {}).get('run_time', '23:00').strip()

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
        
        # 判断当天是否为交易日
        current_date = datetime.now().strftime('%Y-%m-%d')
        if not is_trading_day(current_date):
            logger.info(f"当前日期 {current_date} 不是交易日，跳过K线爬虫任务")
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
                logger.warning(f"K线爬虫定时任务设置失败: {e}，将使用默认时间23:00")
                kline_job = schedule.every().day.at("23:00").do(self.start_kline_crawler)
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
