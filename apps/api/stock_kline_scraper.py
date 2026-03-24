import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("PYTHONPATH", os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import signal
import time
import json

from app.core.config import settings
from app.storage.mongo_client import MongoStorage

try:
    from mootdx.quotes import Quotes

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

TARGET_DATA_COUNT = 2000
BATCH_SIZE = 800
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "data", "kline_progress.json")


class StockKlineScraper:
    def __init__(self):
        self.storage: Optional[MongoStorage] = None
        self.client = None
        self.progress: Dict[str, Dict[str, Any]] = {}

    def _load_progress(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load progress file: {e}")
        return {}

    def _save_progress(self):
        try:
            os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
            with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save progress file: {e}")

    def _get_code_progress(self, code: str, frequency: int) -> Dict[str, Any]:
        key = f"{code}_{frequency}"
        if key not in self.progress:
            self.progress[key] = {
                "code": code,
                "frequency": frequency,
                "start": 0,
                "total_fetched": 0,
                "completed": False,
                "last_update": None,
            }
        return self.progress[key]

    def _update_code_progress(
        self,
        code: str,
        frequency: int,
        start: int,
        fetched: int,
        completed: bool = False,
    ):
        key = f"{code}_{frequency}"
        self.progress[key] = {
            "code": code,
            "frequency": frequency,
            "start": start,
            "total_fetched": self.progress.get(key, {}).get("total_fetched", 0)
            + fetched,
            "completed": completed,
            "last_update": datetime.now().isoformat(),
        }
        self._save_progress()

    def _get_existing_count(self, code: str, frequency: int) -> int:
        self._ensure_storage()
        try:
            return self.storage.kline_collection.count_documents(
                {"code": code, "frequency": frequency}
            )
        except Exception as e:
            logger.warning(f"Failed to count existing data for {code}: {e}")
            return 0

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
            self.client = Quotes.factory(market="std", multithread=True, heartbeat=True)

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
                    "000001",
                    "399001",
                    "399006",
                    "000016",
                    "000300",
                    "000905",
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
        start: int = 0,
        count: int = BATCH_SIZE,
        adjust: str = "qfq",
    ) -> List[Dict[str, Any]]:
        self._ensure_client()
        try:
            code = code.split(".")[-1]
            df = self.client.bars(
                symbol=code,
                freq=frequency,
                start=start,
                offset=count,
            )
            if df is None or df.empty:
                return []

            column_map = {
                "datetime": "date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "amount": "amount",
                "volume": "volume",
            }

            available_cols = [c for c in column_map.keys() if c in df.columns]
            df = df[available_cols].rename(columns=column_map)

            records = []
            for _, row in df.iterrows():
                try:
                    records.append(
                        {
                            "code": code,
                            "date": str(row["date"]),
                            "open": float(row["open"]),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                            "volume": int(row["volume"])
                            if pd.notna(row["volume"])
                            else 0,
                            "amount": float(row["amount"])
                            if pd.notna(row["amount"])
                            else 0.0,
                            "frequency": frequency,
                            "adjust": adjust,
                            "crawl_time": datetime.now().isoformat(),
                        }
                    )
                except (ValueError, TypeError, KeyError) as e:
                    logger.error(f"Parse error for {code}: {e}")
                    continue
            return records
        except Exception as e:
            logger.error(f"Failed to fetch kline for {code}: {e}")
            return []

            # 选择并重命名需要的列
            column_map = {
                "datetime": "date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "amount": "amount",
                "volume": "volume",  # 或 "vol"，看哪个是手数
            }

            # 只保留存在的列
            available_cols = [c for c in column_map.keys() if c in df.columns]
            df = df[available_cols].rename(columns=column_map)

            records = []
            for _, row in df.iterrows():
                try:
                    records.append(
                        {
                            "code": code,
                            "date": str(row["date"]),
                            "open": float(row["open"]),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                            "volume": int(row["volume"])
                            if pd.notna(row["volume"])
                            else 0,
                            "amount": float(row["amount"])
                            if pd.notna(row["amount"])
                            else 0.0,
                            "frequency": frequency,
                            "adjust": adjust,
                            "crawl_time": datetime.now().isoformat(),
                        }
                    )
                except (ValueError, TypeError, KeyError) as e:
                    logger.error(f"Parse error for {code}: {e}")
                    continue
            return records
        except Exception as e:
            logger.error(f"Failed to fetch kline for {code}: {e}")
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
            saved_count = 0
            for record in records:
                record_frequency = record.get("frequency", frequency)
                result = self.storage.kline_collection.update_one(
                    {
                        "code": record["code"],
                        "date": record["date"],
                        "frequency": record_frequency,
                    },
                    {"$set": record},
                    upsert=True,
                )
                if result.upserted_id or result.modified_count > 0:
                    saved_count += 1
            logger.debug(
                f"Saved {saved_count}/{len(records)} kline records for {records[0]['code']}"
            )
        except Exception as e:
            logger.error(f"Failed to save klines: {e}")
        except Exception as e:
            logger.error(f"Failed to save klines: {e}")

    def fetch_daily_klines(
        self,
        codes: List[str] = None,
        adjust: str = "qfq",
        skip_existing: bool = True,
    ):
        if codes is None:
            codes = self._get_all_stock_codes()

        self.progress = self._load_progress()
        frequency = 9
        success = 0
        skipped = 0
        failed = 0

        for i, code in enumerate(codes):
            try:
                pure_code = code.split(".")[-1]
                existing_count = self._get_existing_count(pure_code, frequency)
                code_progress = self._get_code_progress(pure_code, frequency)

                if (
                    code_progress.get("completed")
                    and existing_count >= TARGET_DATA_COUNT
                ):
                    start = 0
                    logger.debug(f"{pure_code}: 已完成历史采集，只获取最新数据")
                elif existing_count >= TARGET_DATA_COUNT:
                    start = 0
                    code_progress["completed"] = True
                    logger.debug(f"{pure_code}: 数据已达标，标记为已完成")
                else:
                    start = code_progress.get("start", 0)
                    if start == 0:
                        start = existing_count
                    logger.debug(f"{pure_code}: 继续采集，start={start}")

                if skip_existing and start == 0 and code_progress.get("completed"):
                    records = self._fetch_kline(
                        pure_code,
                        frequency=frequency,
                        start=0,
                        count=BATCH_SIZE,
                        adjust=adjust,
                    )
                    if records:
                        self.save_klines(records, frequency=frequency)
                        success += 1
                    else:
                        skipped += 1
                    time.sleep(0.1)
                    continue

                total_fetched = 0
                current_start = start
                batch_count = 0

                while True:
                    records = self._fetch_kline(
                        pure_code,
                        frequency=frequency,
                        start=current_start,
                        count=BATCH_SIZE,
                        adjust=adjust,
                    )
                    if not records:
                        if current_start == 0:
                            failed += 1
                        break

                    self.save_klines(records, frequency=frequency)
                    fetched_count = len(records)
                    total_fetched += fetched_count
                    batch_count += 1

                    current_count = self._get_existing_count(pure_code, frequency)

                    if current_count >= TARGET_DATA_COUNT:
                        self._update_code_progress(
                            pure_code, frequency, 0, total_fetched, completed=True
                        )
                        success += 1
                        logger.info(
                            f"{pure_code}: 达到目标 {TARGET_DATA_COUNT} 条，完成采集"
                        )
                        break

                    if fetched_count < BATCH_SIZE:
                        self._update_code_progress(
                            pure_code,
                            frequency,
                            current_count,
                            total_fetched,
                            completed=True,
                        )
                        success += 1
                        logger.info(
                            f"{pure_code}: 无更多数据，完成采集，共 {current_count} 条"
                        )
                        break

                    current_start += BATCH_SIZE
                    self._update_code_progress(
                        pure_code,
                        frequency,
                        current_start,
                        total_fetched,
                        completed=False,
                    )

                    if batch_count % 5 == 0:
                        logger.info(
                            f"{pure_code}: 采集进度 {current_count}/{TARGET_DATA_COUNT}"
                        )

                    time.sleep(0.1)

                if (i + 1) % 10 == 0:
                    logger.info(
                        f"Progress: {i + 1}/{len(codes)}, success={success}, skipped={skipped}, failed={failed}"
                    )

            except Exception as e:
                logger.error(f"Error processing {code}: {e}")
                failed += 1
                continue

        logger.info(
            f"Daily kline fetch completed: total={len(codes)}, success={success}, skipped={skipped}, failed={failed}"
        )
        return {"success": success, "skipped": skipped, "failed": failed}

    def fetch_5min_klines(
        self,
        codes: List[str] = None,
        adjust: str = "qfq",
        skip_existing: bool = True,
    ):
        if codes is None:
            codes = self._get_all_stock_codes()

        self.progress = self._load_progress()
        frequency = 0
        success = 0
        skipped = 0
        failed = 0

        for i, code in enumerate(codes):
            try:
                pure_code = code.split(".")[-1]

                if skip_existing:
                    self._ensure_storage()
                    today = datetime.now().strftime("%Y-%m-%d")
                    existing = self.storage.kline_collection.count_documents(
                        {
                            "code": pure_code,
                            "date": {"$regex": f"^{today}"},
                            "frequency": frequency,
                        }
                    )
                    if existing > 0:
                        skipped += 1
                        if (i + 1) % 100 == 0:
                            logger.info(
                                f"Progress: {i + 1}/{len(codes)}, success={success}, skipped={skipped}, failed={failed}"
                            )
                        continue

                records = self._fetch_kline(
                    pure_code,
                    frequency=frequency,
                    start=0,
                    count=BATCH_SIZE,
                    adjust=adjust,
                )
                if records:
                    self.save_klines(records, frequency=frequency)
                    success += 1
                else:
                    failed += 1

                if (i + 1) % 50 == 0:
                    logger.info(
                        f"Progress: {i + 1}/{len(codes)}, success={success}, skipped={skipped}, failed={failed}"
                    )

                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error processing {code}: {e}")
                failed += 1
                continue

        logger.info(
            f"5min kline fetch completed: total={len(codes)}, success={success}, skipped={skipped}, failed={failed}"
        )
        return {"success": success, "skipped": skipped, "failed": failed}

    def close(self):
        if self.storage:
            self.storage.close()


def run_daily_job():
    scraper = StockKlineScraper()
    try:
        logger.info("Starting daily stock kline fetch job...")
        result = scraper.fetch_daily_klines(adjust="qfq", skip_existing=True)
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
        result = scraper.fetch_5min_klines(adjust="qfq", skip_existing=True)
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
    parser.add_argument(
        "--mode",
        choices=["daily", "5min", "both"],
        default="daily",
        help="Fetch mode: daily (freq=9), 5min (freq=0), or both",
    )
    parser.add_argument(
        "--codes",
        type=str,
        default=None,
        help="Comma-separated stock codes, or leave empty to auto-detect",
    )
    args = parser.parse_args()

    codes = args.codes.split(",") if args.codes else None

    scraper = StockKlineScraper()
    try:
        if args.mode == "daily":
            result = scraper.fetch_daily_klines(codes=codes)
            print(f"Daily result: {result}")
        elif args.mode == "5min":
            result = scraper.fetch_5min_klines(codes=codes)
            print(f"5min result: {result}")
        else:
            r1 = scraper.fetch_daily_klines(codes=codes)
            print(f"Daily result: {r1}")
            r2 = scraper.fetch_5min_klines(codes=codes)
            print(f"5min result: {r2}")
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
    parser.add_argument(
        "--mode",
        choices=["daily", "5min", "both"],
        default="daily",
        help="Fetch mode: daily (freq=9), 5min (freq=0), or both",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=100,
        help="Number of days/bars to fetch (default: 100)",
    )
    parser.add_argument(
        "--codes",
        type=str,
        default=None,
        help="Comma-separated stock codes, or leave empty to auto-detect",
    )
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
