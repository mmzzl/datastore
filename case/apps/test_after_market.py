"""
盘后分析测试脚本
用于测试各项功能是否正常
"""

import logging
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from after_market_analysis import AfterMarketAnalysisService, DingTalkNotifier, StockAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def test_database_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("测试1: 数据库连接")
    print("=" * 60)

    service = AfterMarketAnalysisService()
    analyzer = service.analyzer

    if analyzer.connect():
        print("✅ 数据库连接成功")

        # 获取最新日期
        latest_date = analyzer.get_latest_date()
        print(f"✅ 最新日期: {latest_date}")

        # 获取股票数量
        stock_list = analyzer.get_stock_list()
        print(f"✅ 股票总数: {len(stock_list)} 只")

        analyzer.disconnect()
        return True
    else:
        print("❌ 数据库连接失败")
        return False


def test_market_analysis():
    """测试市场分析"""
    print("\n" + "=" * 60)
    print("测试2: 市场分析")
    print("=" * 60)

    service = AfterMarketAnalysisService()
    analyzer = service.analyzer

    if not analyzer.connect():
        print("❌ 数据库连接失败")
        return False

    try:
        # 获取最新日期
        date = analyzer.get_latest_date()
        if not date:
            print("❌ 无法获取最新日期")
            analyzer.disconnect()
            return False

        print(f"分析日期: {date}")

        # 市场概览
        overview = analyzer.analyze_market_overview(date)
        if overview:
            print("\n市场概览:")
            print(f"  股票总数: {overview.get('total_stocks', 0)}")
            print(f"  上涨: {overview.get('up_stocks', 0)}")
            print(f"  下跌: {overview.get('down_stocks', 0)}")
            print(f"  平盘: {overview.get('flat_stocks', 0)}")
            print(f"  平均涨跌幅: {overview.get('avg_change', 0)}%")
            print(f"  总成交额: {overview.get('total_amount', 0)} 亿元")
            print("✅ 市场概览分析成功")
        else:
            print("❌ 市场概览分析失败")

        # 表现最佳股票
        top_performers = analyzer.analyze_top_performers(date, top_n=5)
        if top_performers:
            print("\n涨幅榜TOP5:")
            for idx, stock in enumerate(top_performers.get('top_gainers', [])[:5], 1):
                print(f"  {idx}. {stock.get('code')} {stock.get('name')} +{stock.get('pct_chg')}%")
            print("✅ 表现最佳股票分析成功")
        else:
            print("❌ 表现最佳股票分析失败")

        analyzer.disconnect()
        return True

    except Exception as e:
        print(f"❌ 市场分析失败: {e}")
        analyzer.disconnect()
        return False


def test_dingtalk_notification():
    """测试钉钉通知"""
    print("\n" + "=" * 60)
    print("测试3: 钉钉通知")
    print("=" * 60)

    service = AfterMarketAnalysisService()
    notifier = service.notifier

    # 检查配置
    if not notifier.webhook:
        print("⚠️  未配置钉钉webhook，跳过测试")
        return True

    print(f"Webhook: {notifier.webhook[:50]}...")
    print(f"Secret: {'已配置' if notifier.secret else '未配置'}")

    # 发送测试消息
    test_title = "🧪 盘后分析测试消息"
    test_text = f"""# 测试消息

这是一条测试消息，用于验证钉钉机器人配置是否正确。

- 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 消息类型: Markdown

如果收到此消息，说明配置正确！
"""

    print("正在发送测试消息...")
    success = notifier.send_markdown(test_title, test_text)

    if success:
        print("✅ 钉钉消息发送成功")
        return True
    else:
        print("❌ 钉钉消息发送失败")
        return False


def test_full_analysis():
    """测试完整分析流程"""
    print("\n" + "=" * 60)
    print("测试4: 完整分析流程")
    print("=" * 60)

    service = AfterMarketAnalysisService()

    # 检查配置
    if not service.after_market_config.get('dingtalk_webhook'):
        print("⚠️  未配置钉钉webhook，将跳过发送通知")
    else:
        print(f"钉钉webhook: 已配置")

    print("开始执行完整分析...")

    try:
        service.run_analysis()
        print("✅ 完整分析流程执行成功")
        return True
    except Exception as e:
        print(f"❌ 完整分析流程执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_report_generation():
    """测试报告生成"""
    print("\n" + "=" * 60)
    print("测试5: 报告生成")
    print("=" * 60)

    # 模拟数据
    mock_overview = {
        'date': '2024-03-10',
        'total_stocks': 5000,
        'up_stocks': 2500,
        'down_stocks': 2000,
        'flat_stocks': 500,
        'limit_up': 30,
        'limit_down': 10,
        'avg_change': 0.5,
        'median_change': 0.3,
        'total_amount': 5000,
        'avg_amplitude': 3.2
    }

    mock_top_performers = {
        'top_gainers': [
            {'code': '000001', 'name': '测试股票', 'close': 10.75, 'pct_chg': 10.02, 'amount': 50.5}
        ],
        'top_losers': [
            {'code': '000002', 'name': '测试股票', 'close': 8.50, 'pct_chg': -9.98, 'amount': 30.2}
        ],
        'top_volume': [
            {'code': '600000', 'name': '测试股票', 'close': 9.80, 'pct_chg': 2.08, 'amount': 100.5}
        ]
    }

    mock_sector_performance = {
        'sector_performance': [
            {'sector': '测试行业', 'avg_change': 2.5, 'median_change': 2.0, 'stock_count': 100, 'total_amount': 500}
        ]
    }

    service = AfterMarketAnalysisService()

    try:
        report = service._generate_report(
            date='2024-03-10',
            market_overview=mock_overview,
            top_performers=mock_top_performers,
            sector_performance=mock_sector_performance
        )

        print("\n生成的报告:")
        print("-" * 60)
        print(report)
        print("-" * 60)
        print("✅ 报告生成成功")
        return True

    except Exception as e:
        print(f"❌ 报告生成失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "盘后分析测试套件" + " " * 23 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    tests = [
        ("数据库连接", test_database_connection),
        ("市场分析", test_market_analysis),
        ("钉钉通知", test_dingtalk_notification),
        ("完整分析流程", test_full_analysis),
        ("报告生成", test_report_generation),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试 '{test_name}' 异常: {e}")
            results.append((test_name, False))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20s} {status}")

    total = len(results)
    passed = sum(1 for _, result in results if result)
    failed = total - passed

    print("-" * 60)
    print(f"总计: {total} 项, 通过: {passed} 项, 失败: {failed} 项")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
