import sys
import schedule
import time
import threading
import subprocess
import logging
import os
import baostock as bs
from datetime import datetime, timedelta
from multiprocessing import Process
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


def _run_spider_in_process(sort_end, req_trace, sort_start):
    """
    在子进程中运行新闻爬虫
    这个函数会在独立的子进程中被调用
    """
    try:
        # 在子进程中重新导入和初始化
        from scrapy.crawler import CrawlerProcess
        from scrapy.utils.project import get_project_settings
        from ..spider.eastmoney_spider import EastMoneyNewsSpider
        
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
        
        print("开始执行新闻爬虫")
        process.start()
        print(f"新闻爬虫执行完成: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
    except Exception as e:
        print(f"启动新闻爬虫失败: {e}")
        import traceback
        traceback.print_exc()


def run_spider(sort_end, req_trace, sort_start):
    """使用多进程运行新闻爬虫，避免 ReactorNotRestartable 错误"""
    try:
        logger.info(f"启动新闻爬虫... 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 创建子进程运行爬虫
        p = Process(target=_run_spider_in_process, args=(sort_end, req_trace, sort_start))
        p.start()
        
        # 等待子进程完成
        p.join()
        
        logger.info(f"新闻爬虫进程已结束: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
    except Exception as e:
        logger.error(f"启动新闻爬虫失败: {e}")
        import traceback
        traceback.print_exc()


def _run_kline_spider_in_process():
    """
    在子进程中运行K线爬虫
    这个函数会在独立的子进程中被调用
    """
    try:
        # 在子进程中重新导入和初始化
        from scrapy.crawler import CrawlerProcess
        from scrapy.utils.project import get_project_settings
        from ..spider.eastmoney_kline_spider import EastMoneyKlineSpider
        
        # 获取Scrapy设置
        settings = get_project_settings()
        
        # 禁用py_mini_racer的自动清理
        settings.set('PY_MINI_RACER_NO_CLEANUP', True)
        
        # 创建并启动CrawlerProcess
        process = CrawlerProcess(settings)
        process.crawl(EastMoneyKlineSpider)
        
        print("开始执行K线爬虫")
        process.start()
        print(f"K线爬虫执行完成: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"启动K线爬虫失败: {e}")
        import traceback
        traceback.print_exc()


def run_kline_spider():
    """使用多进程运行K线爬虫，避免 ReactorNotRestartable 错误"""
    try:
        logger.info(f"启动K线爬虫... 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 创建子进程运行爬虫
        p = Process(target=_run_kline_spider_in_process)
        p.start()
        
        # 等待子进程完成
        p.join()
        
        logger.info(f"K线爬虫进程已结束: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 解锁K线爬虫
        unlock_kline()
        
    except Exception as e:
        logger.error(f"启动K线爬虫失败: {e}")
        import traceback
        traceback.print_exc()
        unlock_kline()


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
        self.kline_run_time = self.config.get('kline_spider', {}).get('run_time', '00:00').strip()
        logger.info(f"K线爬虫配置: 启用={self.kline_enabled}, 运行时间={self.kline_run_time}")

    def start_crawler(self):
        """启动新闻爬虫"""
        try:
            logger.info(f"开始启动新闻爬虫... 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            progress = load_progress()
            sort_end = progress.get('sort_end', '')
            req_trace = progress.get('req_trace', '')
            sort_start = progress.get('sort_start', '')
            logger.info(f"加载历史进度: sort_end='{sort_end}', req_trace='{req_trace}', sort_start='{sort_start}'")
            
            # 使用subprocess运行爬虫
            run_spider(sort_end, req_trace, sort_start)
            
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
            
            # 使用subprocess运行爬虫
            run_kline_spider()
            
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
            logger.info(f"K线爬虫已启用，运行时间: {kline_time}")
            try:
                kline_job = schedule.every().day.at(kline_time).do(self.start_kline_crawler)
                logger.info(f"已设置K线爬虫定时任务，每天{kline_time}执行一次")
                logger.debug(f"K线定时任务详情: {kline_job}")
            except Exception as e:
                logger.error(f"K线爬虫定时任务设置失败: {e}")
                import traceback
                logger.error(f"错误详情: {traceback.format_exc()}")
                logger.info("将使用默认时间23:00")
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
