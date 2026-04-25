import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TopStocksManager:

    COLLECTION_NAME = "qlib_top_stocks"

    def __init__(self, mongo_client: Any = None):
        self._mongo_client = mongo_client
        self._collection = None

        if self._mongo_client is None:
            self._init_collection()

    def _init_collection(self) -> None:
        if self._mongo_client is None:
            try:
                from ..storage import MongoStorage
                from ..core.config import settings

                self._mongo_client = MongoStorage(
                    host=settings.mongodb_host,
                    port=settings.mongodb_port,
                    db_name=settings.mongodb_database,
                    username=settings.mongodb_username,
                    password=settings.mongodb_password,
                )
                self._mongo_client.connect()
            except Exception as e:
                logger.warning(f"Could not initialize MongoDB client: {e}")
                self._mongo_client = None

    @property
    def collection(self) -> Any:
        if self._collection is None and self._mongo_client is not None:
            try:
                self._collection = self._mongo_client.db[self.COLLECTION_NAME]
                self._collection.create_index([("date", -1)])
                self._collection.create_index([("model_id", 1), ("date", -1)])
            except Exception as e:
                logger.error(f"Failed to get collection: {e}")
        return self._collection

    def save_top_stocks(
        self,
        date: str,
        model_id: str,
        model_type: str,
        factor: str,
        stocks: List[Dict[str, Any]],
    ) -> str:
        document = {
            "date": date,
            "model_id": model_id,
            "model_type": model_type,
            "factor": factor,
            "stocks": stocks,
            "created_at": datetime.now(),
        }

        if self.collection is not None:
            try:
                self.collection.replace_one(
                    {"date": date, "model_id": model_id},
                    document,
                    upsert=True,
                )
                logger.info(f"Top stocks saved: date={date}, model_id={model_id}, count={len(stocks)}")
            except Exception as e:
                logger.error(f"Failed to save top stocks: {e}")

        return date

    def get_top_stocks(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if self.collection is None:
            return []

        try:
            query: Dict[str, Any] = {}
            date_filter: Dict[str, Any] = {}

            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date

            if date_filter:
                query["date"] = date_filter

            if model_id:
                query["model_id"] = model_id

            cursor = self.collection.find(query).sort("date", -1)

            results = []
            for doc in cursor:
                doc.pop("_id", None)
                results.append(doc)

            return results

        except Exception as e:
            logger.error(f"Failed to get top stocks: {e}")
            return []

    def get_latest_top_stocks(self, model_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if self.collection is None:
            return None

        try:
            query: Dict[str, Any] = {}
            if model_id:
                query["model_id"] = model_id

            doc = self.collection.find_one(query, sort=[("date", -1)])
            if doc:
                doc.pop("_id", None)
                return doc

        except Exception as e:
            logger.error(f"Failed to get latest top stocks: {e}")

        return None

    def close(self) -> None:
        if self._mongo_client is not None:
            try:
                self._mongo_client.close()
            except Exception:
                pass
