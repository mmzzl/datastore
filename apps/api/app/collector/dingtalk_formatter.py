"""钉钉消息格式化模块"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class DingTalkFormatter:
    """钉钉消息格式化器"""

    @staticmethod
    def format(brief: Dict, stock_info: Dict = None) -> str:
        """格式化简报为钉钉消息"""
        if stock_info is None:
            stock_info = {}

        lines = []
        lines.append(f"## 📊 每日盘前简报 - {brief.get('date', '')}")
        lines.append("")

        DingTalkFormatter._add_market_section(lines, brief.get("market_overview", {}))
        DingTalkFormatter._add_buy_section(
            lines, brief.get("buy_opportunities", {}), stock_info
        )
        DingTalkFormatter.format_news_analysis(lines, brief.get("news_analysis", {}))
        return "\n".join(lines)

    @staticmethod
    def format_news_analysis(lines: List[str], news_analysis: Dict) -> str:
        """格式化新闻分析结果为钉钉消息"""
        lines.append("## 📰 新闻分析简报")
        lines.append("")

        # 今日概要
        summary = news_analysis.get("summary", "")
        if summary:
            lines.append(f"### 📝 今日概要")
            lines.append(f"{summary}")
            lines.append("")

        # 热门板块
        hot_sectors = news_analysis.get("hot_sectors", [])
        if hot_sectors:
            lines.append("### 🔥 热门板块")
            for sector in hot_sectors:
                lines.append(f"- {sector}")
            lines.append("")

        # 关注股票
        hot_stocks = news_analysis.get("hot_stocks", [])
        if hot_stocks:
            lines.append("### 📌 关注股票")
            for stock in hot_stocks:
                lines.append(f"- {stock}")
            lines.append("")

        # 市场情绪
        sentiment = news_analysis.get("sentiment", "")
        if sentiment:
            sentiment_emoji = (
                "🟢" if "利好" in sentiment else "🔴" if "利空" in sentiment else "⚪"
            )
            lines.append(f"### 🎯 市场情绪")
            lines.append(f"{sentiment_emoji} {sentiment}")
            lines.append("")

        # 明日策略
        strategy = news_analysis.get("tomorrow_strategy", {})
        if strategy:
            lines.append("### 📅 明日策略")
            direction = strategy.get("direction", "")
            if direction:
                direction_emoji = (
                    "📈" if "多" in direction else "📉" if "空" in direction else "↔️"
                )
                lines.append(f"- **方向**: {direction_emoji} {direction}")

            attention = strategy.get("attention", "")
            if attention:
                lines.append(f"- **重点关注**: {attention}")

            risk = strategy.get("risk", "")
            if risk:
                lines.append(f"- **风险提示**: ⚠️ {risk}")
            lines.append("")

        # 关键事件
        key_events = news_analysis.get("key_events", [])
        if key_events:
            lines.append("### 📋 关键事件")
            for i, event in enumerate(key_events, 1):
                lines.append(f"{i}. {event}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _add_market_section(lines: List[str], market: Dict) -> None:
        if "error" in market:
            return

        lines.append("### 📈 大盘与市场环境")
        lines.append("")

        sentiment_map = {
            "普涨": "🚀",
            "偏涨": "📈",
            "分化": "⚖️",
            "偏跌": "📉",
            "普跌": "🔻",
        }
        emoji = sentiment_map.get(market.get("market_sentiment", ""), "📊")

        lines.append(f"- 总股票数: **{market.get('total_stocks', 0)}**")
        lines.append(
            f"- 上涨: **{market.get('up_count', 0)}** | 下跌: **{market.get('down_count', 0)}**"
        )

        avg_change = market.get("avg_change_pct", 0)
        color = "🔴" if avg_change < 0 else "🟢"
        lines.append(f"- 平均涨跌幅: {color} **{avg_change:.2f}%**")

        lines.append(
            f"- 涨停: **{market.get('limit_up', 0)}** | 跌停: **{market.get('limit_down', 0)}**"
        )
        lines.append(
            f"- 市场情绪: **{emoji} {market.get('market_sentiment', '未知')}**"
        )
        lines.append("")

    @staticmethod
    def _add_buy_section(lines: List[str], buy: Dict, stock_info: Dict) -> None:
        if "error" in buy:
            lines.append("### 🎯 买入机会")
            lines.append(f"- {buy['error']}")
            lines.append("")
            return

        lines.append("### 🎯 买入机会推荐")
        lines.append("")

        top_stocks = buy.get("top_stocks", [])
        if not top_stocks:
            lines.append("- 暂无推荐")
            lines.append("")
            return

        for i, stock in enumerate(top_stocks[:5], 1):
            symbol = stock.get("symbol", "")
            name = stock.get("name", symbol)
            sector = stock.get("sector", "")
            
            # 如果 symbol 为空，使用 name 作为标识
            display_symbol = symbol if symbol else name
            display_name = name if name else symbol
            
            # 构建板块信息
            sector_text = f" [{sector}]" if sector else ""

            if "reasons" in stock and stock["reasons"]:
                reasons_text = "、".join(stock["reasons"][:3])
                lines.append(f"{i}. **{display_name}**({display_symbol}){sector_text} - {reasons_text}")
            else:
                close = stock.get("close", 0)
                change = stock.get("change_pct", 0)
                score = stock.get("score", 0)
                lines.append(
                    f"{i}. **{display_name}**({display_symbol}){sector_text} | 收盘:{close:.2f} | 涨跌:{change:.2f}% | 评分:{score:.1f}"
                )

        if buy.get("analysis"):
            lines.append("")
            lines.append(f"📝 分析: {buy['analysis']}")

        lines.append("")
