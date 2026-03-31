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
