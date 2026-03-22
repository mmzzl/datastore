import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("PYTHONPATH", os.path.dirname(os.path.abspath(__file__)))

import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import signal
import time

from app.core.config import settings
from app.storage.mongo_client import MongoStorage

try:
    import mootdx
    from mootdx import Stock
    MOOTDX_AVAILABLE = True
except ImportError:
    MOOTDX_AVAILABLE = False
    logging.warning("mootdx not installed, stock kline scraper will not work")

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
logger = logging.getLogger(__name__)


class StockKlineScraper:
    def __init__(self):
        self.storage: Optional[MongoStorage] = None
        self.client = None

    def _ensure_storage(self):
        if self.storage is None:
            self.storage = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_database,
                username=settings.mongodb_username,
                password=settings.mongodb_password,
            )
            self.storage.connect()

    def _ensure_client(self):
        if self.client is None:
            if not MOOTDX_AVAILABLE:
                raise RuntimeError("mootdx is not installed")
            self.client = Stock()

    def _get_all_stock_codes(self) -> List[str]:
        self._ensure_storage()
        codes = set()
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            docs = self.storage.get_all_kline_by_date(today, limit=50000)
            for doc in docs:
                code = doc.get("code")
                if code:
                    codes.add(code)
        except Exception as e:
            logger.warning(f"Failed to get existing codes: {e}")

        if not codes:
            try:
                docs = self.storage.get_all_klines(limit=50000)
                for doc in docs:
                    code = doc.get("code")
                    if code:
                        codes.add(code)
            except Exception as e:
                logger.warning(f"Failed to get existing codes from all klines: {e}")

        if codes:
            logger.info(f"Found {len(codes)} existing stock codes in MongoDB")
            return sorted(list(codes))

        try:
            path = os.path.join(os.path.dirname(__file__), "data", "all_stock.csv")
            if os.path.exists(path):
                import csv
                with open(path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        code = row.get("code") or row.get("symbol")
                        if code:
                            codes.add(code.strip())
            logger.info(f"Loaded {len(codes)} stock codes from all_stock.csv")
        except Exception as e:
            logger.warning(f"Failed to load stock codes from CSV: {e}")

        if not codes:
            try:
                index_codes = [
                    "000001", "399001", "399006",
                    "000016", "000300", "000905",
                ]
                for code in index_codes:
                    codes.add(code)
                sh_codes = [f"{i:06d}" for i in range(600000, 604000)]
                sz_codes = [f"{i:06d}" for i in range(1, 3000)]
                codes.update(sh_codes[:100])
                codes.update(sz_codes[:100])
            except Exception as e:
                logger.warning(f"Failed to generate stock codes: {e}")

        logger.info(f"Using {len(codes)} stock codes")
        return sorted(list(codes))

    def _fetch_kline(
        self,
        code: str,
        frequency: int = 9,
        offset: int = 100,
        adjust: str = "qfq",
    ) -> List[Dict[str, Any]]:
        self._ensure_client()
        try:
            df = self.client.stock(
                symbol=code,
                freq=frequency,
                offset=offset,
                adjust=adjust,
            )
            if df is None or df.empty:
                return []

            if isinstance(df.columns, range(len(df.columns))):
                df.columns = ["date", "open", "high", "low", "close", "amount", "volume"]

            records = []
            for _, row in df.iterrows():
                try:
                    records.append({
                        "code": code,
                        "date": str(row.get("date", "")),
                        "open": float(row.get("open", 0) or 0),
                        "high": float(row.get("high", 0) or 0),
                        "low": float(row.get("low", 0) or 0),
                        "close": float(row.get("close", 0) or 0),
                        "volume": int(row.get("volume", 0) or 0),
                        "amount": float(row.get("amount", 0) or 0),
                        "frequency": frequency,
                        "adjust": adjust,
                        "crawl_time": datetime.now(),
                    })
                except (ValueError, TypeError):
                    continue
            return records
        except Exception as e:
            logger.debug(f"Failed to fetch kline for {code}: {e}")
            return []

    def _need_fetch(self, code: str, frequency: int = 9) -> bool:
        self._ensure_storage()
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            doc = self.storage.kline_collection.find_one(
                {"code": code, "date": today, "frequency": frequency}
            )
            return doc is None
        except Exception as e:
            logger.warning(f"Failed to check existence for {code}: {e}")
            return True

    def save_klines(self, records: List[Dict[str, Any]], frequency: int = 9):
        if not records:
            return
        self._ensure_storage()
        try:
            for record in records:
                self.storage.kline_collection.update_one(
                    {"code": record["code"], "date": record["date"], "frequency": frequency},
                    {"$set": record},
                    upsert=True,
                )
            logger.debug(f"Saved {len(records)} kline records for {records[0]['code']}")
        except Exception as e:
            logger.error(f"Failed to save klines: {e}")

    def fetch_daily_klines(
        self,
        codes: List[str] = None,
        offset: int = 100,
        adjust: str = "qfq",
        skip_existing: bool = True,
    ):
        if codes is None:
            codes = self._get_all_stock_codes()

        frequency = 9
        success = 0
        skipped = 0
        failed = 0

        for i, code in enumerate(codes):
            try:
                if skip_existing and not self._need_fetch(code, frequency):
                    skipped += 1
                    if (i + 1) % 100 == 0:
                        logger.info(f"Progress: {i+1}/{len(codes)}, success={success}, skipped={skipped}, failed={failed}")
                    continue

                records = self._fetch_kline(code, frequency=frequency, offset=offset, adjust=adjust)
                if records:
                    self.save_klines(records, frequency=frequency)
                    success += 1
                else:
                    failed += 1

                if (i + 1) % 50 == 0:
                    logger.info(f"Progress: {i+1}/{len(codes)}, success={success}, skipped={skipped}, failed={failed}")

                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error processing {code}: {e}")
                failed += 1
                continue

        logger.info(f"Daily kline fetch completed: total={len(codes)}, success={success}, skipped={skipped}, failed={failed}")
        return {"success": success, "skipped": skipped, "failed": failed}

    def fetch_5min_klines(
        self,
        codes: List[str] = None,
        offset: int = 100,
        adjust: str = "qfq",
        skip_existing: bool = True,
    ):
        if codes is None:
            codes = self._get_all_stock_codes()

        frequency = 0
        success = 0
        skipped = 0
        failed = 0

        for i, code in enumerate(codes):
            try:
                if skip_existing:
                    self._ensure_storage()
                    today = datetime.now().strftime("%Y-%m-%d")
                    existing = self.storage.kline_collection.count_documents(
                        {"code": code, "date": today, "frequency": frequency}
                    )
                    if existing > 0:
                        skipped += 1
                        if (i + 1) % 100 == 0:
                            logger.info(f"Progress: {i+1}/{len(codes)}, success={success}, skipped={skipped}, failed={failed}")
                        continue

                records = self._fetch_kline(code, frequency=frequency, offset=offset, adjust=adjust)
                if records:
                    self.save_klines(records, frequency=frequency)
                    success += 1
                else:
                    failed += 1

                if (i + 1) % 50 == 0:
                    logger.info(f"Progress: {i+1}/{len(codes)}, success={success}, skipped={skipped}, failed={failed}")

                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error processing {code}: {e}")
                failed += 1
                continue

        logger.info(f"5min kline fetch completed: total={len(codes)}, success={success}, skipped={skipped}, failed={failed}")
        return {"success": success, "skipped": skipped, "failed": failed}

    def close(self):
        if self.storage:
            self.storage.close()


def run_daily_job():
    scraper = StockKlineScraper()
    try:
        logger.info("Starting daily stock kline fetch job...")
        result = scraper.fetch_daily_klines(offset=100, adjust="qfq", skip_existing=True)
        logger.info(f"Daily job result: {result}")
    except Exception as e:
        logger.error(f"Daily kline job failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        scraper.close()


def run_5min_job():
    scraper = StockKlineScraper()
    try:
        logger.info("Starting 5min stock kline fetch job...")
        result = scraper.fetch_5min_klines(offset=100, adjust="qfq", skip_existing=True)
        logger.info(f"5min job result: {result}")
    except Exception as e:
        logger.error(f"5min kline job failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        scraper.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stock Kline Scraper using mootdx")
    parser.add_argument("--mode", choices=["daily", "5min", "both"], default="daily",
                        help="Fetch mode: daily (freq=9), 5min (freq=0), or both")
    parser.add_argument("--offset", type=int, default=100,
                        help="Number of days/bars to fetch (default: 100)")
    parser.add_argument("--codes", type=str, default=None,
                        help="Comma-separated stock codes, or leave empty to auto-detect")
    args = parser.parse_args()

    codes = args.codes.split(",") if args.codes else None

    scraper = StockKlineScraper()
    try:
        if args.mode == "daily":
            result = scraper.fetch_daily_klines(codes=codes, offset=args.offset)
            print(f"Daily result: {result}")
        elif args.mode == "5min":
            result = scraper.fetch_5min_klines(codes=codes, offset=args.offset)
            print(f"5min result: {result}")
        else:
            r1 = scraper.fetch_daily_klines(codes=codes, offset=args.offset)
            print(f"Daily result: {r1}")
            r2 = scraper.fetch_5min_klines(codes=codes, offset=args.offset)
            print(f"5min result: {r2}")
    finally:
        scraper.close()
