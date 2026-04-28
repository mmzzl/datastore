"""Write the implementation plan document."""
import os

plan_path = r"D:\datastore\docs\superpowers\plans\2026-04-25-qlib-model-page-redesign.md"

content = """# Qlib Model Page Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the Qlib model page into a 3-tab layout showing training history, best model info, and daily Top10 stock recommendations with date range filtering.

**Architecture:** Backend adds 5 new API endpoints querying the existing `experiments` MongoDB collection and a new `qlib_top_stocks` collection. A scheduled job auto-generates Top10 predictions daily. Frontend replaces the single-page QlibSelectView with a tabbed layout using 3 sub-components.

**Tech Stack:** FastAPI, MongoDB (pymongo), Pydantic, Vue 3 + Naive UI + Pinia, APScheduler

---

## File Structure

### Backend - Create
- `apps/api/app/qlib/top_stocks_manager.py` - MongoDB CRUD for `qlib_top_stocks` collection

### Backend - Modify
- `apps/api/app/experiment/tracker.py` - Add `list_experiments()` with pagination
- `apps/api/app/api/endpoints/qlib.py` - Add 5 endpoints + Pydantic models
- `apps/api/app/qlib/__init__.py` - Export TopStocksManager
- `apps/api/app/scheduler/qlib_top_stocks_job.py` - New daily job (CREATE)
- `apps/api/app/scheduler/__init__.py` - Export QlibTopStocksJob
- `apps/api/scheduler_standalone.py` - Register cron job

### Frontend - Create
- `frontend/vue-admin/src/views/qlib/QlibTrainHistory.vue`
- `frontend/vue-admin/src/views/qlib/QlibBestModel.vue`
- `frontend/vue-admin/src/views/qlib/QlibTopStocks.vue`

### Frontend - Modify
- `frontend/vue-admin/src/views/QlibSelectView.vue` - Replace with 3-tab layout
- `frontend/vue-admin/src/services/api_qlib.ts` - Add 5 API methods + interfaces
- `frontend/vue-admin/src/stores/qlib.ts` - Add experiments, bestModel, topStocks state

---

### Task 1: Add `list_experiments()` to ExperimentTracker

**Files:**
- Modify: `apps/api/app/experiment/tracker.py`
- Test: `apps/api/tests/experiment/test_tracker_list.py`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/experiment/test_tracker_list.py`:

```python
import pytest
from unittest.mock import MagicMock
from app.experiment.tracker import ExperimentTracker


@pytest.fixture
def mock_collection():
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
    return col


def test_list_experiments_with_defaults(mock_collection):
    tracker = ExperimentTracker.__new__(ExperimentTracker)
    tracker._mongo_client = MagicMock()
    tracker._collection_name = "experiments"
    tracker._collection = mock_collection

    results, total = tracker.list_experiments()

    assert total == 2
    assert len(results) == 2
    assert results[0]["experiment_id"] == "exp_001"
    mock_collection.find.assert_called_once_with({})


def test_list_experiments_with_filters(mock_collection):
    tracker = ExperimentTracker.__new__(ExperimentTracker)
    tracker._mongo_client = MagicMock()
    tracker._collection_name = "experiments"
    tracker._collection = mock_collection

    results, total = tracker.list_experiments(
        tag="weekly", status="completed", page=1, page_size=10
    )

    assert total == 2
    mock_collection.find.assert_called_once_with({"tag": "weekly", "status": "completed"})


def test_list_experiments_no_collection():
    tracker = ExperimentTracker.__new__(ExperimentTracker)
    tracker._mongo_client = MagicMock()
    tracker._collection_name = "experiments"
    tracker._collection = None

    results, total = tracker.list_experiments()

    assert results == []
    assert total == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.12 -m pytest apps/api/tests/experiment/test_tracker_list.py -v`
Expected: FAIL with `AttributeError`

- [ ] **Step 3: Write implementation**

Add to `apps/api/app/experiment/tracker.py` after the `get_by_tag` method (after line 169):

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3.12 -m pytest apps/api/tests/experiment/test_tracker_list.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/experiment/tracker.py apps/api/tests/experiment/test_tracker_list.py
git commit -m "feat: add list_experiments with pagination to ExperimentTracker"
```

---

### Task 2: Create TopStocksManager

**Files:**
- Create: `apps/api/app/qlib/top_stocks_manager.py`
- Modify: `apps/api/app/qlib/__init__.py`
- Test: `apps/api/tests/qlib/test_top_stocks_manager.py`

- [ ] **Step 1: Write the failing test**

Create `apps/api/tests/qlib/test_top_stocks_manager.py`:

```python
import pytest
from unittest.mock import MagicMock
from app.qlib.top_stocks_manager import TopStocksManager


@pytest.fixture
def mock_collection():
    return MagicMock()


def test_save_top_stocks(mock_collection):
    manager = TopStocksManager.__new__(TopStocksManager)
    manager._mongo_client = MagicMock()
    manager._collection = mock_collection

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

    mock_collection.replace_one.assert_called_once()
    call_args = mock_collection.replace_one.call_args
    assert call_args[0][1]["date"] == "2026-04-25"
    assert call_args[0][1]["model_id"] == "model_001"
    assert len(call_args[0][1]["stocks"]) == 2


def test_get_top_stocks_by_date_range(mock_collection):
    manager = TopStocksManager.__new__(TopStocksManager)
    manager._mongo_client = MagicMock()
    manager._collection = mock_collection

    mock_collection.find.return_value.sort.return_value = iter([
        {"date": "2026-04-25", "stocks": [], "model_id": "m1"},
        {"date": "2026-04-24", "stocks": [], "model_id": "m1"},
    ])

    results = manager.get_top_stocks(start_date="2026-04-24", end_date="2026-04-25")

    query = mock_collection.find.call_args[0][0]
    assert "date" in query
    assert "$gte" in query["date"]
    assert "$lte" in query["date"]
    assert len(results) == 2


def test_get_latest_top_stocks(mock_collection):
    manager = TopStocksManager.__new__(TopStocksManager)
    manager._mongo_client = MagicMock()
    manager._collection = mock_collection

    mock_collection.find_one.return_value = {
        "date": "2026-04-25",
        "model_id": "m1",
        "stocks": [{"rank": 1, "code": "SH600000", "name": "test", "score": 0.85}],
    }

    result = manager.get_latest_top_stocks()
    mock_collection.find_one.assert_called_once()
    assert result["date"] == "2026-04-25"


def test_get_latest_top_stocks_empty(mock_collection):
    manager = TopStocksManager.__new__(TopStocksManager)
    manager._mongo_client = MagicMock()
    manager._collection = mock_collection

    mock_collection.find_one.return_value = None
    result = manager.get_latest_top_stocks()
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.12 -m pytest apps/api/tests/qlib/test_top_stocks_manager.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write implementation**

Create `apps/api/app/qlib/top_stocks_manager.py`:

```python
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TopStocksManager:
    """MongoDB-backed storage for daily Top10 stock predictions."""

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
```

- [ ] **Step 4: Export from qlib package**

Modify `apps/api/app/qlib/__init__.py` - add `TopStocksManager` to imports and `__all__`:

```python
from .top_stocks_manager import TopStocksManager
```

Add `"TopStocksManager"` to `__all__`.

- [ ] **Step 5: Run test to verify it passes**

Run: `py -3.12 -m pytest apps/api/tests/qlib/test_top_stocks_manager.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add apps/api/app/qlib/top_stocks_manager.py apps/api/app/qlib/__init__.py apps/api/tests/qlib/test_top_stocks_manager.py
git commit -m "feat: add TopStocksManager for daily Top10 stock cache"
```

---

### Task 3: Add 5 new API endpoints to qlib.py

**Files:**
- Modify: `apps/api/app/api/endpoints/qlib.py`

- [ ] **Step 1: Add imports and dependency injection**

Add after line 12 in `apps/api/app/api/endpoints/qlib.py`:

```python
from app.experiment.tracker import ExperimentTracker
from app.qlib.top_stocks_manager import TopStocksManager
```

Add after line 28 (`_sync_tasks` dict):

```python
_tracker: Optional[ExperimentTracker] = None
_top_stocks_manager: Optional[TopStocksManager] = None


def get_tracker() -> ExperimentTracker:
    global _tracker
    if _tracker is None:
        _tracker = ExperimentTracker()
    return _tracker


def get_top_stocks_manager() -> TopStocksManager:
    global _top_stocks_manager
    if _top_stocks_manager is None:
        _top_stocks_manager = TopStocksManager()
    return _top_stocks_manager
```

- [ ] **Step 2: Add Pydantic response models**

Add after `SyncStatusResponse` class (after line 433):

```python
class ExperimentItem(BaseModel):
    experiment_id: str
    tag: Optional[str] = None
    config: Dict[str, Any]
    training_metrics: Optional[Dict[str, Any]] = None
    backtest_result: Optional[Dict[str, Any]] = None
    model_id: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    error: Optional[str] = None


class ExperimentListResponse(BaseModel):
    items: List[ExperimentItem]
    total: int
    page: int
    page_size: int


class BestModelResponse(BaseModel):
    experiment_id: str
    model_id: Optional[str] = None
    tag: Optional[str] = None
    config: Dict[str, Any]
    training_metrics: Optional[Dict[str, Any]] = None
    backtest_result: Optional[Dict[str, Any]] = None
    status: str


class TopStockItem(BaseModel):
    rank: int
    code: str
    name: Optional[str] = None
    score: float


class TopStocksDayResponse(BaseModel):
    date: str
    model_id: str
    model_type: str
    factor: str
    stocks: List[TopStockItem]
    created_at: Optional[datetime] = None
```

- [ ] **Step 3: Add GET /qlib/experiments endpoint**

Add before the `/sync` endpoints (before line 413):

```python
@router.get("/experiments", response_model=ExperimentListResponse)
async def list_experiments(
    page: int = 1,
    page_size: int = 20,
    tag: Optional[str] = None,
    status: Optional[str] = None,
    tracker: ExperimentTracker = Depends(get_tracker),
):
    try:
        results, total = tracker.list_experiments(
            tag=tag, status=status, page=page, page_size=page_size
        )
        items = [
            ExperimentItem(
                experiment_id=r.get("experiment_id", ""),
                tag=r.get("tag"),
                config=r.get("config", {}),
                training_metrics=r.get("training_metrics"),
                backtest_result=r.get("backtest_result"),
                model_id=r.get("model_id"),
                status=r.get("status", "unknown"),
                created_at=r.get("created_at"),
                error=r.get("error"),
            )
            for r in results
        ]
        return ExperimentListResponse(
            items=items, total=total, page=page, page_size=page_size
        )
    except Exception as e:
        logger.error(f"Failed to list experiments: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list experiments: {str(e)}")
```

- [ ] **Step 4: Add GET /qlib/experiments/compare endpoint**

```python
@router.get("/experiments/compare")
async def compare_experiments(
    ids: str,
    tracker: ExperimentTracker = Depends(get_tracker),
):
    experiment_ids = [i.strip() for i in ids.split(",") if i.strip()]
    if not experiment_ids:
        raise HTTPException(status_code=400, detail="At least one experiment ID required")
    try:
        comparison = tracker.compare(experiment_ids)
        return comparison
    except Exception as e:
        logger.error(f"Failed to compare experiments: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare experiments: {str(e)}")
```

- [ ] **Step 5: Add GET /qlib/best-model endpoint**

```python
@router.get("/best-model", response_model=BestModelResponse)
async def get_best_model(
    tracker: ExperimentTracker = Depends(get_tracker),
):
    try:
        best = tracker.get_best("backtest_result.sharpe_ratio")
        if best is None:
            raise HTTPException(status_code=404, detail="No completed experiment found")
        return BestModelResponse(
            experiment_id=best.get("experiment_id", ""),
            model_id=best.get("model_id"),
            tag=best.get("tag"),
            config=best.get("config", {}),
            training_metrics=best.get("training_metrics"),
            backtest_result=best.get("backtest_result"),
            status=best.get("status", "unknown"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get best model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get best model: {str(e)}")
```

- [ ] **Step 6: Add GET /qlib/top-stocks endpoint**

```python
@router.get("/top-stocks", response_model=List[TopStocksDayResponse])
async def get_top_stocks(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    model_id: Optional[str] = None,
    mgr: TopStocksManager = Depends(get_top_stocks_manager),
):
    try:
        if start_date is None and end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = end_date

        results = mgr.get_top_stocks(
            start_date=start_date,
            end_date=end_date,
            model_id=model_id,
        )

        return [
            TopStocksDayResponse(
                date=r.get("date", ""),
                model_id=r.get("model_id", ""),
                model_type=r.get("model_type", ""),
                factor=r.get("factor", ""),
                stocks=[TopStockItem(**s) for s in r.get("stocks", [])],
                created_at=r.get("created_at"),
            )
            for r in results
        ]
    except Exception as e:
        logger.error(f"Failed to get top stocks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get top stocks: {str(e)}")
```

- [ ] **Step 7: Add POST /qlib/top-stocks/refresh endpoint**

```python
@router.post("/top-stocks/refresh")
async def refresh_top_stocks(
    tracker: ExperimentTracker = Depends(get_tracker),
    predictor: QlibPredictor = Depends(get_predictor),
    mgr: TopStocksManager = Depends(get_top_stocks_manager),
):
    try:
        best = tracker.get_best("backtest_result.sharpe_ratio")
        if best is None:
            raise HTTPException(status_code=404, detail="No completed experiment found")

        model_id = best.get("model_id")
        if not model_id:
            raise HTTPException(status_code=400, detail="Best experiment has no model_id")

        config = best.get("config", {})
        today = datetime.now().strftime("%Y-%m-%d")

        predictions = predictor.predict(
            model_id=model_id,
            topk=10,
            date=today,
        )

        stocks = [
            {"rank": p.get("rank", i + 1), "code": p.get("code", ""), "name": p.get("name", ""), "score": p.get("score", 0.0)}
            for i, p in enumerate(predictions[:10])
        ]

        mgr.save_top_stocks(
            date=today,
            model_id=model_id,
            model_type=config.get("model_type", "lgbm"),
            factor=config.get("factor_type", "alpha158"),
            stocks=stocks,
        )

        return {"message": "Top stocks refreshed", "date": today, "model_id": model_id, "count": len(stocks)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh top stocks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh top stocks: {str(e)}")
```

- [ ] **Step 8: Run existing tests to verify no breakage**

Run: `py -3.12 -m pytest apps/api/tests/qlib/ -v`
Expected: All existing tests pass

- [ ] **Step 9: Commit**

```bash
git add apps/api/app/api/endpoints/qlib.py
git commit -m "feat: add experiment/best-model/top-stocks API endpoints"
```

---

### Task 4: Create QlibTopStocksJob scheduled task

**Files:**
- Create: `apps/api/app/scheduler/qlib_top_stocks_job.py`
- Modify: `apps/api/app/scheduler/__init__.py`
- Modify: `apps/api/scheduler_standalone.py`

- [ ] **Step 1: Create the scheduled job**

Create `apps/api/app/scheduler/qlib_top_stocks_job.py`:

```python
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..qlib import QlibPredictor
from ..experiment.tracker import ExperimentTracker
from ..qlib.top_stocks_manager import TopStocksManager
from ..notify.dingtalk import DingTalkNotifier
from ..core.config import settings

logger = logging.getLogger(__name__)


class QlibTopStocksJob:
    """Daily job to predict Top10 stocks using best model."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._predictor: Optional[QlibPredictor] = None
        self._tracker: Optional[ExperimentTracker] = None
        self._top_stocks_mgr: Optional[TopStocksManager] = None
        self._notifier: Optional[DingTalkNotifier] = None

    def _get_predictor(self) -> QlibPredictor:
        if self._predictor is None:
            self._predictor = QlibPredictor()
        return self._predictor

    def _get_tracker(self) -> ExperimentTracker:
        if self._tracker is None:
            self._tracker = ExperimentTracker()
        return self._tracker

    def _get_top_stocks_manager(self) -> TopStocksManager:
        if self._top_stocks_mgr is None:
            self._top_stocks_mgr = TopStocksManager()
        return self._top_stocks_mgr

    def _get_notifier(self) -> Optional[DingTalkNotifier]:
        if self._notifier is None:
            webhook = self.config.get(
                "dingtalk_webhook",
                settings.after_market_dingtalk_webhook,
            )
            secret = self.config.get(
                "dingtalk_secret",
                settings.after_market_dingtalk_secret,
            )
            if webhook:
                self._notifier = DingTalkNotifier(webhook_url=webhook, secret=secret)
        return self._notifier

    async def _send_notification(self, title: str, content: str):
        notifier = self._get_notifier()
        if notifier:
            markdown = f"## {title}\\n\\n{content}"
            await asyncio.to_thread(notifier.send, markdown=markdown)

    async def run(self) -> Dict[str, Any]:
        job_name = "Qlib Top10 Stock Prediction"

        try:
            tracker = self._get_tracker()
            best = tracker.get_best("backtest_result.sharpe_ratio")

            if best is None:
                logger.warning("No completed experiment found, skipping top stocks job")
                return {"status": "skipped", "reason": "no_completed_experiment"}

            model_id = best.get("model_id")
            if not model_id:
                logger.warning("Best experiment has no model_id, skipping")
                return {"status": "skipped", "reason": "no_model_id"}

            config = best.get("config", {})
            today = datetime.now().strftime("%Y-%m-%d")

            predictor = self._get_predictor()
            predictions = await asyncio.to_thread(
                predictor.predict,
                model_id=model_id,
                topk=10,
                date=today,
            )

            stocks = [
                {"rank": p.get("rank", i + 1), "code": p.get("code", ""), "name": p.get("name", ""), "score": p.get("score", 0.0)}
                for i, p in enumerate(predictions[:10])
            ]

            mgr = self._get_top_stocks_manager()
            mgr.save_top_stocks(
                date=today,
                model_id=model_id,
                model_type=config.get("model_type", "lgbm"),
                factor=config.get("factor_type", "alpha158"),
                stocks=stocks,
            )

            stock_list = "\\n".join([f"{s['rank']}. {s['code']} {s['name']} ({s['score']:.4f})" for s in stocks])
            await self._send_notification(
                f"Top10 Stock Prediction Done",
                f"- Date: {today}\\n- Model: {model_id}\\n- Top10:\\n{stock_list}",
            )

            return {"status": "success", "date": today, "model_id": model_id, "count": len(stocks)}

        except Exception as e:
            logger.error(f"QlibTopStocksJob failed: {e}")
            await self._send_notification(
                f"Top10 Stock Prediction Failed",
                f"Error: {str(e)}",
            )
            raise


async def qlib_top_stocks_handler(config: Dict[str, Any]) -> Dict[str, Any]:
    job = QlibTopStocksJob(config)
    return await job.run()
```

- [ ] **Step 2: Export from scheduler __init__.py**

Modify `apps/api/app/scheduler/__init__.py` - add:

```python
from .qlib_top_stocks_job import QlibTopStocksJob, qlib_top_stocks_handler
```

Add `"QlibTopStocksJob"` and `"qlib_top_stocks_handler"` to `__all__`.

- [ ] **Step 3: Register in scheduler_standalone.py**

Add after `run_qlib_data_sync_job` function (after line 181):

```python
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
```

In `setup_scheduler()`, add after the qlib_data_sync_job scheduler registration (after line 273):

```python
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
```

- [ ] **Step 4: Commit**

```bash
git add apps/api/app/scheduler/qlib_top_stocks_job.py apps/api/app/scheduler/__init__.py apps/api/scheduler_standalone.py
git commit -m "feat: add QlibTopStocksJob for daily Top10 prediction"
```

---

### Task 5: Add frontend API service methods and TypeScript interfaces

**Files:**
- Modify: `frontend/vue-admin/src/services/api_qlib.ts`

- [ ] **Step 1: Add new interfaces**

Add after the `Instrument` interface:

```typescript
interface Experiment {
  experiment_id: string
  tag: string | null
  config: Record<string, any>
  training_metrics: Record<string, any> | null
  backtest_result: Record<string, any> | null
  model_id: string | null
  status: string
  created_at: string | null
  error: string | null
}

interface ExperimentListResult {
  items: Experiment[]
  total: number
  page: number
  page_size: number
}

interface BestModel {
  experiment_id: string
  model_id: string | null
  tag: string | null
  config: Record<string, any>
  training_metrics: Record<string, any> | null
  backtest_result: Record<string, any> | null
  status: string
}

interface TopStockItem {
  rank: number
  code: string
  name: string | null
  score: number
}

interface TopStocksDay {
  date: string
  model_id: string
  model_type: string
  factor: string
  stocks: TopStockItem[]
  created_at: string | null
}
```

- [ ] **Step 2: Add new API methods to apiQlib object**

Add after `getCSI300`:

```typescript
  async getExperiments(page: number = 1, pageSize: number = 20, tag?: string, status?: string): Promise<ExperimentListResult> {
    const params: Record<string, any> = { page, page_size: pageSize }
    if (tag) params.tag = tag
    if (status) params.status = status
    const res = await api.get('/qlib/experiments', { params })
    return res.data
  },

  async compareExperiments(ids: string[]): Promise<Record<string, any>> {
    const res = await api.get('/qlib/experiments/compare', { params: { ids: ids.join(',') } })
    return res.data
  },

  async getBestModel(): Promise<BestModel> {
    const res = await api.get('/qlib/best-model')
    return res.data
  },

  async getTopStocks(startDate?: string, endDate?: string, modelId?: string): Promise<TopStocksDay[]> {
    const params: Record<string, any> = {}
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    if (modelId) params.model_id = modelId
    const res = await api.get('/qlib/top-stocks', { params })
    return res.data
  },

  async refreshTopStocks(): Promise<{ message: string; date: string; model_id: string; count: number }> {
    const res = await api.post('/qlib/top-stocks/refresh')
    return res.data
  },
```

- [ ] **Step 3: Update type exports**

```typescript
export type { TrainingRequest, TrainingStatus, Model, SelectionRequest, SelectionResult, Instrument, Experiment, ExperimentListResult, BestModel, TopStockItem, TopStocksDay }
```

- [ ] **Step 4: Commit**

```bash
git add frontend/vue-admin/src/services/api_qlib.ts
git commit -m "feat: add experiment/best-model/top-stocks API service methods"
```

---

### Task 6: Update Pinia store with new state and actions

**Files:**
- Modify: `frontend/vue-admin/src/stores/qlib.ts`

- [ ] **Step 1: Update imports**

Replace the import line with:

```typescript
import { apiQlib, type Model, type TrainingStatus, type SelectionResult, type Instrument, type Experiment, type ExperimentListResult, type BestModel, type TopStocksDay } from '../services/api_qlib'
```

- [ ] **Step 2: Add new state fields**

Add after `csi300Instruments` in the reactive state:

```typescript
    experiments: [] as Experiment[],
    experimentsTotal: 0,
    experimentsPage: 1,
    bestModel: null as BestModel | null,
    topStocks: [] as TopStocksDay[],
    refreshingTopStocks: false,
```

- [ ] **Step 3: Add new actions**

Add after `fetchCSI300`:

```typescript
  async function fetchExperiments(page: number = 1, pageSize: number = 20, tag?: string, status?: string) {
    state.loading = true
    state.error = null
    try {
      const res = await apiQlib.getExperiments(page, pageSize, tag, status)
      state.experiments = res.items
      state.experimentsTotal = res.total
      state.experimentsPage = page
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取实验列表失败'
    } finally {
      state.loading = false
    }
  }

  async function fetchBestModel() {
    state.loading = true
    state.error = null
    try {
      state.bestModel = await apiQlib.getBestModel()
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取最优模型失败'
    } finally {
      state.loading = false
    }
  }

  async function fetchTopStocks(startDate?: string, endDate?: string, modelId?: string) {
    state.loading = true
    state.error = null
    try {
      state.topStocks = await apiQlib.getTopStocks(startDate, endDate, modelId)
    } catch (e: any) {
      state.error = e.response?.data?.detail || '获取Top10推荐失败'
    } finally {
      state.loading = false
    }
  }

  async function refreshTopStocks() {
    state.refreshingTopStocks = true
    state.error = null
    try {
      await apiQlib.refreshTopStocks()
      const today = new Date().toISOString().split('T')[0]
      state.topStocks = await apiQlib.getTopStocks(today, today)
    } catch (e: any) {
      state.error = e.response?.data?.detail || '刷新Top10失败'
    } finally {
      state.refreshingTopStocks = false
    }
  }
```

- [ ] **Step 4: Update return object**

```typescript
  return {
    state,
    fetchModels,
    fetchModel,
    startTraining,
    checkTrainingStatus,
    runSelection,
    fetchCSI300,
    clearSelectionResults,
    clearTrainingStatus,
    fetchExperiments,
    fetchBestModel,
    fetchTopStocks,
    refreshTopStocks,
  }
```

- [ ] **Step 5: Commit**

```bash
git add frontend/vue-admin/src/stores/qlib.ts
git commit -m "feat: add experiments/bestModel/topStocks state to qlib store"
```

---

### Task 7: Create QlibTrainHistory.vue component

**Files:**
- Create: `frontend/vue-admin/src/views/qlib/QlibTrainHistory.vue`

- [ ] **Step 1: Create the component**

```vue
<script setup lang="ts">
import { ref, onMounted, computed, h } from 'vue'
import { useQlibStore } from '../../stores/qlib'
import { NDataTable, NButton, NSelect, NTag, NDrawer, NDrawerContent, NEmpty } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import type { Experiment } from '../../services/api_qlib'

const store = useQlibStore()

onMounted(async () => {
  await store.fetchExperiments()
})

const currentPage = ref(1)
const pageSize = 20
const selectedIds = ref<string[]>([])
const showCompare = ref(false)
const statusFilter = ref<string | null>(null)

const statusOptions = [
  { label: '全部', value: '' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' },
  { label: 'IC过低跳过', value: 'skipped_low_ic' },
]

const columns: DataTableColumns<Experiment> = [
  { type: 'selection' },
  { title: '实验ID', key: 'experiment_id', width: 180, ellipsis: { tooltip: true } },
  { title: '模型类型', key: 'model_type', width: 100, render: (row: Experiment) => row.config?.model_type || '-' },
  { title: '因子', key: 'factor', width: 100, render: (row: Experiment) => row.config?.factor_type || '-' },
  { title: 'IC', key: 'ic', width: 80, render: (row: Experiment) => row.training_metrics?.ic?.toFixed(4) ?? '-' },
  { title: 'Rank IC', key: 'rank_ic', width: 80, render: (row: Experiment) => row.training_metrics?.rank_ic?.toFixed(4) ?? '-' },
  { title: 'Sharpe', key: 'sharpe', width: 80, render: (row: Experiment) => row.backtest_result?.sharpe_ratio?.toFixed(2) ?? '-' },
  {
    title: '状态', key: 'status', width: 100,
    render: (row: Experiment) => {
      const map: Record<string, string> = { completed: 'success', failed: 'error', skipped_low_ic: 'warning' }
      return h(NTag, { type: map[row.status] || 'default', size: 'small' }, { default: () => row.status })
    },
  },
  { title: '创建时间', key: 'created_at', width: 160, render: (row: Experiment) => row.created_at ? new Date(row.created_at).toLocaleString('zh-CN') : '-' },
]

const pagination = computed(() => ({
  page: currentPage.value,
  pageSize,
  itemCount: store.state.experimentsTotal,
  onChange: (page: number) => {
    currentPage.value = page
    store.fetchExperiments(page, pageSize, undefined, statusFilter.value || undefined)
  },
}))

function handleCheckedRowKeys(keys: string[]) {
  selectedIds.value = keys
}

async function openCompare() {
  if (selectedIds.value.length < 2) return
  showCompare.value = true
}

async function applyFilter() {
  currentPage.value = 1
  await store.fetchExperiments(1, pageSize, undefined, statusFilter.value || undefined)
}
</script>

<template>
  <div class="train-history">
    <div class="filter-bar">
      <NSelect v-model:value="statusFilter" :options="statusOptions" placeholder="状态筛选" style="width: 140px" clearable @update:value="applyFilter" />
      <NButton type="primary" :disabled="selectedIds.length < 2" @click="openCompare">对比 ({{ selectedIds.length }})</NButton>
    </div>
    <NDataTable :columns="columns" :data="store.state.experiments" :pagination="pagination" :row-key="(row: Experiment) => row.experiment_id" :bordered="false" striped @update:checked-row-keys="handleCheckedRowKeys" />
    <NEmpty v-if="store.state.experiments.length === 0 && !store.state.loading" description="暂无训练记录" />
    <NDrawer v-model:show="showCompare" :width="600" placement="right">
      <NDrawerContent title="实验对比">
        <div v-for="id in selectedIds" :key="id" class="compare-item">
          <h3>{{ id }}</h3>
        </div>
      </NDrawerContent>
    </NDrawer>
  </div>
</template>

<style scoped>
.train-history { padding: 0; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; align-items: center; }
.compare-item { margin-bottom: 16px; padding: 12px; border: 1px solid #e0e0e0; border-radius: 4px; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/vue-admin/src/views/qlib/QlibTrainHistory.vue
git commit -m "feat: add QlibTrainHistory component with compare drawer"
```

---

### Task 8: Create QlibBestModel.vue component

**Files:**
- Create: `frontend/vue-admin/src/views/qlib/QlibBestModel.vue`

- [ ] **Step 1: Create the component**

```vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { useQlibStore } from '../../stores/qlib'
import { NCard, NDescriptions, NDescriptionsItem, NTag, NEmpty, NSpin } from 'naive-ui'

const store = useQlibStore()

onMounted(async () => {
  await store.fetchBestModel()
})

function formatValue(val: any, digits: number = 4): string {
  if (val === null || val === undefined) return '-'
  if (typeof val === 'number') return val.toFixed(digits)
  return String(val)
}
</script>

<template>
  <div class="best-model">
    <NSpin :show="store.state.loading">
      <template v-if="store.state.bestModel">
        <NCard title="最优模型 (Sharpe最高)" size="small">
          <NDescriptions label-placement="left" bordered :column="2">
            <NDescriptionsItem label="实验ID">{{ store.state.bestModel.experiment_id }}</NDescriptionsItem>
            <NDescriptionsItem label="模型ID">{{ store.state.bestModel.model_id || '-' }}</NDescriptionsItem>
            <NDescriptionsItem label="模型类型">{{ store.state.bestModel.config?.model_type || '-' }}</NDescriptionsItem>
            <NDescriptionsItem label="因子配置">{{ store.state.bestModel.config?.factor_type || '-' }}</NDescriptionsItem>
            <NDescriptionsItem label="Tag">{{ store.state.bestModel.tag || '-' }}</NDescriptionsItem>
            <NDescriptionsItem label="状态">
              <NTag :type="store.state.bestModel.status === 'completed' ? 'success' : 'default'" size="small">{{ store.state.bestModel.status }}</NTag>
            </NDescriptionsItem>
          </NDescriptions>
          <NCard title="训练指标" size="small" style="margin-top: 16px">
            <NDescriptions label-placement="left" bordered :column="2">
              <NDescriptionsItem label="IC">{{ formatValue(store.state.bestModel.training_metrics?.ic) }}</NDescriptionsItem>
              <NDescriptionsItem label="Rank IC">{{ formatValue(store.state.bestModel.training_metrics?.rank_ic) }}</NDescriptionsItem>
              <NDescriptionsItem label="ICIR">{{ formatValue(store.state.bestModel.training_metrics?.icir) }}</NDescriptionsItem>
              <NDescriptionsItem label="预测数量">{{ store.state.bestModel.training_metrics?.num_predictions ?? '-' }}</NDescriptionsItem>
            </NDescriptions>
          </NCard>
          <NCard title="回测指标" size="small" style="margin-top: 16px">
            <NDescriptions label-placement="left" bordered :column="2">
              <NDescriptionsItem label="Sharpe Ratio">{{ formatValue(store.state.bestModel.backtest_result?.sharpe_ratio, 2) }}</NDescriptionsItem>
              <NDescriptionsItem label="多空收益">{{ formatValue(store.state.bestModel.backtest_result?.long_short_return) }}</NDescriptionsItem>
            </NDescriptions>
          </NCard>
        </NCard>
      </template>
      <NEmpty v-else-if="!store.state.loading" description="暂无已完成的训练实验" />
    </NSpin>
  </div>
</template>

<style scoped>
.best-model { padding: 0; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/vue-admin/src/views/qlib/QlibBestModel.vue
git commit -m "feat: add QlibBestModel component with metrics display"
```

---

### Task 9: Create QlibTopStocks.vue component

**Files:**
- Create: `frontend/vue-admin/src/views/qlib/QlibTopStocks.vue`

- [ ] **Step 1: Create the component**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useQlibStore } from '../../stores/qlib'
import { NDataTable, NDatePicker, NButton, NTag, NEmpty, NSpin, NSpace, NAlert } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import type { TopStockItem } from '../../services/api_qlib'

const store = useQlibStore()

onMounted(async () => {
  const today = new Date().toISOString().split('T')[0]
  await store.fetchTopStocks(today, today)
})

function formatDate(ts: number): string {
  return new Date(ts).toISOString().split('T')[0]
}

async function handleDateRangeChange(value: [number, number] | null) {
  if (value) {
    const start = formatDate(value[0])
    const end = formatDate(value[1])
    await store.fetchTopStocks(start, end)
  }
}

async function handleRefresh() {
  await store.refreshTopStocks()
}

const columns: DataTableColumns<TopStockItem> = [
  { title: '排名', key: 'rank', width: 60 },
  { title: '代码', key: 'code', width: 120 },
  { title: '名称', key: 'name', render: (row) => row.name || row.code },
  { title: '评分', key: 'score', width: 100, render: (row) => row.score.toFixed(4) },
]
</script>

<template>
  <div class="top-stocks">
    <NSpace class="filter-bar" align="center">
      <NDatePicker type="daterange" clearable @update:value="handleDateRangeChange" style="width: 280px" />
      <NButton type="primary" :loading="store.state.refreshingTopStocks" @click="handleRefresh">刷新今日推荐</NButton>
    </NSpace>
    <NAlert v-if="store.state.error" type="error" style="margin-bottom: 12px">{{ store.state.error }}</NAlert>
    <NSpin :show="store.state.loading">
      <div v-if="store.state.topStocks.length > 0">
        <div v-for="day in store.state.topStocks" :key="day.date" style="margin-bottom: 20px">
          <NTag type="info" style="margin-bottom: 8px">{{ day.date }} | 模型: {{ day.model_id }} | {{ day.model_type }} | {{ day.factor }}</NTag>
          <NDataTable :columns="columns" :data="day.stocks" :bordered="false" size="small" striped :row-key="(row: TopStockItem) => row.code" />
        </div>
      </div>
      <NEmpty v-else-if="!store.state.loading" description="暂无推荐数据，点击刷新按钮生成" />
    </NSpin>
  </div>
</template>

<style scoped>
.top-stocks { padding: 0; }
.filter-bar { margin-bottom: 16px; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/vue-admin/src/views/qlib/QlibTopStocks.vue
git commit -m "feat: add QlibTopStocks component with date range filter"
```

---

### Task 10: Refactor QlibSelectView.vue into 3-tab layout

**Files:**
- Modify: `frontend/vue-admin/src/views/QlibSelectView.vue`

- [ ] **Step 1: Replace QlibSelectView.vue with tabbed layout**

```vue
<script setup lang="ts">
import { NTabs, NTabPane } from 'naive-ui'
import QlibTrainHistory from './qlib/QlibTrainHistory.vue'
import QlibBestModel from './qlib/QlibBestModel.vue'
import QlibTopStocks from './qlib/QlibTopStocks.vue'
</script>

<template>
  <div class="qlib-select-view">
    <NTabs type="line" animated>
      <NTabPane name="history" tab="训练历史">
        <QlibTrainHistory />
      </NTabPane>
      <NTabPane name="best-model" tab="最优模型">
        <QlibBestModel />
      </NTabPane>
      <NTabPane name="top-stocks" tab="Top10推荐">
        <QlibTopStocks />
      </NTabPane>
    </NTabs>
  </div>
</template>

<style scoped>
.qlib-select-view { padding: 20px; }
</style>
```

- [ ] **Step 2: Verify frontend builds**

Run: `cd frontend/vue-admin && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/vue-admin/src/views/QlibSelectView.vue frontend/vue-admin/src/views/qlib/
git commit -m "feat: refactor QlibSelectView into 3-tab layout"
```

---

### Task 11: Integration test and final verification

**Files:**
- No new files

- [ ] **Step 1: Run all backend tests**

Run: `py -3.12 -m pytest apps/api/tests/ -v`
Expected: All tests pass

- [ ] **Step 2: Run frontend build**

Run: `cd frontend/vue-admin && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: integration fixes for qlib model page redesign"
```
"""

with open(plan_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Plan written to {plan_path}")
