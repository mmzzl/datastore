from app.scheduler.pre_cache_job import PreCacheJob
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create a test configuration
config = {
    "database": {
        "host": settings.mongodb_host,
        "port": settings.mongodb_port,
        "name": settings.mongodb_database,
        "username": settings.mongodb_username,
        "password": settings.mongodb_password,
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

print("Testing PreCacheJob save functionality...")
try:
    # Create a PreCacheJob instance
    job = PreCacheJob(config)
    
    # Run the job for a specific date (yesterday)
    result = job.run()
    print(f"Test successful: {result}")
except Exception as e:
    print(f"Test failed: {e}")
    import traceback
    traceback.print_exc()
