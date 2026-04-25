import sys
import os
import time
import signal
import logging
import traceback
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

# 修复 1：正确导入 BlockingScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("PYTHONPATH", os.path.dirname(os.path.abspath(__file__)))

from app.core.pandas_compat import _patched_fillna
from app.core.config import settings

log_file = "logs/scheduler.log"
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

# 调度器
scheduler = BlockingScheduler(timezone="Asia/Shanghai")

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

# ====================== 任务函数 ======================
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

def run_daily_scanner_job():
    if datetime.now().weekday() >= 5:
        logging.info("Skipping daily signal scan: weekend")
        return
    try:
        from app.storage.mongo_client import MongoStorage
        from app.monitor.daily_scanner import DailySignalScanner
        storage = MongoStorage(
            host=settings.mongodb_host,
            port=settings.mongodb_port,
            db_name=settings.mongodb_database,
        )
        storage.connect()
        scanner = DailySignalScanner(storage)
        scanner.scan()
        storage.close()
    except Exception as e:
        logging.error(f"Daily signal scanner failed: {e}")
        logging.error(traceback.format_exc())

def run_5min_kline_job():
    if datetime.now().weekday() >= 5:
        logging.info("Skipping 5min kline job: weekend")
        return
    try:
        from stock_kline_scraper import StockKlineScraper

        scraper = StockKlineScraper()
        codes = scraper._get_index_stock_codes()
        scraper.fetch_5min_klines(codes=codes)
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

def run_qlib_data_sync_job():
    if datetime.now().weekday() >= 5:
        logging.info("Skipping qlib data sync job: weekend")
        return
    try:
        import asyncio
        from app.scheduler import QlibDataSyncJob
        job = QlibDataSyncJob(build_config())
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(job.run(mode="incremental"))
            logging.info(f"Qlib data sync job result: {result}")
        finally:
            loop.close()
    except Exception as e:
        logging.error(f"Qlib data sync job failed: {e}")
        logging.error(traceback.format_exc())

def run_qlib_top_stocks_job():
    if datetime.now().weekday() >= 5:
        logging.info("Skipping qlib top stocks job: weekend")
        return
    try:
        import asyncio
        from app.scheduler import QlibTopStocksJob
        job = QlibTopStocksJob(build_config())
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(job.run())
            logging.info(f"Qlib top stocks job result: {result}")
        finally:
            loop.close()
    except Exception as e:
        logging.error(f"Qlib top stocks job failed: {e}")
        logging.error(traceback.format_exc())

# ====================== 调度配置 ======================
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
        coalesce=True  # 修复：合并重复任务
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
        coalesce=True
    )

    if settings.monitor_enabled:
        scheduler.add_job(
            run_monitor_job,
            "interval",
            seconds=monitor_interval,
            id="monitor_job",
            misfire_grace_time=300,
            coalesce=True
        )

    # scheduler.add_job(
    #     run_daily_kline_job,
    #     "cron",
    #     hour=15,
    #     minute=30,
    #     timezone=timezone,
    #     id="daily_kline_job",
    #     misfire_grace_time=3600,
    #     coalesce=True
    # )

    scheduler.add_job(
        run_5min_kline_job,
        "interval",
        minutes=5,
        id="5min_kline_job",
        misfire_grace_time=300,
    )
    logging.info("5min kline scraper configured to run every 5 minutes")

    scheduler.add_job(
        run_daily_scanner_job,
        "cron",
        hour=15,
        minute=45,
        timezone=timezone,
        id="daily_signal_scanner_job",
        misfire_grace_time=3600,
        coalesce=True
    )

    scheduler.add_job(
        run_alert_orchestrator_job,
        "interval",
        minutes=5,
        id="alert_orchestrator_job",
        misfire_grace_time=300,
        coalesce=True
    )

    scheduler.add_job(
        run_qlib_data_sync_job,
        "cron",
        hour=16,
        minute=0,
        timezone=timezone,
        id="qlib_data_sync_job",
        misfire_grace_time=3600,
        coalesce=True
    )

    scheduler.add_job(
        run_qlib_top_stocks_job,
        "cron",
        hour=15,
        minute=30,
        timezone=timezone,
        id="qlib_top_stocks_job",
        misfire_grace_time=3600,
        coalesce=True
    )

# ====================== 安全退出（Windows 100% 可用） ======================
def exit_handler(signum, frame):
    print("\n✅ 收到 Ctrl+C，正在安全退出...")
    try:
        scheduler.shutdown(wait=False)  # 强制关闭
    except:
        pass
    time.sleep(0.5)
    print("✅ 程序已退出")
    sys.exit(0)

if __name__ == "__main__":
    logging.info("Standalone scheduler starting...")

    # 注册退出信号
    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)

    setup_scheduler()

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("程序已退出")
    except Exception as e:
        logging.error(f"调度器异常: {e}")