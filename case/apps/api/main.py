from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from app.api.endpoints import auth, news, aftermarket, stock
from app.core.config import settings
from app.core.error import setup_error_handlers
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import traceback
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
app.include_router(stock.router)


def run_scheduled_job():
    try:
        config = {
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
        from app.scheduler import AfterMarketJob
        job = AfterMarketJob(config)
        job.run()
    except Exception as e:
        logging.error(f"Scheduled job failed: {e}")
        logging.error(traceback.format_exc())


def run_pre_cache_job():
    """执行预缓存任务"""
    try:
        config = {
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
        from app.scheduler import PreCacheJob
        job = PreCacheJob(config)
        job.run()
    except Exception as e:
        logging.error(f"Pre-cache job failed: {e}")
        logging.error(traceback.format_exc())


def run_monitor_job():
    """执行盯盘任务"""
    try:
        config = {
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
        from app.scheduler import MonitorJob
        job = MonitorJob(config)
        job.run()
    except Exception as e:
        logging.error(f"Monitor job failed: {e}")
        logging.error(traceback.format_exc())


def setup_scheduler():
    job_time = settings.after_market_scheduler_time
    pre_cache_time = settings.after_market_pre_cache_scheduler_time
    monitor_time = settings.monitor_scheduler_time
    monitor_interval = settings.monitor_interval
    timezone = settings.after_market_scheduler_timezone
    
    # 添加预缓存任务
    pre_cache_hour, pre_cache_minute = map(int, pre_cache_time.split(':'))
    scheduler.add_job(
        run_pre_cache_job,
        'cron',
        hour=pre_cache_hour,
        minute=pre_cache_minute,
        timezone=timezone,
        id='pre_cache_job'
    )
    logging.info(f"Pre-cache scheduler configured to run at {pre_cache_time} ({timezone})")
    
    # 添加主任务
    hour, minute = map(int, job_time.split(':'))
    scheduler.add_job(
        run_scheduled_job,
        'cron',
        hour=hour,
        minute=minute,
        timezone=timezone,
        id='after_market_job'
    )
    logging.info(f"Main scheduler configured to run at {job_time} ({timezone})")
    
    # 添加盯盘任务
    if settings.monitor_enabled:
        monitor_hour, monitor_minute = map(int, monitor_time.split(':'))
        # 每天在指定时间开始，然后按间隔重复执行
        # 使用cron表达式确保每天固定时间执行，避免start_date不更新的问题
        scheduler.add_job(
            run_monitor_job,
            'cron',
            hour=monitor_hour,
            minute=monitor_minute,
            timezone=timezone,
            id='monitor_job'
        )
        logging.info(f"Monitor scheduler configured to run at {monitor_time} every day ({timezone})")


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
