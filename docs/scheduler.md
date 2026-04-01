# Scheduler Documentation

This document describes the job scheduling system for automated tasks.

## Overview

The scheduler system enables automated execution of recurring tasks such as:
- Model training
- Risk report generation
- Data collection
- System maintenance

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    JobManager                         │   │
│  │  ├── Job Registry                                     │   │
│  │  ├── Scheduler (APScheduler)                         │   │
│  │  └── Execution History                                │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
│  ┌──────────────────────┼──────────────────────────────┐   │
│  │               Job Handlers                           │   │
│  │  ├── qlib_train_handler                             │   │
│  │  ├── risk_report_handler                            │   │
│  │  └── (custom handlers)                              │   │
│  └──────────────────────┴──────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  JobStore (MongoDB)                   │   │
│  │  ├── scheduler_jobs (job definitions)                │   │
│  │  └── scheduler_executions (execution history)        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Job Types

### Available Job Types

| Type | Description | Default Schedule |
|------|-------------|------------------|
| `qlib_train` | Train Qlib ML model | Sunday 2:00 AM |
| `risk_report` | Generate risk analysis report | Weekdays 3:30 PM |

### Job Configuration

Each job has the following attributes:

```typescript
interface JobConfig {
  id: string              // Unique identifier
  name: string            // Display name
  job_type: string        // Job type identifier
  cron_expression: string // Cron schedule
  config: object          // Job-specific config
  enabled: boolean        // Active status
  max_retries: number     // Retry attempts
  last_run: datetime      // Last execution time
  next_run: datetime      // Scheduled next run
}
```

---

## Cron Expressions

### Format

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday = 0)
│ │ │ │ │
* * * * *
```

### Examples

| Expression | Description |
|------------|-------------|
| `0 9 * * 1-5` | Every weekday at 9:00 AM |
| `30 15 * * 1-5` | Every weekday at 3:30 PM |
| `0 2 * * 0` | Every Sunday at 2:00 AM |
| `0 0 1 * *` | First day of month at midnight |
| `*/15 * * * *` | Every 15 minutes |
| `0 9-17 * * 1-5` | Every hour 9 AM - 5 PM on weekdays |
| `0 9 * * 1,3,5` | Mon, Wed, Fri at 9:00 AM |

### Special Characters

| Character | Meaning | Example |
|-----------|---------|---------|
| `*` | Any value | `* * * * *` = every minute |
| `,` | Value list | `1,3,5` = Mon, Wed, Fri |
| `-` | Range | `1-5` = Mon through Fri |
| `/` | Step | `*/15` = every 15 units |
| `?` | No specific value | For day fields |

---

## Timezone Handling

### Configuration

```yaml
# config.yaml
after_market:
  scheduler_timezone: "Asia/Shanghai"
```

### Default Timezone

The system uses `Asia/Shanghai` (UTC+8) as the default timezone.

### Important Notes

1. **Daylight Saving Time**: Cron jobs handle DST automatically
2. **UTC Storage**: Times are stored in UTC internally
3. **Display**: Times displayed in configured timezone

### Converting Timezones

```python
from datetime import datetime
import pytz

# Local time to UTC
local_tz = pytz.timezone("Asia/Shanghai")
local_time = local_tz.localize(datetime(2024, 1, 1, 9, 0))
utc_time = local_time.astimezone(pytz.UTC)

# UTC to local
utc_time = datetime.utcnow()
local_time = utc_time.replace(tzinfo=pytz.UTC).astimezone(local_tz)
```

---

## Error Handling and Retries

### Retry Mechanism

```python
# Job configuration
{
    "max_retries": 3,  # Maximum retry attempts
    "retry_delay": 60  # Seconds between retries (optional)
}
```

### Execution States

| State | Description |
|-------|-------------|
| `pending` | Job waiting to run |
| `running` | Currently executing |
| `success` | Completed successfully |
| `failed` | Failed after retries |
| `cancelled` | Manually cancelled |

### Error Logging

```python
# Execution record
{
    "id": "exec_123",
    "job_id": "job_456",
    "status": "failed",
    "started_at": "2024-01-01T09:00:00",
    "completed_at": "2024-01-01T09:01:30",
    "duration": 90000,  # milliseconds
    "error": "ConnectionError: Failed to connect to MongoDB",
    "retry_count": 3
}
```

### Handling Specific Errors

```python
# Job handler example
async def qlib_train_handler(job: Dict[str, Any]) -> Dict[str, Any]:
    try:
        config = job.get("config", {})
        
        # Validate config
        if not config.get("model_type"):
            raise ValueError("model_type is required")
        
        # Execute training
        result = await train_model(config)
        return {"model_id": result.model_id}
        
    except ValueError as e:
        # Configuration error - no retry
        raise JobError(str(e), retry=False)
        
    except ConnectionError as e:
        # Transient error - retry
        raise JobError(str(e), retry=True)
```

---

## API Endpoints

### List Jobs

```http
GET /api/scheduler/jobs?job_type=qlib_train&enabled=true&skip=0&limit=100
Authorization: Bearer <token>
```

**Response**:
```json
{
    "jobs": [
        {
            "id": "job_123",
            "name": "Qlib Model Training",
            "job_type": "qlib_train",
            "cron_expression": "0 2 * * 0",
            "config": {"model_type": "lgbm"},
            "enabled": true,
            "max_retries": 3,
            "last_run": "2024-01-01T02:00:00",
            "next_run": "2024-01-08T02:00:00"
        }
    ],
    "total": 1
}
```

### Create Job

```http
POST /api/scheduler/jobs
Content-Type: application/json
Authorization: Bearer <token>

{
    "name": "Daily Risk Report",
    "job_type": "risk_report",
    "cron_expression": "30 15 * * 1-5",
    "config": {},
    "enabled": true,
    "max_retries": 3
}
```

### Update Job

```http
PUT /api/scheduler/jobs/{job_id}
Content-Type: application/json
Authorization: Bearer <token>

{
    "name": "Updated Risk Report",
    "cron_expression": "0 16 * * 1-5",
    "enabled": true
}
```

### Delete Job

```http
DELETE /api/scheduler/jobs/{job_id}
Authorization: Bearer <token>
```

### Trigger Job Immediately

```http
POST /api/scheduler/jobs/{job_id}/trigger
Authorization: Bearer <token>
```

**Response**:
```json
{
    "message": "Job triggered successfully",
    "execution_id": "exec_123"
}
```

### Get Execution History

```http
GET /api/scheduler/jobs/{job_id}/executions?skip=0&limit=50
Authorization: Bearer <token>
```

**Response**:
```json
{
    "executions": [
        {
            "id": "exec_123",
            "job_id": "job_456",
            "status": "success",
            "started_at": "2024-01-01T09:00:00",
            "completed_at": "2024-01-01T09:05:00",
            "duration": 300000,
            "result": {"model_id": "model_123"}
        }
    ],
    "total": 50
}
```

### Validate Cron Expression

```http
POST /api/scheduler/validate-cron
Content-Type: application/json

{
    "cron_expression": "0 9 * * 1-5"
}
```

**Response**:
```json
{
    "valid": true,
    "description": "每天 9:00 (周一至周五)",
    "error": null
}
```

---

## Creating Custom Jobs

### 1. Define Handler

```python
# app/scheduler/custom_job.py

async def custom_data_collect_handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for data collection job.
    
    Args:
        job: Job configuration dictionary
    
    Returns:
        Result dictionary (will be stored in execution record)
    
    Raises:
        JobError: If job fails
    """
    config = job.get("config", {})
    
    # Your custom logic here
    data_source = config.get("data_source", "baostock")
    stocks = config.get("stocks", [])
    
    try:
        result = await collect_data(data_source, stocks)
        return {
            "collected_stocks": len(stocks),
            "records": result.count
        }
    except Exception as e:
        raise JobError(f"Collection failed: {e}", retry=True)
```

### 2. Register Handler

```python
# app/api/endpoints/scheduler.py

def _register_handlers(job_manager: JobManager):
    job_manager.register_handler("qlib_train", qlib_train_handler)
    job_manager.register_handler("risk_report", risk_report_handler)
    job_manager.register_handler("data_collect", custom_data_collect_handler)  # Add
```

### 3. Add Job Type

```python
# app/scheduler/job_manager.py

JOB_TYPES = {
    "qlib_train": "Qlib模型训练",
    "risk_report": "风险报告生成",
    "data_collect": "数据采集",  # Add
}
```

### 4. Create Job via API

```bash
curl -X POST http://localhost:8000/api/scheduler/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "name": "Daily Data Collection",
    "job_type": "data_collect",
    "cron_expression": "0 8 * * 1-5",
    "config": {
      "data_source": "baostock",
      "stocks": ["csi300"]
    },
    "enabled": true
  }'
```

---

## Default Jobs

The system registers these default jobs on startup:

### Qlib Model Training

```python
{
    "name": "Qlib模型训练",
    "job_type": "qlib_train",
    "cron_expression": "0 2 * * 0",  # Sunday 2 AM
    "config": {
        "model_type": "lgbm",
        "instruments": "csi300",
        "factor_type": "alpha158",
    },
    "enabled": True,
}
```

### Risk Report Generation

```python
{
    "name": "风险报告生成",
    "job_type": "risk_report",
    "cron_expression": "30 15 * * 1-5",  # Weekdays 3:30 PM
    "config": {},
    "enabled": True,
}
```

---

## Monitoring

### Health Check

```python
# Check scheduler status
GET /api/scheduler/health

# Response
{
    "status": "running",
    "jobs_count": 5,
    "active_jobs": 1,
    "last_execution": "2024-01-01T15:30:00"
}
```

### Execution Metrics

```python
# Track job performance
{
    "job_type": "qlib_train",
    "avg_duration": 1800000,  # 30 minutes
    "success_rate": 0.95,
    "last_success": "2024-01-01T02:30:00",
    "last_failure": "2023-12-25T02:00:00"
}
```

---

## Best Practices

1. **Cron Schedule**: Use appropriate intervals (avoid every minute)
2. **Error Handling**: Implement proper retry logic
3. **Idempotency**: Jobs should be safe to re-run
4. **Logging**: Log job execution details
5. **Monitoring**: Track job health and performance
6. **Time Zones**: Be aware of timezone differences
7. **Resource Limits**: Consider system resources for concurrent jobs
