#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试盯盘功能
"""

import sys
import os
import logging
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.monitor import StockMonitor
from app.monitor.analysis.technical import TechnicalAnalyzer
from app.monitor.analysis.signal import SignalGenerator
from app.monitor.config import MonitorConfig
from app.core.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_technical_analyzer():
    """测试技术分析模块"""
    logger.info("=== 测试技术分析模块 ===")
    
    try:
        analyzer = TechnicalAnalyzer()
        
        # 测试RSI计算
        prices = [100, 101, 102, 103, 102, 101, 100, 99, 98, 99, 100, 101, 102, 103]
        rsi = analyzer.calculate_rsi(prices, 14)
        logger.info(f"RSI计算结果: {rsi}")
        
        # 测试MACD计算
        macd, signal, hist = analyzer.calculate_macd(prices)
        logger.info(f"MACD计算结果 - MACD: {macd}, Signal: {signal}, Hist: {hist}")
        
        # 测试KDJ计算
        high = [105, 106, 107, 108, 107, 106, 105, 104, 103, 104, 105, 106, 107, 108]
        low = [95, 96, 97, 98, 97, 96, 95, 94, 93, 94, 95, 96, 97, 98]
        close = prices
        k, d, j = analyzer.calculate_kdj(high, low, close)
        logger.info(f"KDJ计算结果 - K: {k}, D: {d}, J: {j}")
        
        # 测试布林带计算
        upper, middle, lower = analyzer.calculate_bollinger_bands(prices)
        logger.info(f"布林带计算结果 - 上轨: {upper}, 中轨: {middle}, 下轨: {lower}")
        
        logger.info("技术分析模块测试成功！")
        return True
    except Exception as e:
        logger.error(f"技术分析模块测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_signal_generator():
    """测试信号生成模块"""
    logger.info("=== 测试信号生成模块 ===")
    
    try:
        generator = SignalGenerator()
        
        # 测试买入信号
        rsi = 25  # 低于30，可能的买入信号
        macd = 0.5
        signal_line = 0.3
        k = 15  # 低于20，可能的买入信号
        d = 20
        j = 10
        upper_band = 110
        middle_band = 100
        lower_band = 90
        current_price = 92
        
        buy_signal = generator.generate_buy_signal(
            rsi, macd, signal_line, k, d, j, upper_band, middle_band, lower_band, current_price
        )
        logger.info(f"买入信号生成结果: {buy_signal}")
        
        # 测试卖出信号
        rsi = 75  # 高于70，可能的卖出信号
        macd = -0.5
        signal_line = -0.3
        k = 85  # 高于80，可能的卖出信号
        d = 80
        j = 90
        current_price = 108
        
        sell_signal = generator.generate_sell_signal(
            rsi, macd, signal_line, k, d, j, upper_band, middle_band, lower_band, current_price
        )
        logger.info(f"卖出信号生成结果: {sell_signal}")
        
        # 测试综合信号
        signal = generator.generate_signal(
            rsi, macd, signal_line, k, d, j, upper_band, middle_band, lower_band, current_price, False
        )
        logger.info(f"综合信号生成结果: {signal}")
        
        logger.info("信号生成模块测试成功！")
        return True
    except Exception as e:
        logger.error(f"信号生成模块测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

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

def test_stock_monitor():
    """测试股票监控核心类"""
    logger.info("=== 测试股票监控核心类 ===")
    
    try:
        # 构建配置
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
        
        # 初始化监控器
        monitor = StockMonitor(config)
        
        # 测试获取股票数据
        stock_code = "600519"
        stock_data = monitor.get_stock_data(stock_code)
        logger.info(f"股票 {stock_code} 实时数据: {stock_data}")
        
        # 测试获取股票历史数据
        history_data = monitor.get_stock_history_data(stock_code, days=30)
        logger.info(f"股票 {stock_code} 历史数据长度: {len(history_data) if history_data else 0}")
        
        # 测试分析单只股票
        stock_config = {
            "code": stock_code,
            "name": "贵州茅台",
            "hold": False,
            "buy_threshold": 0.05,
            "sell_threshold": 0.03,
            "cost_price": 0.0,
            "profit_target": 0.1,
            "stop_loss": 0.05
        }
        result = monitor.analyze_stock(stock_config)
        if result:
            logger.info(f"股票分析结果: 信号={result.signal.signal}, 价格={result.price}, 技术指标={result.technical_data.__dict__}")
        
        # 测试监控所有股票
        results = monitor.monitor_stocks()
        logger.info(f"监控股票数量: {len(results)}")
        for i, res in enumerate(results):
            logger.info(f"监控结果 {i+1}: 股票={res.stock_name}, 信号={res.signal.signal}, 价格={res.price}")
        
        # 关闭监控器
        monitor.close()
        
        logger.info("股票监控核心类测试成功！")
        return True
    except Exception as e:
        logger.error(f"股票监控核心类测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主测试函数"""
    logger.info("开始测试盯盘功能...")
    
    # 运行各项测试
    tests = [
        test_technical_analyzer,
        test_signal_generator,
        test_monitor_config,
        test_stock_monitor
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for test in tests:
        if test():
            success_count += 1
        logger.info("-" * 50)
    
    logger.info(f"测试完成: {success_count}/{total_count} 项测试通过")
    
    if success_count == total_count:
        logger.info("所有测试通过，盯盘功能正常！")
    else:
        logger.warning(f"有 {total_count - success_count} 项测试失败，请检查代码")

if __name__ == "__main__":
    main()
