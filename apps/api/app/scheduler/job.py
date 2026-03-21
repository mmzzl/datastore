from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import logging
import time

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
            target = datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=1)
        else:
            target = datetime.now() - timedelta(days=1)
        date_str = target.strftime("%Y-%m-%d")
        logger.info(f"Starting after-market job for {date_str}")
        self._ensure_clients(date_str)
        try:
            # 先尝试从数据库读取缓存的数据
            logger.info("Attempting to load cached data from MongoDB...")
            cached_data = self.storage.load()
            if cached_data:
                logger.info(f"Found cached data for {date_str}, sending notification directly")
                # 直接发送钉钉消息，重试10次
                self.notifier.send(cached_data, max_retries=10)
                logger.info(f"DingTalk notification sent for {date_str} (from cache)")
                return f"盘后信息已发送: {date_str} (来自缓存)"
            else:
                logger.info(f"No cached data found for {date_str}, running full analysis...")
                # 缓存未命中，执行完整流程
                # 先获取新闻
                news = self._fetch_news(date_str)
                # 使用LLM分析新闻，重试10次
                news_analysis = self._analyze_news(news, max_retries=10)
                logger.info(news_analysis)
                # 使用 AkshareClient 获取所有数据，传入新闻分析用于买入机会分析
                data = self.akshare_client.format_dingtalk(news_analysis=news_analysis, llm_client=self.llm_client)
                self.storage.save(data)
                logger.info(f"Data saved to MongoDB for {date_str}")
                # 发送钉钉消息，重试10次
                self.notifier.send(data, max_retries=10)
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

    def _analyze_news(self, news: List[Dict[str, Any]], max_retries: int = 10) -> Dict[str, Any]:
        """使用LLM分析新闻，带重试机制"""
        for attempt in range(max_retries):
            try:
                result = self.llm_client.analyze_news(news)
                logger.info(f"新闻分析成功 (第 {attempt + 1} 次尝试)")
                return result
            except Exception as e:
                logger.error(f"新闻分析失败 (第 {attempt + 1} 次尝试): {e}")
                if attempt < max_retries - 1:
                    logger.warning(f"重试新闻分析 ({attempt + 1}/{max_retries})...")
                    import time
                    time.sleep(2)
        
        logger.error(f"新闻分析失败，已重试 {max_retries} 次")
        return {"error": "新闻分析失败"}
