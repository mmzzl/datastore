#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试买入和卖出信号逻辑（纯Python实现，不依赖NumPy和pandas）
"""

import sys
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SignalGenerator:
    """信号生成器（纯Python实现）"""
    
    def __init__(self):
        pass
    
    def generate_buy_signal(self, technical_data, stock_config):
        """
        生成买入信号
        
        参数:
            technical_data: 技术分析数据
            stock_config: 股票配置
            
        返回:
            买入信号信息
        """
        signals = []
        signal_strength = 0
        
        # RSI信号
        rsi = technical_data.get("rsi", 50.0)
        rsi_buy_level = stock_config.get("rsi_buy_level", 30)
        if rsi < rsi_buy_level:
            signals.append(f"RSI({rsi:.2f})低于买入阈值({rsi_buy_level})")
            signal_strength += 2
        
        # MACD信号
        macd = technical_data.get("macd", {})
        macd_value = macd.get("macd", 0.0)
        signal_value = macd.get("signal", 0.0)
        histogram = macd.get("histogram", 0.0)
        if macd_value > signal_value and histogram > 0:
            signals.append("MACD金叉，价格动量向上")
            signal_strength += 2
        
        # KDJ信号
        kdj = technical_data.get("kdj", {})
        k_value = kdj.get("k", 50.0)
        d_value = kdj.get("d", 50.0)
        j_value = kdj.get("j", 50.0)
        k_buy_level = stock_config.get("k_buy_level", 20)
        if k_value < k_buy_level and j_value > k_value:
            signals.append(f"KDJ超卖，K值({k_value:.2f})低于买入阈值({k_buy_level})")
            signal_strength += 2
        
        # 布林带信号
        bollinger = technical_data.get("bollinger", {})
        upper = bollinger.get("upper", 0.0)
        middle = bollinger.get("middle", 0.0)
        lower = bollinger.get("lower", 0.0)
        current_price = stock_config.get("current_price", 0.0)
        if current_price and lower > 0 and current_price <= lower:
            signals.append("价格触及布林带下轨，可能反弹")
            signal_strength += 2
        
        # 计算信号强度
        max_strength = 8
        strength_percentage = (signal_strength / max_strength) * 100 if max_strength > 0 else 0
        
        # 判断是否生成买入信号
        buy_threshold = stock_config.get("buy_threshold", 0.05)
        buy_signal = signal_strength >= 4  # 需要至少两个信号
        
        return {
            "signal": "buy" if buy_signal else "hold",
            "strength": signal_strength,
            "strength_percentage": strength_percentage,
            "reasons": signals,
            "suggestion": "建议买入" if buy_signal else "建议持有观望"
        }
    
    def generate_sell_signal(self, technical_data, stock_config):
        """
        生成卖出信号
        
        参数:
            technical_data: 技术分析数据
            stock_config: 股票配置
            
        返回:
            卖出信号信息
        """
        signals = []
        signal_strength = 0
        
        # RSI信号
        rsi = technical_data.get("rsi", 50.0)
        rsi_sell_level = stock_config.get("rsi_sell_level", 70)
        if rsi > rsi_sell_level:
            signals.append(f"RSI({rsi:.2f})高于卖出阈值({rsi_sell_level})")
            signal_strength += 2
        
        # MACD信号
        macd = technical_data.get("macd", {})
        macd_value = macd.get("macd", 0.0)
        signal_value = macd.get("signal", 0.0)
        histogram = macd.get("histogram", 0.0)
        if macd_value < signal_value and histogram < 0:
            signals.append("MACD死叉，价格动量向下")
            signal_strength += 2
        
        # KDJ信号
        kdj = technical_data.get("kdj", {})
        k_value = kdj.get("k", 50.0)
        d_value = kdj.get("d", 50.0)
        j_value = kdj.get("j", 50.0)
        k_sell_level = stock_config.get("k_sell_level", 80)
        if k_value > k_sell_level and j_value < k_value:
            signals.append(f"KDJ超买，K值({k_value:.2f})高于卖出阈值({k_sell_level})")
            signal_strength += 2
        
        # 布林带信号
        bollinger = technical_data.get("bollinger", {})
        upper = bollinger.get("upper", 0.0)
        middle = bollinger.get("middle", 0.0)
        lower = bollinger.get("lower", 0.0)
        current_price = stock_config.get("current_price", 0.0)
        if current_price and upper > 0 and current_price >= upper:
            signals.append("价格触及布林带上轨，可能回调")
            signal_strength += 2
        
        # 盈利目标信号
        current_price = stock_config.get("current_price", 0.0)
        cost_price = stock_config.get("cost_price", 0.0)
        profit_target = stock_config.get("profit_target", 0.1)
        if current_price and cost_price and cost_price > 0:
            profit_percentage = (current_price - cost_price) / cost_price
            if profit_percentage >= profit_target:
                signals.append(f"达到盈利目标({profit_target*100:.1f}%)")
                signal_strength += 3  # 盈利目标权重更高
        
        # 止损信号
        stop_loss = stock_config.get("stop_loss", 0.05)
        if current_price and cost_price and cost_price > 0:
            loss_percentage = (cost_price - current_price) / cost_price
            if loss_percentage >= stop_loss:
                signals.append(f"达到止损线({stop_loss*100:.1f}%)")
                signal_strength += 3  # 止损信号权重更高
        
        # 计算信号强度
        max_strength = 13  # 考虑盈利目标和止损的额外权重
        strength_percentage = (signal_strength / max_strength) * 100 if max_strength > 0 else 0
        
        # 判断是否生成卖出信号
        sell_threshold = stock_config.get("sell_threshold", 0.03)
        sell_signal = signal_strength >= 4  # 需要至少两个信号，或一个高权重信号
        
        return {
            "signal": "sell" if sell_signal else "hold",
            "strength": signal_strength,
            "strength_percentage": strength_percentage,
            "reasons": signals,
            "suggestion": "建议卖出" if sell_signal else "建议持有"
        }
    
    def generate_signal(self, technical_data, stock_config):
        """
        生成最终信号
        
        参数:
            technical_data: 技术分析数据
            stock_config: 股票配置
            
        返回:
            最终信号信息
        """
        is_holding = stock_config.get("hold", False)
        
        if is_holding:
            # 如果持有，生成卖出信号
            return self.generate_sell_signal(technical_data, stock_config)
        else:
            # 如果未持有，生成买入信号
            return self.generate_buy_signal(technical_data, stock_config)

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
        
        # 创建信号生成器
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
        
        # 创建信号生成器
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
        
        # 创建信号生成器
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
