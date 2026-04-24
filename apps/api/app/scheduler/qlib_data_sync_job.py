"""
Qlib Data Sync Job

Synchronizes MongoDB K-line data to Qlib binary format.
Runs after daily K-line scraping to keep qlib data fresh.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..qlib.bin_converter import QlibBinConverter
from ..qlib.config import QlibConfig
from ..core.config import settings

logger = logging.getLogger(__name__)


class QlibDataSyncJob:
    """Syncs MongoDB K-line data to Qlib binary format."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._converter: Optional[QlibBinConverter] = None

    def _get_converter(self) -> QlibBinConverter:
        if self._converter is None:
            from ..storage.mongo_client import MongoStorage
            storage = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_database,
                username=settings.mongodb_username,
                password=settings.mongodb_password,
            )
            storage.connect()
            self._converter = QlibBinConverter(
                target_dir=QlibConfig.provider_uri,
                storage=storage,
            )
        return self._converter

    async def run(self, mode: str = "incremental") -> Dict[str, Any]:
        start_time = datetime.now()
        logger.info(f"QlibDataSyncJob starting in {mode} mode")

        try:
            converter = self._get_converter()

            if mode == "full":
                result = await asyncio.to_thread(converter.full_convert)
            else:
                result = await asyncio.to_thread(converter.incremental_sync)

            elapsed = (datetime.now() - start_time).total_seconds()
            result["mode"] = mode
            result["elapsed_seconds"] = round(elapsed, 2)

            logger.info(f"QlibDataSyncJob completed: {result}")
            return result

        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"QlibDataSyncJob failed: {e}")
            return {
                "mode": mode,
                "error": str(e),
                "elapsed_seconds": round(elapsed, 2),
            }
        finally:
            if self._converter and self._converter.storage:
                try:
                    self._converter.storage.close()
                except Exception:
                    pass


async def qlib_data_sync_handler(config: Dict[str, Any], mode: str = "incremental") -> Dict[str, Any]:
    job = QlibDataSyncJob(config)
    return await job.run(mode=mode)
