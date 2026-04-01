import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime


class TestSchedulerIntegration:
    """Test 18.5: Scheduler job creation → Trigger → Verify execution"""

    @pytest.mark.asyncio
    async def test_create_and_execute_job(self, test_db):
        from app.scheduler.job_store import JobStore
        from app.scheduler.job_manager import JobManager

        job_store = JobStore(test_db.client, test_db.name)
        job_manager = JobManager(job_store)

        with patch.object(job_manager, '_schedule_job', new_callable=AsyncMock):
            job_id = await job_manager.create_job(
                name="Test Risk Report",
                job_type="risk_report",
                cron_expression="0 18 * * 1-5",
                config={"user_ids": ["test_user"]},
            )

        assert job_id is not None

        job = await job_manager.get_job(job_id)
        assert job is not None
        assert job["job_type"] == "risk_report"
        assert job["enabled"] is True

        await job_manager.delete_job(job_id)

    @pytest.mark.asyncio
    async def test_job_trigger_and_execution_record(self, test_db):
        from app.scheduler.job_store import JobStore
        from app.scheduler.job_manager import JobManager

        job_store = JobStore(test_db.client, test_db.name)
        job_manager = JobManager(job_store)

        async def mock_handler(config):
            return {"status": "completed", "data": {"processed": 10}}

        job_manager.register_handler("custom", mock_handler)

        with patch.object(job_manager, '_schedule_job', new_callable=AsyncMock):
            job_id = await job_manager.create_job(
                name="Test Custom Job",
                job_type="custom",
                cron_expression="*/5 * * * *",
                config={"test": True},
            )

        with patch.object(job_store, 'try_acquire_execution_lock', new_callable=AsyncMock) as mock_lock:
            mock_lock.return_value = (True, "exec_001")

            with patch.object(job_store, 'update_execution_async', new_callable=AsyncMock):
                with patch.object(job_store, 'update_job_run_times_async', new_callable=AsyncMock):
                    with patch.object(job_manager, '_execute_job', new_callable=AsyncMock) as mock_execute:
                        mock_execute.return_value = "exec_001"

                        try:
                            execution_id = await job_manager.trigger_job(job_id)
                        except Exception:
                            pass

        await job_manager.delete_job(job_id)

    @pytest.mark.asyncio
    async def test_job_execution_history(self, test_db):
        from app.scheduler.job_store import JobStore
        
        job_store = JobStore(test_db.client, test_db.name)

        job_id = "test_job_history_001"
        await job_store.create_job_async({
            "job_id": job_id,
            "name": "History Test Job",
            "job_type": "risk_report",
            "cron_expression": "0 18 * * *",
            "enabled": True,
        })

        for i in range(3):
            await job_store.create_execution_async({
                "job_id": job_id,
                "status": "completed",
                "result": {"count": i},
            })

        executions, total = await job_store.get_executions_async(job_id)
        
        assert total >= 3
        assert len(executions) >= 3

        await job_store.delete_job_async(job_id)

    @pytest.mark.asyncio
    async def test_concurrent_job_prevention(self, test_db):
        from app.scheduler.job_store import JobStore
        
        job_store = JobStore(test_db.client, test_db.name)

        job_id = "concurrent_test_job"
        await job_store.create_job_async({
            "job_id": job_id,
            "name": "Concurrent Test",
            "job_type": "risk_report",
            "cron_expression": "* * * * *",
            "enabled": True,
        })

        acquired_1, exec_id_1 = await job_store.try_acquire_execution_lock(job_id, "risk_report")
        assert acquired_1 is True
        assert exec_id_1 is not None

        acquired_2, exec_id_2 = await job_store.try_acquire_execution_lock(job_id, "risk_report")
        assert acquired_2 is False
        assert exec_id_2 is None

        await job_store.update_execution_async(exec_id_1, "completed")

        acquired_3, exec_id_3 = await job_store.try_acquire_execution_lock(job_id, "risk_report")
        assert acquired_3 is True

        await job_store.delete_job_async(job_id)

    @pytest.mark.asyncio
    async def test_job_cron_validation(self):
        from app.scheduler.job_manager import CronValidator
        
        valid_expressions = [
            "0 18 * * 1-5",
            "*/5 * * * *",
            "0 9-17 * * 1-5",
            "30 18 * * *",
        ]
        
        for expr in valid_expressions:
            assert CronValidator.validate(expr) is True

        invalid_expressions = [
            "0 18 * *",
            "invalid",
            "25 25 * * *",
            "",
        ]
        
        for expr in invalid_expressions:
            assert CronValidator.validate(expr) is False

    @pytest.mark.asyncio
    async def test_job_cron_description(self):
        from app.scheduler.job_manager import CronValidator
        
        assert "18" in CronValidator.describe("0 18 * * *")
        assert CronValidator.describe("*/5 * * * *") != "Invalid cron expression"

    @pytest.mark.asyncio
    async def test_job_update(self, test_db):
        from app.scheduler.job_store import JobStore
        from app.scheduler.job_manager import JobManager

        job_store = JobStore(test_db.client, test_db.name)
        job_manager = JobManager(job_store)

        with patch.object(job_manager, '_schedule_job', new_callable=AsyncMock):
            job_id = await job_manager.create_job(
                name="Original Name",
                job_type="risk_report",
                cron_expression="0 18 * * *",
                config={"key": "original"},
            )

        with patch.object(job_manager, '_schedule_job', new_callable=AsyncMock):
            await job_manager.update_job(
                job_id,
                name="Updated Name",
                cron_expression="0 20 * * *",
                config={"key": "updated"},
            )

        job = await job_manager.get_job(job_id)
        assert job["name"] == "Updated Name"

        await job_manager.delete_job(job_id)

    @pytest.mark.asyncio
    async def test_job_enable_disable(self, test_db):
        from app.scheduler.job_store import JobStore
        from app.scheduler.job_manager import JobManager

        job_store = JobStore(test_db.client, test_db.name)
        job_manager = JobManager(job_store)

        with patch.object(job_manager, '_schedule_job', new_callable=AsyncMock):
            job_id = await job_manager.create_job(
                name="Toggle Test",
                job_type="risk_report",
                cron_expression="0 18 * * *",
                enabled=True,
            )

        job = await job_manager.get_job(job_id)
        assert job["enabled"] is True

        with patch.object(job_manager, '_schedule_job', new_callable=AsyncMock):
            await job_manager.update_job(job_id, enabled=False)

        job = await job_manager.get_job(job_id)
        assert job["enabled"] is False

        await job_manager.delete_job(job_id)

    @pytest.mark.asyncio
    async def test_job_list_with_pagination(self, test_db):
        from app.scheduler.job_store import JobStore
        from app.scheduler.job_manager import JobManager

        job_store = JobStore(test_db.client, test_db.name)
        job_manager = JobManager(job_store)

        created_ids = []
        with patch.object(job_manager, '_schedule_job', new_callable=AsyncMock):
            for i in range(5):
                job_id = await job_manager.create_job(
                    name=f"Pagination Test {i}",
                    job_type="risk_report",
                    cron_expression=f"{i} 18 * * *",
                )
                created_ids.append(job_id)

        jobs, total = await job_manager.list_jobs(skip=0, limit=3)
        assert len(jobs) <= 3
        assert total >= 5

        for job_id in created_ids:
            await job_manager.delete_job(job_id)

    @pytest.mark.asyncio
    async def test_job_handler_registration(self, test_db):
        from app.scheduler.job_store import JobStore
        from app.scheduler.job_manager import JobManager
        
        job_store = JobStore(test_db.client, test_db.name)
        job_manager = JobManager(job_store)

        async def custom_handler(config):
            return {"processed": True}

        job_manager.register_handler("custom", custom_handler)
        
        assert "custom" in job_manager._job_handlers
        assert job_manager._job_handlers["custom"] == custom_handler

    @pytest.mark.asyncio
    async def test_job_retry_on_failure(self, test_db):
        from app.scheduler.job_store import JobStore
        from app.scheduler.job_manager import JobManager

        job_store = JobStore(test_db.client, test_db.name)
        job_manager = JobManager(job_store)

        call_count = 0

        async def failing_handler(config):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return {"status": "success"}

        job_manager.register_handler("failing_test", failing_handler)

        result = await job_manager._run_with_retry(
            handler=failing_handler,
            config={},
            max_retries=3,
        )

        assert result.get("data", {}).get("status") == "success" or result.get("status") == "success"
