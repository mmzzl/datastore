"""
盘后数据分析服务
执行盘后数据分析并发送到钉钉机器人
"""

import logging
import requests
import json
import hmac
import hashlib
import base64
import time
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import yaml
import os

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class DingTalkNotifier:
    """钉钉机器人通知类"""

    def __init__(self, webhook: str, secret: str = None):
        """
        初始化钉钉机器人

        Args:
            webhook: 钉钉机器人webhook地址
            secret: 钉钉机器人加签密钥（可选）
        """
        self.webhook = webhook
        self.secret = secret

    def _generate_sign(self, timestamp: int, secret: str) -> str:
        """生成钉钉机器人签名"""
        secret_enc = secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return sign

    def send_markdown(self, title: str, text: str) -> bool:
        """
        发送markdown格式的消息

        Args:
            title: 消息标题
            text: markdown格式的内容

        Returns:
            bool: 是否发送成功
        """
        try:
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": text
                }
            }

            # 如果有密钥，添加签名
            if self.secret:
                timestamp = int(time.time() * 1000)
                sign = self._generate_sign(timestamp, self.secret)
                url = f"{self.webhook}&timestamp={timestamp}&sign={sign}"
            else:
                url = self.webhook

            headers = {'Content-Type': 'application/json;charset=utf-8'}
            response = requests.post(url, headers=headers, data=json.dumps(data, ensure_ascii=False))

            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.info("钉钉消息发送成功")
                    return True
                else:
                    logger.error(f"钉钉消息发送失败: {result.get('errmsg')}")
                    return False
            else:
                logger.error(f"钉钉消息发送失败: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"发送钉钉消息异常: {e}")
            return False

    def send_text(self, content: str) -> bool:
        """
        发送纯文本消息

        Args:
            content: 消息内容

        Returns:
            bool: 是否发送成功
        """
        try:
            data = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }

            if self.secret:
                timestamp = int(time.time() * 1000)
                sign = self._generate_sign(timestamp, self.secret)
                url = f"{self.webhook}&timestamp={timestamp}&sign={sign}"
            else:
                url = self.webhook

            headers = {'Content-Type': 'application/json;charset=utf-8'}
            response = requests.post(url, headers=headers, data=json.dumps(data, ensure_ascii=False))

            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.info("钉钉消息发送成功")
                    return True
                else:
                    logger.error(f"钉钉消息发送失败: {result.get('errmsg')}")
                    return False
            else:
                logger.error(f"钉钉消息发送失败: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"发送钉钉消息异常: {e}")
            return False


class StockAnalyzer:
    """股票数据分析器"""

    def __init__(self, mongodb_config: Dict):
        """
        初始化分析器

        Args:
            mongodb_config: MongoDB配置字典
        """
        self.mongodb_config = mongodb_config
        self.client = None
        self.db = None
        self.kline_collection = None

    def connect(self):
        """连接MongoDB"""
        try:
            self.client = MongoClient(
                host=self.mongodb_config.get('host', 'localhost'),
                port=self.mongodb_config.get('port', 27017),
                username=self.mongodb_config.get('username', ''),
                password=self.mongodb_config.get('password', ''),
                serverSelectionTimeoutMS=5000
            )
            # 测试连接
            self.client.server_info()

            self.db = self.client[self.mongodb_config.get('database', 'eastmoney_news')]
            self.kline_collection = self.db.get('stock_kline', self.db.get('kline', self.db['stocks']))

            logger.info(f"MongoDB连接成功: {self.mongodb_config.get('host')}:{self.mongodb_config.get('port')}")
            return True

        except ConnectionFailure as e:
            logger.error(f"MongoDB连接失败: {e}")
            return False
        except Exception as e:
            logger.error(f"MongoDB连接异常: {e}")
            return False

    def disconnect(self):
        """断开MongoDB连接"""
        if self.client:
            self.client.close()
            logger.info("MongoDB连接已关闭")

    def get_latest_date(self) -> Optional[str]:
        """获取数据库中最新的交易日期"""
        try:
            result = self.kline_collection.find_one(
                {},
                sort=[('date', -1)],
                projection={'date': 1, '_id': 0}
            )
            if result:
                return result['date']
            return None
        except Exception as e:
            logger.error(f"获取最新日期失败: {e}")
            return None

    def get_stock_list(self) -> List[str]:
        """获取所有股票代码列表"""
        try:
            codes = self.kline_collection.distinct('code')
            logger.info(f"共找到 {len(codes)} 只股票")
            return codes
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []

    def analyze_market_overview(self, date: str = None) -> Dict:
        """
        分析市场概览

        Args:
            date: 分析日期，如果为None则使用最新日期

        Returns:
            市场概览数据
        """
        try:
            if not date:
                date = self.get_latest_date()

            if not date:
                logger.error("无法获取分析日期")
                return {}

            logger.info(f"开始分析市场概览，日期: {date}")

            # 获取当日所有股票数据
            cursor = self.kline_collection.find({'date': date})
            df = pd.DataFrame(list(cursor))

            if df.empty:
                logger.warning(f"日期 {date} 没有数据")
                return {}

            # 基础统计
            total_stocks = len(df)
            up_stocks = len(df[df['pct_chg'] > 0])
            down_stocks = len(df[df['pct_chg'] < 0])
            flat_stocks = len(df[df['pct_chg'] == 0])

            # 涨跌停统计
            limit_up = len(df[df['pct_chg'] >= 9.9])  # 接近涨停
            limit_down = len(df[df['pct_chg'] <= -9.9])  # 接近跌停

            # 涨跌幅分布
            pct_chg = df['pct_chg']
            avg_change = pct_chg.mean()
            median_change = pct_chg.median()

            # 成交额统计
            if 'amount' in df.columns:
                total_amount = df['amount'].sum() / 1e8  # 转换为亿元
            else:
                total_amount = 0

            # 振幅统计
            if 'high' in df.columns and 'low' in df.columns:
                df['amplitude'] = (df['high'] - df['low']) / df['close'].shift(1) * 100
                avg_amplitude = df['amplitude'].mean()
            else:
                avg_amplitude = 0

            overview = {
                'date': date,
                'total_stocks': total_stocks,
                'up_stocks': up_stocks,
                'down_stocks': down_stocks,
                'flat_stocks': flat_stocks,
                'limit_up': limit_up,
                'limit_down': limit_down,
                'avg_change': round(avg_change, 2),
                'median_change': round(median_change, 2),
                'total_amount': round(total_amount, 2),
                'avg_amplitude': round(avg_amplitude, 2)
            }

            logger.info(f"市场概览分析完成: 总{total_stocks}只，涨{up_stocks}只，跌{down_stocks}只")
            return overview

        except Exception as e:
            logger.error(f"市场概览分析失败: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def analyze_top_performers(self, date: str = None, top_n: int = 10) -> Dict:
        """
        分析表现最好的股票

        Args:
            date: 分析日期
            top_n: 返回前N只股票

        Returns:
            上涨和下跌排名前N的股票
        """
        try:
            if not date:
                date = self.get_latest_date()

            logger.info(f"分析表现最佳股票，日期: {date}")

            # 获取当日数据
            cursor = self.kline_collection.find({'date': date}).sort('pct_chg', -1)
            df = pd.DataFrame(list(cursor))

            if df.empty:
                logger.warning(f"日期 {date} 没有数据")
                return {}

            # 涨幅榜
            top_gainers = df.nlargest(top_n, 'pct_chg')[['code', 'name', 'close', 'pct_chg', 'amount', 'volume']].to_dict('records')
            for item in top_gainers:
                item['pct_chg'] = round(item['pct_chg'], 2)
                if 'amount' in item and item['amount']:
                    item['amount'] = round(item['amount'] / 1e8, 2)  # 转换为亿元

            # 跌幅榜
            top_losers = df.nsmallest(top_n, 'pct_chg')[['code', 'name', 'close', 'pct_chg', 'amount', 'volume']].to_dict('records')
            for item in top_losers:
                item['pct_chg'] = round(item['pct_chg'], 2)
                if 'amount' in item and item['amount']:
                    item['amount'] = round(item['amount'] / 1e8, 2)

            # 成交额榜
            if 'amount' in df.columns and df['amount'].sum() > 0:
                top_volume = df.nlargest(top_n, 'amount')[['code', 'name', 'close', 'pct_chg', 'amount', 'volume']].to_dict('records')
                for item in top_volume:
                    item['pct_chg'] = round(item['pct_chg'], 2)
                    item['amount'] = round(item['amount'] / 1e8, 2)
            else:
                top_volume = []

            return {
                'date': date,
                'top_gainers': top_gainers,
                'top_losers': top_losers,
                'top_volume': top_volume
            }

        except Exception as e:
            logger.error(f"分析表现最佳股票失败: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def analyze_sector_performance(self, date: str = None) -> Dict:
        """
        分析行业表现（如果有行业分类字段）

        Args:
            date: 分析日期

        Returns:
            行业表现数据
        """
        try:
            if not date:
                date = self.get_latest_date()

            logger.info(f"分析行业表现，日期: {date}")

            cursor = self.kline_collection.find({'date': date})
            df = pd.DataFrame(list(cursor))

            if df.empty:
                return {}

            # 检查是否有行业字段
            if 'industry' not in df.columns or 'sector' not in df.columns:
                logger.info("数据中没有行业分类字段，跳过行业分析")
                return {}

            industry_col = 'industry' if 'industry' in df.columns else 'sector'

            # 按行业统计
            sector_stats = df.groupby(industry_col).agg({
                'pct_chg': ['mean', 'median', 'count'],
                'amount': 'sum'
            }).reset_index()

            sector_stats.columns = ['sector', 'avg_change', 'median_change', 'stock_count', 'total_amount']
            sector_stats['avg_change'] = sector_stats['avg_change'].round(2)
            sector_stats['median_change'] = sector_stats['median_change'].round(2)
            sector_stats['total_amount'] = (sector_stats['total_amount'] / 1e8).round(2)

            # 按平均涨幅排序
            sector_stats = sector_stats.sort_values('avg_change', ascending=False)

            return {
                'date': date,
                'sector_performance': sector_stats.to_dict('records')
            }

        except Exception as e:
            logger.error(f"行业分析失败: {e}")
            import traceback
            traceback.print_exc()
            return {}


class AfterMarketAnalysisService:
    """盘后数据分析服务"""

    def __init__(self, config_path: str = None):
        """
        初始化盘后分析服务

        Args:
            config_path: 配置文件路径
        """
        if config_path is None:
            # 默认配置路径
            config_path = os.path.join(os.path.dirname(__file__), 'api', 'config.yaml')

        self.config = self._load_config(config_path)
        self.mongodb_config = self.config.get('mongodb', {})
        self.after_market_config = self.config.get('after_market', {})

        # 初始化分析器
        self.analyzer = StockAnalyzer(self.mongodb_config)

        # 初始化钉钉通知器
        webhook = self.after_market_config.get('dingtalk_webhook', '')
        secret = self.after_market_config.get('dingtalk_secret', '')
        self.notifier = DingTalkNotifier(webhook, secret)

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            else:
                logger.error(f"配置文件不存在: {config_path}")
                return {}
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}

    def run_analysis(self, date: str = None):
        """
        执行盘后分析

        Args:
            date: 分析日期，为None时使用最新日期
        """
        logger.info("=" * 60)
        logger.info("开始盘后数据分析")
        logger.info("=" * 60)

        try:
            # 连接数据库
            if not self.analyzer.connect():
                logger.error("数据库连接失败，终止分析")
                return

            # 获取分析日期
            if not date:
                date = self.analyzer.get_latest_date()

            if not date:
                logger.error("无法获取分析日期")
                return

            logger.info(f"分析日期: {date}")

            # 执行各项分析
            market_overview = self.analyzer.analyze_market_overview(date)
            top_performers = self.analyzer.analyze_top_performers(date, top_n=10)
            sector_performance = self.analyzer.analyze_sector_performance(date)

            # 生成分析报告
            report = self._generate_report(
                date=date,
                market_overview=market_overview,
                top_performers=top_performers,
                sector_performance=sector_performance
            )

            # 发送到钉钉
            if self.after_market_config.get('dingtalk_webhook'):
                title = f"📊 盘后数据分析 - {date}"
                success = self.notifier.send_markdown(title, report)

                if success:
                    logger.info("分析报告已发送到钉钉")
                else:
                    logger.error("发送到钉钉失败")
            else:
                logger.info("未配置钉钉webhook，跳过通知")
                print(report)  # 打印到控制台

            # 断开连接
            self.analyzer.disconnect()

            logger.info("=" * 60)
            logger.info("盘后数据分析完成")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"盘后分析失败: {e}")
            import traceback
            traceback.print_exc()

    def _generate_report(self, date: str, market_overview: Dict,
                        top_performers: Dict, sector_performance: Dict) -> str:
        """
        生成分析报告

        Args:
            date: 分析日期
            market_overview: 市场概览
            top_performers: 表现最佳股票
            sector_performance: 行业表现

        Returns:
            Markdown格式的报告
        """
        report = f"# 📊 盘后数据分析报告\n\n"
        report += f"**日期**: {date}\n"
        report += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # 市场概览
        if market_overview:
            report += "## 📈 市场概览\n\n"
            report += f"- **股票总数**: {market_overview.get('total_stocks', 0)} 只\n"
            report += f"- **上涨**: {market_overview.get('up_stocks', 0)} 只\n"
            report += f"- **下跌**: {market_overview.get('down_stocks', 0)} 只\n"
            report += f"- **平盘**: {market_overview.get('flat_stocks', 0)} 只\n"
            report += f"- **涨停**: {market_overview.get('limit_up', 0)} 只\n"
            report += f"- **跌停**: {market_overview.get('limit_down', 0)} 只\n"
            report += f"- **平均涨跌幅**: {market_overview.get('avg_change', 0)}%\n"
            report += f"- **中位数涨跌幅**: {market_overview.get('median_change', 0)}%\n"
            report += f"- **总成交额**: {market_overview.get('total_amount', 0)} 亿元\n"
            report += f"- **平均振幅**: {market_overview.get('avg_amplitude', 0)}%\n\n"

            # 市场情绪
            total = market_overview.get('total_stocks', 0)
            up = market_overview.get('up_stocks', 0)
            if total > 0:
                up_ratio = up / total * 100
                if up_ratio >= 70:
                    sentiment = "🟢 极度强势"
                elif up_ratio >= 55:
                    sentiment = "🟡 强势"
                elif up_ratio >= 45:
                    sentiment = "⚪ 震荡"
                elif up_ratio >= 30:
                    sentiment = "🟡 弱势"
                else:
                    sentiment = "🔴 极度弱势"
                report += f"**市场情绪**: {sentiment} （上涨占比 {up_ratio:.1f}%）\n\n"

        # 涨幅榜
        if top_performers.get('top_gainers'):
            report += "## 🚀 涨幅榜 TOP10\n\n"
            report += "| 排名 | 代码 | 名称 | 收盘价 | 涨跌幅 | 成交额(亿) |\n"
            report += "|------|------|------|--------|--------|-----------|\n"
            for idx, stock in enumerate(top_performers['top_gainers'][:10], 1):
                code = stock.get('code', '')
                name = stock.get('name', '')
                close = stock.get('close', 0)
                pct_chg = stock.get('pct_chg', 0)
                amount = stock.get('amount', 0)
                report += f"| {idx} | {code} | {name} | {close:.2f} | +{pct_chg}% | {amount} |\n"
            report += "\n"

        # 跌幅榜
        if top_performers.get('top_losers'):
            report += "## 📉 跌幅榜 TOP10\n\n"
            report += "| 排名 | 代码 | 名称 | 收盘价 | 涨跌幅 | 成交额(亿) |\n"
            report += "|------|------|------|--------|--------|-----------|\n"
            for idx, stock in enumerate(top_performers['top_losers'][:10], 1):
                code = stock.get('code', '')
                name = stock.get('name', '')
                close = stock.get('close', 0)
                pct_chg = stock.get('pct_chg', 0)
                amount = stock.get('amount', 0)
                report += f"| {idx} | {code} | {name} | {close:.2f} | {pct_chg}% | {amount} |\n"
            report += "\n"

        # 成交额榜
        if top_performers.get('top_volume'):
            report += "## 💰 成交额榜 TOP10\n\n"
            report += "| 排名 | 代码 | 名称 | 收盘价 | 涨跌幅 | 成交额(亿) |\n"
            report += "|------|------|------|--------|--------|-----------|\n"
            for idx, stock in enumerate(top_performers['top_volume'][:10], 1):
                code = stock.get('code', '')
                name = stock.get('name', '')
                close = stock.get('close', 0)
                pct_chg = stock.get('pct_chg', 0)
                amount = stock.get('amount', 0)
                report += f"| {idx} | {code} | {name} | {close:.2f} | {pct_chg}% | {amount} |\n"
            report += "\n"

        # 行业表现
        if sector_performance.get('sector_performance'):
            report += "## 🏭 行业表现 TOP10\n\n"
            report += "| 排名 | 行业 | 平均涨跌幅 | 中位数涨跌幅 | 股票数量 | 总成交额(亿) |\n"
            report += "|------|------|-----------|-------------|---------|-----------|\n"
            for idx, sector in enumerate(sector_performance['sector_performance'][:10], 1):
                sector_name = sector.get('sector', '')
                avg_change = sector.get('avg_change', 0)
                median_change = sector.get('median_change', 0)
                count = sector.get('stock_count', 0)
                amount = sector.get('total_amount', 0)
                report += f"| {idx} | {sector_name} | {avg_change}% | {median_change}% | {count} | {amount} |\n"
            report += "\n"

        report += "---\n"
        report += "*数据来源: MongoDB数据库 | 仅供参考，不构成投资建议*\n"

        return report


def main():
    """主函数"""
    import sys

    # 解析命令行参数
    date = None
    config_path = None

    if len(sys.argv) > 1:
        date = sys.argv[1]

    if len(sys.argv) > 2:
        config_path = sys.argv[2]

    # 创建服务实例
    service = AfterMarketAnalysisService(config_path)

    # 执行分析
    service.run_analysis(date)


if __name__ == "__main__":
    main()
