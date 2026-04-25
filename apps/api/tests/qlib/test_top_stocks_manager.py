from unittest.mock import MagicMock
from app.qlib.top_stocks_manager import TopStocksManager


def _make_manager(mock_collection):
    manager = TopStocksManager.__new__(TopStocksManager)
    manager._mongo_client = MagicMock()
    manager._collection = mock_collection
    return manager


def test_save_top_stocks():
    col = MagicMock()
    manager = _make_manager(col)

    stocks = [
        {"rank": 1, "code": "SH600000", "name": "test1", "score": 0.85},
        {"rank": 2, "code": "SH600519", "name": "test2", "score": 0.82},
    ]

    manager.save_top_stocks(
        date="2026-04-25",
        model_id="model_001",
        model_type="lgbm",
        factor="alpha158",
        stocks=stocks,
    )

    col.replace_one.assert_called_once()
    call_args = col.replace_one.call_args
    assert call_args[0][1]["date"] == "2026-04-25"
    assert call_args[0][1]["model_id"] == "model_001"
    assert len(call_args[0][1]["stocks"]) == 2


def test_get_top_stocks_by_date_range():
    col = MagicMock()
    col.find.return_value.sort.return_value = iter([
        {"date": "2026-04-25", "stocks": [], "model_id": "m1"},
        {"date": "2026-04-24", "stocks": [], "model_id": "m1"},
    ])

    manager = _make_manager(col)
    results = manager.get_top_stocks(start_date="2026-04-24", end_date="2026-04-25")

    query = col.find.call_args[0][0]
    assert "date" in query
    assert "$gte" in query["date"]
    assert "$lte" in query["date"]
    assert len(results) == 2


def test_get_latest_top_stocks():
    col = MagicMock()
    col.find_one.return_value = {
        "date": "2026-04-25",
        "model_id": "m1",
        "stocks": [{"rank": 1, "code": "SH600000", "name": "test", "score": 0.85}],
    }

    manager = _make_manager(col)
    result = manager.get_latest_top_stocks()

    col.find_one.assert_called_once()
    assert result["date"] == "2026-04-25"


def test_get_latest_top_stocks_empty():
    col = MagicMock()
    col.find_one.return_value = None

    manager = _make_manager(col)
    result = manager.get_latest_top_stocks()

    assert result is None


def test_get_top_stocks_no_collection():
    manager = TopStocksManager.__new__(TopStocksManager)
    manager._mongo_client = None
    manager._collection = None

    results = manager.get_top_stocks()
    assert results == []

    result = manager.get_latest_top_stocks()
    assert result is None
