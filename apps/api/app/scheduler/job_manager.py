from datetime import datetime
from typing import Optional, Dict, Any, Callable, Tuple, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError
import logging
import asyncio

from .job_store import JobStore

logger = logging.getLogger(__name__)

JOB_TYPES = ["qlib_train", "backtest", "risk_report", "news_collect", "custom"]


class CronValidator:
    """Cron expression validator and descriptor."""

    @staticmethod
    def validate(cron_expression: str) -> bool:
        """Validate cron expression syntax."""
        try:
            parts = cron_expression.strip().split()
            if len(parts) != 5:
                return False
            CronTrigger.from_crontab(cron_expression)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def describe(cron_expression: str) -> str:
        """Return human-readable description of cron expression."""
        try:
            parts = cron_expression.strip().split()
            if len(parts) != 5:
                return "Invalid cron expression"

            minute, hour, day_of_month, month, day_of_week = parts

            descriptions = []

            if minute == "*" and hour == "*":
                descriptions.append("Every minute")
            elif hour == "*":
                descriptions.append(f"Every hour at minute {minute}")
            elif minute == "0" and hour != "*":
                descriptions.append(f"Daily at {hour}:00")
            elif hour != "*":
                descriptions.append(f"Daily at {hour}:{minute.zfill(2)}")

            if day_of_week != "*":
                days = {
                    "0": "Sunday", "1": "Monday", "2": "Tuesday",
                    "3": "Wednesday", "4": "Thursday", "5": "Friday", "6": "Saturday"
                }
                day_name = days.get(day_of_week, f"day {day_of_week}")
                descriptions.append(f"on {day_name}")

            if day_of_month != "*" and month == "*":
                descriptions.append(f"on day {day_of_month} of the month")

            if month != "*":
                months = {
                    "1": "January", "2": "February", "3": "March",
                    "4": "April", "5": "May", "6": "June",
                    "7": "July", "8": "August", "9": "September",
                    "10": "October", "11": "November", "12": "December"
                }
                month_name = months.get(month, f"month {month}")
                descriptions.append(f"in {month_name}")

            if not descriptions:
                return f"Cron: {cron_expression}"

            return ", ".join(descriptions)

        except Exception:
            return f"Cron: {cron_expression}"


class JobManager:
    """Manages scheduled jobs with APScheduler."""

    def __init__(self, job_store: JobStore, timezone: str = "Asia/Shanghai"):
        self.job_store = job_store
        self.timezone = timezone
        self.scheduler = AsyncIOScheduler(timezone=timezone)
        self._job_handlers: Dict[str, Callable] = {}
        self._running_jobs: set = set()

    def register_handler(self, job_type: str, handler: Callable):
        """Register a handler function for a job type."""
        self._job_handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")

    async def start(self):
        """Start the scheduler and load existing jobs."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

        jobs, _ = await self.job_store.list_jobs_async(enabled=True)
        for job in jobs:
            await self._schedule_job(job)

    async def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped")

    async def create_job(
        self,
        name: str,
        job_type: str,
        cron_expression: str,
        config: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        max_retries: int = 3
    ) -> str:
        """Create a new scheduled job."""
        if job_type not in JOB_TYPES:
            raise ValueError(f"Invalid job_type: {job_type}. Valid types: {JOB_TYPES}")

        if not CronValidator.validate(cron_expression):
            raise ValueError(f"Invalid cron expression: {cron_expression}")

        job_data = {
            "name": name,
            "job_type": job_type,
            "cron_expression": cron_expression,
            "enabled": enabled,
            "config": config or {},
            "max_retries": max_retries,
        }

        job_id = await self.job_store.create_job_async(job_data)

        if enabled:
            job_data["job_id"] = job_id
            await self._schedule_job(job_data)

        return job_id

    async def update_job(
        self,
        job_id: str,
        name: Optional[str] = None,
        cron_expression: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        enabled: Optional[bool] = None
    ) -> bool:
        """Update an existing job."""
        job = await self.job_store.get_job_async(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        update_data = {}
        if name is not None:
            update_data["name"] = name
        if cron_expression is not None:
            if not CronValidator.validate(cron_expression):
                raise ValueError(f"Invalid cron expression: {cron_expression}")
            update_data["cron_expression"] = cron_expression
        if config is not None:
            update_data["config"] = config
        if enabled is not None:
            update_data["enabled"] = enabled

        if not update_data:
            return False

        await self.job_store.update_job_async(job_id, update_data)

        try:
            self.scheduler.remove_job(job_id)
        except JobLookupError:
            pass

        updated_job = await self.job_store.get_job_async(job_id)
        if updated_job and updated_job.get("enabled"):
            await self._schedule_job(updated_job)

        return True

    async def delete_job(self, job_id: str) -> bool:
        """Delete a job."""
        try:
            self.scheduler.remove_job(job_id)
        except JobLookupError:
            pass

        return await self.job_store.delete_job_async(job_id)

    async def trigger_job(self, job_id: str) -> str:
        """Trigger a job to run immediately."""
        job = await self.job_store.get_job_async(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        return await self._execute_job(job)

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details."""
        job = await self.job_store.get_job_async(job_id)
        if job:
            job["cron_description"] = CronValidator.describe(job.get("cron_expression", ""))
        return job

    async def list_jobs(
        self,
        job_type: Optional[str] = None,
        enabled: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List all jobs with pagination."""
        jobs, total = await self.job_store.list_jobs_async(
            job_type=job_type,
            enabled=enabled,
            skip=skip,
            limit=limit
        )
        for job in jobs:
            job["cron_description"] = CronValidator.describe(job.get("cron_expression", ""))
        return jobs, total

    async def get_executions(
        self,
        job_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get execution history for a job with pagination."""
        return await self.job_store.get_executions_async(job_id, skip=skip, limit=limit)

    async def _schedule_job(self, job: Dict[str, Any]):
        """Schedule a job with APScheduler."""
        job_id = job.get("job_id")
        cron_expression = job.get("cron_expression")

        try:
            trigger = CronTrigger.from_crontab(cron_expression, timezone=self.timezone)

            self.scheduler.add_job(
                self._execute_job_wrapper,
                trigger=trigger,
                id=job_id,
                args=[job],
                replace_existing=True
            )

            scheduled_job = self.scheduler.get_job(job_id)
            next_run = scheduled_job.next_run_time if scheduled_job else None
            await self.job_store.update_job_run_times_async(job_id, None, next_run)

            logger.info(f"Scheduled job {job_id}: {cron_expression}")

        except Exception as e:
            logger.error(f"Failed to schedule job {job_id}: {e}")
            raise

    async def _execute_job_wrapper(self, job: Dict[str, Any]):
        """Wrapper to handle job execution with error handling."""
        job_id = job.get("job_id")
        try:
            await self._execute_job(job)
        except Exception as e:
            logger.error(f"Job {job_id} execution failed: {e}")

    async def _execute_job(self, job: Dict[str, Any]) -> str:
        """Execute a job with atomic concurrency check and execution tracking."""
        job_id = job.get("job_id")
        job_type = job.get("job_type")
        config = job.get("config", {})
        max_retries = job.get("max_retries", 3)

        if job_id in self._running_jobs:
            raise RuntimeError(f"Job {job_id} is already running (local concurrent execution prevented)")

        self._running_jobs.add(job_id)

        acquired, execution_id = await self.job_store.try_acquire_execution_lock(job_id, job_type)
        if not acquired:
            self._running_jobs.discard(job_id)
            raise RuntimeError(f"Job {job_id} is already running (atomic lock failed)")

        try:
            handler = self._job_handlers.get(job_type)

            if handler:
                result = await self._run_with_retry(handler, config, max_retries)
            else:
                result = await self._default_handler(job_type, config)

            await self.job_store.update_execution_async(
                execution_id,
                "success",
                result=result
            )

            last_run = datetime.now()
            scheduled_job = self.scheduler.get_job(job_id)
            next_run = scheduled_job.next_run_time if scheduled_job else None
            await self.job_store.update_job_run_times_async(job_id, last_run, next_run)

            logger.info(f"Job {job_id} completed successfully")
            return execution_id

        except Exception as e:
            await self.job_store.update_execution_async(
                execution_id,
                "failed",
                error_message=str(e)
            )
            logger.error(f"Job {job_id} failed: {e}")
            raise

        finally:
            self._running_jobs.discard(job_id)

    async def _run_with_retry(
        self,
        handler: Callable,
        config: Dict[str, Any],
        max_retries: int
    ) -> Dict[str, Any]:
        """Run handler with retry logic."""
        last_error = None

        for attempt in range(max_retries):
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(config)
                else:
                    result = handler(config)
                return {"data": result} if result else {"status": "completed"}
            except Exception as e:
                last_error = e
                logger.warning(f"Handler execution attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        raise last_error or RuntimeError("Handler execution failed")

    async def _default_handler(self, job_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Default handler for job types without registered handlers."""
        logger.info(f"Executing default handler for {job_type}")
        return {"status": "completed", "job_type": job_type}
