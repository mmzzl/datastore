# -*- coding: utf-8 -*-
"""东方财富24小时新闻采集主程序"""
import time
from internal.scheduler.scheduler import NewsScheduler

def main():
    """主函数"""
    print("东方财富24小时新闻采集系统启动")
    print("=" * 60)
    
    # 创建调度器实例
    scheduler = NewsScheduler()
    
    try:
        # 启动调度器
        scheduler.start()
        
        # 保持主进程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n收到中断信号，正在停止...")
        scheduler.stop()
        print("系统已停止")

