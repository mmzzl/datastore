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
        lines.append(f"## 📊 每日收盘简报 - {brief.get('date', '')}")
        lines.append("")
        
        DingTalkFormatter._add_market_section(lines, brief.get('market_overview', {}))
        DingTalkFormatter._add_buy_section(lines, brief.get('buy_opportunities', {}), stock_info)
        
        return "\n".join(lines)
    
    @staticmethod
    def _add_market_section(lines: List[str], market: Dict) -> None:
        if 'error' in market:
            return
        
        lines.append("### 📈 大盘与市场环境")
        lines.append("")
        
        sentiment_map = {"普涨": "🚀", "偏涨": "📈", "分化": "⚖️", "偏跌": "📉", "普跌": "🔻"}
        emoji = sentiment_map.get(market.get('market_sentiment', ""), "📊")
        
        lines.append(f"- 总股票数: **{market.get('total_stocks', 0)}**")
        lines.append(f"- 上涨: **{market.get('up_count', 0)}** | 下跌: **{market.get('down_count', 0)}**")
        
        avg_change = market.get('avg_change_pct', 0)
        color = "🔴" if avg_change < 0 else "🟢"
        lines.append(f"- 平均涨跌幅: {color} **{avg_change:.2f}%**")
        
        lines.append(f"- 涨停: **{market.get('limit_up', 0)}** | 跌停: **{market.get('limit_down', 0)}**")
        lines.append(f"- 市场情绪: **{emoji} {market.get('market_sentiment', '未知')}**")
        lines.append("")
    
    @staticmethod
    def _add_buy_section(lines: List[str], buy: Dict, stock_info: Dict) -> None:
        if 'error' in buy:
            lines.append("### 🎯 买入机会")
            lines.append(f"- {buy['error']}")
            lines.append("")
            return
        
        lines.append("### 🎯 买入机会推荐")
        lines.append("")
        
        top_stocks = buy.get('top_stocks', [])
        if not top_stocks:
            lines.append("- 暂无推荐")
            lines.append("")
            return
        
        for i, stock in enumerate(top_stocks[:5], 1):
            symbol = stock.get('symbol', '')
            name = stock_info.get(symbol, {}).get('name', symbol)
            
            if 'reason' in stock:
                reason = stock.get('reason', '')
                lines.append(f"{i}. **{name}**({symbol}) - {reason}")
            else:
                close = stock.get('close', 0)
                change = stock.get('change_pct', 0)
                rsi = stock.get('rsi', 0)
                lines.append(f"{i}. **{name}**({symbol}) | 收盘:{close:.2f} | 涨跌:{change:.2f}% | RSI:{rsi:.1f}")
        
        if buy.get('analysis'):
            lines.append("")
            lines.append(f"📝 分析: {buy['analysis']}")
        
        lines.append("")
