"""股票数据客户端 - 简洁版本"""

import pandas as pd
from typing import Dict, Optional
from datetime import datetime, timedelta

from .stock_data_fetcher import StockDataFetcher
from .technical_indicators import TechnicalIndicators
from .stock_analyzer import StockAnalyzer
from .dingtalk_formatter import DingTalkFormatter
from ..core.config import settings


class AkshareClient:
    """股票数据客户端"""
    
    def __init__(self, target_date: str = None):
        self.target_date = target_date or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.fetcher = StockDataFetcher()
        self.data = self.fetcher.load_daily_data(self.target_date)
    
    def get_latest_date(self) -> str:
        if self.data is None or 'date' not in self.data.columns:
            return self.target_date
        return str(self.data['date'].max())[:10]
    
    def analyze_market(self) -> Dict:
        """分析市场概览"""
        if self.data is None or self.data.empty:
            return {"error": "数据为空"}
        
        df = self.data
        up_count = len(df[df.get('change_pct', 0) > 0])
        down_count = len(df[df.get('change_pct', 0) < 0])
        
        return {
            "date": self.target_date,
            "total_stocks": len(df),
            "up_count": up_count,
            "down_count": down_count,
            "avg_change_pct": round(df.get('change_pct', 0).mean(), 2),
            "limit_up": len(df[df.get('change_pct', 0) >= 9.9]),
            "limit_down": len(df[df.get('change_pct', 0) <= -9.9]),
            "market_sentiment": self._judge_sentiment(up_count, down_count)
        }
    
    def _judge_sentiment(self, up: int, down: int) -> str:
        total = up + down
        if total == 0:
            return "无数据"
        ratio = up / total
        if ratio >= 0.7: return "普涨"
        if ratio >= 0.5: return "偏涨"
        if ratio >= 0.3: return "分化"
        if ratio >= 0.1: return "偏跌"
        return "普跌"
    
    def analyze_buy_opportunities(self, news_analysis: Dict, llm_client=None, top_n: int = 5) -> Dict:
        """根据新闻分析结果推荐买入股票"""
        analyzer = StockAnalyzer({
            "host": settings.mongodb_host,
            "port": settings.mongodb_port,
            "db_name": settings.mongodb_database,
            "username": settings.mongodb_username,
            "password": settings.mongodb_password
        })
        return analyzer.analyze(news_analysis, llm_client, top_n)
    
    def generate_brief(self, news_analysis: Dict = None, llm_client=None) -> Dict:
        """生成每日简报"""
        market_overview = self.analyze_market()
        buy_opportunities = {"error": "未执行"}
        if news_analysis:
            buy_opportunities = self.analyze_buy_opportunities(news_analysis, llm_client)
        
        return {
            "date": self.target_date,
            "market_overview": market_overview,
            "buy_opportunities": buy_opportunities,
            "news_analysis": news_analysis
        }
    
    def format_dingtalk(self, news_analysis: Dict = None, llm_client=None) -> str:
        """生成钉钉消息"""
        brief = self.generate_brief(news_analysis, llm_client)
        
        stock_info = {}
        if self.data is not None and not self.data.empty:
            for _, row in self.data.iterrows():
                symbol = row.get('symbol', '')
                stock_info[symbol] = {
                    'name': row.get('name', symbol),
                    'close': row.get('close', 0)
                }
        
        return DingTalkFormatter.format(brief, stock_info)
