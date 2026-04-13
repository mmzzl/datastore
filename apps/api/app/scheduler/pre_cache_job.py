from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import logging

from ..collector import NewsClient, LLMClient, AkshareClient
from ..storage import MongoStorage

logger = logging.getLogger(__name__)


class PreCacheJob:
    """预缓存任务，提前缓存盘后分析所需的数据"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.news_client = None
        self.llm_client = None
        self.akshare_client = None
        self.storage = None

    def _ensure_clients(self, target_date: Optional[str] = None):
        """确保所有客户端已初始化"""
        if self.news_client is None:
            after_market_config = self.config.get("after_market", {})
            self.news_client = NewsClient(
                after_market_config.get("news_api_url", "https://www.life233.top"),
                after_market_config.get("news_api_username", "admin"),
                after_market_config.get("news_api_password", "aa123aaqqA@")
            )
        
        if self.llm_client is None:
            llm_config = self.config.get("llm", {})
            self.llm_client = LLMClient(
                llm_config.get("provider", "deepseek"),
                llm_config.get("api_key", ""),
                llm_config.get("model", "deepseek-chat"),
                llm_config.get("base_url", "https://api.deepseek.com")
            )
        
        if self.akshare_client is None:
            self.akshare_client = AkshareClient(target_date=target_date)
            logger.info("Using Akshare data source for stock data")
        
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

    def run(self, target_date: Optional[str] = None) -> str:
        """
        执行预缓存任务
        
        参数:
            target_date: 目标日期，格式为 YYYY-MM-DD
        
        返回:
            执行结果消息
        """
        if target_date:
            target = datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=1)
        else:
            target = datetime.now() - timedelta(days=1)
        date_str = target.strftime("%Y-%m-%d")
        
        logger.info(f"Starting pre-cache job for {date_str}")
        self._ensure_clients(date_str)
        
        try:
            # 1. 预缓存新闻数据
            logger.info("Step 1: Pre-caching news data...")
            news = self._fetch_news(date_str)
            logger.info(f"News data cached: {len(news)} items")
            
            # 2. 预缓存新闻分析结果
            logger.info("Step 2: Pre-caching news analysis...")
            news_analysis = self._analyze_news(news, max_retries=10)
            logger.info(f"News analysis cached: {news_analysis}")
            
            # 3. 预缓存股票数据（使用新闻分析结果）
            logger.info("Step 3: Pre-caching stock data...")
            data = self.akshare_client.format_dingtalk(news_analysis=news_analysis, llm_client=self.llm_client) 
            # 4. 保存到数据库
            logger.info("Step 4: Saving cached data to MongoDB...")
            self.storage.save(data)
            logger.info(f"Data saved to MongoDB for {date_str}")
            
            # 5. 清空新闻客户端缓存，释放内存
            if self.news_client:
                self.news_client.clear_cache()
                logger.info("News client cache cleared")
            
            logger.info(f"Pre-cache job completed successfully for {date_str}")
            return f"预缓存完成: {date_str}"
            
        except Exception as e:
            logger.error(f"Pre-cache job failed for {date_str}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        finally:
            if self.storage:
                self.storage.close()

    def _fetch_news(self, date_str: str) -> List[Dict[str, Any]]:
        """
        获取新闻数据（会自动缓存）
        
        参数:
            date_str: 日期字符串
        
        返回:
            新闻数据列表
        """
        return self.news_client.get_all_daily_news(date_str)

    def _analyze_news(self, news: List[Dict[str, Any]], max_retries: int = 10) -> Dict[str, Any]:
        """
        使用LLM分析新闻，带重试机制
        
        参数:
            news: 新闻数据列表
            max_retries: 最大重试次数
        
        返回:
            新闻分析结果
        """
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
