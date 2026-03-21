# -*- coding: utf-8 -*-
"""爬虫管理服务 - 仅保留新闻爬虫"""

import os
import sys
import time
import threading
import multiprocessing
import logging
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from internal.scheduler.scheduler import NewsScheduler
from internal.utils.config import load_config, load_progress, save_progress

logger = logging.getLogger(__name__)

STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "status.json")


def save_service_status(status):
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"status": status, "timestamp": time.time()},
                f,
                ensure_ascii=False,
                indent=2,
            )
    except Exception as e:
        logger.error(f"保存服务状态失败: {e}")


def load_service_status():
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("status", "idle")
    except Exception as e:
        logger.error(f"加载服务状态失败: {e}")
    return "idle"


def run_scheduler():
    logger.info("调度器进程启动...")
    try:
        scheduler = NewsScheduler()
        scheduler.start()
    except Exception as e:
        logger.error(f"调度器运行失败: {e}")
        import traceback

        traceback.print_exc()
        save_service_status("error")


class SpiderService:
    def __init__(self):
        self.status = load_service_status()
        self.status_lock = threading.Lock()
        self.scheduler_process = None
        self.config = load_config()

    def start(self):
        with self.status_lock:
            if self.status == "running":
                logger.warning("爬虫服务已在运行中")
                return False
            try:
                logger.info("启动爬虫服务...")
                self.scheduler_process = multiprocessing.Process(target=run_scheduler)
                self.scheduler_process.daemon = False
                self.scheduler_process.start()
                time.sleep(0.5)
                if not self.scheduler_process.is_alive():
                    logger.error("调度器进程启动后立即退出")
                    return False
                self.status = "running"
                save_service_status(self.status)
                logger.info(f"爬虫服务启动成功，PID: {self.scheduler_process.pid}")
                return True
            except Exception as e:
                logger.error(f"启动失败: {e}")
                if self.scheduler_process and self.scheduler_process.is_alive():
                    self.scheduler_process.terminate()
                self.status = "error"
                save_service_status(self.status)
                return False

    def stop(self):
        with self.status_lock:
            if self.status != "running":
                logger.warning(f"当前状态 {self.status}，无需停止")
                return False
            try:
                if self.scheduler_process and self.scheduler_process.is_alive():
                    logger.info(f"终止调度器进程，PID: {self.scheduler_process.pid}")
                    self.scheduler_process.terminate()
                    self.scheduler_process.join(timeout=5)
                self.status = "stopped"
                save_service_status(self.status)
                logger.info("爬虫服务已停止")
                return True
            except Exception as e:
                logger.error(f"停止失败: {e}")
                self.status = "error"
                save_service_status(self.status)
                return False

    def restart(self):
        self.stop()
        time.sleep(2)
        return self.start()

    def get_status(self):
        with self.status_lock:
            status_str = load_service_status()
            if self.scheduler_process and self.scheduler_process.is_alive():
                self.status = "running"
            elif status_str == "running":
                self.status = "stopped"
            else:
                self.status = status_str
            return {"service_status": self.status}

    def get_progress(self):
        try:
            return load_progress()
        except Exception as e:
            logger.error(f"获取进度失败: {e}")
            return {}

    def run_once(self):
        try:
            from internal.scheduler.scheduler import run_spider

            progress = load_progress()
            sort_end = progress.get("sort_end", "")
            req_trace = progress.get("req_trace", "")
            sort_start = progress.get("sort_start", "")
            p = multiprocessing.Process(
                target=run_spider, args=(sort_end, req_trace, sort_start)
            )
            p.start()
            p.join()
            logger.info("爬虫运行完成")
            return True
        except Exception as e:
            logger.error(f"运行爬虫失败: {e}")
            return False


spider_service = SpiderService()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if len(sys.argv) < 2:
        print("用法: python spider_service.py [start|stop|restart|status|run_once]")
        return

    command = sys.argv[1]
    try:
        if command == "start":
            result = spider_service.start()
            print(f"启动爬虫服务: {'成功' if result else '失败'}")
        elif command == "stop":
            result = spider_service.stop()
            print(f"停止爬虫服务: {'成功' if result else '失败'}")
        elif command == "restart":
            result = spider_service.restart()
            print(f"重启爬虫服务: {'成功' if result else '失败'}")
        elif command == "status":
            status = spider_service.get_status()
            print(f"服务状态: {status['service_status']}")
            print(json.dumps(status, ensure_ascii=False, indent=2))
        elif command == "run_once":
            result = spider_service.run_once()
            print(f"运行一次爬虫: {'成功' if result else '失败'}")
        else:
            print("无效命令: start|stop|restart|status|run_once")
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止爬虫服务...")
        spider_service.stop()
        print("爬虫服务已停止")


if __name__ == "__main__":
    main()
