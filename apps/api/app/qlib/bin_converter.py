"""
Qlib Binary Data Converter

Converts MongoDB K-line data into Qlib's native binary file format,
enabling the ML pipeline to use fresh MongoDB data instead of stale cn_data.

Binary format reference (from qlib FileFeatureStorage):
  - calendars/day.txt: one date per line, 0-based index is start_index in bins
  - instruments/all.txt: tab-separated instrument\tstart_date\tend_date
  - features/<instrument>/<field>.day.bin: float32 LE [start_index, val0, val1, ...]
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..storage.mongo_client import MongoStorage

logger = logging.getLogger(__name__)

FEATURE_FIELDS = ["open", "high", "low", "close", "volume", "amount", "factor"]
FREQUENCY_DAILY = 9


class QlibBinConverter:
    """Converts MongoDB K-line data to Qlib binary format.

    Args:
        target_dir: Output directory for Qlib data (default ./qlib_data/cn_data)
        storage: MongoStorage instance for reading K-line data
    """

    def __init__(
        self,
        target_dir: str = "./qlib_data/cn_data",
        storage: Optional[MongoStorage] = None,
    ):
        self.target_dir = Path(target_dir)
        self.storage = storage
        self._calendar_cache: Optional[List[str]] = None

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """Strip time suffix from MongoDB date strings.

        '2015-12-07 15:00' -> '2015-12-07'
        '2024-03-15' -> '2024-03-15'
        """
        return date_str.split(" ")[0].strip()

    @staticmethod
    def _code_to_qlib_instrument(code: str) -> str:
        """Convert MongoDB stock code to qlib instrument format.

        '600519' -> 'SH600519', '000001' -> 'SZ000001', '300001' -> 'SZ300001'
        """
        code = code.strip()
        if code.startswith(("SH", "SZ", "sh", "sz")):
            return code.upper()
        if code.startswith(("6",)):
            return f"SH{code}"
        return f"SZ{code}"

    @staticmethod
    def _code_to_feature_dir(code: str) -> str:
        """Convert stock code to lowercase feature directory name.

        '600519' -> 'sh600519', '000001' -> 'sz000001'
        """
        code = code.strip()
        if code.startswith(("SH", "sh", "SZ", "sz")):
            return code.lower()
        if code.startswith(("6",)):
            return f"sh{code}"
        return f"sz{code}"

    def _ensure_storage(self) -> MongoStorage:
        if self.storage is None:
            from ..core.config import settings
            self.storage = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_database,
                username=settings.mongodb_username,
                password=settings.mongodb_password,
            )
            self.storage.connect()
        return self.storage

    # ------------------------------------------------------------------
    # Calendar & Instruments
    # ------------------------------------------------------------------

    def _build_calendar(self) -> List[str]:
        """Query MongoDB for all distinct daily trading dates, sorted ascending."""
        storage = self._ensure_storage()
        col = storage.kline_collection
        if col is None:
            storage.connect()

        dates = col.distinct("date", {"frequency": FREQUENCY_DAILY})
        normalized = sorted({self._normalize_date(d) for d in dates if d})
        logger.info(f"Built calendar with {len(normalized)} trading dates")
        return normalized

    def _build_instruments(self, instruments: Optional[List[str]] = None) -> List[Tuple[str, str, str]]:
        """For each stock in MongoDB, compute (instrument, start_date, end_date).

        Args:
            instruments: Optional list of stock codes to filter by (e.g. ["600519", "000001"]).
                         If not provided, builds for all stocks.
        """
        storage = self._ensure_storage()
        col = storage.kline_collection
        if col is None:
            storage.connect()

        pipeline: List[Dict[str, Any]] = [
            {"$match": {"frequency": FREQUENCY_DAILY}},
        ]
        if instruments:
            pipeline[0]["$match"]["code"] = {"$in": instruments}
        pipeline.append({
            "$group": {
                "_id": "$code",
                "min_date": {"$min": "$date"},
                "max_date": {"$max": "$date"},
            },
        })
        results = list(col.aggregate(pipeline))

        instruments = []
        for r in results:
            raw_code = r["_id"]
            if not raw_code:
                continue
            instrument = self._code_to_qlib_instrument(raw_code)
            start = self._normalize_date(r["min_date"])
            end = self._normalize_date(r["max_date"])
            instruments.append((instrument, start, end))

        instruments.sort(key=lambda x: x[0])
        logger.info(f"Built instruments list with {len(instruments)} stocks")
        return instruments

    def _write_calendar(self, calendar: List[str]) -> int:
        """Write calendars/day.txt. If file exists, append only new dates.

        Returns number of new dates appended.
        """
        cal_file = self.target_dir / "calendars" / "day.txt"
        cal_file.parent.mkdir(parents=True, exist_ok=True)

        existing: set = set()
        if cal_file.exists():
            existing = set(cal_file.read_text(encoding="utf-8").strip().splitlines())

        new_dates = [d for d in calendar if d not in existing]
        if new_dates:
            with open(cal_file, "a", encoding="utf-8") as f:
                for d in new_dates:
                    f.write(d + "\n")
            logger.info(f"Calendar: appended {len(new_dates)} new dates (total {len(existing) + len(new_dates)})")
        else:
            logger.info("Calendar: no new dates to append")

        return len(new_dates)

    def _write_instruments(self, instruments: List[Tuple[str, str, str]]) -> int:
        inst_file = self.target_dir / "instruments" / "all.txt"
        inst_file.parent.mkdir(parents=True, exist_ok=True)

        existing_map: Dict[str, Tuple[str, str]] = {}
        if inst_file.exists():
            for line in inst_file.read_text(encoding="utf-8").strip().splitlines():
                parts = line.strip().split("\t")
                if len(parts) == 3:
                    existing_map[parts[0]] = (parts[1], parts[2])

        updated = 0
        for instrument, start, end in instruments:
            if instrument in existing_map:
                old_start, old_end = existing_map[instrument]
                new_start = min(old_start, start)
                new_end = max(old_end, end)
                if new_start != old_start or new_end != old_end:
                    existing_map[instrument] = (new_start, new_end)
                    updated += 1
            else:
                existing_map[instrument] = (start, end)
                updated += 1

        with open(inst_file, "w", encoding="utf-8") as f:
            for instrument in sorted(existing_map.keys()):
                s, e = existing_map[instrument]
                f.write(f"{instrument}\t{s}\t{e}\n")

        logger.info(f"Instruments: {updated} updated/added (total {len(existing_map)})")
        return updated

    def _write_pool_files(self, instruments_list: List[Tuple[str, str, str]]):
        """Generate per-pool instrument files (csi300.txt, csi500.txt) from all.txt.

        Uses the hardcoded stock lists from config.py to filter all.txt entries.
        """
        from .config import CSI_300_STOCKS, CSI_500_STOCKS
        inst_dir = self.target_dir / "instruments"
        all_instruments = {inst: (s, e) for inst, s, e in instruments_list}

        for pool_name, stock_codes in [("csi300", CSI_300_STOCKS), ("csi500", CSI_500_STOCKS)]:
            pool_file = inst_dir / f"{pool_name}.txt"
            entries = []
            for code in stock_codes:
                instrument = self._code_to_qlib_instrument(code)
                if instrument in all_instruments:
                    s, e = all_instruments[instrument]
                    entries.append((instrument, s, e))
            entries.sort(key=lambda x: x[0])
            with open(pool_file, "w", encoding="utf-8") as f:
                for inst, s, e in entries:
                    f.write(f"{inst}\t{s}\t{e}\n")
            logger.info(f"Written {len(entries)} stocks to instruments/{pool_name}.txt")

    # ------------------------------------------------------------------
    # Feature Binary Files
    # ------------------------------------------------------------------

    def _load_calendar(self) -> List[str]:
        """Load calendar from file, cache in memory."""
        if self._calendar_cache is not None:
            return self._calendar_cache

        cal_file = self.target_dir / "calendars" / "day.txt"
        if not cal_file.exists():
            return []
        self._calendar_cache = cal_file.read_text(encoding="utf-8").strip().splitlines()
        return self._calendar_cache

    def _date_to_calendar_index(self, date_str: str) -> int:
        """Map a date string to its 0-based index in calendars/day.txt.

        Returns -1 if not found.
        """
        calendar = self._load_calendar()
        try:
            return calendar.index(date_str)
        except ValueError:
            return -1

    @staticmethod
    def _read_bin(bin_path: Path) -> Optional[np.ndarray]:
        """Read an existing bin file as float32 numpy array.

        Returns None if file does not exist or is empty.
        """
        if not bin_path.exists() or bin_path.stat().st_size == 0:
            return None
        return np.fromfile(str(bin_path), dtype="<f")

    @staticmethod
    def _write_bin(bin_path: Path, data: np.ndarray) -> None:
        """Write float32 numpy array to bin file atomically."""
        bin_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = bin_path.with_suffix(".tmp")
        data.astype("<f").tofile(str(tmp_path))
        tmp_path.replace(bin_path)

    def _write_feature_bin(
        self,
        instrument_dir: str,
        field: str,
        start_index: int,
        values: np.ndarray,
    ) -> None:
        """Write a single stock+field bin file.

        Creates [start_index, val0, val1, ...] as float32 LE.
        If bin file already exists, merges using append/rewrite logic.
        """
        bin_path = self.target_dir / "features" / instrument_dir / f"{field}.day.bin"
        existing = self._read_bin(bin_path)

        if existing is None or len(existing) == 0:
            new_data = np.concatenate([[np.float32(start_index)], values.astype("<f")])
            self._write_bin(bin_path, new_data)
            return

        old_start = int(existing[0])
        old_values = existing[1:]
        old_end = old_start + len(old_values) - 1
        new_end = start_index + len(values) - 1

        if start_index > old_end:
            gap = start_index - old_end - 1
            merged = np.concatenate([
                old_values,
                np.full(gap, np.nan, dtype=np.float32),
                values.astype(np.float32),
            ])
        elif new_end > old_end:
            overlap = old_end - start_index + 1
            merged = old_values.copy()
            merged[start_index - old_start: start_index - old_start + overlap] = values[:overlap].astype(np.float32)
            merged = np.concatenate([merged, values[overlap:].astype(np.float32)])
        else:
            merged = old_values.copy()
            merged[start_index - old_start: start_index - old_start + len(values)] = values.astype(np.float32)

        new_data = np.concatenate([[np.float32(old_start)], merged.astype(np.float32)])
        self._write_bin(bin_path, new_data)

    def _incremental_update_bin(
        self,
        instrument_dir: str,
        field: str,
        start_index: int,
        values: np.ndarray,
    ) -> None:
        """Incrementally update a bin file (delegate to _write_feature_bin)."""
        self._write_feature_bin(instrument_dir, field, start_index, values)

    # ------------------------------------------------------------------
    # High-level conversion methods
    # ------------------------------------------------------------------

    def full_convert(self, instruments: Optional[List[str]] = None) -> Dict[str, int]:
        """Full rebuild: create calendar, instruments, and all feature bins.

        Args:
            instruments: Optional list of stock codes to convert (e.g. ["600519", "000001"]).
                         If not provided, converts all stocks.

        Returns summary dict with counts.
        """
        import time
        start_time = time.time()

        logger.info("Starting full Qlib data conversion...")

        calendar = self._build_calendar()
        self._write_calendar(calendar)
        instrument_list = self._build_instruments(instruments)
        self._write_instruments(instrument_list)
        self._write_pool_files(instrument_list)

        storage = self._ensure_storage()
        col = storage.kline_collection
        if col is None:
            storage.connect()
            col = storage.kline_collection

        cal_list = self._load_calendar()
        cal_index_map = {d: i for i, d in enumerate(cal_list)}
        stocks_written = 0

        total = len(instrument_list)
        for idx, (instrument, _start, _end) in enumerate(instrument_list):
            raw_code = instrument[2:]
            try:
                docs = list(col.find(
                    {"code": raw_code, "frequency": FREQUENCY_DAILY},
                    {"date": 1, "open": 1, "high": 1, "low": 1, "close": 1,
                     "volume": 1, "amount": 1, "_id": 0},
                ).sort("date", 1))

                if not docs:
                    continue

                inst_dir = self._code_to_feature_dir(raw_code)

                date_indices = []
                field_arrays: Dict[str, List[float]] = {f: [] for f in FEATURE_FIELDS}

                for doc in docs:
                    norm_date = self._normalize_date(doc.get("date", ""))
                    ci = cal_index_map.get(norm_date, -1)
                    if ci < 0:
                        continue
                    date_indices.append(ci)
                    field_arrays["open"].append(float(doc.get("open", np.nan)))
                    field_arrays["high"].append(float(doc.get("high", np.nan)))
                    field_arrays["low"].append(float(doc.get("low", np.nan)))
                    field_arrays["close"].append(float(doc.get("close", np.nan)))
                    field_arrays["volume"].append(float(doc.get("volume", 0)))
                    field_arrays["amount"].append(float(doc.get("amount", 0)))
                    field_arrays["factor"].append(1.0)

                if not date_indices:
                    continue

                s_idx = date_indices[0]
                e_idx = date_indices[-1]
                span_len = e_idx - s_idx + 1

                for field in FEATURE_FIELDS:
                    full_arr = np.full(span_len, np.nan, dtype=np.float32)
                    for i, ci in enumerate(date_indices):
                        full_arr[ci - s_idx] = field_arrays[field][i]
                    self._write_feature_bin(inst_dir, field, s_idx, full_arr)

                stocks_written += 1

                if (idx + 1) % 500 == 0:
                    logger.info(f"Full convert: {idx + 1}/{total} stocks processed")

            except Exception as e:
                logger.error(f"Failed to convert {instrument}: {e}")
                continue

        elapsed = time.time() - start_time
        summary = {
            "stocks_written": stocks_written,
            "calendar_dates": len(calendar),
            "elapsed_seconds": round(elapsed, 2),
        }
        logger.info(f"Full conversion complete: {summary}")
        return summary

    def incremental_sync(self, instruments: Optional[List[str]] = None) -> Dict[str, int]:
        """Incremental update: append new dates, update only affected stocks.

        Args:
            instruments: Optional list of stock codes to sync (e.g. ["600519", "000001"]).
                         If not provided, syncs all stocks.

        Returns summary dict with counts.
        """
        import time
        start_time = time.time()

        logger.info("Starting incremental Qlib data sync...")

        cal_file = self.target_dir / "calendars" / "day.txt"
        if not cal_file.exists():
            logger.info("No existing data found, running full conversion instead")
            return self.full_convert(instruments)

        existing_calendar = self._load_calendar()
        if not existing_calendar:
            return self.full_convert(instruments)

        last_cal_date = existing_calendar[-1]
        new_calendar = self._build_calendar()
        new_dates = [d for d in new_calendar if d > last_cal_date]

        if not new_dates:
            elapsed = time.time() - start_time
            summary = {"new_dates": 0, "stocks_updated": 0, "elapsed_seconds": round(elapsed, 2)}
            logger.info(f"Incremental sync: no new data. {summary}")
            return summary

        self._write_calendar(new_calendar)
        self._calendar_cache = None

        updated_calendar = self._load_calendar()
        cal_index_map = {d: i for i, d in enumerate(updated_calendar)}

        storage = self._ensure_storage()
        col = storage.kline_collection
        if col is None:
            storage.connect()
            col = storage.kline_collection

        start_date_query = new_dates[0]

        pipeline: List[Dict[str, Any]] = [
            {"$match": {
                "frequency": FREQUENCY_DAILY,
                "date": {"$gte": start_date_query},
            }},
        ]
        if instruments:
            pipeline[0]["$match"]["code"] = {"$in": instruments}
        pipeline.append({"$group": {"_id": "$code"}})
        codes_with_new_data = [r["_id"] for r in col.aggregate(pipeline)]

        stocks_updated = 0
        for raw_code in codes_with_new_data:
            if not raw_code:
                continue
            try:
                docs = list(col.find(
                    {"code": raw_code, "frequency": FREQUENCY_DAILY, "date": {"$gte": start_date_query}},
                    {"date": 1, "open": 1, "high": 1, "low": 1, "close": 1,
                     "volume": 1, "amount": 1, "_id": 0},
                ).sort("date", 1))

                if not docs:
                    continue

                inst_dir = self._code_to_feature_dir(raw_code)

                date_indices = []
                field_arrays: Dict[str, List[float]] = {f: [] for f in FEATURE_FIELDS}

                for doc in docs:
                    norm_date = self._normalize_date(doc.get("date", ""))
                    ci = cal_index_map.get(norm_date, -1)
                    if ci < 0:
                        continue
                    date_indices.append(ci)
                    field_arrays["open"].append(float(doc.get("open", np.nan)))
                    field_arrays["high"].append(float(doc.get("high", np.nan)))
                    field_arrays["low"].append(float(doc.get("low", np.nan)))
                    field_arrays["close"].append(float(doc.get("close", np.nan)))
                    field_arrays["volume"].append(float(doc.get("volume", 0)))
                    field_arrays["amount"].append(float(doc.get("amount", 0)))
                    field_arrays["factor"].append(1.0)

                if not date_indices:
                    continue

                s_idx = date_indices[0]
                e_idx = date_indices[-1]
                span_len = e_idx - s_idx + 1

                for field in FEATURE_FIELDS:
                    full_arr = np.full(span_len, np.nan, dtype=np.float32)
                    for i, ci in enumerate(date_indices):
                        full_arr[ci - s_idx] = field_arrays[field][i]
                    self._incremental_update_bin(inst_dir, field, s_idx, full_arr)

                stocks_updated += 1

            except Exception as e:
                logger.error(f"Failed to incrementally update {raw_code}: {e}")
                continue

        instruments_list = self._build_instruments(instruments)
        self._write_instruments(instruments_list)
        self._write_pool_files(instruments_list)

        elapsed = time.time() - start_time
        summary = {
            "new_dates": len(new_dates),
            "stocks_updated": stocks_updated,
            "elapsed_seconds": round(elapsed, 2),
        }
        logger.info(f"Incremental sync complete: {summary}")
        return summary
