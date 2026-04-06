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
from app.user.password import hash_password


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db_name():
    return f"test_auth_{uuid.uuid4().hex[:8]}"


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
def test_user_data() -> Dict[str, Any]:
    return {
        "username": "testuser",
        "password": "testpassword123",
        "display_name": "Test User",
        "role_id": "role_viewer",
        "status": "active",
    }


@pytest.fixture
def test_admin_data() -> Dict[str, Any]:
    return {
        "username": "admin",
        "password": "aa123aaqqA@",
        "display_name": "Test Admin",
        "role_id": "role_superuser",
        "status": "active",
        "is_superuser": True,
    }


@pytest.fixture
def test_role_data() -> Dict[str, Any]:
    return {
        "role_id": "role_test",
        "name": "测试角色",
        "description": "用于测试的角色",
        "permissions": ["user:view", "role:view"],
    }


@pytest.fixture
def setup_test_db(test_db, test_user_data, test_admin_data, test_role_data):
    from app.core.permissions import DEFAULT_ROLES

    roles_coll = test_db["roles"]
    for role in DEFAULT_ROLES:
        role["_id"] = f"test_{role['role_id']}"
        role["created_at"] = datetime.now().isoformat()
        role["updated_at"] = datetime.now().isoformat()
        roles_coll.update_one({"role_id": role["role_id"]}, {"$set": role}, upsert=True)

    test_role_data["created_at"] = datetime.now().isoformat()
    test_role_data["updated_at"] = datetime.now().isoformat()
    test_role_data["is_system"] = False
    roles_coll.update_one(
        {"role_id": test_role_data["role_id"]}, {"$set": test_role_data}, upsert=True
    )

    users_coll = test_db["users"]

    now = datetime.now()
    admin_user = {
        "username": test_admin_data["username"],
        "password_hash": hash_password(test_admin_data["password"]),
        "display_name": test_admin_data["display_name"],
        "role_id": test_admin_data["role_id"],
        "status": test_admin_data["status"],
        "is_superuser": test_admin_data.get("is_superuser", False),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "login_count": 0,
    }
    users_coll.update_one(
        {"username": admin_user["username"]}, {"$set": admin_user}, upsert=True
    )

    test_user = {
        "username": test_user_data["username"],
        "password_hash": hash_password(test_user_data["password"]),
        "display_name": test_user_data["display_name"],
        "role_id": test_user_data["role_id"],
        "status": test_user_data["status"],
        "is_superuser": False,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "login_count": 0,
    }
    users_coll.update_one(
        {"username": test_user["username"]}, {"$set": test_user}, upsert=True
    )

    yield

    users_coll.delete_many(
        {"username": {"$in": [test_user_data["username"], test_admin_data["username"]]}}
    )
    roles_coll.delete_many({"role_id": test_role_data["role_id"]})


@pytest.fixture
def auth_headers(setup_test_db, test_admin_data) -> Dict[str, str]:
    from app.core.security import security

    token = security.create_access_token(
        data={
            "sub": test_admin_data["username"],
            "user_id": "test_admin_id",
            "role_id": test_admin_data["role_id"],
            "is_superuser": True,
            "permissions": ["*"],
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_auth_headers(setup_test_db, test_user_data) -> Dict[str, str]:
    from app.core.security import security

    token = security.create_access_token(
        data={
            "sub": test_user_data["username"],
            "user_id": "test_user_id",
            "role_id": test_user_data["role_id"],
            "is_superuser": False,
            "permissions": [
                "user:view",
                "role:view",
                "plugin:view",
                "backtest:view",
                "selection:view",
                "holdings:view",
                "risk:view",
                "scheduler:view",
                "dingtalk:view",
            ],
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def trader_auth_headers(setup_test_db) -> Dict[str, str]:
    from app.core.security import security

    token = security.create_access_token(
        data={
            "sub": "trader_user",
            "user_id": "trader_user_id",
            "role_id": "role_trader",
            "is_superuser": False,
            "permissions": ["backtest:*", "selection:*", "holdings:*", "risk:view"],
        }
    )
    return {"Authorization": f"Bearer {token}"}
