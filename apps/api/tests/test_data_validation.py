#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据获取和处理功能
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_data_source_config():
    """测试数据源配置"""
    logger.info("=== 测试数据源配置 ===")
    
    try:
        # 测试数据源配置
        logger.info(f"数据源类型: {settings.data_source}")
        
        if settings.data_source == "tushare":
            logger.info(f"Tushare Token: {'已配置' if settings.tushare_token else '未配置'}")
        elif settings.data_source == "akshare":
            logger.info("使用 Akshare 数据源")
        else:
            logger.warning(f"未知数据源: {settings.data_source}")
        
        logger.info("数据源配置测试成功！")
        return True
    except Exception as e:
        logger.error(f"数据源配置测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_stock_configs():
    """测试股票配置"""
    logger.info("=== 测试股票配置 ===")
    
    try:
        # 测试股票配置
        stocks = settings.monitor_stocks
        logger.info(f"监控股票数量: {len(stocks)}")
        
        for i, stock in enumerate(stocks):
            logger.info(f"股票 {i+1}:")
            logger.info(f"  代码: {stock.get('code', '未知')}")
            logger.info(f"  名称: {stock.get('name', '未知')}")
            logger.info(f"  持仓状态: {stock.get('hold', False)}")
            logger.info(f"  买入阈值: {stock.get('buy_threshold', 0.05)}")
            logger.info(f"  卖出阈值: {stock.get('sell_threshold', 0.03)}")
            logger.info(f"  成本价: {stock.get('cost_price', 0.0)}")
            logger.info(f"  盈利目标: {stock.get('profit_target', 0.1)}")
            logger.info(f"  止损比例: {stock.get('stop_loss', 0.05)}")
        
        logger.info("股票配置测试成功！")
        return True
    except Exception as e:
        logger.error(f"股票配置测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_database_config():
    """测试数据库配置"""
    logger.info("=== 测试数据库配置 ===")
    
    try:
        # 测试数据库配置
        logger.info(f"MongoDB主机: {settings.mongodb_host}")
        logger.info(f"MongoDB端口: {settings.mongodb_port}")
        logger.info(f"MongoDB数据库: {settings.mongodb_database}")
        logger.info(f"MongoDB集合: {settings.mongodb_collection}")
        logger.info(f"MongoDB用户名: {'已配置' if settings.mongodb_username else '未配置'}")
        logger.info(f"MongoDB密码: {'已配置' if settings.mongodb_password else '未配置'}")
        
        logger.info("数据库配置测试成功！")
        return True
    except Exception as e:
        logger.error(f"数据库配置测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_dingtalk_config():
    """测试钉钉配置"""
    logger.info("=== 测试钉钉配置 ===")
    
    try:
        # 测试钉钉配置
        logger.info(f"钉钉Webhook: {'已配置' if settings.after_market_dingtalk_webhook else '未配置'}")
        logger.info(f"钉钉Secret: {'已配置' if settings.after_market_dingtalk_secret else '未配置'}")
        
        logger.info("钉钉配置测试成功！")
        return True
    except Exception as e:
        logger.error(f"钉钉配置测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_time_config():
    """测试时间配置"""
    logger.info("=== 测试时间配置 ===")
    
    try:
        # 测试时间配置
        logger.info(f"盯盘开始时间: {settings.monitor_scheduler_time}")
        logger.info(f"监控间隔: {settings.monitor_interval}秒")
        logger.info(f"盘后任务时间: {settings.after_market_scheduler_time}")
        logger.info(f"预缓存任务时间: {settings.after_market_pre_cache_scheduler_time}")
        logger.info(f"时区: {settings.after_market_scheduler_timezone}")
        
        # 验证时间格式
        try:
            hour, minute = map(int, settings.monitor_scheduler_time.split(':'))
            if 0 <= hour < 24 and 0 <= minute < 60:
                logger.info("盯盘开始时间格式正确")
            else:
                logger.error("盯盘开始时间格式错误")
                return False
        except Exception as e:
            logger.error(f"盯盘开始时间格式错误: {e}")
            return False
        
        logger.info("时间配置测试成功！")
        return True
    except Exception as e:
        logger.error(f"时间配置测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主测试函数"""
    logger.info("开始测试数据配置和验证...")
    
    # 运行各项测试
    tests = [
        test_data_source_config,
        test_stock_configs,
        test_database_config,
        test_dingtalk_config,
        test_time_config
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for test in tests:
        if test():
            success_count += 1
        logger.info("-" * 50)
    
    logger.info(f"测试完成: {success_count}/{total_count} 项测试通过")
    
    if success_count == total_count:
        logger.info("所有测试通过，数据配置正常！")
    else:
        logger.warning(f"有 {total_count - success_count} 项测试失败，请检查配置")

if __name__ == "__main__":
    main()
