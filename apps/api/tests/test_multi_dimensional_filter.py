#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试多维度共振筛选功能"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.collector.stock_analyzer import StockAnalyzer


def test_multi_dimensional_filter():
    """测试多维度共振筛选"""
    print("开始测试多维度共振筛选...")

    mongodb_config = {
        "host": "121.37.47.63",
        "port": 27017,
        "db_name": "eastmoney_news",
        "username": "admin",
        "password": "aa123aaqqA!",
    }

    analyzer = StockAnalyzer(mongodb_config)

    news_analysis = {
        "summary": "地缘冲突持续升级， 美伊紧张局势推高油价；公募信披新规强化透明度，港交所改革提升市场吸引力；AI芯片出口管制草案撤回，科技板块 情绪改善。",
        "hot_sectors": ["无人机", "人工智能", "网络安全", "IPO受益"],
        "hot_concepts": ["HALO资产", "基民盈利比", "霍尔木兹海峡"],
        "hot_stocks": ["海康威视", "大华股份", "中兴通讯", "浪潮信息", "中科曙光"],
        "sentiment": "中性",
        "tomorrow_strategy": {
            "direction": "震荡",
            "attention": "关注地缘冲突对能源、航运板块影响及科技股情绪修复。",
            "risk": "地缘局势不确定性高，市场波动可能加剧，注意避险。",
        },
        "key_events": [
            " 美伊冲突持续，霍尔木兹海峡航运受阻",
            "美国撤回AI芯片出口管制草案",
            "港交所拟放宽上市门槛",
        ],
    }

    try:
        result = analyzer.analyze(news_analysis, top_n=10)
        print(result)
        print("\n" + "=" * 80)
        print("多维度共振筛选结果")
        print("=" * 80)

        if "error" in result:
            print(f"错误: {result['error']}")
            return False

        print(f"\n总候选数: {result.get('total_candidates', 0)}")
        print(f"\n前10名股票:")
        print("-" * 80)

        for i, stock in enumerate(result.get("top_stocks", []), 1):
            print(f"\n{i}. {stock['symbol']} ({stock['name']})")
            print(f"   收盘价: {stock['close']}")
            print(f"   涨跌幅: {stock['change_pct']}%")
            print(f"   综合得分: {stock['score']}")
            print(f"   板块得分: {stock['sector_score']}")
            print(f"   资金得分: {stock['capital_score']}")
            print(f"   技术得分: {stock['technical_score']}")
            print(f"   基本面得分: {stock['fundamental_score']}")
            print(f"   风险得分: {stock['risk_score']}")
            if stock.get("reasons"):
                print(f"   优势: {', '.join(stock['reasons'])}")
            if stock.get("warnings"):
                print(f"   警告: {', '.join(stock['warnings'])}")

        summary = result.get("summary", {})
        print("\n" + "=" * 80)
        print("分析摘要")
        print("=" * 80)
        print(f"\n{summary.get('message', '')}")
        print(f"平均得分: {summary.get('avg_score', 0)}")
        print(f"高分股票数: {summary.get('high_score_count', 0)}")
        print(f"热门板块: {', '.join(summary.get('hot_sectors', []))}")
        print(f"市场情绪: {summary.get('market_sentiment', '')}")
        print(f"\n{summary.get('disclaimer', '')}")

        return True

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_multi_dimensional_filter()
    sys.exit(0 if success else 1)
