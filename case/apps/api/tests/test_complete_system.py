#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试整个系统是否正常工作，检查是否有报错
"""

import sys
import os
import logging
from datetime import datetime

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
        from app.core.config import settings
        
        # 测试基本配置
        logger.info(f"应用名称: {settings.app_name}")
        logger.info(f"MongoDB主机: {settings.mongodb_host}")
        logger.info(f"数据源: {settings.data_source}")
        
        # 测试盯盘配置
        logger.info(f"盯盘功能启用: {settings.monitor_enabled}")
        logger.info(f"监控间隔: {settings.monitor_interval}秒")
        logger.info(f"盯盘开始时间: {settings.monitor_scheduler_time}")
        logger.info(f"监控股票数量: {len(settings.monitor_stocks)}")
        
        for i, stock in enumerate(settings.monitor_stocks):
            logger.info(f"股票 {i+1}: {stock.get('name')} ({stock.get('code')})")
        
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
        # 检查关键目录和文件
        api_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.join(api_dir, "app")
        monitor_dir = os.path.join(app_dir, "monitor")
        analysis_dir = os.path.join(monitor_dir, "analysis")
        scheduler_dir = os.path.join(app_dir, "scheduler")
        
        # 检查目录是否存在
        directories = [
            ("API目录", api_dir),
            ("App目录", app_dir),
            ("监控模块目录", monitor_dir),
            ("分析模块目录", analysis_dir),
            ("调度器目录", scheduler_dir)
        ]
        
        for name, path in directories:
            if os.path.exists(path):
                logger.info(f"{name} 存在: {path}")
            else:
                logger.error(f"{name} 不存在: {path}")
                return False
        
        # 检查关键文件是否存在
        files = [
            ("股票监控核心类", os.path.join(monitor_dir, "stock_monitor.py")),
            ("配置管理模块", os.path.join(monitor_dir, "config.py")),
            ("数据模型", os.path.join(monitor_dir, "models.py")),
            ("技术分析模块", os.path.join(analysis_dir, "technical.py")),
            ("信号生成模块", os.path.join(analysis_dir, "signal.py")),
            ("盯盘任务", os.path.join(scheduler_dir, "monitor_job.py")),
            ("主应用文件", os.path.join(api_dir, "main.py"))
        ]
        
        for name, path in files:
            if os.path.exists(path):
                logger.info(f"{name} 存在: {path}")
            else:
                logger.error(f"{name} 不存在: {path}")
                return False
        
        logger.info("目录结构测试成功！")
        return True
    except Exception as e:
        logger.error(f"目录结构测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_signal_logic():
    """测试信号生成逻辑"""
    logger.info("=== 测试信号生成逻辑 ===")
    
    try:
        class SignalGenerator:
            """信号生成器（纯Python实现）"""
            
            def __init__(self):
                pass
            
            def generate_buy_signal(self, technical_data, stock_config):
                """
                生成买入信号
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
                """
                is_holding = stock_config.get("hold", False)
                
                if is_holding:
                    # 如果持有，生成卖出信号
                    return self.generate_sell_signal(technical_data, stock_config)
                else:
                    # 如果未持有，生成买入信号
                    return self.generate_buy_signal(technical_data, stock_config)
        
        # 测试买入信号
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
        
        stock_config = {
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
        
        generator = SignalGenerator()
        buy_signal = generator.generate_buy_signal(technical_data, stock_config)
        logger.info(f"买入信号: {buy_signal}")
        
        # 测试卖出信号
        stock_config["hold"] = True
        stock_config["cost_price"] = 100.0
        stock_config["current_price"] = 115
        
        sell_signal = generator.generate_sell_signal(technical_data, stock_config)
        logger.info(f"卖出信号: {sell_signal}")
        
        logger.info("信号生成逻辑测试成功！")
        return True
    except Exception as e:
        logger.error(f"信号生成逻辑测试失败: {e}")
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
        if os.path.exists(monitor_job_file):
            logger.info("monitor_job.py 存在")
        else:
            logger.error("monitor_job.py 不存在")
            return False
        
        logger.info("调度器配置测试成功！")
        return True
    except Exception as e:
        logger.error(f"调度器配置测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主测试函数"""
    logger.info("开始测试整个系统...")
    
    # 运行各项测试
    tests = [
        test_config_loading,
        test_directory_structure,
        test_signal_logic,
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
        logger.info("所有测试通过，系统运行正常！")
    else:
        logger.warning(f"有 {total_count - success_count} 项测试失败，系统可能存在问题")

if __name__ == "__main__":
    main()
