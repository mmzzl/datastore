# Celery Qlib Training System Design

## Scope

Only Qlib model training. All other background jobs (APScheduler) remain unchanged.

## Architecture

```
Server
├── uvicorn (API)
│   ├── POST /api/qlib/train              → celery_app.send_task()
│   ├── POST /api/qlib/train/{id}/revoke  → celery_app.control.revoke()
│   ├── POST /api/qlib/train/{id}/rerun   → celery_app.send_task()
│   └── GET  /api/qlib/tasks              → MongoDB job_executions
│
├── celery worker (独立进程)
│   └── QlibTrainer._run_training() 在线程中执行
│
├── Redis (broker)
└── MongoDB (result backend + 任务记录)
```

## Files

| Layer | File | Purpose |
|-------|------|---------|
| Celery app | `apps/api/app/celery_app.py` | Celery instance, points to Redis broker + MongoDB backend |
| Task def | `apps/api/app/qlib/train_task.py` | The actual training Celery task |
| API | `apps/api/app/api/endpoints/qlib.py` | Add tasks, revoke, rerun endpoints |
| Frontend | `QlibTopStocks.vue` + `qlib store` | Task list table with progress, cancel, rerun buttons |
| Deploy | server systemd service | `celery-worker.service` |

## Celery Task Flow

```
1. POST /api/qlib/train
   → celery_app.send_task('app.qlib.train_task.run_training', kwargs={config})
   → 写入 job_executions {task_id, status: "pending", progress: 0}
   → 返回 {task_id}

2. Worker 接收任务
   → QlibTrainer.start_training(config)
   → 轮询每10秒:
      trainer.get_status(task_id) → {progress, status, message}
      → 更新 job_executions.progress
      → 更新 job_executions.status

3. 训练完成/失败
   → 更新 job_executions {status: "success"/"failed", result, completed_at}
```

## API Endpoints

| Method | Path | Returns | Purpose |
|--------|------|---------|---------|
| GET | `/api/qlib/tasks` | `{items: TaskItem[], total}` | List all training tasks sorted by time |
| POST | `/api/qlib/train/{task_id}/revoke` | `{ok: true}` | Cancel running task |
| POST | `/api/qlib/train/{task_id}/rerun` | `{task_id}` | Re-run with same config |

TaskItem:
```python
{
    "task_id": str,
    "status": "pending" | "running" | "success" | "failed" | "revoked",
    "progress": int,
    "message": str | None,
    "config": dict,
    "result": dict | None,
    "error": str | None,
    "created_at": datetime,
    "completed_at": datetime | None,
}
```

## Frontend

QlibTopStocks.vue top section changes:

```
┌──────────────────────────────────────────────┐
│ [刷新今日推荐] [开始训练] [训练记录 ▼]        │
├──────────────────────────────────────────────┤
│ 训练任务列表                                  │
│ ┌──────┬──────┬────────┬──────┬───────────┐  │
│ │ 时间  │ 状态 │ 进度   │ 操作  │ 结果      │  │
│ ├──────┼──────┼────────┼──────┼───────────┤  │
│ │ 12:30│ ▶运行│ 45%███ │[取消]│           │  │
│ │ 12:00│ ✓完成│ 100%   │[重跑]│ sharpe:2.1│  │
│ │ 11:00│ ✗失败│ --     │[重跑]│ error msg │  │
│ └──────┴──────┴────────┴──────┴───────────┘  │
└──────────────────────────────────────────────┘
```

- 训练任务列表 = celery task history from MongoDB
- 进度条 = NProgress + 百分比
- 取消按钮 = 仅 running 状态显示
- 重跑按钮 = 仅 success/failed 状态显示
- 取消后定时器停止轮询，页面刷新重新查

## Systemd Service

File: `/etc/systemd/system/celery-worker.service`

```
[Unit]
Description=Celery Worker for Qlib Training
After=redis-server.service

[Service]
Type=simple
User=fantom
WorkingDirectory=/home/fantom/datastore/apps/api
ExecStart=/home/fantom/.pyenv/versions/3.12.0/bin/celery -A app.celery_app worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Dependencies

Add to `requirements.txt`:
- celery
- redis (for celery, not a direct project dependency)
