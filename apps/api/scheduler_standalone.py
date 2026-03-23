import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("PYTHONPATH", os.path.dirname(os.path.abspath(__file__)))

# Apply pandas compatibility patch before any other imports
from app.core.pandas_compat import _patched_fillna

import logging
from logging.handlers import TimedRotatingFileHandler
import traceback
import time
import signal
from datetime import datetime

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
    if datetime.now().weekday() >= 5:
        logging.info("Skipping pre-cache job: weekend")
        return
    try:
        from app.scheduler import PreCacheJob

        job = PreCacheJob(build_config())
        job.run()
    except Exception as e:
        logging.error(f"Pre-cache job failed: {e}")
        logging.error(traceback.format_exc())


def run_scheduled_job():
    if datetime.now().weekday() >= 5:
        logging.info("Skipping after-market job: weekend")
        return
    try:
        from app.scheduler import AfterMarketJob

        job = AfterMarketJob(build_config())
        job.run()
    except Exception as e:
        logging.error(f"After-market job failed: {e}")
        logging.error(traceback.format_exc())


def run_monitor_job():
    if datetime.now().weekday() >= 5:
        logging.info("Skipping monitor job: weekend")
        return
    try:
        from app.scheduler import MonitorJob

        job = MonitorJob(build_config())
        job.run()
    except Exception as e:
        logging.error(f"Monitor job failed: {e}")
        logging.error(traceback.format_exc())


def run_daily_kline_job():
    if datetime.now().weekday() >= 5:
        logging.info("Skipping daily kline job: weekend")
        return
    try:
        from stock_kline_scraper import run_daily_job

        run_daily_job()
    except Exception as e:
        logging.error(f"Daily kline scraper failed: {e}")
        logging.error(traceback.format_exc())


def run_5min_kline_job():
    if datetime.now().weekday() >= 5:
        logging.info("Skipping 5min kline job: weekend")
        return
    try:
        from stock_kline_scraper import run_5min_job

        run_5min_job()
    except Exception as e:
        logging.error(f"5min kline scraper failed: {e}")
        logging.error(traceback.format_exc())


def run_alert_orchestrator_job():
    if datetime.now().weekday() >= 5:
        logging.info("Skipping alert orchestrator job: weekend")
        return
    try:
        from app.scheduler import AlertOrchestratorJob

        job = AlertOrchestratorJob(build_config())
        result = job.run()
        logging.info(f"Alert orchestrator job result: {result}")
    except Exception as e:
        logging.error(f"Alert orchestrator job failed: {e}")
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

    scheduler.add_job(
        run_daily_kline_job,
        "cron",
        hour=15,
        minute=30,
        timezone=timezone,
        id="daily_kline_job",
        misfire_grace_time=3600,
    )
    logging.info(f"Daily kline scraper configured to run at 15:30 ({timezone})")

    scheduler.add_job(
        run_5min_kline_job,
        "interval",
        minutes=5,
        id="5min_kline_job",
        misfire_grace_time=300,
    )
    logging.info("5min kline scraper configured to run every 5 minutes")

    # Alert Orchestrator Job - 交易时间每5分钟执行一次
    scheduler.add_job(
        run_alert_orchestrator_job,
        "interval",
        minutes=5,
        id="alert_orchestrator_job",
        misfire_grace_time=300,
    )
    logging.info("Alert orchestrator configured to run every 5 minutes")


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
