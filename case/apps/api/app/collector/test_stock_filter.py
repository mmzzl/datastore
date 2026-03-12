"""股票批量筛选示例 - 从6000+只股票中筛选最值得买的"""

from typing import Dict
from datetime import datetime

# 导入配置
try:
    from app.core.config import settings

    mongodb_config = {
        "host": settings.mongodb_host,
        "port": settings.mongodb_port,
        "db_name": settings.mongodb_database,
        "username": settings.mongodb_username,
        "password": settings.mongodb_password,
    }
except:
    # 测试配置
    mongodb_config = {
        "host": "localhost",
        "port": 27017,
        "db_name": "stock_db",
        "username": "",
        "password": "",
    }


def example_filter_by_hot_sectors():
    """示例：根据热门板块筛选股票"""
    from app.collector.stock_analyzer import StockAnalyzer

    # 模拟新闻分析结果
    news_analysis = {
        "summary": "中东局势紧张推升能源价格，国际释放战略储备平抑油价，国内科技与新能源板块受关注。",
        "hot_sectors": ["能源/油气", "储能/固态电池", "人工智能/金融科技"],
        "hot_stocks": ["中国能建", "雄韬股份", "甲骨文（美股）"],
        "sentiment": "中性偏利好",
        "tomorrow_strategy": {
            "direction": "震荡",
            "attention": "能源板块、固态电池及AI应用",
            "risk": "中东局势反复可能引发油价剧烈波动",
        },
        "key_events": ["美国称对伊朗军事行动将结束"],
    }

    # 创建分析器
    analyzer = StockAnalyzer(mongodb_config)

    # 执行分析（默认使用规则筛选）
    result = analyzer.analyze(news_analysis, llm_client=None, top_n=5)

    print("=" * 60)
    print("股票筛选结果")
    print("=" * 60)

    if "error" in result:
        print(f"错误: {result['error']}")
    else:
        total = result.get("total_analyzed", 0)
        candidates = result.get("total_candidates", 0)
        print(f"分析股票总数: {total}")
        print(f"符合条件股票数: {candidates}")
        print()

        top_stocks = result.get("top_stocks", [])
        if top_stocks:
            print("最值得买的股票（Top 5）:")
            print("-" * 60)
            for i, stock in enumerate(top_stocks, 1):
                print(
                    f"{i}. {stock['symbol']} | "
                    f"收盘: {stock['close']:.2f} | "
                    f"涨幅: {stock['change_pct']:.2f}% | "
                    f"RSI: {stock['rsi']:.1f} | "
                    f"MA5: {stock['ma5']:.2f} | "
                    f"MA10: {stock['ma10']:.2f} | "
                    f"得分: {stock['score']:.2f} | "
                    f"行业: {stock.get('industry', 'N/A')}"
                )

    return result


def example_filter_all_stocks():
    """示例：从全部股票中筛选（前500只）"""
    from app.collector.stock_batch_filter import StockBatchFilter

    # 创建批量筛选器
    filterer = StockBatchFilter(mongodb_config)

    # 热门行业（不需要映射，直接搜索全部股票）
    hot_sectors = ["能源", "储能", "人工智能"]

    # 执行筛选
    result = filterer.filter_top_stocks(hot_sectors, top_n=10)

    print("=" * 60)
    print("批量筛选结果（从500只股票中）")
    print("=" * 60)

    if "error" in result:
        print(f"错误: {result['error']}")
    else:
        total = result.get("total_analyzed", 0)
        candidates = result.get("total_candidates", 0)
        print(f"分析股票总数: {total}")
        print(f"符合条件股票数: {candidates}")
        print()

        top_stocks = result.get("top_stocks", [])
        if top_stocks:
            print("最值得买的股票（Top 10）:")
            print("-" * 60)
            for i, stock in enumerate(top_stocks, 1):
                print(
                    f"{i}. {stock['symbol']} | "
                    f"收盘: {stock['close']:.2f} | "
                    f"涨幅: {stock['change_pct']:.2f}% | "
                    f"RSI: {stock['rsi']:.1f} | "
                    f"得分: {stock['score']:.2f} | "
                    f"行业: {stock.get('industry', 'N/A')}"
                )

    return result


if __name__ == "__main__":
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 示例1: 根据热门板块筛选
    example_filter_by_hot_sectors()

    print()
    print("=" * 60)
    print()

    # 示例2: 从全部股票筛选
    # example_filter_all_stocks()
