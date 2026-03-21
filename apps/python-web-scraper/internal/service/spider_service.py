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
        self.kline_process = None
        self.kline_status = SpiderStatus.IDLE
        self.kline_status_lock = threading.Lock()
        self.capital_flow_process = None
        self.capital_flow_status = SpiderStatus.IDLE
        self.capital_flow_status_lock = threading.Lock()
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
                
                # 创建并启动新闻调度器进程（调度器会统一管理新闻、K线、资金流向爬虫）
                logger.info("创建并启动新闻调度器进程...")
                self.scheduler_process = multiprocessing.Process(target=run_scheduler)
                self.scheduler_process.daemon = False
                self.scheduler_process.start()
                
                # 等待一小段时间，确保新闻调度器进程已经启动
                time.sleep(0.5)
                
                # 检查新闻调度器进程是否还在运行
                if self.scheduler_process.is_alive():
                    logger.info(f"新闻调度器进程已启动，PID: {self.scheduler_process.pid}")
                    logger.info("调度器将根据配置文件自动管理新闻、K线、资金流向爬虫")
                else:
                    logger.error("新闻调度器进程启动后立即退出")
                    return False
                
                # 更新状态
                self.status = SpiderStatus.RUNNING
                # 保存状态到文件
                save_service_status(self.status.value)
                logger.info("爬虫服务启动成功（调度器统一管理所有爬虫）")
                return True
            except Exception as e:
                logger.error(f"启动爬虫服务失败: {e}")
                import traceback
                traceback.print_exc()
                # 清理已启动的进程
                if self.scheduler_process and self.scheduler_process.is_alive():
                    self.scheduler_process.terminate()
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
                # 终止新闻调度器进程（调度器会停止所有子爬虫）
                if self.scheduler_process and self.scheduler_process.is_alive():
                    logger.info(f"终止新闻调度器进程，PID: {self.scheduler_process.pid}")
                    self.scheduler_process.terminate()
                    self.scheduler_process.join(timeout=5)
                
                # 更新状态
                self.status = SpiderStatus.STOPPED
                # 保存状态到文件
                save_service_status(self.status.value)
                logger.info("爬虫服务停止成功（调度器统一管理所有爬虫）")
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
            
            # 检查进程是否还在运行
            if self.scheduler_process and self.scheduler_process.is_alive():
                self.status = SpiderStatus.RUNNING
            elif self.status == SpiderStatus.RUNNING:
                self.status = SpiderStatus.STOPPED
            
            # 从配置文件读取各爬虫的启用状态
            kline_enabled = self.config.get("kline_spider", {}).get("enabled", False)
            capital_flow_enabled = self.config.get("capital_flow_spider", {}).get("enabled", False)
            
            # 返回服务状态和各爬虫的启用状态
            return {
                "service_status": self.status.value,
                "kline_spider": {
                    "enabled": kline_enabled,
                    "run_time": self.config.get("kline_spider", {}).get("run_time", "00:00")
                },
                "capital_flow_spider": {
                    "enabled": capital_flow_enabled,
                    "run_time": self.config.get("capital_flow_spider", {}).get("run_time", "00:00")
                }
            }
    
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
            status = self.get_status()
            stats = {
                "news_scheduler_status": status["news_scheduler"],
                "kline_spider_status": status["kline_spider"],
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
    
    def start_kline(self):
        """启动K线爬虫"""
        with self.kline_status_lock:
            if self.kline_status == SpiderStatus.RUNNING:
                logger.warning("K线爬虫已经在运行中")
                return False
            
            try:
                logger.info("开始启动K线爬虫...")
                
                # 导入需要的模块
                from ..scheduler.scheduler import run_kline_spider
                
                # 创建并启动进程
                logger.info("创建并启动K线爬虫进程...")
                self.kline_process = multiprocessing.Process(target=run_kline_spider)
                self.kline_process.daemon = False
                self.kline_process.start()
                
                # 等待一小段时间，确保进程已经启动
                time.sleep(1)
                
                # 检查进程是否还在运行
                if self.kline_process.is_alive():
                    logger.info(f"K线爬虫进程已启动，PID: {self.kline_process.pid}")
                else:
                    logger.error("K线爬虫进程启动后立即退出")
                    return False
                
                # 更新状态
                self.kline_status = SpiderStatus.RUNNING
                logger.info("K线爬虫启动成功")
                return True
            except Exception as e:
                logger.error(f"启动K线爬虫失败: {e}")
                import traceback
                traceback.print_exc()
                self.kline_status = SpiderStatus.ERROR
                return False
    
    def stop_kline(self):
        """停止K线爬虫"""
        with self.kline_status_lock:
            if self.kline_status != SpiderStatus.RUNNING:
                logger.warning(f"K线爬虫当前状态为 {self.kline_status.value}，无需停止")
                return False
            
            try:
                # 终止进程
                if self.kline_process and self.kline_process.is_alive():
                    logger.info(f"终止K线爬虫进程，PID: {self.kline_process.pid}")
                    self.kline_process.terminate()
                    self.kline_process.join(timeout=5)
                
                # 更新状态
                self.kline_status = SpiderStatus.STOPPED
                logger.info("K线爬虫停止成功")
                return True
            except Exception as e:
                logger.error(f"停止K线爬虫失败: {e}")
                self.kline_status = SpiderStatus.ERROR
                return False
    
    def restart_kline(self):
        """重启K线爬虫"""
        logger.info("开始重启K线爬虫")
        
        # 停止服务
        self.stop_kline()
        
        # 等待一段时间
        time.sleep(2)
        
        # 启动服务
        result = self.start_kline()
        
        if result:
            logger.info("K线爬虫重启成功")
        else:
            logger.error("K线爬虫重启失败")
        
        return result
    
    def get_kline_status(self):
        """获取K线爬虫状态"""
        with self.kline_status_lock:
            # 检查进程是否还在运行
            if self.kline_process and self.kline_process.is_alive():
                self.kline_status = SpiderStatus.RUNNING
            elif self.kline_status == SpiderStatus.RUNNING:
                self.kline_status = SpiderStatus.STOPPED
            return self.kline_status.value
    
    def run_kline_once(self):
        """运行一次K线爬虫"""
        try:
            logger.info("开始运行一次K线爬虫")
            
            # 导入需要的模块
            from ..scheduler.scheduler import run_kline_spider
            
            # 在子进程中运行爬虫
            p = multiprocessing.Process(target=run_kline_spider)
            p.start()
            p.join()
            
            logger.info("K线爬虫运行完成")
            return True
        except Exception as e:
            logger.error(f"运行K线爬虫失败: {e}")
            return False
    
    def start_capital_flow(self):
        """启动资金流向爬虫"""
        with self.capital_flow_status_lock:
            if self.capital_flow_status == SpiderStatus.RUNNING:
                logger.warning("资金流向爬虫已经在运行中")
                return False
            
            try:
                logger.info("开始启动资金流向爬虫...")
                
                # 导入需要的模块
                from ..scheduler.scheduler import run_capital_flow_spider
                
                # 创建并启动进程
                logger.info("创建并启动资金流向爬虫进程...")
                self.capital_flow_process = multiprocessing.Process(target=run_capital_flow_spider)
                self.capital_flow_process.daemon = False
                self.capital_flow_process.start()
                
                # 等待一小段时间，确保进程已经启动
                time.sleep(1)
                
                # 检查进程是否还在运行
                if self.capital_flow_process.is_alive():
                    logger.info(f"资金流向爬虫进程已启动，PID: {self.capital_flow_process.pid}")
                else:
                    logger.error("资金流向爬虫进程启动后立即退出")
                    return False
                
                # 更新状态
                self.capital_flow_status = SpiderStatus.RUNNING
                logger.info("资金流向爬虫启动成功")
                return True
            except Exception as e:
                logger.error(f"启动资金流向爬虫失败: {e}")
                import traceback
                traceback.print_exc()
                self.capital_flow_status = SpiderStatus.ERROR
                return False
    
    def stop_capital_flow(self):
        """停止资金流向爬虫"""
        with self.capital_flow_status_lock:
            if self.capital_flow_status != SpiderStatus.RUNNING:
                logger.warning(f"资金流向爬虫当前状态为 {self.capital_flow_status.value}，无需停止")
                return False
            
            try:
                # 终止进程
                if self.capital_flow_process and self.capital_flow_process.is_alive():
                    logger.info(f"终止资金流向爬虫进程，PID: {self.capital_flow_process.pid}")
                    self.capital_flow_process.terminate()
                    self.capital_flow_process.join(timeout=5)
                
                # 更新状态
                self.capital_flow_status = SpiderStatus.STOPPED
                logger.info("资金流向爬虫停止成功")
                return True
            except Exception as e:
                logger.error(f"停止资金流向爬虫失败: {e}")
                self.capital_flow_status = SpiderStatus.ERROR
                return False
    
    def restart_capital_flow(self):
        """重启资金流向爬虫"""
        logger.info("开始重启资金流向爬虫")
        
        # 停止服务
        self.stop_capital_flow()
        
        # 等待一段时间
        time.sleep(2)
        
        # 启动服务
        result = self.start_capital_flow()
        
        if result:
            logger.info("资金流向爬虫重启成功")
        else:
            logger.error("资金流向爬虫重启失败")
        
        return result
    
    def get_capital_flow_status(self):
        """获取资金流向爬虫状态"""
        with self.capital_flow_status_lock:
            # 检查进程是否还在运行
            if self.capital_flow_process and self.capital_flow_process.is_alive():
                self.capital_flow_status = SpiderStatus.RUNNING
            elif self.capital_flow_status == SpiderStatus.RUNNING:
                self.capital_flow_status = SpiderStatus.STOPPED
            return self.capital_flow_status.value
    
    def run_capital_flow_once(self):
        """运行一次资金流向爬虫"""
        try:
            logger.info("开始运行一次资金流向爬虫")
            
            # 导入需要的模块
            from ..scheduler.scheduler import run_capital_flow_spider
            
            # 在子进程中运行爬虫
            p = multiprocessing.Process(target=run_capital_flow_spider)
            p.start()
            p.join()
            
            logger.info("资金流向爬虫运行完成")
            return True
        except Exception as e:
            logger.error(f"运行资金流向爬虫失败: {e}")
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
        print("用法: python spider_service.py [start|stop|restart|status|run_once|start_kline|stop_kline|restart_kline|kline_status|run_kline_once|start_capital_flow|stop_capital_flow|restart_capital_flow|capital_flow_status|run_capital_flow_once]")
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
            print(f"新闻调度器状态: {status['news_scheduler']}")
            print(f"K线爬虫状态: {status['kline_spider']}")
            stats = spider_service.get_stats()
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        elif command == "run_once":
            result = spider_service.run_once()
            print(f"运行一次爬虫: {'成功' if result else '失败'}")
        elif command == "start_kline":
            result = spider_service.start_kline()
            print(f"启动K线爬虫: {'成功' if result else '失败'}")
        elif command == "stop_kline":
            result = spider_service.stop_kline()
            print(f"停止K线爬虫: {'成功' if result else '失败'}")
        elif command == "restart_kline":
            result = spider_service.restart_kline()
            print(f"重启K线爬虫: {'成功' if result else '失败'}")
        elif command == "kline_status":
            status = spider_service.get_kline_status()
            print(f"K线爬虫状态: {status}")
        elif command == "run_kline_once":
            result = spider_service.run_kline_once()
            print(f"运行一次K线爬虫: {'成功' if result else '失败'}")
        elif command == "start_capital_flow":
            result = spider_service.start_capital_flow()
            print(f"启动资金流向爬虫: {'成功' if result else '失败'}")
        elif command == "stop_capital_flow":
            result = spider_service.stop_capital_flow()
            print(f"停止资金流向爬虫: {'成功' if result else '失败'}")
        elif command == "restart_capital_flow":
            result = spider_service.restart_capital_flow()
            print(f"重启资金流向爬虫: {'成功' if result else '失败'}")
        elif command == "capital_flow_status":
            status = spider_service.get_capital_flow_status()
            print(f"资金流向爬虫状态: {status}")
        elif command == "run_capital_flow_once":
            result = spider_service.run_capital_flow_once()
            print(f"运行一次资金流向爬虫: {'成功' if result else '失败'}")
        else:
            print("无效命令，请使用: start|stop|restart|status|run_once|start_kline|stop_kline|restart_kline|kline_status|run_kline_once|start_capital_flow|stop_capital_flow|restart_capital_flow|capital_flow_status|run_capital_flow_once")
    except KeyboardInterrupt as e:
        logger.error(f"收到中断信号，正在停止爬虫服务...")
        spider_service.stop()
        print(f"爬虫服务已停止")

if __name__ == "__main__":
    main()
