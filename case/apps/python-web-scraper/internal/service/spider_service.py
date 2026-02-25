# -*- coding: utf-8 -*-
"""爬虫管理服务"""
import os
import sys
import time
import threading
import multiprocessing
import logging
import json
from enum import Enum
from ..scheduler.scheduler import NewsScheduler
from ..utils.config import load_config, load_progress, save_progress

# 创建logger实例
logger = logging.getLogger(__name__)

# 状态文件路径
STATUS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'status.json')


def run_scheduler():
    """运行调度器"""
    logger.info("调度器进程启动...")
    try:
        logger.info("创建调度器实例...")
        scheduler = NewsScheduler()
        logger.info("调用调度器start方法...")
        scheduler.start()
        logger.info("调度器start方法执行完成")
    except Exception as e:
        logger.error(f"调度器运行失败: {e}")
        import traceback
        traceback.print_exc()
        # 更新状态为错误
        save_service_status("error")


def save_service_status(status):
    """保存服务状态到文件"""
    try:
        status_data = {
            "status": status,
            "timestamp": time.time()
        }
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        logger.info(f"服务状态已保存: {status}")
    except Exception as e:
        logger.error(f"保存服务状态失败: {e}")


def load_service_status():
    """从文件加载服务状态"""
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
                return status_data.get("status", "idle")
        return "idle"
    except Exception as e:
        logger.error(f"加载服务状态失败: {e}")
        return "idle"


class SpiderStatus(Enum):
    """爬虫状态枚举"""
    IDLE = "idle"  # 空闲
    RUNNING = "running"  # 运行中
    STOPPED = "stopped"  # 已停止
    ERROR = "error"  # 错误


class SpiderService:
    """爬虫管理服务"""
    
    def __init__(self):
        """初始化爬虫服务"""
        self.scheduler = None
        # 从文件加载状态
        status_str = load_service_status()
        logger.info(f"从文件加载的状态: {status_str}")
        # 检查状态值是否在枚举中
        status_values = [member.value for member in SpiderStatus]
        logger.info(f"枚举状态值: {status_values}")
        if status_str in status_values:
            self.status = SpiderStatus(status_str)
            logger.info(f"使用文件中的状态: {self.status.value}")
        else:
            self.status = SpiderStatus.IDLE
            logger.info(f"使用默认状态: {self.status.value}")
        self.status_lock = threading.Lock()
        self.scheduler_process = None
        self.config = load_config()
        logger.info(f"爬虫管理服务初始化完成，当前状态: {self.status.value}")
    
    def start(self):
        """启动爬虫服务"""
        with self.status_lock:
            if self.status == SpiderStatus.RUNNING:
                logger.warning("爬虫服务已经在运行中")
                return False
            
            try:
                logger.info("开始启动爬虫服务...")
                
                # 创建并启动进程
                logger.info("创建并启动调度器进程...")
                self.scheduler_process = multiprocessing.Process(target=run_scheduler)
                self.scheduler_process.daemon = False  # 改为非守护进程，允许创建子进程
                self.scheduler_process.start()
                
                # 等待一小段时间，确保进程已经启动
                time.sleep(1)
                
                # 检查进程是否还在运行
                if self.scheduler_process.is_alive():
                    logger.info(f"调度器进程已启动，PID: {self.scheduler_process.pid}")
                else:
                    logger.error("调度器进程启动后立即退出")
                    return False
                
                # 更新状态
                self.status = SpiderStatus.RUNNING
                # 保存状态到文件
                save_service_status(self.status.value)
                logger.info("爬虫服务启动成功")
                return True
            except Exception as e:
                logger.error(f"启动爬虫服务失败: {e}")
                import traceback
                traceback.print_exc()
                self.status = SpiderStatus.ERROR
                # 保存状态到文件
                save_service_status(self.status.value)
                return False
    
    def stop(self):
        """停止爬虫服务"""
        with self.status_lock:
            if self.status != SpiderStatus.RUNNING:
                logger.warning(f"爬虫服务当前状态为 {self.status.value}，无需停止")
                return False
            
            try:
                # 终止进程
                if self.scheduler_process and self.scheduler_process.is_alive():
                    logger.info(f"终止调度器进程，PID: {self.scheduler_process.pid}")
                    self.scheduler_process.terminate()
                    self.scheduler_process.join(timeout=5)
                
                # 更新状态
                self.status = SpiderStatus.STOPPED
                # 保存状态到文件
                save_service_status(self.status.value)
                logger.info("爬虫服务停止成功")
                return True
            except Exception as e:
                logger.error(f"停止爬虫服务失败: {e}")
                self.status = SpiderStatus.ERROR
                # 保存状态到文件
                save_service_status(self.status.value)
                return False
    
    def restart(self):
        """重启爬虫服务"""
        logger.info("开始重启爬虫服务")
        
        # 停止服务
        self.stop()
        
        # 等待一段时间
        time.sleep(2)
        
        # 启动服务
        result = self.start()
        
        if result:
            logger.info("爬虫服务重启成功")
        else:
            logger.error("爬虫服务重启失败")
        
        return result
    
    def get_status(self):
        """获取爬虫服务状态"""
        with self.status_lock:
            # 从文件加载最新状态
            status_str = load_service_status()
            logger.info(f"从文件加载的状态: {status_str}")
            # 检查状态值是否在枚举中
            status_values = [member.value for member in SpiderStatus]
            logger.info(f"枚举状态值: {status_values}")
            if status_str in status_values:
                self.status = SpiderStatus(status_str)
                logger.info(f"更新状态为: {self.status.value}")
            return self.status.value
    
    def get_progress(self):
        """获取爬虫进度"""
        try:
            progress = load_progress()
            return progress
        except Exception as e:
            logger.error(f"获取爬虫进度失败: {e}")
            return {}
    
    def get_stats(self):
        """获取爬虫统计信息"""
        try:
            progress = self.get_progress()
            stats = {
                "status": self.get_status(),
                "progress": progress,
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "config": {
                    "interval": self.config.get("spider", {}).get("interval", 10),
                    "mongodb": {
                        "host": self.config.get("mongodb", {}).get("host", ""),
                        "db": self.config.get("mongodb", {}).get("db", ""),
                        "collection": self.config.get("mongodb", {}).get("collection", "")
                    }
                }
            }
            return stats
        except Exception as e:
            logger.error(f"获取爬虫统计信息失败: {e}")
            return {}
    
    def run_once(self):
        """运行一次爬虫"""
        try:
            logger.info("开始运行一次爬虫")
            
            # 导入需要的模块
            from ..scheduler.scheduler import run_spider
            
            # 加载进度
            progress = load_progress()
            sort_end = progress.get("sort_end", "")
            req_trace = progress.get("req_trace", "")
            sort_start = progress.get("sort_start", "")
            
            # 在子进程中运行爬虫
            p = multiprocessing.Process(target=run_spider, args=(sort_end, req_trace, sort_start))
            p.start()
            p.join()
            
            logger.info("爬虫运行完成")
            return True
        except Exception as e:
            logger.error(f"运行爬虫失败: {e}")
            return False


# 创建全局服务实例
spider_service = SpiderService()


def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 解析命令行参数
    if len(sys.argv) < 2:
        print("用法: python spider_service.py [start|stop|restart|status|run_once]")
        return
    
    command = sys.argv[1]
    
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
        print(f"爬虫服务状态: {status}")
        stats = spider_service.get_stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    elif command == "run_once":
        result = spider_service.run_once()
        print(f"运行一次爬虫: {'成功' if result else '失败'}")
    else:
        print("无效命令，请使用: start|stop|restart|status|run_once")


if __name__ == "__main__":
    main()
