from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import logging

from ..collector import NewsClient, LLMClient, AkshareClient
from ..storage import MongoStorage
from ..notify import DingTalkNotifier

logger = logging.getLogger(__name__)


class AfterMarketJob:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.akshare_client = None
        self.news_client = None
        self.llm_client = None
        self.storage = None
        self.notifier = None

    def _ensure_clients(self):
        if self.akshare_client is None:
            self.akshare_client = AkshareClient()
            logger.info("Using Akshare data source for stock data")
        
        if self.news_client is None:
            after_market_config = self.config.get("after_market", {})
            self.news_client = NewsClient(
                after_market_config.get("news_api_url", "https://www.life233.top"),
                after_market_config.get("news_api_username", "admin"),
                after_market_config.get("news_api_password", "admin")
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
                db_config.get("name", "after_market"),
                db_config.get("username"),
                db_config.get("password")
            )
            self.storage.connect()
        
        if self.notifier is None:
            after_market_config = self.config.get("after_market", {})
            self.notifier = DingTalkNotifier(
                after_market_config.get("dingtalk_webhook", ""),
                after_market_config.get("dingtalk_secret", ""),
                self.akshare_client
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
            # 使用 AkshareClient 获取所有数据
            brief = self.akshare_client.generate_daily_brief(date_str)
            
            # 获取新闻
            news = self._fetch_news(date_str)
            
            # 使用LLM分析新闻
            news_analysis = self._analyze_news(news)
            
            # 构建数据
            data = {
                "date": date_str,
                "market_overview": brief.get('market_overview', {}),
                "stocks": brief.get('stock_performance', {}),
                "capital_flow": brief.get('capital_flow', {}),
                "sectors": brief.get('sector_performance', {}),
                "technical_signals": brief.get('technical_signals', {}),
                "news": news,
                "news_analysis": news_analysis,
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

    def _fetch_news(self, date_str: str) -> List[Dict[str, Any]]:
        return self.news_client.get_all_daily_news(date_str, limit=100)

    def _analyze_news(self, news: List[Dict[str, Any]]) -> Dict[str, Any]:
        """使用LLM分析新闻"""
        return self.llm_client.analyze_news(news)
