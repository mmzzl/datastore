import sys 
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("PYTHONPATH", os.path.dirname(os.path.abspath(__file__)))
from app.scheduler import PreCacheJob
from app.core.config import settings
from app.scheduler import AfterMarketJob
from app.scheduler import MonitorJob
from stock_kline_scraper import run_daily_job
from app.storage.mongo_client import MongoStorage
from app.monitor.daily_scanner import DailySignalScanner
from stock_kline_scraper import StockKlineScraper
from app.scheduler import AlertOrchestratorJob
        
        

def build_config():
    return {
        "database": {
            "host": settings.mongodb_host,
            "port": settings.mongodb_port,
            "name": settings.mongodb_database,
            "username": settings.mongodb_username,
            "password": settings.mongodb_password,
        },
        "data_source": {
            "provider": settings.data_source,
            "tushare_token": settings.tushare_token,
        },
        "after_market": {
            "news_api_url": settings.after_market_news_api_url,
            "news_api_username": settings.after_market_news_api_username,
            "news_api_password": settings.after_market_news_api_password,
            "dingtalk_webhook": settings.after_market_dingtalk_webhook,
            "dingtalk_secret": settings.after_market_dingtalk_secret,
        },
        "llm": {
            "provider": settings.llm_provider,
            "api_key": settings.llm_api_key,
            "model": settings.llm_model,
            "base_url": settings.llm_base_url,
        },
    }

if __name__ == "__main__":
    # PreCacheJob(build_config()).run()
    # job = AfterMarketJob(build_config())
    # job.run()
    # job = MonitorJob(build_config())
    # job.run() 
    # run_daily_job()
    # storage = MongoStorage(
    #         host=settings.mongodb_host,
    #         port=settings.mongodb_port,
    #         db_name=settings.mongodb_database,
    #     )
    # storage.connect()
    # scanner = DailySignalScanner(storage)
    # scanner.scan()
    # storage.close()
    # run_5min_job()
    # scraper = StockKlineScraper()
    # codes = scraper._get_index_stock_codes()
    # scraper.fetch_5min_klines(codes=codes)
    job = AlertOrchestratorJob(build_config())
    result = job.run()