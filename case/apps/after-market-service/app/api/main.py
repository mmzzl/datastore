from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from apscheduler.schedulers.background import BackgroundScheduler

from .routes import router
from ..scheduler import AfterMarketJob
from ..config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

app = FastAPI(
    title="盘后信息服务",
    version="1.0.0",
    description="获取盘后信息、数据采集、定时任务"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


def run_scheduled_job():
    try:
        config = {
            "database": settings.database,
            "news_api": settings.news_api,
            "dingtalk": settings.dingtalk,
        }
        job = AfterMarketJob(config)
        job.run()
    except Exception as e:
        logger.error(f"Scheduled job failed: {e}")


def setup_scheduler():
    scheduler_config = settings.scheduler
    job_time = scheduler_config.get("time", "20:00")
    timezone = scheduler_config.get("timezone", "Asia/Shanghai")
    
    hour, minute = map(int, job_time.split(':'))
    scheduler.add_job(
        run_scheduled_job,
        'cron',
        hour=hour,
        minute=minute,
        timezone=timezone,
        id='after_market_job'
    )
    logger.info(f"Scheduler configured to run at {job_time} ({timezone})")


@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up")
    setup_scheduler()
    scheduler.start()
    logger.info("Scheduler started")


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    logger.info("Scheduler stopped, application shutting down")


@app.get("/health")
def health():
    return {"status": "ok", "service": "after-market-service"}
