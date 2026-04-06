"""Tests for Backtest API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from datetime import datetime

pytestmark = pytest.mark.asyncio


def create_mock_user(username="testadmin", user_id="test_admin_id", role_id="role_admin", is_superuser=True, permissions=None, display_name="Test User"):
    """Create a mock authenticated user."""
    from app.core.auth import AuthenticatedUser
    return AuthenticatedUser(
        username=username,
        user_id=user_id,
        display_name=display_name,
        role_id=role_id,
        permissions=permissions or ["*"],
        is_superuser=is_superuser,
    )


class TestBacktestEndpoints:
    """Tests for Backtest API endpoints."""

    @pytest.mark.asyncio
    async def test_run_backtest(self, async_client: AsyncClient, app):
        """Test running a backtest."""
        mock_engine = MagicMock()
        mock_engine.run_backtest = AsyncMock(return_value="task_001")

        from app.api.endpoints import backtest
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["backtest:run"])

        def get_engine_override(request=None):
            return mock_engine

        app.dependency_overrides[backtest.get_backtest_engine] = get_engine_override
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/backtest/run",
                json={
                    "strategy": "ma_cross",
                    "params": {"short_window": 5, "long_window": 20},
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "initial_capital": 100000,
                    "instruments": ["000001.SZ", "000002.SZ"],
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "task_001"
            assert data["status"] == "pending"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_run_backtest_invalid_strategy(self, async_client: AsyncClient, app):
        """Test running backtest with invalid strategy."""
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["backtest:run"])
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/backtest/run",
                json={
                    "strategy": "invalid_strategy",
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                }
            )

            assert response.status_code == 422  # Validation error

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_run_backtest_invalid_date_range(self, async_client: AsyncClient, app):
        """Test running backtest with invalid date range."""
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["backtest:run"])
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/backtest/run",
                json={
                    "strategy": "ma_cross",
                    "start_date": "2023-12-31",
                    "end_date": "2023-01-01",  # End date before start date
                }
            )

            assert response.status_code == 422  # Validation error

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_run_backtest_plugin_without_id(self, async_client: AsyncClient, app):
        """Test running plugin strategy without plugin_id."""
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["backtest:run"])
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/backtest/run",
                json={
                    "strategy": "plugin",
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                }
            )

            assert response.status_code == 400
            assert "plugin_id is required" in response.json()["detail"]

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_backtest_results(self, async_client: AsyncClient, app):
        """Test getting backtest results list."""
        mock_storage = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count_documents.return_value = 1
        mock_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = [
            {
                "task_id": "task_001",
                "strategy": "ma_cross",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "metrics": {"sharpe_ratio": 1.5, "total_return": 0.15},
                "trades": [],
            }
        ]
        mock_storage.db.__getitem__.return_value = mock_collection
        mock_storage.close = MagicMock()

        from app.api.endpoints import backtest
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["backtest:view"])

        with patch.object(backtest, "get_storage", return_value=mock_storage):
            app.dependency_overrides[get_current_user] = lambda: mock_user

            from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
            async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/backtest/results")

                assert response.status_code == 200
                data = response.json()
                assert "items" in data
                assert "total" in data

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_strategy_plugins(self, async_client: AsyncClient, app):
        """Test getting strategy plugins list."""
        mock_storage = MagicMock()
        mock_storage.get_all_strategy_plugins.return_value = [
            {
                "_id": "plugin_001",
                "name": "Test Plugin",
                "description": "A test plugin",
                "module_name": "test_plugin",
                "class_name": "TestStrategy",
                "path": "plugins/test_plugin",
                "author": "test",
                "version": "1.0.0",
                "tags": ["test"],
                "parameters": {},
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
        ]
        mock_storage.close = MagicMock()

        from app.api.endpoints import backtest

        with patch.object(backtest, "get_storage", return_value=mock_storage):
            from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
            async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/backtest/plugins")

                assert response.status_code == 200
                data = response.json()
                assert "items" in data
                assert "total" in data

    @pytest.mark.asyncio
    async def test_get_strategy_plugin_by_id(self, async_client: AsyncClient, app):
        """Test getting a specific strategy plugin."""
        mock_storage = MagicMock()
        mock_storage.get_strategy_plugin.return_value = {
            "_id": "plugin_001",
            "name": "Test Plugin",
            "description": "A test plugin",
            "module_name": "test_plugin",
            "class_name": "TestStrategy",
            "path": "plugins/test_plugin",
            "author": "test",
            "version": "1.0.0",
            "tags": ["test"],
            "parameters": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        mock_storage.close = MagicMock()

        from app.api.endpoints import backtest

        with patch.object(backtest, "get_storage", return_value=mock_storage):
            from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
            async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/backtest/plugins/plugin_001")

                assert response.status_code == 200
                data = response.json()
                assert data["name"] == "Test Plugin"

    @pytest.mark.asyncio
    async def test_get_strategy_plugin_not_found(self, async_client: AsyncClient, app):
        """Test getting a non-existent strategy plugin."""
        mock_storage = MagicMock()
        mock_storage.get_strategy_plugin.return_value = None
        mock_storage.close = MagicMock()

        from app.api.endpoints import backtest

        with patch.object(backtest, "get_storage", return_value=mock_storage):
            from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
            async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.delete("/api/backtest/plugins/nonexistent")

                assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, async_client: AsyncClient, app):
        """Test accessing endpoints without authentication."""
        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/backtest/run",
                json={
                    "strategy": "ma_cross",
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                }
            )

            assert response.status_code == 401


class TestBacktestPermissions:
    """Tests for Backtest endpoint permissions."""

    @pytest.mark.asyncio
    async def test_run_requires_permission(self, async_client: AsyncClient, app):
        """Test that running backtest requires backtest:run permission."""
        # User without backtest:run permission
        mock_user = create_mock_user(permissions=["backtest:view"], is_superuser=False)

        from app.core.auth import get_current_user

        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/backtest/run",
                json={
                    "strategy": "ma_cross",
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                }
            )

            # Should fail with 403 due to missing permission
            assert response.status_code == 403
            assert "缺少权限" in response.json()["detail"]

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_view_results_requires_auth(self, async_client: AsyncClient, app):
        """Test that viewing results requires authentication."""
        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/backtest/results")

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_plugin(self, async_client: AsyncClient, app):
        """Test deleting a strategy plugin."""
        mock_storage = MagicMock()
        mock_storage.get_strategy_plugin.return_value = {
            "_id": "plugin_001",
            "module_name": "test_plugin",
        }
        mock_storage.delete_strategy_plugin.return_value = True
        mock_storage.close = MagicMock()

        from app.api.endpoints import backtest

        with patch.object(backtest, "get_storage", return_value=mock_storage), \
             patch("os.path.exists", return_value=False):
            from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
            async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.delete("/api/backtest/plugins/plugin_001")

                assert response.status_code == 200
                assert "deleted successfully" in response.json()["message"]
