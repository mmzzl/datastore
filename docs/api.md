# API Documentation

This document provides comprehensive API documentation for the quantitative trading system.

## Overview

The system provides RESTful APIs built with FastAPI, automatically generating OpenAPI/Swagger documentation at `/docs`.

**Base URL**: `http://localhost:8000`

## Authentication

### Login

```http
POST /api/auth/token
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Use the token in subsequent requests:
```http
Authorization: Bearer <access_token>
```

---

## Qlib Module APIs

### Start Model Training

```http
POST /api/qlib/train
Content-Type: application/json
Authorization: Bearer <token>

{
  "instruments": ["SH600000", "SH600519"],
  "start_time": "2015-01-01",
  "end_time": "2026-01-01",
  "model_type": "lgbm",
  "factor_type": "alpha158"
}
```

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| instruments | string[] | No | Stock codes (defaults to CSI 300) |
| start_time | string | No | Start date (default: "2015-01-01") |
| end_time | string | No | End date (default: "2026-01-01") |
| model_type | string | No | Model type: "lgbm", "mlp" (default: "lgbm") |
| factor_type | string | No | Factor type: "alpha158", "alpha360" (default: "alpha158") |

**Response**:
```json
{
  "task_id": "train_20240101_120000_abc12345",
  "status": "pending",
  "message": "Training task started successfully"
}
```

### Get Training Status

```http
GET /api/qlib/train/{task_id}
Authorization: Bearer <token>
```

**Response**:
```json
{
  "task_id": "train_20240101_120000_abc12345",
  "status": "completed",
  "progress": 100,
  "started_at": "2024-01-01T12:00:00",
  "completed_at": "2024-01-01T12:30:00",
  "model_id": "model_20240101_123000",
  "metrics": {
    "sharpe_ratio": 2.15,
    "ic": 0.05,
    "num_predictions": 5000
  }
}
```

### List Models

```http
GET /api/qlib/models?limit=50&skip=0&status=approved
Authorization: Bearer <token>
```

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | int | 50 | Max results |
| skip | int | 0 | Results to skip |
| status | string | - | Filter by status: "approved", "rejected", "pending" |

**Response**:
```json
[
  {
    "model_id": "model_20240101_123000",
    "version": 1,
    "created_at": "2024-01-01T12:30:00",
    "status": "approved",
    "metrics": {
      "sharpe_ratio": 2.15,
      "ic": 0.05
    },
    "config": {
      "model_type": "lgbm",
      "factor_type": "alpha158"
    }
  }
]
```

### Run Stock Selection

```http
POST /api/qlib/select
Content-Type: application/json
Authorization: Bearer <token>

{
  "model_id": "model_20240101_123000",
  "date": "2024-01-15",
  "topk": 50
}
```

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| model_id | string | No | Model ID (uses latest approved if omitted) |
| date | string | No | Selection date (uses latest if omitted) |
| topk | int | No | Number of stocks (1-300, default: 50) |

**Response**:
```json
{
  "model_id": "model_20240101_123000",
  "date": "2024-01-15",
  "results": [
    {"rank": 1, "code": "SH600000", "name": "浦发银行", "score": 0.8521},
    {"rank": 2, "code": "SH600519", "name": "贵州茅台", "score": 0.8234}
  ],
  "generated_at": "2024-01-15T09:30:00"
}
```

### Get CSI 300 List

```http
GET /api/qlib/instruments/csi300
Authorization: Bearer <token>
```

**Response**:
```json
{
  "instruments": ["SH600000", "SH600519", ...],
  "count": 300
}
```

---

## Backtest APIs

### Run Backtest

```http
POST /run
Content-Type: application/json
Authorization: Bearer <token>

{
  "strategy": "ma_cross",
  "params": {
    "fast_period": 5,
    "slow_period": 20
  },
  "start_date": "2023-01-01",
  "end_date": "2024-01-01",
  "initial_capital": 100000,
  "instruments": ["SH600000", "SH600519"]
}
```

**Supported Strategies**:
| Strategy | Parameters |
|----------|------------|
| `ma_cross` | `fast_period`, `slow_period` |
| `rsi` | `period`, `oversold`, `overbought` |
| `bollinger` | `period`, `num_std` |
| `macd` | `fast_period`, `slow_period`, `signal_period` |
| `qlib_model` | `model_id`, `topk` |

**Response**:
```json
{
  "task_id": "bt_20240101_120000",
  "status": "pending",
  "message": "Backtest task started successfully"
}
```

### WebSocket Progress Stream

Connect to receive real-time progress:
```
ws://localhost:8000/ws/backtest/{task_id}
```

**Message Types**:
```json
// Connected
{"type": "connected", "task_id": "bt_20240101_120000"}

// Progress update
{"type": "progress", "percent": 50, "message": "Processing day 125/250"}

// Completed
{"type": "completed", "metrics": {"total_return": 0.15, "sharpe_ratio": 1.8}}

// Error
{"type": "error", "message": "Invalid date range"}
```

### Get Backtest Results

```http
GET /results?page=1&page_size=20
Authorization: Bearer <token>
```

**Response**:
```json
{
  "items": [
    {
      "task_id": "bt_20240101_120000",
      "strategy": "ma_cross",
      "date_range": "2023-01-01 ~ 2024-01-01",
      "key_metrics": {
        "total_return": 0.15,
        "annual_return": 0.18,
        "sharpe_ratio": 1.8,
        "max_drawdown": 0.08,
        "win_rate": 0.55,
        "total_trades": 24
      }
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

---

## Scheduler APIs

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
      "name": "Qlib模型训练",
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

**Job Types**:
| Type | Description |
|------|-------------|
| `qlib_train` | Train Qlib model |
| `risk_report` | Generate risk report |

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

## DingTalk Configuration APIs

### Create Configuration

```http
POST /api/dingtalk/
Content-Type: application/json
Authorization: Bearer <token>

{
  "user_id": "user_123",
  "name": "Trading Alerts",
  "webhook": "https://oapi.dingtalk.com/robot/msg?access_token=xxx",
  "secret": "SECxxx"
}
```

### List Configurations

```http
GET /api/dingtalk/{user_id}
Authorization: Bearer <token>
```

### Test Notification

```http
POST /api/dingtalk/test/{config_id}
Content-Type: application/json

{
  "message": "Test notification from trading system"
}
```

---

## Error Responses

All endpoints follow standard error format:

```json
{
  "detail": "Error description"
}
```

**Common HTTP Status Codes**:
| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing token |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 500 | Internal Server Error |

---

## OpenAPI Documentation

Access interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
