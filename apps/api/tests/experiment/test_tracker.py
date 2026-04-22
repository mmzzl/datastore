"""Unit tests for ExperimentTracker.

Tests experiment recording, querying, comparison, and edge cases
using mocked MongoDB collection.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from collections import OrderedDict

from app.experiment.tracker import ExperimentTracker


@pytest.fixture
def mock_collection():
    """Create a mock MongoDB collection."""
    collection = MagicMock()
    collection.insert_one = MagicMock(return_value=MagicMock(inserted_id="mock_id"))
    collection.create_index = MagicMock()
    return collection


@pytest.fixture
def mock_mongo_client(mock_collection):
    """Create a mock MongoStorage with a db that returns the mock collection."""
    client = MagicMock()
    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(return_value=mock_collection)
    client.db = mock_db
    client.close = MagicMock()
    return client


@pytest.fixture
def tracker(mock_mongo_client, mock_collection):
    """Create an ExperimentTracker with a mocked MongoDB client."""
    t = ExperimentTracker(mongo_client=mock_mongo_client)
    t._collection = mock_collection
    return t


class TestRecordExperiment:
    def test_record_completed_experiment(self, tracker, mock_collection):
        config = {"model_type": "lgbm", "factor_type": "alpha158", "n_estimators": 1000}
        metrics = {"ic": 0.05, "rank_ic": 0.04, "icir": 0.3, "long_short_return": 0.08}
        backtest = {"sharpe_ratio": 1.8, "annual_return": 0.25, "max_drawdown": 0.15}

        exp_id = tracker.record_experiment(
            tag="weekly_lgbm_search",
            config=config,
            training_metrics=metrics,
            backtest_result=backtest,
            model_id="model_20260421_183000",
            status="completed",
        )

        assert exp_id.startswith("exp_")
        mock_collection.insert_one.assert_called_once()

        inserted_doc = mock_collection.insert_one.call_args[0][0]
        assert inserted_doc["tag"] == "weekly_lgbm_search"
        assert inserted_doc["config"] == config
        assert inserted_doc["training_metrics"] == metrics
        assert inserted_doc["backtest_result"] == backtest
        assert inserted_doc["model_id"] == "model_20260421_183000"
        assert inserted_doc["status"] == "completed"
        assert inserted_doc["error"] is None
        assert inserted_doc["completed_at"] is not None

    def test_record_skipped_experiment(self, tracker, mock_collection):
        config = {"model_type": "lgbm", "factor_type": "alpha158"}
        metrics = {"ic": 0.01, "rank_ic": 0.01}

        exp_id = tracker.record_experiment(
            tag="test",
            config=config,
            training_metrics=metrics,
            backtest_result=None,
            model_id="model_low_ic",
            status="skipped_low_ic",
        )

        inserted_doc = mock_collection.insert_one.call_args[0][0]
        assert inserted_doc["status"] == "skipped_low_ic"
        assert inserted_doc["backtest_result"] is None
        assert inserted_doc["completed_at"] is not None

    def test_record_failed_experiment(self, tracker, mock_collection):
        config = {"model_type": "lgbm"}

        exp_id = tracker.record_experiment(
            tag="test",
            config=config,
            training_metrics=None,
            backtest_result=None,
            model_id=None,
            status="failed",
            error="Training failed: RuntimeError",
        )

        inserted_doc = mock_collection.insert_one.call_args[0][0]
        assert inserted_doc["status"] == "failed"
        assert inserted_doc["error"] == "Training failed: RuntimeError"
        assert inserted_doc["training_metrics"] is None
        assert inserted_doc["backtest_result"] is None

    def test_record_experiment_no_tag(self, tracker, mock_collection):
        exp_id = tracker.record_experiment(
            tag=None,
            config={},
            training_metrics={},
            backtest_result={},
            model_id="model_1",
            status="completed",
        )

        inserted_doc = mock_collection.insert_one.call_args[0][0]
        assert inserted_doc["tag"] is None


class TestGetByTag:
    def test_get_by_tag_returns_results(self, tracker, mock_collection):
        mock_docs = [
            {"experiment_id": "exp_1", "tag": "test", "status": "completed"},
            {"experiment_id": "exp_2", "tag": "test", "status": "completed"},
        ]
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.limit.return_value = iter(mock_docs)
        mock_collection.find.return_value = mock_cursor

        results = tracker.get_by_tag("test")

        assert len(results) == 2
        mock_collection.find.assert_called_once_with({"tag": "test"})

    def test_get_by_tag_empty(self, tracker, mock_collection):
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.limit.return_value = iter([])
        mock_collection.find.return_value = mock_cursor

        results = tracker.get_by_tag("nonexistent")
        assert results == []

    def test_get_by_tag_with_sort_and_limit(self, tracker, mock_collection):
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.limit.return_value = iter([])
        mock_collection.find.return_value = mock_cursor

        tracker.get_by_tag("test", sort_by="training_metrics.rank_ic", limit=5)

        mock_cursor.sort.assert_called_once_with("training_metrics.rank_ic", -1)
        mock_cursor.sort.return_value.limit.assert_called_once_with(5)


class TestGetBest:
    def test_get_best_by_sharpe(self, tracker, mock_collection):
        best_doc = {
            "experiment_id": "exp_best",
            "backtest_result": {"sharpe_ratio": 2.5},
            "status": "completed",
        }
        mock_collection.find_one.return_value = best_doc

        result = tracker.get_best("backtest_result.sharpe_ratio")

        assert result is not None
        assert result["experiment_id"] == "exp_best"
        mock_collection.find_one.assert_called_once()
        call_kwargs = mock_collection.find_one.call_args
        query = call_kwargs[0][0] if call_kwargs[0] else call_kwargs.kwargs.get("filter", {})
        assert query["status"] == "completed"

    def test_get_best_with_tag_filter(self, tracker, mock_collection):
        mock_collection.find_one.return_value = {
            "experiment_id": "exp_tagged_best",
            "tag": "weekly_lgbm_search",
            "status": "completed",
        }

        result = tracker.get_best("training_metrics.rank_ic", tag="weekly_lgbm_search")

        assert result is not None
        call_args = mock_collection.find_one.call_args
        query = call_args[0][0]
        assert query["tag"] == "weekly_lgbm_search"

    def test_get_best_no_results(self, tracker, mock_collection):
        mock_collection.find_one.return_value = None

        result = tracker.get_best("backtest_result.sharpe_ratio")
        assert result is None


class TestCompare:
    def test_compare_experiments(self, tracker, mock_collection):
        docs = {
            "exp_001": {
                "experiment_id": "exp_001",
                "config": {"model_type": "lgbm"},
                "training_metrics": {"ic": 0.05},
                "backtest_result": {"sharpe_ratio": 1.8},
                "status": "completed",
                "created_at": datetime.now(),
            },
            "exp_002": {
                "experiment_id": "exp_002",
                "config": {"model_type": "mlp"},
                "training_metrics": {"ic": 0.03},
                "backtest_result": {"sharpe_ratio": 1.2},
                "status": "completed",
                "created_at": datetime.now(),
            },
        }
        mock_collection.find_one.side_effect = lambda q: docs.get(q.get("experiment_id"))

        result = tracker.compare(["exp_001", "exp_002"])

        assert len(result) == 2
        assert result["exp_001"]["config"]["model_type"] == "lgbm"
        assert result["exp_002"]["config"]["model_type"] == "mlp"

    def test_compare_with_missing_experiment(self, tracker, mock_collection):
        mock_collection.find_one.side_effect = lambda q: None

        result = tracker.compare(["nonexistent"])
        assert len(result) == 0

    def test_compare_mixed_found_and_missing(self, tracker, mock_collection):
        doc = {
            "experiment_id": "exp_001",
            "config": {},
            "training_metrics": {},
            "backtest_result": {},
            "status": "completed",
            "created_at": datetime.now(),
        }

        def find_side_effect(query):
            if query.get("experiment_id") == "exp_001":
                return doc
            return None

        mock_collection.find_one.side_effect = find_side_effect

        result = tracker.compare(["exp_001", "exp_missing"])
        assert len(result) == 1
        assert "exp_001" in result


class TestNoCollection:
    def test_operations_with_no_collection(self):
        tracker = ExperimentTracker.__new__(ExperimentTracker)
        tracker._mongo_client = None
        tracker._collection_name = "experiments"
        tracker._collection = None

        assert tracker.collection is None
        assert tracker.get_by_tag("test") == []
        assert tracker.get_best("metric") is None
        assert tracker.compare(["exp_1"]) == {}

        exp_id = tracker.record_experiment(
            tag="test", config={}, training_metrics={}, backtest_result={}, model_id="m1", status="completed"
        )
        assert exp_id.startswith("exp_")
