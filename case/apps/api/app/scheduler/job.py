from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import logging

from ..collector import AkshareClient, NewsClient, LLMClient
from ..storage import MongoStorage
from ..notify import DingTalkNotifier

logger = logging.getLogger(__name__)


class AfterMarketJob:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ak_client = None
        self.news_client = None
        self.llm_client = None
        self.storage = None
        self.notifier = None

    def _ensure_clients(self):
        if self.ak_client is None:
            self.ak_client = AkshareClient()
        
        if self.news_client is None:
            news_config = self.config.get("news_api", {})
            self.news_client = NewsClient(
                news_config.get("base_url", "http://life233.top"),
                news_config.get("username", "admin"),
                news_config.get("password", "admin")
            )
        
        if self.llm_client is None:
            llm_config = self.config.get("llm", {})
            self.llm_client = LLMClient(
                llm_config.get("provider", "deepseek"),
                llm_config.get("api_key", ""),
                llm_config.get("model", "deepseek-chat"),
                llm_config.get("base_url", "https://api.deepseek.com")
            )
        
        if self.storage is None:
            db_config = self.config.get("database", {})
            self.storage = MongoStorage(
                db_config.get("host", "localhost"),
                db_config.get("port", 27017),
                db_config.get("name", "after_market")
            )
            self.storage.connect()
        
        if self.notifier is None:
            ding_config = self.config.get("dingtalk", {})
            self.notifier = DingTalkNotifier(
                ding_config.get("webhook_url", ""),
                ding_config.get("secret", "")
            )

    def run(self, target_date: Optional[str] = None) -> str:
        self._ensure_clients()
        
        if target_date:
            target = datetime.strptime(target_date, "%Y-%m-%d").date()
        else:
            target = date.today()
        
        date_str = target.strftime("%Y-%m-%d")
        logger.info(f"Starting after-market job for {date_str}")
        
        try:
            market_overview = self._fetch_market_overview(date_str)
            stocks = self._fetch_stock_data(date_str)
            capital_flow = self._fetch_capital_flow(date_str)
            sectors = self._fetch_sector_data(date_str)
            news = self._fetch_news(date_str)
            
            # 使用LLM分析新闻
            news_analysis = self._analyze_news(news)
            
            # 基于市场数据和新闻分析生成建议
            recommendations = self._generate_recommendations(market_overview, sectors, news_analysis)
            
            data = {
                "date": date_str,
                "market_overview": market_overview,
                "stocks": stocks,
                "capital_flow": capital_flow,
                "sectors": sectors,
                "news": news,
                "news_analysis": news_analysis,
                "recommendations": recommendations,
            }
            
            self.storage.save(data)
            logger.info(f"Data saved to MongoDB for {date_str}")
            
            self.notifier.send(data)
            logger.info(f"DingTalk notification sent for {date_str}")
            
            return f"盘后信息已生成: {date_str}"
            
        except Exception as e:
            logger.error(f"Job failed for {date_str}: {e}")
            raise
        finally:
            if self.storage:
                self.storage.close()

    def _fetch_market_overview(self, date_str: str) -> Dict[str, Any]:
        return self.ak_client.get_market_overview(date_str)

    def _fetch_stock_data(self, date_str: str) -> List[Dict[str, Any]]:
        return self.ak_client.get_stock_data(date_str, limit=50)

    def _fetch_capital_flow(self, date_str: str) -> Dict[str, Any]:
        return self.ak_client.get_capital_flow(date_str)

    def _fetch_sector_data(self, date_str: str) -> List[Dict[str, Any]]:
        return self.ak_client.get_sector_data(date_str)

    def _fetch_news(self, date_str: str) -> List[Dict[str, Any]]:
        return self.news_client.get_all_news(date_str, limit=20)

    def _analyze_news(self, news: List[Dict[str, Any]]) -> Dict[str, Any]:
        """使用LLM分析新闻"""
        return self.llm_client.analyze_news(news)

    def _generate_recommendations(
        self, 
        market: Dict[str, Any], 
        sectors: List[Dict[str, Any]], 
        news: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        indices = market.get("indices", [])
        market_trend = "震荡"
        if indices:
            total_pct = sum(idx.get("pct_chg", 0) for idx in indices)
            if total_pct > 1:
                market_trend = "上行"
            elif total_pct < -1:
                market_trend = "下行"
        
        position = "5成"
        if market_trend == "上行":
            position = "7成"
        elif market_trend == "下行":
            position = "3成"
        
        main_sectors = [s.get("name", "") for s in sectors[:3]]
        avoid_sectors = [s.get("name", "") for s in sectors[-2:] if s.get("pct_chg", 0) < 0]
        
        return {
            "market": {
                "trend": market_trend,
                "position": position,
                "risk": "无"
            },
            "sectors": {
                "main": main_sectors,
                "avoid": avoid_sectors,
                "rotation": "关注高低切换"
            },
            "stocks": {
                "hold": [],
                "watch": [],
                "avoid": []
            }
        }
