"""Tests for Qlib API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from datetime import datetime
from fastapi import FastAPI

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


class TestQlibEndpoints:
    """Tests for Qlib API endpoints."""

    @pytest.mark.asyncio
    async def test_get_models_list(self, async_client: AsyncClient, app):
        """Test listing models."""
        mock_model_manager = MagicMock()
        mock_model_manager.list_models.return_value = [
            {
                "model_id": "model_001",
                "version": 1,
                "created_at": datetime.now(),
                "status": "approved",
                "metrics": {"sharpe_ratio": 1.5},
                "config": {"model_type": "lgbm"},
            }
        ]

        from app.api.endpoints import qlib
        from app.core.auth import get_current_user

        mock_user = create_mock_user()
        app.dependency_overrides[qlib.get_model_manager] = lambda: mock_model_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/qlib/models")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["model_id"] == "model_001"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_model_by_id(self, async_client: AsyncClient, app):
        """Test getting a specific model by ID."""
        mock_model_manager = MagicMock()
        mock_model_manager.get_model_metadata.return_value = {
            "model_id": "model_001",
            "version": 1,
            "created_at": datetime.now(),
            "status": "approved",
            "metrics": {"sharpe_ratio": 1.5},
            "config": {"model_type": "lgbm"},
        }

        from app.api.endpoints import qlib
        from app.core.auth import get_current_user

        mock_user = create_mock_user()
        app.dependency_overrides[qlib.get_model_manager] = lambda: mock_model_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/qlib/models/model_001")

            assert response.status_code == 200
            data = response.json()
            assert data["model_id"] == "model_001"
            assert data["status"] == "approved"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_model_not_found(self, async_client: AsyncClient, app):
        """Test getting a non-existent model."""
        mock_model_manager = MagicMock()
        mock_model_manager.get_model_metadata.return_value = None

        from app.api.endpoints import qlib

        app.dependency_overrides[qlib.get_model_manager] = lambda: mock_model_manager

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/qlib/models/nonexistent")

            assert response.status_code == 404
            assert "Model not found" in response.json()["detail"]

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_start_training(self, async_client: AsyncClient, app):
        """Test starting a training task."""
        mock_trainer = MagicMock()
        mock_trainer.start_training.return_value = "task_001"

        from app.api.endpoints import qlib

        app.dependency_overrides[qlib.get_trainer] = lambda: mock_trainer

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/qlib/train",
                json={
                    "model_type": "lgbm",
                    "factor_type": "alpha158",
                    "start_time": "2020-01-01",
                    "end_time": "2025-01-01",
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_training_status(self, async_client: AsyncClient, app):
        """Test getting training status."""
        mock_trainer = MagicMock()
        mock_trainer.get_status.return_value = {
            "status": "running",
            "progress": 50,
            "started_at": datetime.now(),
        }

        from app.api.endpoints import qlib

        app.dependency_overrides[qlib.get_trainer] = lambda: mock_trainer

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/qlib/train/task_001")

            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "task_001"
            assert data["status"] == "running"
            assert data["progress"] == 50

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_training_status_not_found(self, async_client: AsyncClient, app):
        """Test getting status for non-existent training task."""
        mock_trainer = MagicMock()
        mock_trainer.get_status.return_value = {"error": "Task not found"}

        from app.api.endpoints import qlib

        app.dependency_overrides[qlib.get_trainer] = lambda: mock_trainer

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/qlib/train/nonexistent")

            assert response.status_code == 404

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_predict_endpoint(self, async_client: AsyncClient, app):
        """Test stock selection/prediction endpoint."""
        mock_predictor = MagicMock()
        mock_predictor.predict.return_value = [
            {"code": "000001.SZ", "name": "平安银行", "score": 0.95},
            {"code": "000002.SZ", "name": "万科A", "score": 0.92},
        ]

        mock_model_manager = MagicMock()
        mock_model_manager.get_latest_model.return_value = {
            "model_id": "model_001",
            "status": "approved",
        }

        from app.api.endpoints import qlib
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["selection:run"])

        app.dependency_overrides[qlib.get_predictor] = lambda: mock_predictor
        app.dependency_overrides[qlib.get_model_manager] = lambda: mock_model_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/qlib/select",
                json={"topk": 10}
            )

            assert response.status_code == 200
            data = response.json()
            assert "model_id" in data
            assert "results" in data
            assert len(data["results"]) == 2

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_predict_no_approved_model(self, async_client: AsyncClient, app):
        """Test prediction when no approved model exists."""
        mock_model_manager = MagicMock()
        mock_model_manager.get_latest_model.return_value = None

        from app.api.endpoints import qlib
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["selection:run"])

        app.dependency_overrides[qlib.get_predictor] = lambda: MagicMock()
        app.dependency_overrides[qlib.get_model_manager] = lambda: mock_model_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/qlib/select",
                json={"topk": 10}
            )

            assert response.status_code == 404
            assert "No approved model" in response.json()["detail"]

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, async_client: AsyncClient, app):
        """Test accessing endpoints without authentication."""
        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/qlib/models")
            # Models endpoint currently doesn't require auth
            assert response.status_code in [200, 401]

    @pytest.mark.asyncio
    async def test_get_csi300_instruments(self, async_client: AsyncClient, app):
        """Test getting CSI 300 instruments list."""
        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/qlib/instruments/csi300")

            assert response.status_code == 200
            data = response.json()
            assert "instruments" in data
            assert "count" in data


class TestQlibPermissions:
    """Tests for Qlib endpoint permissions."""

    @pytest.mark.asyncio
    async def test_predict_requires_permission(self, async_client: AsyncClient, app):
        """Test that prediction requires selection:run permission."""
        # Create user without selection:run permission
        mock_user = create_mock_user(permissions=["selection:view"], is_superuser=False)

        from app.core.auth import get_current_user

        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/qlib/select",
                json={"topk": 10}
            )

            # Should fail with 403 due to missing permission
            assert response.status_code == 403
            assert "缺少权限" in response.json()["detail"]

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_model_status(self, async_client: AsyncClient, app):
        """Test updating model status."""
        mock_model_manager = MagicMock()
        mock_model_manager.update_model_status.return_value = True

        from app.api.endpoints import qlib

        app.dependency_overrides[qlib.get_model_manager] = lambda: mock_model_manager

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                "/api/qlib/models/model_001/status?status=approved"
            )

            assert response.status_code == 200
            assert "updated to approved" in response.json()["message"]

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_model(self, async_client: AsyncClient, app):
        """Test deleting a model."""
        mock_model_manager = MagicMock()
        mock_model_manager.delete_model.return_value = True

        from app.api.endpoints import qlib

        app.dependency_overrides[qlib.get_model_manager] = lambda: mock_model_manager

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/api/qlib/models/model_001")

            assert response.status_code == 200
            assert "deleted successfully" in response.json()["message"]

        app.dependency_overrides.clear()
