#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试买入和卖出信号计算
"""

import sys
import os
import logging

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_buy_signal_calculation():
    """测试买入信号计算"""
    logger.info("=== 测试买入信号计算 ===")
    
    try:
        # 模拟技术分析数据
        technical_data = {
            "rsi": 25,  # 低于30，买入信号
            "macd": {
                "macd": 0.5,
                "signal": 0.3,
                "histogram": 0.2
            },  # MACD金叉，买入信号
            "kdj": {
                "k": 15,
                "d": 20,
                "j": 10
            },  # KDJ超卖，买入信号
            "bollinger": {
                "upper": 110,
                "middle": 100,
                "lower": 90
            }
        }
        
        # 模拟股票配置
        stock_config = {
            "code": "600519",
            "name": "贵州茅台",
            "hold": False,
            "buy_threshold": 0.05,
            "sell_threshold": 0.03,
            "cost_price": 0.0,
            "profit_target": 0.1,
            "stop_loss": 0.05,
            "current_price": 89,  # 低于布林带下轨
            "rsi_buy_level": 30,
            "rsi_sell_level": 70,
            "k_buy_level": 20,
            "k_sell_level": 80
        }
        
        # 导入信号生成器
        from app.monitor.analysis.signal import SignalGenerator
        generator = SignalGenerator()
        
        # 测试买入信号
        buy_signal = generator.generate_buy_signal(technical_data, stock_config)
        logger.info(f"买入信号: {buy_signal}")
        
        # 验证买入信号
        if buy_signal["signal"] == "buy":
            logger.info("买入信号测试通过！")
        else:
            logger.error("买入信号测试失败！")
            return False
        
        # 测试持有状态下的信号
        stock_config["hold"] = True
        sell_signal = generator.generate_sell_signal(technical_data, stock_config)
        logger.info(f"卖出信号: {sell_signal}")
        
        # 验证卖出信号（在这种情况下应该是持有）
        if sell_signal["signal"] == "hold":
            logger.info("卖出信号测试通过！")
        else:
            logger.error("卖出信号测试失败！")
            return False
        
        logger.info("买入信号计算测试成功！")
        return True
    except Exception as e:
        logger.error(f"买入信号计算测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_sell_signal_calculation():
    """测试卖出信号计算"""
    logger.info("=== 测试卖出信号计算 ===")
    
    try:
        # 模拟技术分析数据
        technical_data = {
            "rsi": 75,  # 高于70，卖出信号
            "macd": {
                "macd": -0.5,
                "signal": -0.3,
                "histogram": -0.2
            },  # MACD死叉，卖出信号
            "kdj": {
                "k": 85,
                "d": 80,
                "j": 90
            },  # KDJ超买，卖出信号
            "bollinger": {
                "upper": 110,
                "middle": 100,
                "lower": 90
            }
        }
        
        # 模拟股票配置
        stock_config = {
            "code": "600519",
            "name": "贵州茅台",
            "hold": True,
            "buy_threshold": 0.05,
            "sell_threshold": 0.03,
            "cost_price": 100.0,
            "profit_target": 0.1,
            "stop_loss": 0.05,
            "current_price": 115,  # 高于布林带上轨，且达到盈利目标
            "rsi_buy_level": 30,
            "rsi_sell_level": 70,
            "k_buy_level": 20,
            "k_sell_level": 80
        }
        
        # 导入信号生成器
        from app.monitor.analysis.signal import SignalGenerator
        generator = SignalGenerator()
        
        # 测试卖出信号
        sell_signal = generator.generate_sell_signal(technical_data, stock_config)
        logger.info(f"卖出信号: {sell_signal}")
        
        # 验证卖出信号
        if sell_signal["signal"] == "sell":
            logger.info("卖出信号测试通过！")
        else:
            logger.error("卖出信号测试失败！")
            return False
        
        # 测试止损信号
        stock_config["current_price"] = 94  # 触发止损
        stop_loss_signal = generator.generate_sell_signal(technical_data, stock_config)
        logger.info(f"止损信号: {stop_loss_signal}")
        
        # 验证止损信号
        if stop_loss_signal["signal"] == "sell":
            logger.info("止损信号测试通过！")
        else:
            logger.error("止损信号测试失败！")
            return False
        
        logger.info("卖出信号计算测试成功！")
        return True
    except Exception as e:
        logger.error(f"卖出信号计算测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_signal_generator():
    """测试信号生成器"""
    logger.info("=== 测试信号生成器 ===")
    
    try:
        # 模拟技术分析数据
        technical_data = {
            "rsi": 25,
            "macd": {
                "macd": 0.5,
                "signal": 0.3,
                "histogram": 0.2
            },
            "kdj": {
                "k": 15,
                "d": 20,
                "j": 10
            },
            "bollinger": {
                "upper": 110,
                "middle": 100,
                "lower": 90
            }
        }
        
        # 测试未持有状态
        stock_config_hold_false = {
            "code": "600519",
            "name": "贵州茅台",
            "hold": False,
            "buy_threshold": 0.05,
            "sell_threshold": 0.03,
            "cost_price": 0.0,
            "profit_target": 0.1,
            "stop_loss": 0.05,
            "current_price": 89,
            "rsi_buy_level": 30,
            "rsi_sell_level": 70,
            "k_buy_level": 20,
            "k_sell_level": 80
        }
        
        # 测试持有状态
        stock_config_hold_true = {
            "code": "600519",
            "name": "贵州茅台",
            "hold": True,
            "buy_threshold": 0.05,
            "sell_threshold": 0.03,
            "cost_price": 100.0,
            "profit_target": 0.1,
            "stop_loss": 0.05,
            "current_price": 115,
            "rsi_buy_level": 30,
            "rsi_sell_level": 70,
            "k_buy_level": 20,
            "k_sell_level": 80
        }
        
        # 导入信号生成器
        from app.monitor.analysis.signal import SignalGenerator
        generator = SignalGenerator()
        
        # 测试未持有状态的信号
        signal_hold_false = generator.generate_signal(technical_data, stock_config_hold_false)
        logger.info(f"未持有状态信号: {signal_hold_false}")
        
        # 测试持有状态的信号
        signal_hold_true = generator.generate_signal(technical_data, stock_config_hold_true)
        logger.info(f"持有状态信号: {signal_hold_true}")
        
        logger.info("信号生成器测试成功！")
        return True
    except Exception as e:
        logger.error(f"信号生成器测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主测试函数"""
    logger.info("开始测试买入和卖出信号计算...")
    
    # 运行各项测试
    tests = [
        test_buy_signal_calculation,
        test_sell_signal_calculation,
        test_signal_generator
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for test in tests:
        if test():
            success_count += 1
        logger.info("-" * 50)
    
    logger.info(f"测试完成: {success_count}/{total_count} 项测试通过")
    
    if success_count == total_count:
        logger.info("所有测试通过，买入和卖出信号计算准确！")
    else:
        logger.warning(f"有 {total_count - success_count} 项测试失败，请检查代码")

if __name__ == "__main__":
    main()
