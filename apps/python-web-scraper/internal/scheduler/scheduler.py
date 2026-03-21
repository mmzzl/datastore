# -*- coding: utf-8 -*-
"""爬虫调度器 - 仅保留新闻爬虫"""

import sys
import schedule
import time
import threading
import logging
import signal
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from internal.utils.config import load_config, load_progress

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

_current_spider_process = None
_stop_event = threading.Event()


def _run_spider_in_process(sort_end, req_trace, sort_start):
    try:
        from scrapy.crawler import CrawlerProcess
        from scrapy.utils.project import get_project_settings
        from internal.spider.eastmoney_spider import EastMoneyNewsSpider

        settings = get_project_settings()
        settings.set("PY_MINI_RACER_NO_CLEANUP", True)

        process = CrawlerProcess(settings)
        process.crawl(
            EastMoneyNewsSpider,
            sort_end=sort_end,
            req_trace=req_trace,
            sort_start=sort_start,
        )

        print("开始执行新闻爬虫")
        process.start()
        print(f"新闻爬虫执行完成: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"启动新闻爬虫失败: {e}")
        import traceback

        traceback.print_exc()


def run_spider(sort_end, req_trace, sort_start):
    global _current_spider_process

    try:
        from multiprocessing import Process

        logger.info(f"启动新闻爬虫... 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        _current_spider_process = Process(
            target=_run_spider_in_process,
            args=(sort_end, req_trace, sort_start),
        )
        _current_spider_process.start()

        while _current_spider_process.is_alive():
            _current_spider_process.join(timeout=1)
            if _stop_event.is_set():
                logger.info("收到停止信号，正在停止爬虫...")
                _current_spider_process.terminate()
                _current_spider_process.join(timeout=5)
                break

        logger.info(f"新闻爬虫进程已结束: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    except KeyboardInterrupt:
        logger.info("收到键盘中断信号，停止爬虫")
        if _current_spider_process and _current_spider_process.is_alive():
            _current_spider_process.terminate()
            _current_spider_process.join(timeout=5)
    except Exception as e:
        logger.error(f"启动新闻爬虫失败: {e}")
        import traceback

        traceback.print_exc()


class NewsScheduler:
    def __init__(self):
        self.config = load_config()
        self.interval = self.config.get("spider", {}).get("interval", 10)
        self.running = False

    def job(self):
        logger.info(f"定时任务触发，当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            progress = load_progress()
            sort_end = progress.get("sort_end", "")
            req_trace = progress.get("req_trace", "")
            sort_start = progress.get("sort_start", "")
            run_spider(sort_end, req_trace, sort_start)
            logger.info(f"定时任务执行完成: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logger.error(f"定时任务执行失败: {e}")

    def start(self):
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        schedule.every(self.interval).seconds.do(self.job)
        logger.info(f"已设置定时任务，每{self.interval}秒执行一次")

        logger.info("立即执行第一次任务")
        self.job()

        self.running = True

        def run_schedule():
            logger.info(
                f"调度线程已启动，当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            while self.running and not _stop_event.is_set():
                schedule.run_pending()
                time.sleep(1)
            logger.info("调度线程已停止")

        thread = threading.Thread(target=run_schedule)
        thread.daemon = False
        thread.start()

        logger.info(f"调度器已启动，新闻爬虫每{self.interval}秒执行一次")

        try:
            while self.running and not _stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def _signal_handler(self, signum, frame):
        logger.info(f"收到信号 {signum}，正在停止调度器...")
        _stop_event.set()
        self.stop()

    def stop(self):
        self.running = False
        _stop_event.set()

        global _current_spider_process
        if _current_spider_process and _current_spider_process.is_alive():
            logger.info("正在停止新闻爬虫进程...")
            _current_spider_process.terminate()
            _current_spider_process.join(timeout=5)

        logger.info("调度器已停止")
