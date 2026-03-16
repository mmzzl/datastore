#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础测试盯盘功能
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

def test_config_loading():
    """测试配置加载"""
    logger.info("=== 测试配置加载 ===")
    
    try:
        # 测试配置文件加载
        logger.info(f"应用名称: {settings.app_name}")
        logger.info(f"MongoDB主机: {settings.mongodb_host}")
        logger.info(f"数据源: {settings.data_source}")
        
        # 测试盯盘配置
        logger.info(f"盯盘功能启用: {settings.monitor_enabled}")
        logger.info(f"监控间隔: {settings.monitor_interval}秒")
        logger.info(f"盯盘开始时间: {settings.monitor_scheduler_time}")
        logger.info(f"监控股票数量: {len(settings.monitor_stocks)}")
        
        for i, stock in enumerate(settings.monitor_stocks):
            logger.info(f"股票 {i+1}: {stock.get('name')} ({stock.get('code')}), 持仓: {stock.get('hold')}")
        
        logger.info("配置加载测试成功！")
        return True
    except Exception as e:
        logger.error(f"配置加载测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_directory_structure():
    """测试目录结构"""
    logger.info("=== 测试目录结构 ===")
    
    try:
        # 检查监控模块目录结构
        monitor_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "monitor")
        analysis_dir = os.path.join(monitor_dir, "analysis")
        
        logger.info(f"监控模块目录存在: {os.path.exists(monitor_dir)}")
        logger.info(f"分析模块目录存在: {os.path.exists(analysis_dir)}")
        
        # 检查关键文件是否存在
        files_to_check = [
            "stock_monitor.py",
            "config.py",
            "models.py",
            "analysis/technical.py",
            "analysis/signal.py"
        ]
        
        for file_path in files_to_check:
            full_path = os.path.join(monitor_dir, file_path)
            logger.info(f"文件 {file_path} 存在: {os.path.exists(full_path)}")
        
        logger.info("目录结构测试成功！")
        return True
    except Exception as e:
        logger.error(f"目录结构测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_scheduler_config():
    """测试调度器配置"""
    logger.info("=== 测试调度器配置 ===")
    
    try:
        # 检查main.py中的调度器配置
        main_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
        
        if os.path.exists(main_file):
            with open(main_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 检查是否包含盯盘任务配置
            if "run_monitor_job" in content:
                logger.info("run_monitor_job 函数存在")
            else:
                logger.error("run_monitor_job 函数不存在")
                return False
            
            if "monitor_job" in content:
                logger.info("盯盘任务配置存在")
            else:
                logger.error("盯盘任务配置不存在")
                return False
        else:
            logger.error("main.py 文件不存在")
            return False
        
        # 检查monitor_job.py是否存在
        monitor_job_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "scheduler", "monitor_job.py")
        logger.info(f"monitor_job.py 存在: {os.path.exists(monitor_job_file)}")
        
        logger.info("调度器配置测试成功！")
        return True
    except Exception as e:
        logger.error(f"调度器配置测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主测试函数"""
    logger.info("开始测试盯盘功能...")
    
    # 运行各项测试
    tests = [
        test_config_loading,
        test_directory_structure,
        test_scheduler_config
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
