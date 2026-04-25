from unittest.mock import MagicMock
from app.experiment.tracker import ExperimentTracker


def _make_tracker(mock_collection):
    tracker = ExperimentTracker.__new__(ExperimentTracker)
    tracker._mongo_client = MagicMock()
    tracker._collection_name = "experiments"
    tracker._collection = mock_collection
    return tracker


def test_list_experiments_with_defaults():
    col = MagicMock()
    col.count_documents.return_value = 2
    col.find.return_value.sort.return_value.skip.return_value.limit.return_value = iter([
        {
            "experiment_id": "exp_001",
            "tag": "weekly",
            "config": {"model_type": "lgbm"},
            "training_metrics": {"ic": 0.05},
            "backtest_result": {"sharpe_ratio": 1.5},
            "model_id": "model_001",
            "status": "completed",
            "created_at": "2026-04-25T10:00:00",
            "error": None,
        },
        {
            "experiment_id": "exp_002",
            "tag": "weekly",
            "config": {"model_type": "mlp"},
            "training_metrics": {"ic": 0.03},
            "backtest_result": None,
            "model_id": None,
            "status": "failed",
            "created_at": "2026-04-25T11:00:00",
            "error": "OOM",
        },
    ])

    tracker = _make_tracker(col)
    results, total = tracker.list_experiments()

    assert total == 2
    assert len(results) == 2
    assert results[0]["experiment_id"] == "exp_001"
    col.find.assert_called_once_with({})


def test_list_experiments_with_filters():
    col = MagicMock()
    col.count_documents.return_value = 1
    col.find.return_value.sort.return_value.skip.return_value.limit.return_value = iter([])

    tracker = _make_tracker(col)
    results, total = tracker.list_experiments(
        tag="weekly", status="completed", page=1, page_size=10
    )

    col.find.assert_called_once_with({"tag": "weekly", "status": "completed"})


def test_list_experiments_no_collection():
    tracker = ExperimentTracker.__new__(ExperimentTracker)
    tracker._mongo_client = None
    tracker._collection_name = "experiments"
    tracker._collection = None

    results, total = tracker.list_experiments()

    assert results == []
    assert total == 0
