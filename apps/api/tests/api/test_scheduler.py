"""Tests for Scheduler API endpoints."""

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


def create_mock_job(job_id="job_001", name="Test Job"):
    """Create a complete mock job object."""
    return {
        "job_id": job_id,
        "name": name,
        "job_type": "qlib_train",
        "cron_expression": "0 2 * * *",
        "enabled": True,
        "config": {},
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


class TestSchedulerEndpoints:
    """Tests for Scheduler API endpoints."""

    @pytest.mark.asyncio
    async def test_list_jobs(self, async_client: AsyncClient, app):
        """Test listing scheduled jobs."""
        mock_manager = MagicMock()
        mock_manager.list_jobs = AsyncMock(return_value=(
            [create_mock_job()],
            1
        ))

        from app.api.endpoints import scheduler
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["scheduler:view"])
        app.dependency_overrides[scheduler.get_job_manager] = lambda: mock_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/scheduler/jobs")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert data["total"] == 1

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_jobs_with_filters(self, async_client: AsyncClient, app):
        """Test listing jobs with filters."""
        mock_manager = MagicMock()
        mock_manager.list_jobs = AsyncMock(return_value=([], 0))

        from app.api.endpoints import scheduler
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["scheduler:view"])
        app.dependency_overrides[scheduler.get_job_manager] = lambda: mock_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/scheduler/jobs?job_type=qlib_train&enabled=true")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_job(self, async_client: AsyncClient, app):
        """Test creating a scheduled job."""
        mock_manager = MagicMock()
        mock_manager.create_job = AsyncMock(return_value="job_001")
        mock_manager.get_job = AsyncMock(return_value=create_mock_job())

        from app.api.endpoints import scheduler
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["scheduler:manage"])
        app.dependency_overrides[scheduler.get_job_manager] = lambda: mock_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/scheduler/jobs",
                json={
                    "name": "Test Job",
                    "job_type": "qlib_train",
                    "cron_expression": "0 2 * * *",
                    "enabled": True,
                    "config": {"model_type": "lgbm"},
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "job_001"
            assert data["name"] == "Test Job"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_job_invalid_cron(self, async_client: AsyncClient, app):
        """Test creating job with invalid cron expression."""
        mock_manager = MagicMock()
        mock_manager.create_job = AsyncMock(side_effect=ValueError("Invalid cron expression"))

        from app.api.endpoints import scheduler
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["scheduler:manage"])
        app.dependency_overrides[scheduler.get_job_manager] = lambda: mock_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/scheduler/jobs",
                json={
                    "name": "Test Job",
                    "job_type": "qlib_train",
                    "cron_expression": "invalid",
                    "enabled": True,
                }
            )

            assert response.status_code == 400

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_job(self, async_client: AsyncClient, app):
        """Test getting a specific job by ID."""
        mock_manager = MagicMock()
        mock_manager.get_job = AsyncMock(return_value=create_mock_job())

        from app.api.endpoints import scheduler
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["scheduler:view"])
        app.dependency_overrides[scheduler.get_job_manager] = lambda: mock_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/scheduler/jobs/job_001")

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "job_001"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, async_client: AsyncClient, app):
        """Test getting a non-existent job."""
        mock_manager = MagicMock()
        mock_manager.get_job = AsyncMock(return_value=None)

        from app.api.endpoints import scheduler
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["scheduler:view"])
        app.dependency_overrides[scheduler.get_job_manager] = lambda: mock_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/scheduler/jobs/nonexistent")

            assert response.status_code == 404
            assert "Job not found" in response.json()["detail"]

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_job(self, async_client: AsyncClient, app):
        """Test updating a scheduled job."""
        mock_manager = MagicMock()
        mock_manager.update_job = AsyncMock(return_value=True)
        mock_manager.get_job = AsyncMock(return_value=create_mock_job(name="Updated Job"))

        from app.api.endpoints import scheduler
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["scheduler:manage"])
        app.dependency_overrides[scheduler.get_job_manager] = lambda: mock_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                "/api/scheduler/jobs/job_001",
                json={
                    "name": "Updated Job",
                    "cron_expression": "0 3 * * *",
                    "enabled": False,
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Job"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_job(self, async_client: AsyncClient, app):
        """Test deleting a scheduled job."""
        mock_manager = MagicMock()
        mock_manager.delete_job = AsyncMock(return_value=True)

        from app.api.endpoints import scheduler
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["scheduler:manage"])
        app.dependency_overrides[scheduler.get_job_manager] = lambda: mock_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/api/scheduler/jobs/job_001")

            assert response.status_code == 200
            assert "deleted successfully" in response.json()["message"]

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_job_not_found(self, async_client: AsyncClient, app):
        """Test deleting a non-existent job."""
        mock_manager = MagicMock()
        mock_manager.delete_job = AsyncMock(return_value=False)

        from app.api.endpoints import scheduler
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["scheduler:manage"])
        app.dependency_overrides[scheduler.get_job_manager] = lambda: mock_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/api/scheduler/jobs/nonexistent")

            assert response.status_code == 404

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_trigger_job(self, async_client: AsyncClient, app):
        """Test triggering a job to run immediately."""
        mock_manager = MagicMock()
        mock_manager.trigger_job = AsyncMock(return_value="exec_001")

        from app.api.endpoints import scheduler
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["scheduler:manage"])
        app.dependency_overrides[scheduler.get_job_manager] = lambda: mock_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/scheduler/jobs/job_001/trigger")

            assert response.status_code == 200
            data = response.json()
            assert "triggered successfully" in data["message"]
            assert data["execution_id"] == "exec_001"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_trigger_job_not_found(self, async_client: AsyncClient, app):
        """Test triggering a non-existent job."""
        mock_manager = MagicMock()
        mock_manager.trigger_job = AsyncMock(side_effect=ValueError("Job not found"))

        from app.api.endpoints import scheduler
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["scheduler:manage"])
        app.dependency_overrides[scheduler.get_job_manager] = lambda: mock_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/scheduler/jobs/nonexistent/trigger")

            assert response.status_code == 404

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_trigger_job_conflict(self, async_client: AsyncClient, app):
        """Test triggering a job that is already running."""
        mock_manager = MagicMock()
        mock_manager.trigger_job = AsyncMock(side_effect=RuntimeError("Job is already running"))

        from app.api.endpoints import scheduler
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["scheduler:manage"])
        app.dependency_overrides[scheduler.get_job_manager] = lambda: mock_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/scheduler/jobs/job_001/trigger")

            assert response.status_code == 409

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_executions(self, async_client: AsyncClient, app):
        """Test getting job execution history."""
        mock_manager = MagicMock()
        mock_manager.get_job = AsyncMock(return_value=create_mock_job())
        mock_manager.get_executions = AsyncMock(return_value=(
            [
                {
                    "execution_id": "exec_001",
                    "job_id": "job_001",
                    "job_type": "qlib_train",
                    "status": "success",
                    "started_at": datetime.now(),
                    "completed_at": datetime.now(),
                }
            ],
            1
        ))

        from app.api.endpoints import scheduler
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["scheduler:view"])
        app.dependency_overrides[scheduler.get_job_manager] = lambda: mock_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/scheduler/jobs/job_001/executions")

            assert response.status_code == 200
            data = response.json()
            assert "executions" in data
            assert "total" in data
            assert data["total"] == 1

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_executions_job_not_found(self, async_client: AsyncClient, app):
        """Test getting executions for non-existent job."""
        mock_manager = MagicMock()
        mock_manager.get_job = AsyncMock(return_value=None)

        from app.api.endpoints import scheduler
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["scheduler:view"])
        app.dependency_overrides[scheduler.get_job_manager] = lambda: mock_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/scheduler/jobs/nonexistent/executions")

            assert response.status_code == 404

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, async_client: AsyncClient, app):
        """Test accessing endpoints without authentication."""
        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/scheduler/jobs")

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_validate_cron(self, async_client: AsyncClient, app):
        """Test validating a cron expression."""
        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/scheduler/validate-cron",
                json={"cron_expression": "0 2 * * *"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "valid" in data
            assert "description" in data

    @pytest.mark.asyncio
    async def test_get_job_types(self, async_client: AsyncClient, app):
        """Test getting available job types."""
        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/scheduler/job-types")

            assert response.status_code == 200
            data = response.json()
            assert "job_types" in data


class TestSchedulerPermissions:
    """Tests for Scheduler endpoint permissions."""

    @pytest.mark.asyncio
    async def test_create_requires_permission(self, async_client: AsyncClient, app):
        """Test that creating jobs requires scheduler:manage permission."""
        mock_user = create_mock_user(permissions=["scheduler:view"], is_superuser=False)

        from app.core.auth import get_current_user

        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/scheduler/jobs",
                json={
                    "name": "Test Job",
                    "job_type": "qlib_train",
                    "cron_expression": "0 2 * * *",
                    "enabled": True,
                }
            )

            assert response.status_code == 403
            assert "缺少权限" in response.json()["detail"]

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_requires_permission(self, async_client: AsyncClient, app):
        """Test that deleting jobs requires scheduler:manage permission."""
        mock_user = create_mock_user(permissions=["scheduler:view"], is_superuser=False)

        from app.core.auth import get_current_user

        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/api/scheduler/jobs/job_001")

            assert response.status_code == 403

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_trigger_requires_permission(self, async_client: AsyncClient, app):
        """Test that triggering jobs requires scheduler:manage permission."""
        mock_user = create_mock_user(permissions=["scheduler:view"], is_superuser=False)

        from app.core.auth import get_current_user

        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/scheduler/jobs/job_001/trigger")

            assert response.status_code == 403

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_requires_permission(self, async_client: AsyncClient, app):
        """Test that updating jobs requires scheduler:manage permission."""
        mock_user = create_mock_user(permissions=["scheduler:view"], is_superuser=False)

        from app.core.auth import get_current_user

        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                "/api/scheduler/jobs/job_001",
                json={"name": "Updated"}
            )

            assert response.status_code == 403

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_viewer_can_list_jobs(self, async_client: AsyncClient, app):
        """Test that viewer can list jobs."""
        mock_manager = MagicMock()
        mock_manager.list_jobs = AsyncMock(return_value=([], 0))

        from app.api.endpoints import scheduler
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["scheduler:view"], is_superuser=False)
        app.dependency_overrides[scheduler.get_job_manager] = lambda: mock_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/scheduler/jobs")

            assert response.status_code == 200

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_viewer_can_get_job(self, async_client: AsyncClient, app):
        """Test that viewer can get job details."""
        mock_manager = MagicMock()
        mock_manager.get_job = AsyncMock(return_value={
            "job_id": "job_001",
            "name": "Test Job",
        })

        from app.api.endpoints import scheduler
        from app.core.auth import get_current_user

        mock_user = create_mock_user(permissions=["scheduler:view"], is_superuser=False)
        app.dependency_overrides[scheduler.get_job_manager] = lambda: mock_manager
        app.dependency_overrides[get_current_user] = lambda: mock_user

        from httpx import ASGITransport, AsyncClient as HttpxAsyncClient
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/scheduler/jobs/job_001")

            assert response.status_code == 200

        app.dependency_overrides.clear()
