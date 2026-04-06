import asyncio
import os
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from pymongo import MongoClient
from pymongo.errors import PyMongoError

import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db_name():
    return f"test_trading_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
def mongo_client(test_db_name):
    client = MongoClient(
        settings.mongodb_host,
        settings.mongodb_port,
        username=settings.mongodb_username,
        password=settings.mongodb_password,
    )
    yield client
    try:
        client.drop_database(test_db_name)
    except PyMongoError:
        pass
    client.close()


@pytest.fixture(scope="session")
def test_db(mongo_client, test_db_name):
    db = mongo_client[test_db_name]
    yield db


@pytest_asyncio.fixture(scope="session")
async def app():
    from main import app as fastapi_app

    yield fastapi_app


@pytest_asyncio.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def sync_client(app) -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_dingtalk_notifier():
    mock = MagicMock()
    mock.send = MagicMock(return_value=True)
    return mock


@pytest.fixture
def mock_dingtalk_notifier_async():
    mock = AsyncMock()
    mock.send = MagicMock(return_value=True)
    return mock


@pytest.fixture
def sample_holdings() -> Dict[str, Any]:
    return {
        "user_id": "test_user_001",
        "positions": [
            {
                "code": "SH600519",
                "name": "贵州茅台",
                "quantity": 100,
                "average_cost": 1800.0,
            },
            {
                "code": "SH600036",
                "name": "招商银行",
                "quantity": 500,
                "average_cost": 35.0,
            },
        ],
    }


@pytest.fixture
def sample_kline_data() -> list:
    base_date = datetime(2025, 1, 1)
    klines = []
    for i in range(30):
        klines.append(
            {
                "code": "SH600519",
                "name": "贵州茅台",
                "date": (
                    base_date.replace(day=1) + __import__("datetime").timedelta(days=i)
                ).strftime("%Y-%m-%d"),
                "open": 1800.0 + i * 2,
                "high": 1820.0 + i * 2,
                "low": 1790.0 + i * 2,
                "close": 1810.0 + i * 2,
                "volume": 1000000,
                "amount": 1800000000,
            }
        )
    return klines


@pytest.fixture
def sample_stock_info() -> list:
    return [
        {"code": "SH600519", "name": "贵州茅台", "industry": "白酒"},
        {"code": "SH600036", "name": "招商银行", "industry": "银行"},
        {"code": "SH600000", "name": "浦发银行", "industry": "银行"},
        {"code": "SZ000858", "name": "五粮液", "industry": "白酒"},
    ]


@pytest.fixture
def auth_headers() -> Dict[str, str]:
    from app.core.security import create_access_token

    token = create_access_token(data={"sub": "test_user_001"})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def setup_test_data(
    test_db, sample_holdings, sample_kline_data, sample_stock_info
):
    holdings_coll = test_db["holdings"]
    holdings_coll.insert_one(sample_holdings)

    kline_coll = test_db["stock_kline"]
    if sample_kline_data:
        kline_coll.insert_many(sample_kline_data)

    stock_info_coll = test_db["stock_info"]
    if sample_stock_info:
        stock_info_coll.insert_many(sample_stock_info)

    yield

    holdings_coll.delete_many({"user_id": "test_user_001"})
    kline_coll.delete_many({"code": "SH600519"})
    stock_info_coll.delete_many({})


@pytest.fixture
def mock_qlib_trainer():
    mock = MagicMock()
    mock.start_training = MagicMock(return_value="train_test_001")
    mock.get_status = MagicMock(
        return_value={
            "status": "completed",
            "progress": 100,
            "model_id": "model_test_001",
            "metrics": {
                "sharpe_ratio": 2.1,
                "ic": 0.05,
                "num_predictions": 300,
            },
        }
    )
    return mock


@pytest.fixture
def mock_qlib_predictor():
    mock = MagicMock()
    mock.predict = MagicMock(
        return_value=[
            {"code": "SH600519", "name": "贵州茅台", "score": 0.85, "rank": 1},
            {"code": "SH600036", "name": "招商银行", "score": 0.78, "rank": 2},
        ]
    )
    return mock


@pytest.fixture
def mock_backtest_engine():
    from app.backtest.async_engine import BacktestStatus

    _task_counter = [0]
    _task_results = {}

    def _get_next_task_id():
        _task_counter[0] += 1
        return f"backtest_test_{_task_counter[0]:03d}"

    async def _run_backtest(config):
        task_id = _get_next_task_id()
        _task_results[task_id] = {
            "config": config,
            "status": BacktestStatus.COMPLETED.value,
        }
        return task_id

    async def _get_status(task_id):
        return {
            "task_id": task_id,
            "status": BacktestStatus.COMPLETED.value,
            "progress": 1.0,
            "metrics": {
                "total_return": 0.15,
                "sharpe_ratio": 1.8,
                "max_drawdown": -0.08,
            },
        }

    async def _get_result(task_id):
        config = _task_results.get(task_id, {}).get("config", {})
        return {
            "task_id": task_id,
            "status": "completed",
            "config": config,
            "portfolio_values": [100000, 101000, 102500],
            "trades": [],
            "metrics": {
                "total_return": 0.15,
                "sharpe_ratio": 1.8,
                "max_drawdown": -0.08,
            },
        }

    async def _cancel(task_id):
        return True

    mock = AsyncMock()
    mock.run_backtest = AsyncMock(side_effect=_run_backtest)
    mock.get_status = AsyncMock(side_effect=_get_status)
    mock.get_result = AsyncMock(side_effect=_get_result)
    mock.cancel = AsyncMock(side_effect=_cancel)
    return mock


@pytest.fixture
def mock_stock_selection_engine():
    """Mock StockSelectionEngine for testing"""
    mock = AsyncMock()
    mock.run_selection = AsyncMock(
        return_value={"task_id": "test_task_001", "status": "pending"}
    )
    mock.get_task = AsyncMock(
        return_value={"task_id": "test_task_001", "status": "completed", "results": []}
    )
    mock.get_history = AsyncMock(
        return_value={"items": [], "total": 0, "page": 1, "page_size": 20}
    )
    return mock


@pytest.fixture
def test_user():
    """标准测试用户"""
    return {"username": "admin", "password": "aa123aaqqA@", "role_id": "role_superuser"}


@pytest_asyncio.fixture
async def api_client(async_client, test_user):
    """带认证的 API 客户端 - 模拟前端 axios 实例"""
    response = await async_client.post(
        "/api/auth/token",
        json={"username": test_user["username"], "password": test_user["password"]},
    )

    if response.status_code != 200:
        raise Exception(f"Login failed: {response.status_code}")

    token = response.json()["access_token"]

    class AuthenticatedClient:
        def __init__(self, client, token):
            self._client = client
            self._token = token

        async def get(self, path, **kwargs):
            kwargs.setdefault("headers", {})["Authorization"] = f"Bearer {self._token}"
            return await self._client.get(path, **kwargs)

        async def post(self, path, **kwargs):
            kwargs.setdefault("headers", {})["Authorization"] = f"Bearer {self._token}"
            return await self._client.post(path, **kwargs)

        async def put(self, path, **kwargs):
            kwargs.setdefault("headers", {})["Authorization"] = f"Bearer {self._token}"
            return await self._client.put(path, **kwargs)

        async def delete(self, path, **kwargs):
            kwargs.setdefault("headers", {})["Authorization"] = f"Bearer {self._token}"
            return await self._client.delete(path, **kwargs)

    return AuthenticatedClient(async_client, token)
