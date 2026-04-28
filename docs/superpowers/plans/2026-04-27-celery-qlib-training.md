# Celery Qlib Training System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate Qlib model training from API-process threading to Celery worker with Redis broker + MongoDB backend, adding cancel/rerun/task-list support.

**Architecture:** Celery worker runs as a separate process. API submits tasks via `send_task()`. Worker executes `QlibTrainer._run_training()` in its own process. Progress is written to MongoDB `job_executions` collection by the task itself. Frontend polls a `GET /api/qlib/tasks` endpoint to display task list with progress bars, cancel and rerun buttons.

**Tech Stack:** Celery + Redis (broker) + MongoDB (result backend) + FastAPI + Vue 3

---

### Task 1: Celery App + Config

**Files:**
- Create: `apps/api/app/celery_app.py`
- Modify: `apps/api/app/core/config.py` (add Redis + Celery config fields)
- Modify: `apps/api/requirements.txt` (add celery)
- Modify: `apps/api/config/config.yaml` (add redis section)
- Create: `/etc/systemd/system/celery-worker.service` (deploy file, not in repo)

- [ ] **Step 1: Add Redis config to Settings**

Edit `apps/api/app/core/config.py`. Add after line 91 (`qlib_provider_uri`):

```python
redis_host: str = "localhost"
redis_port: int = 6379
redis_db: int = 0
celery_broker_url: Optional[str] = None  # falls back to redis://redis_host:redis_port/redis_db
celery_result_backend: Optional[str] = None  # falls back to mongodb://...
```

- [ ] **Step 2: Create celery_app.py**

Create `apps/api/app/celery_app.py`:

```python
from celery import Celery
from app.core.config import settings

broker = settings.celery_broker_url or f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
backend = settings.celery_result_backend or (
    f"mongodb://{settings.mongodb_username}:{settings.mongodb_password}"
    f"@{settings.mongodb_host}:{settings.mongodb_port}/{settings.mongodb_database}"
)

celery_app = Celery("qlib_tasks", broker=broker, backend=backend)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
```

- [ ] **Step 3: Add to requirements.txt**

```
celery[mongodb]
```

- [ ] **Step 4: Add Redis config to config.yaml**

Edit `apps/api/config/config.yaml`, add after `qlib:` section:

```yaml
# Redis配置（用于Celery任务队列）
redis:
  host: "localhost"
  port: 6379
  db: 0
```

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/celery_app.py apps/api/app/core/config.py apps/api/requirements.txt apps/api/config/config.yaml
git commit -m "feat: add Celery app and Redis config for async training tasks"
```

---

### Task 2: Celery Training Task

**Files:**
- Create: `apps/api/app/qlib/train_task.py`

- [ ] **Step 1: Create train_task.py**

```python
import logging
import time
from datetime import datetime

from celery import current_task
from pymongo import MongoClient

from app.celery_app import celery_app
from app.qlib.trainer import QlibTrainer
from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_executions_collection():
    client = MongoClient(
        host=settings.mongodb_host,
        port=settings.mongodb_port,
        username=settings.mongodb_username,
        password=settings.mongodb_password,
    )
    return client[settings.mongodb_database]["job_executions"]


@celery_app.task(bind=True, max_retries=0)
def run_training(self, config: dict):
    task_id = self.request.id
    coll = _get_executions_collection()
    coll.update_one(
        {"task_id": task_id},
        {"$set": {
            "task_id": task_id,
            "job_id": "qlib_train",
            "job_type": "qlib_train",
            "status": "running",
            "progress": 0,
            "message": "starting",
            "config": config,
            "created_at": datetime.now(),
            "started_at": datetime.now(),
        }},
        upsert=True,
    )

    trainer = QlibTrainer(
        model_dir=config.get("model_dir", settings.qlib_model_dir),
        min_sharpe_ratio=config.get("min_sharpe_ratio", settings.qlib_min_sharpe_ratio),
    )

    training_config = {
        "instruments": config.get("instruments", "csi300"),
        "start_time": config.get("start_time", "2015-01-01"),
        "end_time": config.get("end_time", datetime.now().strftime("%Y-%m-%d")),
        "model_type": config.get("model_type", "lgbm"),
        "factor_type": config.get("factor_type", "alpha158"),
    }

    internal_task_id = trainer.start_training(training_config)

    try:
        while True:
            status = trainer.get_status(internal_task_id)
            current_status = status.get("status")
            progress = status.get("progress", 0)
            message = status.get("progress_message", "")

            coll.update_one(
                {"task_id": task_id},
                {"$set": {
                    "status": "running",
                    "progress": progress,
                    "message": message,
                    "updated_at": datetime.now(),
                }}
            )
            self.update_state(state="PROGRESS", meta={"progress": progress, "message": message})

            if self.request.id and hasattr(current_task, "request") and current_task.request.id:
                from celery.app.control import Inspect
                i = Inspect()
                revoked = i.revoked()
                if revoked and task_id in revoked:
                    logger.info(f"Task {task_id} revoked by user")
                    coll.update_one(
                        {"task_id": task_id},
                        {"$set": {"status": "revoked", "completed_at": datetime.now(), "message": "Cancelled by user"}}
                    )
                    return {"status": "revoked", "message": "Cancelled by user"}

            if current_status in ("completed", "failed", "cancelled"):
                break

            time.sleep(10)

        if current_status == "completed":
            metrics = status.get("metrics", {})
            model_id = status.get("model_id", "")
            result = {"model_id": model_id, "metrics": metrics, "status": "success"}
            coll.update_one(
                {"task_id": task_id},
                {"$set": {
                    "status": "success",
                    "progress": 100,
                    "result": result,
                    "message": "completed",
                    "completed_at": datetime.now(),
                }}
            )
            return result
        else:
            error = status.get("error", "Unknown error")
            coll.update_one(
                {"task_id": task_id},
                {"$set": {
                    "status": "failed",
                    "error_message": error,
                    "completed_at": datetime.now(),
                }}
            )
            raise RuntimeError(error)

    except Exception as e:
        coll.update_one(
            {"task_id": task_id},
            {"$set": {
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.now(),
            }}
        )
        raise

    finally:
        trainer.close()
```

- [ ] **Step 2: Verify syntax**

```bash
py -3.12 -c "import ast; ast.parse(open('apps/api/app/qlib/train_task.py', encoding='utf-8').read()); print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add apps/api/app/qlib/train_task.py
git commit -m "feat: add Celery task for Qlib model training with progress reporting"
```

---

### Task 3: Update API Endpoints

**Files:**
- Modify: `apps/api/app/api/endpoints/qlib.py`

- [ ] **Step 1: Update start_training to use Celery**

Replace the `@router.post("/train")` handler. The new version:

```python
@router.post("/train", response_model=TrainResponse)
async def start_training(
    request: TrainRequest,
):
    instruments = request.instruments or get_csi300_instruments()
    config = {
        "instruments": instruments,
        "start_time": request.start_time,
        "end_time": request.end_time,
        "model_type": request.model_type,
        "factor_type": request.factor_type,
    }
    try:
        from app.celery_app import celery_app
        task = celery_app.send_task("app.qlib.train_task.run_training", kwargs={"config": config})
        logger.info(f"Training task submitted: {task.id}")
        return TrainResponse(task_id=task.id, status="pending", message="Training task submitted")
    except Exception as e:
        logger.error(f"Failed to submit training task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit training task: {str(e)}")
```

Add import at top of file if not present:
```python
from app.core.config import settings
```

- [ ] **Step 2: Add GET /qlib/tasks endpoint**

Add before or after the training endpoints:

```python
@router.get("/tasks")
async def list_training_tasks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(require_permission("qlib:view")),
):
    try:
        from pymongo import MongoClient
        client = MongoClient(
            host=settings.mongodb_host,
            port=settings.mongodb_port,
            username=settings.mongodb_username,
            password=settings.mongodb_password,
        )
        coll = client[settings.mongodb_database]["job_executions"]
        query = {"job_id": "qlib_train"}
        total = coll.count_documents(query)
        skip = (page - 1) * page_size
        docs = list(coll.find(query).sort("created_at", -1).skip(skip).limit(page_size))
        items = []
        for doc in docs:
            doc["_id"] = str(doc["_id"])
            for f in ("created_at", "updated_at", "completed_at", "started_at"):
                if isinstance(doc.get(f), datetime):
                    doc[f] = doc[f].isoformat()
            items.append(doc)
        client.close()
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    except Exception as e:
        logger.error(f"Failed to list training tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 3: Add POST /qlib/train/{task_id}/revoke endpoint**

```python
@router.post("/train/{task_id}/revoke")
async def revoke_training_task(
    task_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("qlib:manage")),
):
    try:
        from app.celery_app import celery_app
        celery_app.control.revoke(task_id, terminate=True, signal="SIGTERM")
        from pymongo import MongoClient
        client = MongoClient(
            host=settings.mongodb_host,
            port=settings.mongodb_port,
            username=settings.mongodb_username,
            password=settings.mongodb_password,
        )
        coll = client[settings.mongodb_database]["job_executions"]
        coll.update_one(
            {"task_id": task_id},
            {"$set": {"status": "revoked", "message": "Cancelled by user", "completed_at": datetime.now()}}
        )
        client.close()
        logger.info(f"Training task revoked: {task_id}")
        return {"ok": True, "task_id": task_id}
    except Exception as e:
        logger.error(f"Failed to revoke task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 4: Add POST /qlib/train/{task_id}/rerun endpoint**

```python
@router.post("/train/{task_id}/rerun")
async def rerun_training_task(
    task_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("qlib:manage")),
):
    try:
        from pymongo import MongoClient
        client = MongoClient(
            host=settings.mongodb_host,
            port=settings.mongodb_port,
            username=settings.mongodb_username,
            password=settings.mongodb_password,
        )
        coll = client[settings.mongodb_database]["job_executions"]
        doc = coll.find_one({"task_id": task_id})
        client.close()
        if not doc:
            raise HTTPException(status_code=404, detail="Task not found")
        config = doc.get("config", {})
        from app.celery_app import celery_app
        task = celery_app.send_task("app.qlib.train_task.run_training", kwargs={"config": config})
        return {"task_id": task.id, "message": "Training re-submitted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rerun task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

Remove the old `get_training_status` endpoint (`GET /qlib/train/{task_id}`) since training status is now read from the tasks list. Also remove the `trainer` dependency injection for training (no longer needed for the `start_training` endpoint — but keep it if `sync/experiments` etc still use it).

- [ ] **Step 5: Verify syntax**

```bash
py -3.12 -c "import ast; ast.parse(open('apps/api/app/api/endpoints/qlib.py', encoding='utf-8').read()); print('OK')"
```

- [ ] **Step 6: Commit**

```bash
git add apps/api/app/api/endpoints/qlib.py
git commit -m "feat: update training API to use Celery, add tasks list/revoke/rerun endpoints"
```

---

### Task 4: Frontend — API Service

**Files:**
- Modify: `frontend/vue-admin/src/services/api_qlib.ts`

- [ ] **Step 1: Add new API methods and types**

Add after `refreshTopStocks` method:

```typescript
interface TrainingTask {
  task_id: string
  job_id: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'revoked'
  progress: number
  message: string | null
  config: Record<string, any>
  result: Record<string, any> | null
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

interface TrainingTasksResponse {
  items: TrainingTask[]
  total: number
  page: number
  page_size: number
}
```

Add to `apiQlib` object (after `refreshTopStocks`):

```typescript
  async getTrainingTasks(page: number = 1, pageSize: number = 20): Promise<TrainingTasksResponse> {
    const res = await api.get('/qlib/tasks', { params: { page, page_size: pageSize } })
    return res.data
  },

  async revokeTrainingTask(taskId: string): Promise<{ ok: boolean }> {
    const res = await api.post(`/qlib/train/${taskId}/revoke`)
    return res.data
  },

  async rerunTrainingTask(taskId: string): Promise<{ task_id: string }> {
    const res = await api.post(`/qlib/train/${taskId}/rerun`)
    return res.data
  },
```

Add to the export type line:

```typescript
export type { ..., TrainingTask, TrainingTasksResponse }
```

- [ ] **Step 2: Verify build**

```bash
cd frontend/vue-admin && npm run build 2>&1 | Select-String -Pattern "error"
```

- [ ] **Step 3: Commit**

```bash
git add frontend/vue-admin/src/services/api_qlib.ts
git commit -m "feat: add training task list/revoke/rerun API methods to frontend service"
```

---

### Task 5: Frontend — Store

**Files:**
- Modify: `frontend/vue-admin/src/stores/qlib.ts`

- [ ] **Step 1: Add training tasks state and actions**

Add to `state` object:

```typescript
trainingTasks: [] as TrainingTask[],
trainingTasksTotal: 0,
```

Add to imports:
```typescript
import { ..., type TrainingTask, type TrainingTasksResponse } from '../services/api_qlib'
```

Add new actions:

```typescript
async function fetchTrainingTasks(page: number = 1, pageSize: number = 20) {
  state.loading = true
  state.error = null
  try {
    const res = await apiQlib.getTrainingTasks(page, pageSize)
    state.trainingTasks = res.items
    state.trainingTasksTotal = res.total
  } catch (e: any) {
    state.error = e.response?.data?.detail || '获取训练任务列表失败'
  } finally {
    state.loading = false
  }
}

async function revokeTask(taskId: string) {
  try {
    await apiQlib.revokeTrainingTask(taskId)
    await fetchTrainingTasks()
  } catch (e: any) {
    state.error = e.response?.data?.detail || '取消任务失败'
  }
}

async function rerunTask(taskId: string) {
  try {
    await apiQlib.rerunTrainingTask(taskId)
    await fetchTrainingTasks()
  } catch (e: any) {
    state.error = e.response?.data?.detail || '重跑任务失败'
  }
}
```

Add to the return statement: `fetchTrainingTasks`, `revokeTask`, `rerunTask`

- [ ] **Step 2: Verify build**

```bash
cd frontend/vue-admin && npm run build 2>&1 | Select-String -Pattern "error"
```

- [ ] **Step 3: Commit**

```bash
git add frontend/vue-admin/src/stores/qlib.ts
git commit -m "feat: add training task list/revoke/rerun actions to qlib store"
```

---

### Task 6: Frontend — UI Component

**Files:**
- Modify: `frontend/vue-admin/src/views/qlib/QlibTopStocks.vue`

- [ ] **Step 1: Rewrite the component**

Replace the entire file with the new version that shows a training task list instead of the old polling-based progress.

Key changes:
- `onMounted` fetches tasks list and top stocks
- `onActivated` refreshes task list
- `setInterval` every 15s to refresh task list (stored in Pinia, not local ref)
- `handleTrainNow()` calls `apiQlib.startTraining()` then refreshes tasks
- `handleRevoke(taskId)` calls store `revokeTask`
- `handleRerun(taskId)` calls store `rerunTask`
- Task list table with columns: Time, Status (tag), Progress (NProgress), Actions (cancel/rerun buttons), Result
- Remove old `activeTaskId`/`activeProgress`/`activeStatus` from store refs in template (now reads from `trainingTasks`)
- Keep top stocks display unchanged below the task list

Full implementation:

```vue
<script setup lang="ts">
import { ref, onMounted, onActivated, onUnmounted, h } from 'vue'
import { useQlibStore } from '../../stores/qlib'
import { apiQlib } from '../../services/api_qlib'
import { NDataTable, NDatePicker, NButton, NTag, NEmpty, NSpin, NSpace, NAlert, NDivider, NProgress } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import type { TopStockItem, TrainingTask } from '../../services/api_qlib'

const store = useQlibStore()
const showHistory = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  const today = new Date().toISOString().split('T')[0]
  await store.fetchTopStocks(today, today)
  await store.fetchTrainingTasks()
  if (store.state.trainingTasks.some(t => t.status === 'running' || t.status === 'pending')) {
    showHistory.value = true
  }
  pollTimer = setInterval(() => store.fetchTrainingTasks(), 15000)
})

onActivated(async () => {
  await store.fetchTrainingTasks()
  if (!pollTimer) {
    pollTimer = setInterval(() => store.fetchTrainingTasks(), 15000)
  }
})

onUnmounted(() => {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
})

function formatDate(ts: number): string {
  return new Date(ts).toISOString().split('T')[0]
}

async function handleDateRangeChange(value: [number, number] | null) {
  if (value) {
    const start = formatDate(value[0])
    const end = formatDate(value[1])
    await store.fetchTopStocks(start, end)
  }
}

async function handleRefresh() {
  await store.refreshTopStocks()
}

async function handleTrainNow() {
  await apiQlib.startTraining({ model_type: 'lgbm' })
  showHistory.value = true
  await store.fetchTrainingTasks()
}

async function handleRevoke(taskId: string) {
  await store.revokeTask(taskId)
}

async function handleRerun(taskId: string) {
  await store.rerunTask(taskId)
}

const taskColumns: DataTableColumns<TrainingTask> = [
  { title: '时间', key: 'created_at', width: 150,
    render: (row) => row.created_at ? new Date(row.created_at).toLocaleString('zh-CN') : '-',
  },
  { title: '状态', key: 'status', width: 80,
    render: (row) => {
      const map: Record<string, [string, string]> = {
        pending: ['等待', 'default'],
        running: ['运行中', 'info'],
        success: ['完成', 'success'],
        failed: ['失败', 'error'],
        revoked: ['已取消', 'warning'],
      }
      const [label, type] = map[row.status] || [row.status, 'default']
      return h(NTag, { type, size: 'small' }, () => label)
    },
  },
  { title: '进度', key: 'progress', width: 150,
    render: (row) => {
      if (row.status === 'success') return h(NProgress, { type: 'success', percentage: 100, height: 16, :indicator-placement="'inside'" })
      if (row.status === 'failed' || row.status === 'revoked') return '-'
      return h(NProgress, { percentage: row.progress || 0, height: 16, :indicator-placement="'inside'" })
    },
  },
  { title: '消息', key: 'message', ellipsis: { tooltip: true },
    render: (row) => row.message || row.error_message || '-',
  },
  { title: '操作', key: 'actions', width: 120,
    render: (row) => {
      const btns = []
      if (row.status === 'running' || row.status === 'pending') {
        btns.push(h(NButton, { size: 'tiny', type: 'warning', onClick: () => handleRevoke(row.task_id) }, () => '取消'))
      }
      if (row.status === 'success' || row.status === 'failed' || row.status === 'revoked') {
        btns.push(h(NButton, { size: 'tiny', type: 'primary', onClick: () => handleRerun(row.task_id) }, () => '重跑'))
      }
      return h(NSpace, { size: 'small' }, () => btns)
    },
  },
  { title: '结果', key: 'result', ellipsis: { tooltip: true }, width: 150,
    render: (row) => {
      if (row.error_message) return row.error_message
      if (row.result) {
        const sr = row.result.metrics?.sharpe_ratio
        return sr ? `Sharpe: ${sr.toFixed(3)}` : `模型: ${row.result.model_id || ''}`
      }
      return '-'
    },
  },
]

const topColumns: DataTableColumns<TopStockItem> = [
  { title: '排名', key: 'rank', width: 60 },
  { title: '代码', key: 'code', width: 120 },
  { title: '名称', key: 'name', render: (row) => row.name || row.code },
  { title: '评分', key: 'score', width: 100, render: (row) => row.score.toFixed(4) },
]
</script>

<template>
  <div class="top-stocks">
    <NSpace class="filter-bar" align="center">
      <NDatePicker type="daterange" clearable @update:value="handleDateRangeChange" style="width: 280px" />
      <NButton type="primary" :loading="store.state.refreshingTopStocks" @click="handleRefresh">刷新今日推荐</NButton>
      <NButton type="warning" @click="handleTrainNow">开始训练</NButton>
      <NButton size="small" quaternary @click="showHistory = !showHistory">
        {{ showHistory ? '隐藏训练记录' : '训练记录' }}
      </NButton>
    </NSpace>

    <div v-if="showHistory" style="margin-bottom: 16px">
      <NDivider>训练任务</NDivider>
      <NDataTable
        v-if="store.state.trainingTasks.length > 0"
        :columns="taskColumns"
        :data="store.state.trainingTasks"
        :bordered="false"
        size="small"
        :max-height="300"
        :scroll-x="800"
      />
      <NEmpty v-else description="暂无训练任务" />
    </div>

    <NAlert v-if="store.state.error" type="error" style="margin-bottom: 12px" closable>{{ store.state.error }}</NAlert>
    <NSpin :show="store.state.loading">
      <div v-if="store.state.topStocks.length > 0">
        <div v-for="day in store.state.topStocks" :key="day.date" style="margin-bottom: 20px">
          <NTag type="info" style="margin-bottom: 8px">{{ day.date }} | 模型: {{ day.model_id }} | {{ day.model_type }} | {{ day.factor }}</NTag>
          <NDataTable :columns="topColumns" :data="day.stocks" :bordered="false" size="small" striped :row-key="(row: TopStockItem) => row.code" />
        </div>
      </div>
      <NEmpty v-else-if="!store.state.loading" description="暂无推荐数据，点击刷新按钮生成" />
    </NSpin>
  </div>
</template>

<style scoped>
.top-stocks { padding: 0; }
.filter-bar { margin-bottom: 16px; }
</style>
```

- [ ] **Step 2: Verify build**

```bash
cd frontend/vue-admin && npm run build 2>&1 | Select-String -Pattern "error"
```

- [ ] **Step 3: Commit**

```bash
git add frontend/vue-admin/src/views/qlib/QlibTopStocks.vue
git commit -m "feat: rewrite training UI with task list table, cancel/rerun buttons, auto-poll every 15s"
```

---

### Task 7: systemd Service File

**Files:**
- Create: `deploy/celery-worker.service` (for reference, not auto-deployed)

- [ ] **Step 1: Create service file**

Create `deploy/celery-worker.service`:

```
[Unit]
Description=Celery Worker for Qlib Training
After=network.target redis-server.service

[Service]
Type=simple
User=fantom
WorkingDirectory=/home/fantom/datastore/apps/api
ExecStart=/home/fantom/.pyenv/versions/3.12.0/bin/celery -A app.celery_app worker --loglevel=info --concurrency=1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 2: Commit**

```bash
git add deploy/celery-worker.service
git commit -m "docs: add Celery worker systemd service file for deployment"
```

---

### Task 8: Integration Verification

- [ ] **Step 1: Verify all AST checks pass**

```bash
py -3.12 -c "import ast; ast.parse(open('apps/api/app/celery_app.py', encoding='utf-8').read()); print('celery_app OK')"
py -3.12 -c "import ast; ast.parse(open('apps/api/app/qlib/train_task.py', encoding='utf-8').read()); print('train_task OK')"
py -3.12 -c "import ast; ast.parse(open('apps/api/app/api/endpoints/qlib.py', encoding='utf-8').read()); print('qlib.py OK')"
```

- [ ] **Step 2: Verify frontend build**

```bash
cd frontend/vue-admin && npm run build 2>&1 | Select-String -Pattern "error"
```

- [ ] **Step 3: Clean up old training progress state from store**

In `frontend/vue-admin/src/stores/qlib.ts`, remove `activeTaskId`, `activeProgress`, `activeStatus` from state since they are no longer used by the new component. Also remove unused `startTraining` and `checkTrainingStatus` store actions (the component calls `apiQlib.startTraining` directly now).

```bash
git add frontend/vue-admin/src/stores/qlib.ts
git commit -m "refactor: remove old activeTaskId/activeProgress store state, no longer needed"
```

- [ ] **Step 4: Final commit with summary**

```bash
git log --oneline --count HEAD...$(git rev-list --max-parents=0 HEAD) 2>/dev/null || echo "check commits manually"
```
