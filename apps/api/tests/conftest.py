"""
Root conftest.py for shared fixtures across all test modules.

This module provides common fixtures for:
- Event loop management
- MongoDB test database
- FastAPI app and clients
- Qlib mocking utilities
"""

import asyncio
import os
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Generator, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from pymongo import MongoClient
from pymongo.errors import PyMongoError

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db_name():
    """Generate a unique test database name."""
    return f"test_qlib_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
def mongo_client(test_db_name):
    """Create a MongoDB client for testing."""
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
    """Get the test database."""
    db = mongo_client[test_db_name]
    yield db


@pytest_asyncio.fixture(scope="session")
async def app():
    """Get the FastAPI application."""
    from main import app as fastapi_app
    yield fastapi_app


@pytest_asyncio.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def sync_client(app) -> Generator[TestClient, None, None]:
    """Create a sync HTTP client for testing."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_qlib():
    """Mock qlib module for testing without actual qlib installation."""
    mock = MagicMock()
    mock.init = MagicMock(return_value=True)

    # Mock D.features for data retrieval
    mock_data = MagicMock()
    mock.features = MagicMock(return_value=None)
    mock.D = mock_data

    return mock


@pytest.fixture
def mock_model_manager():
    """Mock ModelManager for testing QlibPredictor."""
    mock = MagicMock()

    # Default behavior: model found
    mock.load_model = MagicMock(return_value=MagicMock())

    # Mock metadata
    mock.get_model_metadata = MagicMock(return_value={
        "model_id": "test_model_001",
        "version": 1,
        "created_at": datetime.now(),
        "config": {
            "model_type": "lgbm",
            "factor_type": "alpha158",
        },
        "metrics": {
            "sharpe_ratio": 2.1,
            "ic": 0.05,
        },
        "status": "approved",
    })

    mock.list_models = MagicMock(return_value=[])
    mock.get_latest_model = MagicMock(return_value=None)

    return mock


@pytest.fixture
def sample_predictions() -> List[Dict[str, Any]]:
    """Sample prediction results for testing."""
    return [
        {"code": "SH600519", "name": "贵州茅台", "score": 0.95, "rank": 1},
        {"code": "SH600036", "name": "招商银行", "score": 0.88, "rank": 2},
        {"code": "SH600000", "name": "浦发银行", "score": 0.82, "rank": 3},
        {"code": "SH601318", "name": "中国平安", "score": 0.75, "rank": 4},
        {"code": "SZ000858", "name": "五粮液", "score": 0.72, "rank": 5},
        {"code": "SZ000001", "name": "平安银行", "score": 0.68, "rank": 6},
        {"code": "SH600111", "name": "北方稀土", "score": 0.65, "rank": 7},
        {"code": "SH600887", "name": "伊利股份", "score": 0.62, "rank": 8},
        {"code": "SZ000002", "name": "万科A", "score": 0.58, "rank": 9},
        {"code": "SH601398", "name": "工商银行", "score": 0.55, "rank": 10},
    ]
