from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging

from app.core.config import settings
from app.scheduler.job_store import JobStore
from app.scheduler.job_manager import JobManager, CronValidator, JOB_TYPES
from app.scheduler import qlib_train_handler, risk_report_handler
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
        _register_handlers(_job_manager)
    return _job_manager


def _register_handlers(job_manager: JobManager):
    """Register job type handlers."""
    job_manager.register_handler("qlib_train", qlib_train_handler)
    job_manager.register_handler("risk_report", risk_report_handler)
    logger.info("Registered qlib_train and risk_report handlers")


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
        jobs, total = await job_manager.list_jobs(job_type=job_type, enabled=enabled, skip=skip, limit=limit)
        return JobListResponse(
            items=[JobResponse(**job) for job in jobs],
            total=total
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

        job = await job_manager.get_job(job_id)
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
    job = await job_manager.get_job(job_id)
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

        job = await job_manager.get_job(job_id)
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
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        executions, total = await job_manager.get_executions(job_id, skip=skip, limit=limit)
        return ExecutionListResponse(
            executions=[ExecutionResponse(**exec_doc) for exec_doc in executions],
            total=total
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


async def register_default_jobs(job_manager: JobManager):
    """Register default scheduled jobs if they don't exist."""
    default_jobs = [
        {
            "name": "Qlib模型训练",
            "job_type": "qlib_train",
            "cron_expression": "0 2 * * 0",
            "config": {
                "model_type": "lgbm",
                "instruments": "csi300",
                "factor_type": "alpha158",
            },
            "enabled": True,
        },
        {
            "name": "风险报告生成",
            "job_type": "risk_report",
            "cron_expression": "30 15 * * 1-5",
            "config": {},
            "enabled": True,
        },
    ]

    jobs, total = await job_manager.list_jobs()

    for default_job in default_jobs:
        existing = any(
            j.get("job_type") == default_job["job_type"]
            for j in jobs
        )
        if not existing:
            try:
                await job_manager.create_job(
                    name=default_job["name"],
                    job_type=default_job["job_type"],
                    cron_expression=default_job["cron_expression"],
                    config=default_job["config"],
                    enabled=default_job["enabled"],
                )
                logger.info(f"Created default job: {default_job['name']}")
            except Exception as e:
                logger.warning(f"Failed to create default job {default_job['name']}: {e}")
