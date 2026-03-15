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

    def _ensure_clients(self, target_date: Optional[str] = None):
        if self.akshare_client is None:
            self.akshare_client = AkshareClient(target_date=target_date)
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
        if target_date:
            # 每天早上执行，查询昨天的股票数据
            target = datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=1)
        else:
            target = datetime.now() - timedelta(days=1)
        date_str = target.strftime("%Y-%m-%d")
        logger.info(f"Starting after-market job for {date_str}")
        self._ensure_clients(date_str)
        try:
            # 先获取新闻
            news = self._fetch_news(date_str)
            # 使用LLM分析新闻
            news_analysis = self._analyze_news(news)
            logger.info(news_analysis)
            # 使用 AkshareClient 获取所有数据，传入新闻分析用于买入机会分析
            data = self.akshare_client.format_dingtalk(news_analysis=news_analysis, llm_client=self.llm_client)
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
        return self.news_client.get_all_daily_news(date_str)

    def _analyze_news(self, news: List[Dict[str, Any]]) -> Dict[str, Any]:
        """使用LLM分析新闻"""
        return self.llm_client.analyze_news(news)
