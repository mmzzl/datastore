from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from app.api.endpoints import auth, news, aftermarket
from app.core.config import settings
from app.core.error import setup_error_handlers
import logging

logging.basicConfig(
    level=getattr(logging, settings.logging_level),
    format=settings.logging_format
)

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
                "host": settings.after_market_mongodb_host,
                "port": settings.after_market_mongodb_port,
                "name": settings.after_market_mongodb_database,
            },
            "news_api": {
                "base_url": settings.after_market_news_api_url,
                "username": settings.after_market_news_api_username,
                "password": settings.after_market_news_api_password,
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
