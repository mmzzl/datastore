#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试盯盘功能的配置
"""

import sys
import os
import logging
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_settings_config():
    """测试配置文件中的盯盘配置"""
    logger.info("=== 测试配置文件中的盯盘配置 ===")
    
    try:
        # 测试获取盯盘配置
        logger.info(f"盯盘功能启用状态: {settings.monitor_enabled}")
        logger.info(f"监控间隔: {settings.monitor_interval}秒")
        logger.info(f"盯盘开始时间: {settings.monitor_scheduler_time}")
        logger.info(f"监控股票数量: {len(settings.monitor_stocks)}")
        
        for i, stock in enumerate(settings.monitor_stocks):
            logger.info(f"股票 {i+1}: {stock.get('name')} ({stock.get('code')}), 持仓状态: {stock.get('hold')}")
        
        logger.info("配置文件中的盯盘配置测试成功！")
        return True
    except Exception as e:
        logger.error(f"配置文件中的盯盘配置测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_scheduler_import():
    """测试任务调度系统中的MonitorJob导入"""
    logger.info("=== 测试任务调度系统中的MonitorJob导入 ===")
    
    try:
        # 直接导入MonitorJob，不导入其他模块
        from app.scheduler.monitor_job import MonitorJob
        logger.info("MonitorJob 导入成功")
        
        logger.info("任务调度系统中的MonitorJob导入测试成功！")
        return True
    except Exception as e:
        logger.error(f"任务调度系统中的MonitorJob导入测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_main_scheduler_config():
    """测试main.py中的调度器配置"""
    logger.info("=== 测试main.py中的调度器配置 ===")
    
    try:
        # 读取main.py文件，检查是否包含盯盘任务配置
        main_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
        with open(main_file_path, "r", encoding="utf-8") as f:
            main_content = f.read()
        
        # 检查是否包含run_monitor_job函数
        if "def run_monitor_job()" in main_content:
            logger.info("run_monitor_job 函数存在")
        else:
            logger.error("run_monitor_job 函数不存在")
            return False
        
        # 检查是否在setup_scheduler中添加了盯盘任务
        if "monitor_job" in main_content:
            logger.info("盯盘任务配置存在")
        else:
            logger.error("盯盘任务配置不存在")
            return False
        
        logger.info("main.py中的调度器配置测试成功！")
        return True
    except Exception as e:
        logger.error(f"main.py中的调度器配置测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主测试函数"""
    logger.info("开始测试盯盘功能配置...")
    
    # 运行各项测试
    tests = [
        test_settings_config,
        test_scheduler_import,
        test_main_scheduler_config
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for test in tests:
        if test():
            success_count += 1
        logger.info("-" * 50)
    
    logger.info(f"测试完成: {success_count}/{total_count} 项测试通过")
    
    if success_count == total_count:
        logger.info("所有测试通过，盯盘功能配置正常！")
    else:
        logger.warning(f"有 {total_count - success_count} 项测试失败，请检查代码")

if __name__ == "__main__":
    main()
