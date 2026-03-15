#!/usr/bin/env python3
"""
akShare客户端问题诊断脚本
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目路径
project_root = Path("D:\work\datastore\case\apps")
sys.path.insert(0, str(project_root / "api"))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_akshare_client():
    """测试akShare客户端"""
    try:
        logger.info("开始测试akShare客户端...")
        
        # 导入相关模块
        from app.collector.akshare_client import AkshareClient
        from app.collector.stock_data_fetcher import StockDataFetcher
        
        logger.info("模块导入成功")
        
        # 测试数据获取器
        logger.info("测试StockDataFetcher...")
        fetcher = StockDataFetcher()
        
        # 获取最近的数据
        import datetime
        target_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        logger.info(f"目标日期: {target_date}")
        
        data = fetcher.load_daily_data(target_date)
        
        if data is None or data.empty:
            logger.error("获取数据失败或数据为空")
            return False
        
        logger.info(f"获取数据成功，数据形状: {data.shape}")
        logger.info(f"数据列名: {list(data.columns)}")
        logger.info(f"数据前5行:\n{data.head()}")
        
        # 测试akShare客户端
        logger.info("测试AkshareClient...")
        client = AkshareClient(target_date)
        
        # 测试市场分析
        market_analysis = client.analyze_market()
        logger.info(f"市场分析结果: {market_analysis}")
        
        # 测试简报生成
        brief = client.generate_brief()
        logger.info(f"每日简报: {brief}")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        return False

def test_stock_data_fetcher():
    """测试股票数据获取器"""
    try:
        logger.info("详细测试StockDataFetcher...")
        
        from app.collector.stock_data_fetcher import StockDataFetcher
        
        fetcher = StockDataFetcher()
        
        # 测试各种方法
        methods = [
            ('load_daily_data', '2024-01-15'),
            ('load_kline_data', 'sh600000', '2024-01-01', '2024-01-15'),
        ]
        
        for method_info in methods:
            method_name = method_info[0]
            args = method_info[1:]
            
            try:
                method = getattr(fetcher, method_name)
                result = method(*args)
                
                if result is None:
                    logger.warning(f"{method_name} 返回 None")
                elif hasattr(result, 'shape'):
                    logger.info(f"{method_name} 成功，数据形状: {result.shape}")
                else:
                    logger.info(f"{method_name} 成功，结果类型: {type(result)}")
                    
            except Exception as e:
                logger.error(f"{method_name} 失败: {e}")
                
        return True
        
    except Exception as e:
        logger.error(f"StockDataFetcher测试失败: {e}", exc_info=True)
        return False

def check_dependencies():
    """检查依赖包"""
    logger.info("检查依赖包...")
    
    required_packages = [
        'akshare',
        'pandas',
        'numpy',
        'requests',
        'baostock',
        'pymongo'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✓ {package}")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"✗ {package} 未安装")
    
    if missing_packages:
        logger.error(f"缺少依赖包: {missing_packages}")
        return False
    
    logger.info("所有依赖包检查通过")
    return True

def analyze_industry_data():
    """分析行业数据"""
    try:
        logger.info("分析行业数据...")
        
        # 检查行业数据文件
        industry_csv_path = Path("D:\work\datastore\case\apps\api\data\all_st006_industry.csv")
        stock_industry_path = Path("D:\work\datastore\case\apps\api\data\stock_industry.csv")
        
        if industry_csv_path.exists():
            import pandas as pd
            df = pd.read_csv(industry_csv_path, nrows=10)
            logger.info(f"all_stock_industry.csv 前10行:\n{df}")
            logger.info(f"列名: {list(df.columns)}")
            logger.info(f"数据形状: {df.shape}")
        else:
            logger.warning(f"文件不存在: {industry_csv_path}")
        
        if stock_industry_path.exists():
            import pandas as pd
            df = pd.read_csv(stock_industry_path, nrows=10)
            logger.info(f"stock_industry.csv 前10行:\n{df}")
            logger.info(f"列名: {list(df.columns)}")
            logger.info(f"数据形状: {df.shape}")
        else:
            logger.warning(f"文件不存在: {stock_industry_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"行业数据分析失败: {e}", exc_info=True)
        return False

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("akShare客户端问题诊断")
    logger.info("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        logger.error("依赖检查失败，请先安装缺失的包")
        return
    
    # 分析行业数据
    analyze_industry_data()
    
    # 测试股票数据获取器
    test_st5ock_data_fetcher()
    
    # 测试akShare客户端
    success = test_akshare_client()
    
    if success:
        logger.info("✅ 所有测试通过")
    else:
        logger.error("❌ 测试失败，需要修复问题")
    
    logger.info("=" * 60)
    logger.info("诊断完成")

if __name__ == "__main__":
    main()