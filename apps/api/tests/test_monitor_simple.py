#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版测试盯盘功能
"""

import sys
import os
import logging
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.monitor.config import MonitorConfig
from app.core.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_monitor_config():
    """测试配置管理模块"""
    logger.info("=== 测试配置管理模块 ===")
    
    try:
        config = MonitorConfig()
        
        # 测试获取配置
        full_config = config.get_config()
        logger.info(f"完整配置: {full_config}")
        
        # 测试获取股票列表
        stocks = config.get_stocks()
        logger.info(f"监控股票列表: {stocks}")
        
        # 测试获取指标配置
        indicators = config.get_indicator_config()
        logger.info(f"指标配置: {indicators}")
        
        # 测试获取监控间隔
        interval = config.get_monitor_interval()
        logger.info(f"监控间隔: {interval}秒")
        
        logger.info("配置管理模块测试成功！")
        return True
    except Exception as e:
        logger.error(f"配置管理模块测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

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

def test_scheduler_config():
    """测试任务调度系统中的盯盘任务配置"""
    logger.info("=== 测试任务调度系统中的盯盘任务配置 ===")
    
    try:
        # 测试导入MonitorJob
        from app.scheduler import MonitorJob
        logger.info("MonitorJob 导入成功")
        
        # 测试创建MonitorJob实例
        config = {
            "database": {
                "host": settings.mongodb_host,
                "port": settings.mongodb_port,
                "name": settings.mongodb_database,
                "username": settings.mongodb_username,
                "password": settings.mongodb_password,
            },
            "data_source": {
                "provider": settings.data_source,
                "tushare_token": settings.tushare_token,
            },
            "after_market": {
                "news_api_url": settings.after_market_news_api_url,
                "news_api_username": settings.after_market_news_api_username,
                "news_api_password": settings.after_market_news_api_password,
                "dingtalk_webhook": settings.after_market_dingtalk_webhook,
                "dingtalk_secret": settings.after_market_dingtalk_secret,
            },
            "llm": {
                "provider": settings.llm_provider,
                "api_key": settings.llm_api_key,
                "model": settings.llm_model,
                "base_url": settings.llm_base_url,
            },
        }
        
        job = MonitorJob(config)
        logger.info("MonitorJob 实例创建成功")
        
        logger.info("任务调度系统中的盯盘任务配置测试成功！")
        return True
    except Exception as e:
        logger.error(f"任务调度系统中的盯盘任务配置测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主测试函数"""
    logger.info("开始测试盯盘功能...")
    
    # 运行各项测试
    tests = [
        test_monitor_config,
        test_settings_config,
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
