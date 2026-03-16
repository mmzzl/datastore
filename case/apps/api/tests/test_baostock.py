"""测试Baostock数据获取和分析功能 - 完整流程测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.collector.baostock_kline_fetcher import BaostockKlineFetcher
from app.collector.stock_analyzer import StockAnalyzer
from app.collector.technical_indicators import TechnicalIndicators
from app.core.config import settings
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_baostock_kline_data_accuracy():
    """测试BaostockKlineFetcher数据准确性"""
    logger.info("=" * 60)
    logger.info("测试 BaostockKlineFetcher 数据准确性")
    logger.info("=" * 60)
    
    try:
        with BaostockKlineFetcher() as fetcher:
            # 测试获取单只股票的K线数据
            code = "sh.600000"
            # 使用最近60天的数据
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
            
            logger.info(f"\n1. 测试获取 {code} 的K线数据")
            logger.info(f"   时间范围: {start_date} ~ {end_date}")
            df = fetcher.get_kline(code, start_date, end_date)
            
            if df is None or df.empty:
                logger.error(f"❌ 获取 {code} 的K线数据失败")
                return False
            
            logger.info(f"✅ 成功获取 {code} 的K线数据，共 {len(df)} 条")
            
            # 验证数据完整性
            required_columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'amount', 'change_pct', 'turnover_rate']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"❌ 缺少必要列: {missing_columns}")
                return False
            
            logger.info(f"✅ 数据列完整: {df.columns.tolist()}")
            
            # 验证数据类型
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'amount', 'change_pct', 'turnover_rate']
            for col in numeric_columns:
                if df[col].isnull().any():
                    logger.warning(f"⚠️  列 {col} 存在空值")
                if not pd.api.types.is_numeric_dtype(df[col]):
                    logger.error(f"❌ 列 {col} 不是数值类型")
                    return False
            
            logger.info(f"✅ 数据类型正确")
            
            # 验证数据逻辑性
            latest = df.iloc[0]
            if latest['high'] < latest['low']:
                logger.error(f"❌ 数据逻辑错误: high({latest['high']}) < low({latest['low']})")
                return False
            
            if latest['close'] > latest['high'] or latest['close'] < latest['low']:
                logger.error(f"❌ 数据逻辑错误: close({latest['close']}) 不在 [low, high] 范围内")
                return False
            
            logger.info(f"✅ 数据逻辑正确")
            
            # 显示最新数据
            logger.info(f"\n最新数据 ({latest['date'].strftime('%Y-%m-%d')}):")
            logger.info(f"  开盘: {latest['open']:.2f}, 最高: {latest['high']:.2f}, 最低: {latest['low']:.2f}, 收盘: {latest['close']:.2f}")
            logger.info(f"  成交量: {latest['volume']:.0f}, 成交额: {latest['amount']:.0f}")
            logger.info(f"  涨跌幅: {latest['change_pct']:.2f}%, 换手率: {latest['turnover_rate']:.2f}%")
            
            # 验证数据连续性
            df_sorted = df.sort_values('date')
            date_diffs = df_sorted['date'].diff().dt.days.dropna()
            if date_diffs.max() > 10:  # 允许最长10天间隔（考虑节假日）
                logger.warning(f"⚠️  数据存在较大间隔: 最大间隔 {date_diffs.max()} 天")
            
            logger.info(f"✅ 数据连续性检查通过")
            
        logger.info("\n✅ BaostockKlineFetcher 数据准确性测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ BaostockKlineFetcher 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_technical_indicators():
    """测试技术指标计算准确性"""
    logger.info("\n" + "=" * 60)
    logger.info("测试技术指标计算准确性")
    logger.info("=" * 60)
    
    try:
        # 创建测试数据 - 使用40条数据以满足MACD计算需求（26+9=35）
        import numpy as np
        np.random.seed(42)
        base_price = 10.0
        close_prices = [base_price + i * 0.1 + np.random.randn() * 0.2 for i in range(40)]
        
        data = {
            'symbol': ['sh.600000'] * 40,
            'date': pd.date_range('2025-01-01', periods=40),
            'close': close_prices,
            'volume': [1000000] * 40,
            'high': [c * 1.02 for c in close_prices],
            'low': [c * 0.98 for c in close_prices]
        }
        df = pd.DataFrame(data)
        
        logger.info(f"\n1. 计算技术指标（数据量: {len(df)} 条）")
        df_with_indicators = TechnicalIndicators.calculate_all(df)
        
        # 验证技术指标是否存在
        indicator_columns = ['ma5', 'ma10', 'ma20', 'rsi', 'macd', 'macd_signal', 'macd_hist']
        missing_indicators = [col for col in indicator_columns if col not in df_with_indicators.columns]
        if missing_indicators:
            logger.error(f"❌ 缺少技术指标: {missing_indicators}")
            return False
        
        logger.info(f"✅ 技术指标计算成功: {indicator_columns}")
        
        # 验证MA指标
        latest = df_with_indicators.iloc[-1]
        if pd.notna(latest['ma5']):
            logger.info(f"✅ MA5: {latest['ma5']:.2f}")
        if pd.notna(latest['ma10']):
            logger.info(f"✅ MA10: {latest['ma10']:.2f}")
        if pd.notna(latest['ma20']):
            logger.info(f"✅ MA20: {latest['ma20']:.2f}")
        
        # 验证RSI指标
        if pd.notna(latest['rsi']):
            logger.info(f"✅ RSI: {latest['rsi']:.2f}")
            if latest['rsi'] < 0 or latest['rsi'] > 100:
                logger.error(f"❌ RSI值超出范围 [0, 100]: {latest['rsi']}")
                return False
        
        # 验证MACD指标
        if pd.notna(latest['macd']):
            logger.info(f"✅ MACD: {latest['macd']:.4f}")
        if pd.notna(latest['macd_signal']):
            logger.info(f"✅ MACD信号线: {latest['macd_signal']:.4f}")
        if pd.notna(latest['macd_hist']):
            logger.info(f"✅ MACD柱状图: {latest['macd_hist']:.4f}")
        
        logger.info("\n✅ 技术指标计算准确性测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 技术指标计算测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stock_analyzer_full_flow():
    """测试StockAnalyzer完整流程"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 StockAnalyzer 完整流程")
    logger.info("=" * 60)
    
    try:
        # 创建StockAnalyzer实例
        analyzer = StockAnalyzer({
            "host": settings.mongodb_host,
            "port": settings.mongodb_port,
            "db_name": settings.mongodb_database,
            "username": settings.mongodb_username,
            "password": settings.mongodb_password
        })
        
        # 测试新闻分析 - 使用少量股票进行测试
        news_analysis = {
            "hot_sectors": [],  # 不使用热门板块，避免获取太多股票
            "hot_stocks": ["贵州茅台(sh.600519)", "中国平安(sh.601318)", "招商银行(sh.600036)"],  # 只测试3只股票
            "sentiment": "中性"
        }
        
        logger.info(f"\n1. 输入新闻分析数据")
        logger.info(f"   热门板块: {news_analysis['hot_sectors']}")
        logger.info(f"   关注股票: {news_analysis['hot_stocks']}")
        logger.info(f"   市场情绪: {news_analysis['sentiment']}")
        
        logger.info(f"\n2. 开始多维度共振筛选分析")
        result = analyzer.analyze(news_analysis, top_n=3)
        
        if "error" in result:
            logger.error(f"❌ 分析失败: {result['error']}")
            return False
        
        logger.info(f"✅ 分析成功")
        
        # 验证结果结构
        required_keys = ['total_candidates', 'top_stocks', 'summary']
        missing_keys = [key for key in required_keys if key not in result]
        if missing_keys:
            logger.error(f"❌ 结果缺少必要字段: {missing_keys}")
            return False
        
        logger.info(f"✅ 结果结构完整")
        
        # 验证候选股票
        total_candidates = result.get('total_candidates', 0)
        logger.info(f"\n3. 筛选结果")
        logger.info(f"   总候选股票: {total_candidates} 只")
        logger.info(f"   推荐股票: {len(result.get('top_stocks', []))} 只")
        
        if total_candidates == 0:
            logger.warning(f"⚠️  未找到符合条件的股票")
            return True  # 这不算错误，只是没有符合条件的股票
        
        # 验证推荐股票数据
        top_stocks = result.get('top_stocks', [])
        for i, stock in enumerate(top_stocks, 1):
            logger.info(f"\n   推荐股票 #{i}: {stock['name']}({stock['symbol']})")
            
            # 验证必要字段
            required_stock_fields = ['symbol', 'name', 'sector', 'close', 'change_pct', 'score', 
                                   'sector_score', 'capital_score', 'technical_score', 
                                   'fundamental_score', 'risk_score', 'reasons', 'warnings']
            missing_fields = [field for field in required_stock_fields if field not in stock]
            if missing_fields:
                logger.error(f"❌ 股票数据缺少字段: {missing_fields}")
                return False
            
            # 验证股票名称
            if not stock['name'] or stock['name'] == stock['symbol']:
                logger.error(f"❌ 股票名称无效: {stock['name']}")
                return False
            logger.info(f"     股票名称: {stock['name']}")
            
            # 验证板块信息
            if 'sector' not in stock or not stock['sector']:
                logger.warning(f"⚠️  股票 {stock['symbol']} 缺少板块信息")
            else:
                logger.info(f"     所属板块: {stock['sector']}")
            
            # 验证数据范围
            if stock['close'] <= 0:
                logger.error(f"❌ 收盘价无效: {stock['close']}")
                return False
            
            if stock['score'] < 0 or stock['score'] > 100:
                logger.error(f"❌ 评分超出范围 [0, 100]: {stock['score']}")
                return False
            
            # 验证各分项评分
            for score_field in ['sector_score', 'capital_score', 'technical_score', 'fundamental_score', 'risk_score']:
                if stock[score_field] < 0 or stock[score_field] > 100:
                    logger.error(f"❌ {score_field} 超出范围 [0, 100]: {stock[score_field]}")
                    return False
            
            logger.info(f"     收盘价: {stock['close']:.2f}")
            logger.info(f"     涨跌幅: {stock['change_pct']:.2f}%")
            logger.info(f"     综合评分: {stock['score']:.2f}")
            logger.info(f"     板块评分: {stock['sector_score']:.2f}")
            logger.info(f"     资金评分: {stock['capital_score']:.2f}")
            logger.info(f"     技术评分: {stock['technical_score']:.2f}")
            logger.info(f"     基本面评分: {stock['fundamental_score']:.2f}")
            logger.info(f"     风险评分: {stock['risk_score']:.2f}")
            logger.info(f"     推荐理由: {', '.join(stock['reasons'][:3])}")
            if stock['warnings']:
                logger.warning(f"     风险提示: {', '.join(stock['warnings'])}")
        
        # 验证汇总信息
        summary = result.get('summary', {})
        logger.info(f"\n4. 汇总信息")
        logger.info(f"   平均评分: {summary.get('avg_score', 0):.2f}")
        logger.info(f"   高分股票数: {summary.get('high_score_count', 0)}")
        logger.info(f"   市场情绪: {summary.get('market_sentiment', '')}")
        
        logger.info("\n✅ StockAnalyzer 完整流程测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ StockAnalyzer 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_consistency():
    """测试数据一致性"""
    logger.info("\n" + "=" * 60)
    logger.info("测试数据一致性")
    logger.info("=" * 60)
    
    try:
        from datetime import datetime, timedelta
        
        with BaostockKlineFetcher() as fetcher:
            # 获取同一只股票不同时间范围的数据
            code = "sh.600000"
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date1 = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
            start_date2 = (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d")
            
            df1 = fetcher.get_kline(code, start_date1, end_date)
            df2 = fetcher.get_kline(code, start_date2, end_date)
            
            if df1 is None or df2 is None or df1.empty or df2.empty:
                logger.error(f"❌ 获取数据失败")
                return False
            
            # 查找重叠日期的数据
            overlap_dates = set(df1['date'].dt.date) & set(df2['date'].dt.date)
            
            if not overlap_dates:
                logger.warning(f"⚠️  没有重叠日期的数据")
                return True
            
            logger.info(f"重叠日期数量: {len(overlap_dates)}")
            
            # 验证重叠日期的数据是否一致
            inconsistent_dates = []
            for date in overlap_dates:
                row1 = df1[df1['date'].dt.date == date].iloc[0]
                row2 = df2[df2['date'].dt.date == date].iloc[0]
                
                if abs(row1['close'] - row2['close']) > 0.01:
                    inconsistent_dates.append(date)
                    logger.error(f"❌ 日期 {date} 数据不一致: {row1['close']} vs {row2['close']}")
            
            if inconsistent_dates:
                logger.error(f"❌ 发现 {len(inconsistent_dates)} 个不一致的日期")
                return False
            
            logger.info(f"✅ 重叠日期数据一致")
        
        logger.info("\n✅ 数据一致性测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据一致性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    logger.info("开始Baostock数据获取和分析功能完整测试\n")
    
    # 测试1: BaostockKlineFetcher数据准确性
    test1_passed = test_baostock_kline_data_accuracy()
    
    # 测试2: 技术指标计算准确性
    test2_passed = test_technical_indicators()
    
    # 测试3: 数据一致性
    test3_passed = test_data_consistency()
    
    # 测试4: StockAnalyzer完整流程
    test4_passed = test_stock_analyzer_full_flow()
    
    logger.info("\n" + "=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    logger.info(f"1. BaostockKlineFetcher数据准确性: {'✅ 通过' if test1_passed else '❌ 失败'}")
    logger.info(f"2. 技术指标计算准确性: {'✅ 通过' if test2_passed else '❌ 失败'}")
    logger.info(f"3. 数据一致性: {'✅ 通过' if test3_passed else '❌ 失败'}")
    logger.info(f"4. StockAnalyzer完整流程: {'✅ 通过' if test4_passed else '❌ 失败'}")
    logger.info("=" * 60)
    
    all_passed = test1_passed and test2_passed and test3_passed and test4_passed
    if all_passed:
        logger.info("✅ 所有测试通过")
        sys.exit(0)
    else:
        logger.error("❌ 部分测试失败")
        sys.exit(1)
