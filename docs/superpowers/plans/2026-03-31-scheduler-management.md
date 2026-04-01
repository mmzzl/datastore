# Scheduler Management Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a complete job scheduling management module with APScheduler integration, MongoDB persistence, and REST API endpoints.

**Architecture:** 
- JobStore handles MongoDB persistence for scheduler_jobs and job_executions collections
- JobManager wraps APScheduler with job lifecycle management and concurrent execution prevention
- API endpoints provide CRUD operations and manual job triggering

**Tech Stack:** FastAPI, APScheduler, MongoDB, Pydantic

---

## File Structure

- Create: `apps/api/app/scheduler/job_store.py` - MongoDB persistence layer
- Create: `apps/api/app/scheduler/job_manager.py` - APScheduler wrapper with job management
- Modify: `apps/api/app/scheduler/__init__.py` - Export new classes
- Create: `apps/api/app/api/endpoints/scheduler.py` - REST API endpoints
- Modify: `apps/api/main.py` - Register scheduler router
- Create: `apps/api/app/schemas/scheduler.py` - Pydantic models for API

---

### Task 1: Create Job Store for MongoDB Persistence

**Files:**
- Create: `apps/api/app/scheduler/job_store.py`

- [ ] **Step 1: Write job_store.py with MongoDB collections**
```python
from datetime import datetime
from typing import Optional, List, Dict, Any
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import logging
import uuid

logger = logging.getLogger(__name__)


class JobStore:
    """MongoDB persistence for scheduler jobs and executions."""

    def __init__(self, mongo_client: MongoClient, db_name: str):
        self.db = mongo_client[db_name]
        self.jobs_collection = self.db["scheduler_jobs"]
        self.executions_collection = self.db["job_executions"]

    def create_job(self, job_data: Dict[str, Any]) -> str:
        """Create a new scheduled job."""
        job_id = job_data.get("job_id") or str(uuid.uuid4())
        job_data["job_id"] = job_id
        job_data["created_at"] = datetime.now()
        job_data["updated_at"] = datetime.now()
        
        try:
            self.jobs_collection.insert_one(job_data)
            logger.info(f"Created job: {job_id}")
            return job_id
        except PyMongoError as e:
            logger.error(f"Failed to create job: {e}")
            raise

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job by ID."""
        try:
            job = self.jobs_collection.find_one({"job_id": job_id})
            if job:
                job["_id"] = str(job["_id"])
            return job
        except PyMongoError as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            raise

    def list_jobs(
        self, 
        job_type: Optional[str] = None, 
        enabled: Optional[bool] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List jobs with optional filtering."""
        query = {}
        if job_type:
            query["job_type"] = job_type
        if enabled is not None:
            query["enabled"] = enabled
        
        try:
            cursor = self.jobs_collection.find(query).skip(skip).limit(limit)
            jobs = []
            for job in cursor:
                job["_id"] = str(job["_id"])
                jobs.append(job)
            return jobs
        except PyMongoError as e:
            logger.error(f"Failed to list jobs: {e}")
            raise

    def update_job(self, job_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a job."""
        update_data["updated_at"] = datetime.now()
        
        try:
            result = self.jobs_collection.update_one(
                {"job_id": job_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Failed to update job {job_id}: {e}")
            raise

    def delete_job(self, job_id: str) -> bool:
        """Delete a job."""
        try:
            result = self.jobs_collection.delete_one({"job_id": job_id})
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            raise

    def update_job_run_times(
        self, 
        job_id: str, 
        last_run: datetime, 
        next_run: Optional[datetime]
    ) -> bool:
        """Update job last_run and next_run times."""
        try:
            result = self.jobs_collection.update_one(
                {"job_id": job_id},
                {"$set": {
                    "last_run": last_run,
                    "next_run": next_run,
                    "updated_at": datetime.now()
                }}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Failed to update run times for {job_id}: {e}")
            raise

    def create_execution(self, execution_data: Dict[str, Any]) -> str:
        """Create an execution record."""
        execution_id = str(uuid.uuid4())
        execution_data["execution_id"] = execution_id
        execution_data["started_at"] = datetime.now()
        
        try:
            self.executions_collection.insert_one(execution_data)
            logger.info(f"Created execution: {execution_id}")
            return execution_id
        except PyMongoError as e:
            logger.error(f"Failed to create execution: {e}")
            raise

    def update_execution(
        self, 
        execution_id: str, 
        status: str, 
        result: Optional[Dict] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update execution status and result."""
        update_data = {
            "status": status,
            "completed_at": datetime.now()
        }
        if result:
            update_data["result"] = result
        if error_message:
            update_data["error_message"] = error_message
        
        try:
            result = self.executions_collection.update_one(
                {"execution_id": execution_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Failed to update execution {execution_id}: {e}")
            raise

    def get_executions(
        self, 
        job_id: str, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get execution history for a job."""
        try:
            cursor = self.executions_collection.find(
                {"job_id": job_id}
            ).sort("started_at", -1).skip(skip).limit(limit)
            
            executions = []
            for exec_doc in cursor:
                exec_doc["_id"] = str(exec_doc["_id"])
                executions.append(exec_doc)
            return executions
        except PyMongoError as e:
            logger.error(f"Failed to get executions for {job_id}: {e}")
            raise

    def get_running_execution(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Check if a job is currently running."""
        try:
            return self.executions_collection.find_one(
                {"job_id": job_id, "status": "running"}
            )
        except PyMongoError as e:
            logger.error(f"Failed to check running execution: {e}")
            raise
```

---

### Task 2: Create Job Manager with APScheduler Integration

**Files:**
- Create: `apps/api/app/scheduler/job_manager.py`

- [ ] **Step 1: Write job_manager.py with APScheduler wrapper**
```python
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError
import logging

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
        
        jobs = self.job_store.list_jobs(enabled=True)
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
        
        job_id = self.job_store.create_job(job_data)
        
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
        job = self.job_store.get_job(job_id)
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
        
        self.job_store.update_job(job_id, update_data)
        
        self.scheduler.remove_job(job_id)
        
        updated_job = self.job_store.get_job(job_id)
        if updated_job and updated_job.get("enabled"):
            await self._schedule_job(updated_job)
        
        return True

    async def delete_job(self, job_id: str) -> bool:
        """Delete a job."""
        try:
            self.scheduler.remove_job(job_id)
        except JobLookupError:
            pass
        
        return self.job_store.delete_job(job_id)

    async def trigger_job(self, job_id: str) -> str:
        """Trigger a job to run immediately."""
        job = self.job_store.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        running = self.job_store.get_running_execution(job_id)
        if running:
            raise RuntimeError(f"Job {job_id} is already running")
        
        return await self._execute_job(job)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details."""
        job = self.job_store.get_job(job_id)
        if job:
            job["cron_description"] = CronValidator.describe(job.get("cron_expression", ""))
        return job

    def list_jobs(
        self,
        job_type: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> list:
        """List all jobs."""
        jobs = self.job_store.list_jobs(job_type=job_type, enabled=enabled)
        for job in jobs:
            job["cron_description"] = CronValidator.describe(job.get("cron_expression", ""))
        return jobs

    def get_executions(self, job_id: str, limit: int = 50) -> list:
        """Get execution history for a job."""
        return self.job_store.get_executions(job_id, limit=limit)

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
            
            next_run = self.scheduler.get_job(job_id).next_run_time
            self.job_store.update_job_run_times(job_id, None, next_run)
            
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
        """Execute a job with concurrency check and execution tracking."""
        job_id = job.get("job_id")
        job_type = job.get("job_type")
        config = job.get("config", {})
        max_retries = job.get("max_retries", 3)
        
        if job_id in self._running_jobs:
            raise RuntimeError(f"Job {job_id} is already running (concurrent execution prevented)")
        
        self._running_jobs.add(job_id)
        execution_id = self.job_store.create_execution({
            "job_id": job_id,
            "job_type": job_type,
            "status": "running"
        })
        
        try:
            handler = self._job_handlers.get(job_type)
            
            if handler:
                result = await self._run_with_retry(handler, config, max_retries)
            else:
                result = await self._default_handler(job_type, config)
            
            self.job_store.update_execution(
                execution_id, 
                "success", 
                result=result
            )
            
            last_run = datetime.now()
            next_run = self.scheduler.get_job(job_id).next_run_time if self.scheduler.get_job(job_id) else None
            self.job_store.update_job_run_times(job_id, last_run, next_run)
            
            logger.info(f"Job {job_id} completed successfully")
            return execution_id
            
        except Exception as e:
            self.job_store.update_execution(
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
                if hasattr(handler, '__call__'):
                    import asyncio
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(config)
                    else:
                        result = handler(config)
                    return {"data": result} if result else {"status": "completed"}
                return {"status": "completed"}
            except Exception as e:
                last_error = e
                logger.warning(f"Handler execution attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
        
        raise last_error or RuntimeError("Handler execution failed")

    async def _default_handler(self, job_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Default handler for job types without registered handlers."""
        logger.info(f"Executing default handler for {job_type}")
        return {"status": "completed", "job_type": job_type}
```

---

### Task 3: Create Pydantic Schemas for API

**Files:**
- Create: `apps/api/app/schemas/scheduler.py`

- [ ] **Step 1: Write scheduler.py schemas**
```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class JobType(str, Enum):
    QLIB_TRAIN = "qlib_train"
    BACKTEST = "backtest"
    RISK_REPORT = "risk_report"
    NEWS_COLLECT = "news_collect"
    CUSTOM = "custom"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class JobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    job_type: JobType
    cron_expression: str = Field(..., min_length=9, max_length=100)
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    enabled: bool = Field(default=True)
    max_retries: int = Field(default=3, ge=0, le=10)


class JobUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    cron_expression: Optional[str] = Field(None, min_length=9, max_length=100)
    config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class JobResponse(BaseModel):
    job_id: str
    name: str
    job_type: str
    cron_expression: str
    cron_description: Optional[str] = None
    enabled: bool
    config: Dict[str, Any]
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int


class ExecutionResponse(BaseModel):
    execution_id: str
    job_id: str
    job_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ExecutionListResponse(BaseModel):
    executions: List[ExecutionResponse]
    total: int


class CronValidateRequest(BaseModel):
    cron_expression: str


class CronValidateResponse(BaseModel):
    valid: bool
    description: str
    error: Optional[str] = None
```

---

### Task 4: Create API Endpoints

**Files:**
- Create: `apps/api/app/api/endpoints/scheduler.py`

- [ ] **Step 1: Write scheduler API endpoints**
```python
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging

from app.core.config import settings
from app.storage import MongoStorage
from app.scheduler.job_store import JobStore
from app.scheduler.job_manager import JobManager, CronValidator, JOB_TYPES
from app.schemas.scheduler import (
    JobCreate, JobUpdate, JobResponse, JobListResponse,
    ExecutionResponse, ExecutionListResponse,
    CronValidateRequest, CronValidateResponse
)
from pymongo import MongoClient
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scheduler", tags=["scheduler"])

_job_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """Get or create JobManager instance."""
    global _job_manager
    if _job_manager is None:
        if settings.mongodb_username and settings.mongodb_password:
            encoded_password = quote_plus(settings.mongodb_password)
            connection_string = f"mongodb://{settings.mongodb_username}:{encoded_password}@{settings.mongodb_host}:{settings.mongodb_port}"
            client = MongoClient(connection_string)
        else:
            client = MongoClient(settings.mongodb_host, settings.mongodb_port)
        
        job_store = JobStore(client, settings.mongodb_database)
        _job_manager = JobManager(
            job_store=job_store,
            timezone=settings.after_market_scheduler_timezone
        )
    return _job_manager


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    job_manager: JobManager = Depends(get_job_manager)
):
    """List all scheduled jobs."""
    try:
        jobs = job_manager.list_jobs(job_type=job_type, enabled=enabled)
        return JobListResponse(
            jobs=[JobResponse(**job) for job in jobs[skip:skip + limit]],
            total=len(jobs)
        )
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    job_manager: JobManager = Depends(get_job_manager)
):
    """Create a new scheduled job."""
    try:
        job_id = await job_manager.create_job(
            name=job_data.name,
            job_type=job_data.job_type.value,
            cron_expression=job_data.cron_expression,
            config=job_data.config,
            enabled=job_data.enabled,
            max_retries=job_data.max_retries
        )
        
        job = job_manager.get_job(job_id)
        return JobResponse(**job)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
):
    """Get job details by ID."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(**job)


@router.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    job_data: JobUpdate,
    job_manager: JobManager = Depends(get_job_manager)
):
    """Update a scheduled job."""
    try:
        updated = await job_manager.update_job(
            job_id=job_id,
            name=job_data.name,
            cron_expression=job_data.cron_expression,
            config=job_data.config,
            enabled=job_data.enabled
        )
        
        if not updated:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        job = job_manager.get_job(job_id)
        return JobResponse(**job)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
):
    """Delete a scheduled job."""
    try:
        deleted = await job_manager.delete_job(job_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"message": "Job deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/trigger")
async def trigger_job(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
):
    """Trigger a job to run immediately."""
    try:
        execution_id = await job_manager.trigger_job(job_id)
        return {
            "message": "Job triggered successfully",
            "execution_id": execution_id
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to trigger job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/executions", response_model=ExecutionListResponse)
async def get_job_executions(
    job_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Get execution history for a job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        executions = job_manager.get_executions(job_id, limit=limit)
        return ExecutionListResponse(
            executions=[ExecutionResponse(**exec_doc) for exec_doc in executions[skip:skip + limit]],
            total=len(executions)
        )
    except Exception as e:
        logger.error(f"Failed to get executions for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-cron", response_model=CronValidateResponse)
async def validate_cron(request: CronValidateRequest):
    """Validate a cron expression and get human-readable description."""
    valid = CronValidator.validate(request.cron_expression)
    description = CronValidator.describe(request.cron_expression) if valid else "Invalid cron expression"
    
    return CronValidateResponse(
        valid=valid,
        description=description,
        error=None if valid else "Invalid cron expression syntax"
    )


@router.get("/job-types")
async def get_job_types():
    """Get available job types."""
    return {"job_types": JOB_TYPES}
```

---

### Task 5: Update scheduler __init__.py

**Files:**
- Modify: `apps/api/app/scheduler/__init__.py`

- [ ] **Step 1: Update __init__.py exports**
```python
from .job import AfterMarketJob
from .pre_cache_job import PreCacheJob
from .monitor_job import MonitorJob
from .alert_job import AlertOrchestratorJob
from .job_store import JobStore
from .job_manager import JobManager, CronValidator, JOB_TYPES

__all__ = [
    "AfterMarketJob", 
    "PreCacheJob", 
    "MonitorJob", 
    "AlertOrchestratorJob",
    "JobStore",
    "JobManager",
    "CronValidator",
    "JOB_TYPES"
]
```

---

### Task 6: Register Router in main.py

**Files:**
- Modify: `apps/api/main.py`

- [ ] **Step 1: Add scheduler router import and registration**
Add import: `from app.api.endpoints import scheduler`
Add router registration: `app.include_router(scheduler.router, prefix="/api")`

---

## Verification

After implementation, verify:
1. API endpoints work: GET /api/scheduler/jobs
2. Job creation with valid cron
3. Cron validation rejects invalid expressions
4. Execution history is tracked
