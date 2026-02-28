from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from app.api.endpoints import auth, news, aftermarket
from app.core.config import settings
from app.core.error import setup_error_handlers
import logging
from logging.handlers import TimedRotatingFileHandler
import os

from logging.handlers import TimedRotatingFileHandler

# 确保日志目录存在
log_file = settings.logging_file
log_dir = os.path.dirname(log_file)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.logging_level),
    format=settings.logging_format
)

# 添加按日期分割的文件日志处理器
file_handler = TimedRotatingFileHandler(
    log_file,
    when='midnight',
    interval=1,
    backupCount=settings.logging_backup_count,
    encoding='utf-8'
)
file_handler.setLevel(getattr(logging, settings.logging_level))
file_handler.setFormatter(logging.Formatter(settings.logging_format))
file_handler.suffix = "%Y-%m-%d"

# 添加到根logger
logging.getLogger().addHandler(file_handler)

scheduler = BackgroundScheduler()

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_error_handlers(app)

app.include_router(auth.router)
app.include_router(news.router)
app.include_router(aftermarket.router)


def run_scheduled_job():
    try:
        config = {
            "database": {
                "host": settings.mongodb_host,
                "port": settings.mongodb_port,
                "name": settings.mongodb_database,
            },
            "news_api": {
                "base_url": settings.after_market_news_api_url,
                "username": settings.after_market_news_api_username,
                "password": settings.after_market_news_api_password,
            },
            "llm": {
                "provider": settings.llm_provider,
                "api_key": settings.llm_api_key,
                "model": settings.llm_model,
                "base_url": settings.llm_base_url,
            },
            "dingtalk": {
                "webhook_url": settings.after_market_dingtalk_webhook,
                "secret": settings.after_market_dingtalk_secret,
            },
        }
        from app.scheduler import AfterMarketJob
        job = AfterMarketJob(config)
        job.run()
    except Exception as e:
        logging.error(f"Scheduled job failed: {e}")


def setup_scheduler():
    job_time = settings.after_market_scheduler_time
    timezone = settings.after_market_scheduler_timezone
    
    hour, minute = map(int, job_time.split(':'))
    scheduler.add_job(
        run_scheduled_job,
        'cron',
        hour=hour,
        minute=minute,
        timezone=timezone,
        id='after_market_job'
    )
    logging.info(f"Scheduler configured to run at {job_time} ({timezone})")


@app.on_event("startup")
async def startup_event():
    setup_scheduler()
    scheduler.start()
    logging.info("Scheduler started")


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    logging.info("Scheduler stopped, application shutting down")


@app.get("/")
def read_root():
    return {"message": "News API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
