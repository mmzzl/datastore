import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("PYTHONPATH", os.path.dirname(os.path.abspath(__file__)))

import logging
from logging.handlers import TimedRotatingFileHandler
import traceback
import time
import signal

from apscheduler.schedulers.blocking import BlockingScheduler
from app.core.config import settings

log_file = settings.logging_file
log_dir = os.path.dirname(log_file)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=getattr(logging, settings.logging_level),
    format=settings.logging_format,
    handlers=[
        logging.StreamHandler(),
        TimedRotatingFileHandler(
            log_file,
            when="midnight",
            interval=1,
            backupCount=settings.logging_backup_count,
            encoding="utf-8",
        ),
    ],
)
scheduler = BlockingScheduler()


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


def run_pre_cache_job():
    try:
        from app.scheduler import PreCacheJob

        job = PreCacheJob(build_config())
        job.run()
    except Exception as e:
        logging.error(f"Pre-cache job failed: {e}")
        logging.error(traceback.format_exc())


def run_scheduled_job():
    try:
        from app.scheduler import AfterMarketJob

        job = AfterMarketJob(build_config())
        job.run()
    except Exception as e:
        logging.error(f"After-market job failed: {e}")
        logging.error(traceback.format_exc())


def run_monitor_job():
    try:
        from app.scheduler import MonitorJob

        job = MonitorJob(build_config())
        job.run()
    except Exception as e:
        logging.error(f"Monitor job failed: {e}")
        logging.error(traceback.format_exc())


def setup_scheduler():
    job_time = settings.after_market_scheduler_time
    pre_cache_time = settings.after_market_pre_cache_scheduler_time
    monitor_interval = settings.monitor_interval
    timezone = settings.after_market_scheduler_timezone

    pre_cache_hour, pre_cache_minute = map(int, pre_cache_time.split(":"))
    scheduler.add_job(
        run_pre_cache_job,
        "cron",
        hour=pre_cache_hour,
        minute=pre_cache_minute,
        timezone=timezone,
        id="pre_cache_job",
        misfire_grace_time=3600,
    )
    logging.info(
        f"Pre-cache scheduler configured to run at {pre_cache_time} ({timezone})"
    )

    hour, minute = map(int, job_time.split(":"))
    scheduler.add_job(
        run_scheduled_job,
        "cron",
        hour=hour,
        minute=minute,
        timezone=timezone,
        id="after_market_job",
        misfire_grace_time=3600,
    )
    logging.info(f"After-market scheduler configured to run at {job_time} ({timezone})")

    if settings.monitor_enabled:
        scheduler.add_job(
            run_monitor_job,
            "interval",
            seconds=monitor_interval,
            id="monitor_job",
            misfire_grace_time=300,
        )
        logging.info(
            f"Monitor scheduler configured to run every {monitor_interval} seconds"
        )


def shutdown_handler(signum, frame):
    logging.info("Received shutdown signal, stopping scheduler...")
    scheduler.shutdown(wait=False)
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    logging.info("Standalone scheduler starting...")
    setup_scheduler()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler stopped")
