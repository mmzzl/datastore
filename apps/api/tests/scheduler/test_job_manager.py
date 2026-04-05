"""Tests for JobManager class."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.scheduler.job_manager import JobManager, CronValidator, JOB_TYPES


class TestJobManager:
    """Test cases for JobManager class."""

    def test_init(self):
        """Test JobManager initialization."""
        mock_job_store = MagicMock()
        manager = JobManager(mock_job_store)

        assert manager.job_store == mock_job_store
        assert manager.timezone == "Asia/Shanghai"
        assert manager._job_handlers == {}
        assert manager._running_jobs == set()
        assert manager.scheduler is not None

    def test_init_custom_timezone(self):
        """Test JobManager initialization with custom timezone."""
        mock_job_store = MagicMock()
        manager = JobManager(mock_job_store, timezone="UTC")

        assert manager.timezone == "UTC"

    def test_register_handler(self):
        """Test handler registration."""
        mock_job_store = MagicMock()
        manager = JobManager(mock_job_store)

        handler = MagicMock()
        manager.register_handler("backtest", handler)

        assert "backtest" in manager._job_handlers
        assert manager._job_handlers["backtest"] == handler

    @pytest.mark.asyncio
    async def test_create_job_valid(self):
        """Test creating a valid job."""
        mock_job_store = AsyncMock()
        mock_job_store.create_job_async = AsyncMock(return_value="job_123")

        manager = JobManager(mock_job_store)
        manager._schedule_job = AsyncMock()

        job_id = await manager.create_job(
            name="Test Job",
            job_type="backtest",
            cron_expression="0 9 * * *",
            config={"strategy": "test"},
            enabled=True
        )

        assert job_id == "job_123"
        mock_job_store.create_job_async.assert_called_once()
        manager._schedule_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_job_invalid_type(self):
        """Test creating a job with invalid type."""
        mock_job_store = AsyncMock()
        manager = JobManager(mock_job_store)

        with pytest.raises(ValueError) as exc_info:
            await manager.create_job(
                name="Test Job",
                job_type="invalid_type",
                cron_expression="0 9 * * *"
            )

        assert "Invalid job_type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_job_invalid_cron(self):
        """Test creating a job with invalid cron expression."""
        mock_job_store = AsyncMock()
        manager = JobManager(mock_job_store)

        with pytest.raises(ValueError) as exc_info:
            await manager.create_job(
                name="Test Job",
                job_type="backtest",
                cron_expression="invalid_cron"
            )

        assert "Invalid cron expression" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_job(self):
        """Test updating an existing job."""
        mock_job_store = AsyncMock()
        mock_job_store.get_job_async = AsyncMock(return_value={
            "job_id": "job_123",
            "name": "Old Name",
            "cron_expression": "0 9 * * *",
            "enabled": True
        })
        mock_job_store.update_job_async = AsyncMock(return_value=True)

        manager = JobManager(mock_job_store)
        manager._schedule_job = AsyncMock()

        result = await manager.update_job(
            job_id="job_123",
            name="New Name",
            cron_expression="0 10 * * *"
        )

        assert result is True
        mock_job_store.update_job_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_job_not_found(self):
        """Test updating a non-existent job."""
        mock_job_store = AsyncMock()
        mock_job_store.get_job_async = AsyncMock(return_value=None)

        manager = JobManager(mock_job_store)

        with pytest.raises(ValueError) as exc_info:
            await manager.update_job(
                job_id="nonexistent",
                name="New Name"
            )

        assert "Job not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_job(self):
        """Test deleting a job."""
        mock_job_store = AsyncMock()
        mock_job_store.delete_job_async = AsyncMock(return_value=True)

        manager = JobManager(mock_job_store)

        result = await manager.delete_job("job_123")

        assert result is True
        mock_job_store.delete_job_async.assert_called_once_with("job_123")

    @pytest.mark.asyncio
    async def test_get_job(self):
        """Test getting job details."""
        mock_job_store = AsyncMock()
        mock_job_store.get_job_async = AsyncMock(return_value={
            "job_id": "job_123",
            "name": "Test Job",
            "cron_expression": "0 9 * * *",
            "enabled": True
        })

        manager = JobManager(mock_job_store)

        job = await manager.get_job("job_123")

        assert job is not None
        assert job["job_id"] == "job_123"
        assert "cron_description" in job

    @pytest.mark.asyncio
    async def test_list_jobs(self):
        """Test listing jobs with pagination."""
        mock_job_store = AsyncMock()
        mock_job_store.list_jobs_async = AsyncMock(return_value=(
            [
                {"job_id": "job_1", "cron_expression": "0 9 * * *"},
                {"job_id": "job_2", "cron_expression": "0 10 * * *"}
            ],
            2
        ))

        manager = JobManager(mock_job_store)

        jobs, total = await manager.list_jobs(skip=0, limit=10)

        assert total == 2
        assert len(jobs) == 2
        for job in jobs:
            assert "cron_description" in job

    @pytest.mark.asyncio
    async def test_trigger_job(self):
        """Test triggering a job to run immediately."""
        mock_job_store = AsyncMock()
        mock_job_store.get_job_async = AsyncMock(return_value={
            "job_id": "job_123",
            "job_type": "backtest",
            "cron_expression": "0 9 * * *",
            "config": {}
        })

        manager = JobManager(mock_job_store)
        manager._execute_job = AsyncMock(return_value="exec_123")

        execution_id = await manager.trigger_job("job_123")

        assert execution_id == "exec_123"
        manager._execute_job.assert_called_once()


class TestJobTypes:
    """Test cases for JOB_TYPES constant."""

    def test_job_types_defined(self):
        """Test that JOB_TYPES is properly defined."""
        assert JOB_TYPES is not None
        assert isinstance(JOB_TYPES, list)

    def test_job_types_count(self):
        """Test that JOB_TYPES contains expected types."""
        expected_types = ["qlib_train", "backtest", "risk_report", "news_collect", "signal_generate", "custom"]
        assert len(JOB_TYPES) == len(expected_types)

        for job_type in expected_types:
            assert job_type in JOB_TYPES
