"""Experiment Tracker.

Stores and queries experiment records in MongoDB for model training
and evaluation comparison.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ExperimentTracker:
    """MongoDB-backed experiment record storage.

    Tracks model training experiments with their configurations,
    training metrics, and backtest results for comparison and
    reproducibility.

    Example:
        >>> tracker = ExperimentTracker()
        >>> exp_id = tracker.record_experiment(
        ...     tag="weekly_lgbm_search",
        ...     config={"model_type": "lgbm", "factor_type": "alpha158"},
        ...     training_metrics={"ic": 0.05, "rank_ic": 0.04},
        ...     backtest_result={"sharpe_ratio": 1.8},
        ...     model_id="model_20260421_183000",
        ...     status="completed",
        ... )
        >>> best = tracker.get_best("backtest_result.sharpe_ratio", tag="weekly_lgbm_search")
    """

    COLLECTION_NAME = "experiments"

    def __init__(
        self,
        mongo_client: Any = None,
        collection_name: str = "experiments",
    ):
        """Initialize the experiment tracker.

        Args:
            mongo_client: Optional MongoStorage instance
            collection_name: MongoDB collection name for experiment records
        """
        self._mongo_client = mongo_client
        self._collection_name = collection_name
        self._collection = None

        if self._mongo_client is None:
            self._init_collection()

    def _init_collection(self) -> None:
        """Initialize MongoDB collection lazily."""
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
        """Get MongoDB collection lazily."""
        if self._collection is None and self._mongo_client is not None:
            try:
                self._collection = self._mongo_client.db[self._collection_name]
                self._collection.create_index("experiment_id", unique=True)
                self._collection.create_index("tag")
                self._collection.create_index("status")
                self._collection.create_index("created_at")
            except Exception as e:
                logger.error(f"Failed to get collection: {e}")
        return self._collection

    def record_experiment(
        self,
        tag: Optional[str],
        config: Dict[str, Any],
        training_metrics: Optional[Dict[str, Any]],
        backtest_result: Optional[Dict[str, Any]],
        model_id: Optional[str],
        status: str,
        error: Optional[str] = None,
    ) -> str:
        """Record an experiment result.

        Args:
            tag: Optional experiment tag for grouping
            config: Training configuration (model_type, factor_type, hyperparams, etc.)
            training_metrics: Training metrics (ic, rank_ic, icir, long_short_return, etc.)
            backtest_result: Backtest results (sharpe_ratio, annual_return, max_drawdown, etc.)
            model_id: Reference to the trained model
            status: Experiment status ("completed", "skipped_low_ic", "failed")
            error: Error message if status is "failed"

        Returns:
            Experiment ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_id = f"exp_{timestamp}"

        document: Dict[str, Any] = {
            "experiment_id": experiment_id,
            "tag": tag,
            "config": config,
            "training_metrics": training_metrics,
            "backtest_result": backtest_result,
            "model_id": model_id,
            "status": status,
            "error": error,
            "created_at": datetime.now(),
            "completed_at": datetime.now() if status in ("completed", "skipped_low_ic", "failed") else None,
        }

        if self.collection is not None:
            try:
                self.collection.insert_one(document)
                logger.info(f"Experiment recorded: {experiment_id} (status={status})")
            except Exception as e:
                logger.error(f"Failed to record experiment: {e}")
                return experiment_id

        return experiment_id

    def list_experiments(
        self,
        tag: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple:
        if self.collection is None:
            return [], 0

        try:
            query: Dict[str, Any] = {}
            if tag:
                query["tag"] = tag
            if status:
                query["status"] = status

            total = self.collection.count_documents(query)

            skip = (page - 1) * page_size
            cursor = self.collection.find(query)
            cursor = cursor.sort("created_at", -1).skip(skip).limit(page_size)

            results = []
            for doc in cursor:
                doc.pop("_id", None)
                results.append(doc)

            return results, total

        except Exception as e:
            logger.error(f"Failed to list experiments: {e}")
            return [], 0

    def get_by_tag(
        self,
        tag: str,
        sort_by: str = "created_at",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query experiments by tag.

        Args:
            tag: Experiment tag to filter by
            sort_by: Field to sort by (default: created_at)
            limit: Maximum number of results

        Returns:
            List of experiment documents
        """
        if self.collection is None:
            return []

        try:
            cursor = self.collection.find({"tag": tag})
            cursor = cursor.sort(sort_by, -1).limit(limit)

            results = []
            for doc in cursor:
                doc.pop("_id", None)
                results.append(doc)

            return results

        except Exception as e:
            logger.error(f"Failed to query experiments by tag: {e}")
            return []

    def get_best(
        self,
        metric: str,
        tag: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Find the best experiment by a numeric metric.

        Args:
            metric: Dot-notation metric path (e.g., "backtest_result.sharpe_ratio",
                     "training_metrics.rank_ic")
            tag: Optional tag to filter by

        Returns:
            Best experiment document, or None if not found
        """
        if self.collection is None:
            return None

        try:
            query: Dict[str, Any] = {
                "status": "completed",
                metric: {"$exists": True},
            }
            if tag is not None:
                query["tag"] = tag

            doc = self.collection.find_one(
                query,
                sort=[(metric, -1)],
            )

            if doc:
                doc.pop("_id", None)

            return doc

        except Exception as e:
            logger.error(f"Failed to get best experiment: {e}")
            return None

    def compare(
        self,
        experiment_ids: List[str],
    ) -> Dict[str, Dict[str, Any]]:
        """Compare multiple experiments by their metrics.

        Args:
            experiment_ids: List of experiment IDs to compare

        Returns:
            Dictionary mapping experiment_id to {config, training_metrics, backtest_result, status}
        """
        if self.collection is None:
            return {}

        comparison: Dict[str, Dict[str, Any]] = {}

        for exp_id in experiment_ids:
            try:
                doc = self.collection.find_one({"experiment_id": exp_id})
                if doc:
                    doc.pop("_id", None)
                    comparison[exp_id] = {
                        "config": doc.get("config", {}),
                        "training_metrics": doc.get("training_metrics", {}),
                        "backtest_result": doc.get("backtest_result", {}),
                        "status": doc.get("status", "unknown"),
                        "created_at": doc.get("created_at"),
                    }
            except Exception as e:
                logger.error(f"Failed to get experiment {exp_id}: {e}")

        return comparison

    def close(self) -> None:
        """Close MongoDB connection."""
        if self._mongo_client is not None:
            try:
                self._mongo_client.close()
            except Exception:
                pass
