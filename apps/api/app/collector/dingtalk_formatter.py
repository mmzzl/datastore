"""钉钉消息格式化模块 — 财经日报格式"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DingTalkFormatter:
    """钉钉消息格式化器 — 财经日报"""

    @staticmethod
    def format(brief: Dict, stock_info: Dict = None, news_analysis: Dict = None) -> str:
        """格式化简报为财经日报格式"""
        if stock_info is None:
            stock_info = {}

        na = news_analysis or brief.get("news_analysis", {})
        lines = []

        # 标题 + 新闻总数
        date_str = brief.get("date", "")
        news_count = na.get("news_count", 0)
        lines.append(f"## 📊 财经日报 · {date_str}")
        lines.append("")
        lines.append(f"📋 新闻总数: {news_count}条")
        lines.append("")

        # 今日市场要点
        DingTalkFormatter._add_market_summary(lines, na)

        # 热点板块 TOP 5
        DingTalkFormatter._add_hot_sectors(lines, na)

        # 热点股票
        DingTalkFormatter._add_hot_stocks(lines, na)

        # 今日热门新闻（按分类）
        DingTalkFormatter._add_news_by_category(lines, na)

        # 大盘数据
        DingTalkFormatter._add_market_overview(lines, brief.get("market_overview", {}))

        # AI 市场分析
        DingTalkFormatter._add_market_analysis(lines, na)

        # 明日策略
        DingTalkFormatter._add_strategy(lines, na)

        lines.append("> 仅供参考，不构成投资建议")
        return "\n".join(lines)

    @staticmethod
    def _add_market_summary(lines: List[str], na: Dict) -> None:
        summary = na.get("summary", "")
        if summary:
            lines.append("📈 今日市场要点")
            lines.append(summary)
            lines.append("")

    @staticmethod
    def _add_hot_sectors(lines: List[str], na: Dict) -> None:
        sectors = na.get("hot_sectors_detail") or []
        if not sectors:
            # 兼容旧格式
            names = na.get("hot_sectors", [])
            sectors = [{"name": s, "heat": 0} for s in names]
        if not sectors:
            return

        lines.append("🔥 热点板块 TOP %d" % min(len(sectors), 5))
        lines.append("")
        lines.append("| 排名 | 板块 | 热度 |")
        lines.append("|------|------|------|")
        for i, sec in enumerate(sectors[:5], 1):
            name = sec.get("name", "")
            heat = sec.get("heat", 0)
            heat_str = f"{heat}" if heat else "-"
            lines.append(f"| {i} | {name} | {heat_str} |")
        lines.append("")

    @staticmethod
    def _add_hot_stocks(lines: List[str], na: Dict) -> None:
        stocks = na.get("hot_stocks_detail") or []
        if not stocks and na.get("hot_stocks"):
            stocks = [{"name": s, "sector": "", "heat": 0} for s in na["hot_stocks"]]
        if not stocks:
            return

        lines.append("📈 热点股票")
        lines.append("")
        lines.append("| 股票 | 板块 | 热度 |")
        lines.append("|------|------|------|")
        for s in stocks[:10]:
            name = s.get("name", "")
            sector = s.get("sector", "") or "-"
            heat = s.get("heat", 0)
            heat_str = f"{heat}" if heat else "-"
            lines.append(f"| {name} | {sector} | {heat_str} |")
        lines.append("")

    @staticmethod
    def _add_news_by_category(lines: List[str], na: Dict) -> None:
        news_cat = na.get("news_by_category") or {}
        if not news_cat:
            return

        lines.append("📰 今日热门新闻")
        lines.append("")
        for cat, news_items in news_cat.items():
            if not news_items:
                continue
            lines.append(f"**【{cat}】**")
            for j, item in enumerate(news_items[:8], 1):
                lines.append(f"{j}. {item}")
            lines.append("")

    @staticmethod
    def _add_market_overview(lines: List[str], market: Dict) -> None:
        if "error" in market or not market:
            return

        up = market.get("up_count", 0)
        down = market.get("down_count", 0)
        avg = market.get("avg_change_pct", 0)
        limit_up = market.get("limit_up", 0)
        limit_down = market.get("limit_down", 0)
        sentiment = market.get("market_sentiment", "")

        lines.append("📊 大盘数据")
        lines.append(f"- 上涨: **{up}** | 下跌: **{down}** | 平均涨跌幅: **{avg:.2f}%**")
        lines.append(f"- 涨停: **{limit_up}** | 跌停: **{limit_down}** | 情绪: **{sentiment}**")
        lines.append("")

    @staticmethod
    def _add_market_analysis(lines: List[str], na: Dict) -> None:
        ma = na.get("market_analysis") or {}
        if not ma:
            return

        lines.append("🤖 今日市场分析")
        lines.append("")

        overall = ma.get("overall", "")
        if overall:
            lines.append("1. 市场整体态势")
            lines.append(overall)
            lines.append("")

        rotation = ma.get("sector_rotation", "")
        if rotation:
            lines.append("2. 板块轮动")
            lines.append(rotation)
            lines.append("")

        opportunities = ma.get("opportunities", [])
        risks = ma.get("risks", [])

        if opportunities:
            lines.append("3. 投资机会")
            for opp in opportunities:
                lines.append(f"   ✅ {opp}")
            lines.append("")

        if risks:
            lines.append("4. 风险提示")
            for r in risks:
                lines.append(f"   ⚠️ {r}")
            lines.append("")

        outlook = ma.get("outlook", "")
        if outlook:
            lines.append("5. 明日展望")
            lines.append(outlook)
            lines.append("")

        core_focus = ma.get("core_focus", [])
        if core_focus:
            lines.append("💡 今日核心关注：")
            for item in core_focus:
                lines.append(f"- {item}")
            lines.append("")

    @staticmethod
    def _add_strategy(lines: List[str], na: Dict) -> None:
        strategy = na.get("tomorrow_strategy") or {}
        if not strategy:
            return

        direction = strategy.get("direction", "")
        attention = strategy.get("attention", "")
        risk = strategy.get("risk", "")

        if any([direction, attention, risk]):
            lines.append("📋 策略参考")
            if direction:
                emoji = "📈" if "多" in direction else "📉" if "空" in direction else "↔️"
                lines.append(f"- 方向: {emoji} {direction}")
            if attention:
                lines.append(f"- 关注: {attention}")
            if risk:
                lines.append(f"- 风控: ⚠️ {risk}")
            lines.append("")

    @staticmethod
    def format_news_analysis(lines: List[str], news_analysis: Dict) -> str:
        """兼容旧接口 — 追加新格式到 lines"""
        na = news_analysis or {}

        cat = na.get("news_by_category") or {}
        if cat:
            lines.append("## 📰 财经日报")
            lines.append("")
            for category, items in cat.items():
                if items:
                    lines.append(f"### {category}")
                    for item in items[:5]:
                        lines.append(f"- {item}")
                    lines.append("")

        ma = na.get("market_analysis") or {}
        overall = ma.get("overall", "")
        if overall:
            lines.append("### 📊 市场分析")
            lines.append(overall)
            lines.append("")

        opportunities = ma.get("opportunities", [])
        risks = ma.get("risks", [])
        if opportunities:
            lines.append("**机会:** " + "、".join(opportunities))
        if risks:
            lines.append("**风险:** " + "、".join(risks))

        sentiment = na.get("sentiment", "")
        if sentiment:
            emoji = "🟢" if "利好" in sentiment else "🔴" if "利空" in sentiment else "⚪"
            lines.append(f"**市场情绪:** {emoji} {sentiment}")

        return "\n".join(lines)
