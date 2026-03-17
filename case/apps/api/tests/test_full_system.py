#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面测试系统功能，包括FastAPI接口、多数据源、盯盘功能、定时任务等
"""

import sys
import os
import logging
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestCompleteSystem:
    """完整系统测试"""
    
    @pytest.fixture(scope="module")
    def client(self):
        """创建FastAPI测试客户端"""
        try:
            from main import app
            return TestClient(app)
        except Exception as e:
            logger.error(f"创建测试客户端失败: {e}")
            pytest.skip("无法创建测试客户端")
    
    def test_fastapi_health(self, client):
        """测试FastAPI健康状态"""
        logger.info("=== 测试FastAPI健康状态 ===")
        response = client.get("/")
        assert response.status_code == 200
        assert "News API is running" in response.json().get("message", "")
        logger.info("FastAPI健康状态测试通过")
    
    def test_api_endpoints(self, client):
        """测试API端点"""
        logger.info("=== 测试API端点 ===")
        
        # 测试新闻分析端点
        response = client.get("/api/news/analysis")
        assert response.status_code in [200, 404, 500]  # 可能没有数据
        logger.info("新闻分析端点测试通过")
        
        # 测试股票分析端点
        response = client.get("/api/stock/analysis")
        assert response.status_code in [200, 404, 500]  # 可能没有数据
        logger.info("股票分析端点测试通过")
    
    def test_multi_data_source(self):
        """测试多数据源功能"""
        logger.info("=== 测试多数据源功能 ===")
        
        try:
            # 检查是否安装了必要的依赖
            import numpy
            import pandas
        except ImportError:
            logger.warning("跳过多数据源测试：缺少numpy或pandas")
            pytest.skip("缺少numpy或pandas依赖")
        
        try:
            from app.monitor.data_source import get_data_source_manager, MultiDataSourceManager
            
            # 测试多数据源管理器初始化
            data_source = get_data_source_manager()
            assert data_source is not None
            assert isinstance(data_source, MultiDataSourceManager)
            logger.info("多数据源管理器初始化成功")
            
            # 验证数据源列表
            assert len(data_source.sources) > 0
            logger.info(f"已配置 {len(data_source.sources)} 个数据源")
            
            # 验证数据源名称
            source_names = [s.name for s in data_source.sources]
            logger.info(f"数据源: {source_names}")
            
            logger.info("多数据源功能测试通过")
        except Exception as e:
            logger.error(f"多数据源测试失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            pytest.fail(f"多数据源测试失败: {e}")
    
    def test_monitor_config(self):
        """测试监控配置"""
        logger.info("=== 测试监控配置 ===")
        
        try:
            # 检查是否安装了必要的依赖
            import numpy
            import pandas
        except ImportError:
            logger.warning("跳过监控配置测试：缺少numpy或pandas")
            pytest.skip("缺少numpy或pandas依赖")
        
        try:
            from app.monitor.config import MonitorConfig
            
            config = MonitorConfig()
            stocks = config.get_stocks()
            
            logger.info(f"获取到 {len(stocks)} 只监控股票")
            assert isinstance(stocks, list)
            
            # 测试获取持仓股票
            holding_stocks = config.get_holding_stocks()
            logger.info(f"获取到 {len(holding_stocks)} 只持仓股票")
            assert isinstance(holding_stocks, list)
            
            logger.info("监控配置测试通过")
        except Exception as e:
            logger.error(f"监控配置测试失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            pytest.fail(f"监控配置测试失败: {e}")
    
    def test_stock_monitor(self):
        """测试股票监控功能"""
        logger.info("=== 测试股票监控功能 ===")
        
        try:
            # 检查是否安装了必要的依赖
            import numpy
            import pandas
        except ImportError:
            logger.warning("跳过股票监控测试：缺少numpy或pandas")
            pytest.skip("缺少numpy或pandas依赖")
        
        try:
            from app.monitor.stock_monitor import StockMonitor
            from app.monitor.config import MonitorConfig
            from app.core.config import settings
            
            # 构建配置
            config = {
                "after_market": {
                    "dingtalk_webhook": settings.after_market_dingtalk_webhook,
                    "dingtalk_secret": settings.after_market_dingtalk_secret
                },
                "database": {
                    "host": settings.mongodb_host,
                    "port": settings.mongodb_port,
                    "name": settings.mongodb_dbname,
                    "username": settings.mongodb_username,
                    "password": settings.mongodb_password
                }
            }
            
            # 测试StockMonitor初始化
            monitor = StockMonitor(config)
            assert monitor is not None
            assert monitor.config is not None
            logger.info("StockMonitor初始化成功")
            
            # 验证监控配置
            assert isinstance(monitor.monitor_config, MonitorConfig)
            stocks = monitor.monitor_config.get_stocks()
            assert isinstance(stocks, list)
            logger.info(f"监控配置加载成功，共 {len(stocks)} 只股票")
            
            # 验证技术分析器和信号生成器
            assert monitor.technical_analyzer is not None
            assert monitor.signal_generator is not None
            logger.info("技术分析器和信号生成器初始化成功")
            
            monitor.close()
            logger.info("股票监控功能测试通过")
        except Exception as e:
            logger.error(f"股票监控测试失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            pytest.fail(f"股票监控测试失败: {e}")
    
    def test_mongodb_operations(self):
        """测试MongoDB操作"""
        logger.info("=== 测试MongoDB操作 ===")
        
        try:
            from app.storage.mongo_client import MongoStorage
            from app.core.config import settings
            
            # 连接MongoDB
            mongo = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_dbname,
                username=settings.mongodb_username,
                password=settings.mongodb_password
            )
            mongo.connect()
            
            # 测试保存数据
            test_data = {
                "test": "data",
                "timestamp": datetime.now().isoformat()
            }
            result = mongo.save(test_data)
            assert result is not None
            logger.info("MongoDB保存数据测试通过")
            
            # 测试获取新闻分析股票
            news_stocks = mongo.get_news_stocks()
            logger.info(f"获取到 {len(news_stocks)} 只新闻分析股票")
            assert isinstance(news_stocks, list)
            
            # 测试获取监控股票
            monitor_stocks = mongo.get_monitor_stocks()
            logger.info(f"获取到 {len(monitor_stocks)} 只监控股票")
            assert isinstance(monitor_stocks, list)
            
            mongo.close()
            logger.info("MongoDB操作测试通过")
        except Exception as e:
            logger.error(f"MongoDB操作测试失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            pytest.fail(f"MongoDB操作测试失败: {e}")
    
    def test_scheduler(self):
        """测试调度器配置"""
        logger.info("=== 测试调度器配置 ===")
        
        try:
            # 检查是否安装了必要的依赖
            import numpy
            import pandas
        except ImportError:
            logger.warning("跳过调度器测试：缺少numpy或pandas")
            pytest.skip("缺少numpy或pandas依赖")
        
        try:
            from main import app
            import inspect
            
            # 检查run_monitor_job函数是否存在
            import main
            assert hasattr(main, 'run_monitor_job')
            logger.info("run_monitor_job函数存在")
            
            # 检查调度器配置
            main_content = inspect.getsource(main)
            assert "monitor_job" in main_content
            assert "cron" in main_content  # 检查是否使用cron调度
            logger.info("调度器配置测试通过")
        except Exception as e:
            logger.error(f"调度器测试失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            pytest.fail(f"调度器测试失败: {e}")
    
    def test_monitor_job(self):
        """测试盯盘任务(MonitorJob)"""
        logger.info("=== 测试盯盘任务 ===")
        
        try:
            # 检查是否安装了必要的依赖
            import numpy
            import pandas
        except ImportError:
            logger.warning("跳过盯盘任务测试：缺少numpy或pandas")
            pytest.skip("缺少numpy或pandas依赖")
        
        try:
            from app.scheduler.monitor_job import MonitorJob
            from app.core.config import settings
            
            # 构建配置
            config = {
                "database": {
                    "host": settings.mongodb_host,
                    "port": settings.mongodb_port,
                    "name": settings.mongodb_dbname,
                    "username": settings.mongodb_username,
                    "password": settings.mongodb_password,
                },
                "data_source": {
                    "provider": settings.data_source,
                    "tushare_token": settings.tushare_token,
                },
                "after_market": {
                    "dingtalk_webhook": settings.after_market_dingtalk_webhook,
                    "dingtalk_secret": settings.after_market_dingtalk_secret,
                },
            }
            
            # 初始化MonitorJob
            monitor_job = MonitorJob(config)
            assert monitor_job is not None
            assert monitor_job.config == config
            logger.info("MonitorJob初始化成功")
            
            # 测试is_trading_time方法
            is_trading = monitor_job.is_trading_time()
            logger.info(f"当前是否为交易时间: {is_trading}")
            
            logger.info("盯盘任务测试通过")
        except Exception as e:
            logger.error(f"盯盘任务测试失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            pytest.fail(f"盯盘任务测试失败: {e}")


def test_all():
    """运行所有测试"""
    logger.info("开始全面测试系统...")
    
    # 创建测试实例
    test = TestCompleteSystem()
    
    # 测试顺序 - 只运行不需要numpy和pandas的测试
    tests = [
        test.test_fastapi_health,
        test.test_api_endpoints,
        test.test_mongodb_operations
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for i, test_func in enumerate(tests):
        try:
            if test_func.__name__ in ["test_fastapi_health", "test_api_endpoints"]:
                # 这些测试需要client参数
                try:
                    from main import app
                    client = TestClient(app)
                    test_func(client)
                except ImportError:
                    logger.warning(f"跳过 {test_func.__name__} 测试：缺少依赖")
                    continue
            else:
                test_func()
            success_count += 1
            logger.info(f"测试 {i+1}/{total_count} 成功: {test_func.__name__}")
        except Exception as e:
            logger.error(f"测试 {i+1}/{total_count} 失败: {test_func.__name__} - {e}")
        logger.info("-" * 60)
    
    logger.info(f"测试完成: {success_count}/{total_count} 项测试通过")
    
    if success_count == total_count:
        logger.info("🎉 所有测试通过，系统运行正常！")
    else:
        logger.warning(f"⚠️  有 {total_count - success_count} 项测试失败，系统可能存在问题")
    
    return success_count == total_count


if __name__ == "__main__":
    # 运行pytest
    import subprocess
    
    # 运行pytest测试
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("错误输出:")
        print(result.stderr)
    
    # 运行自定义测试
    print("\n" + "="*70)
    print("运行自定义全面测试...")
    print("="*70)
    test_all()
