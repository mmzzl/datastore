# AGENTS.md

This document provides guidelines for agentic coding agents working in this codebase.

## Project Overview

This is a quantitative trading system with:
- **Backend**: FastAPI (Python 3.12) with MongoDB storage
- **Frontend**: Vue 3 + Vite + TypeScript + Naive UI
- **Data Sources**: Akshare, Baostock, TDX for stock data
- **ML Integration**: Qlib for model training and stock selection

## Build/Lint/Test Commands

### Backend (FastAPI)

```bash
# Install dependencies (use py -3.12 for Python 3.12)
py -3.12 -m pip install -r apps/api/requirements.txt

# Run development server
py -3.12 -m uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

# Run scheduler standalone
py -3.12 apps/api/scheduler_standalone.py

# Run specific Python script
py -3.12 apps/api/stock_kline_scraper.py
```

### Frontend (Vue)

```bash
# Install dependencies
cd frontend/vue-admin
npm install

# Run development server (proxies to localhost:8000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Running Tests

Currently, the project doesn't have a formal test suite. When adding tests:
- Backend: Use pytest, place tests in `apps/api/tests/`
- Frontend: Use Vitest, place tests alongside components with `.spec.ts` extension

## Project Structure

```
D:\datastore\
├── apps/api/                    # FastAPI backend
│   ├── main.py                  # Application entry point
│   ├── scheduler_standalone.py  # Background scheduler
│   ├── app/
│   │   ├── api/endpoints/       # API route handlers
│   │   ├── core/                # Config, security, error handling
│   │   ├── storage/             # MongoDB client and models
│   │   ├── data_source/         # Data adapters (akshare, baostock, mongodb)
│   │   ├── monitor/             # Stock monitoring logic
│   │   ├── collector/           # Data collection utilities
│   │   ├── notify/              # DingTalk notifications
│   │   ├── qlib/                # Qlib ML integration
│   │   └── schemas/             # Pydantic schemas
│   └── config/config.yaml       # Configuration file
│
├── frontend/vue-admin/          # Vue 3 frontend
│   └── src/
│       ├── views/               # Page components
│       ├── components/          # Reusable components
│       ├── stores/              # Pinia state management
│       ├── services/            # API services
│       └── router/              # Vue Router config
│
└── openspec/changes/            # OpenSpec change proposals
```

## Code Style Guidelines

### Python Backend

**Imports**: Group imports in this order:
1. Standard library (alphabetical)
2. Third-party packages (alphabetical)
3. Local imports (use relative imports within app)

```python
# Good
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends

from .config import Settings
from app.storage import MongoStorage
```

**Type Hints**: Always use type hints for function parameters and return types.

```python
# Good
def get_holdings(user_id: str, page: int = 1) -> Dict[str, Any]:
    ...

# Bad
def get_holdings(user_id, page=1):
    ...
```

**Naming Conventions**:
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: prefix with `_`

**Error Handling**: Use HTTPException for API errors with proper status codes.

```python
from fastapi import HTTPException

# Good
if not holding:
    raise HTTPException(status_code=404, detail="Holding not found")

# Use logging for errors
logger.error(f"Failed to fetch holdings: {e}")
```

**Logging**: Use Python's logging module, not print statements.

```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Processing request for user {user_id}")
logger.error(f"Failed to connect: {e}")
```

**Configuration**: Access settings from `app.core.config.settings`.

```python
from app.core.config import settings

mongodb_host = settings.mongodb_host
```

**MongoDB**: Use the MongoStorage class from `app.storage`.

```python
from app.storage import MongoStorage

storage = MongoStorage(
    host=settings.mongodb_host,
    port=settings.mongodb_port,
    db_name=settings.mongodb_database,
)
storage.connect()
```

**Async**: Use async/await for I/O operations in API endpoints.

```python
@router.get("/holdings/{user_id}")
async def get_holdings(user_id: str):
    return await storage.get_holdings(user_id)
```

### TypeScript Frontend

**Imports**: Group imports: Vue first, then third-party, then local.

```typescript
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { authService } from '../services/api'
```

**Type Definitions**: Define interfaces for all data structures.

```typescript
interface Holding {
  code: string
  name?: string
  quantity: number
  average_cost: number
}
```

**Stores**: Use Pinia with composition API.

```typescript
export const useHoldingsStore = defineStore('holdings', () => {
  const state = reactive({
    holdings: [] as Holding[],
    loading: false,
    error: null as string | null,
  })

  async function fetchHoldings(userId: string) {
    state.loading = true
    try {
      const res = await apiHoldings.getHoldings(userId)
      state.holdings = res.items
    } catch (e: any) {
      state.error = e.response?.data?.detail
    } finally {
      state.loading = false
    }
  }

  return { state, fetchHoldings }
})
```

**API Calls**: Use the axios instance from `services/api.ts` with auth handling.

**Components**: Use Vue 3 composition API with `<script setup lang="ts">`.

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'

const props = defineProps<{ title: string }>()
const count = ref(0)

onMounted(() => {
  console.log('mounted')
})
</script>

<template>
  <div>{{ props.title }}: {{ count }}</div>
</template>

<style scoped>
/* scoped styles here */
</style>
```

## Important Notes

### Authentication

- JWT tokens stored in localStorage as `auth_token`
- Include `Authorization: Bearer <token>` header in requests
- Middleware handles authentication in `app/api/middleware/auth.py`

### Data Flow

1. Data fetched from Akshare/Baostock APIs
2. Stored in MongoDB via adapters
3. Processed by monitor/collector modules
4. Exposed via FastAPI endpoints
5. Consumed by Vue frontend

### Qlib Integration

- Qlib models stored in `./models/` directory
- Model metadata in MongoDB `qlib_models` collection
- Use `py -3.12` for all Qlib-related scripts
- CSI 300 stock list in `app/qlib/config.py`

### Commit Guidelines

- Write clear commit messages describing the change
- Reference related issues if applicable
- Don't commit sensitive data (API keys, passwords)
- Use conventional commits format: `feat:`, `fix:`, `docs:`, etc.

### Common Pitfalls

1. **Pandas compatibility**: Use `app.core.pandas_compat` patch for pandas 3.0+
2. **Python version**: Always use `py -3.12` command
3. **MongoDB connection**: Always close connections after use
4. **CORS**: Already configured to allow all origins in development
5. **Async**: Don't mix sync and async operations in same endpoint

#### 测试用例指导原则
 
**禁止为通过测试而采取以下行为**：
- **简化业务逻辑**：为测试通过而简化或跳过真实业务逻辑
- **伪造测试数据**：使用不符合真实场景的模拟数据
- **篡改业务代码**：为适配测试而修改业务代码的正常流程
- **跳过流程步骤**：跳过必要的验证、权限检查、错误处理等步骤

**正确的测试做法**：
- 保持业务代码逻辑完整，使用 Mock 技术隔离外部依赖
- 测试数据应尽可能模拟真实场景
- 测试用例应验证业务代码的真实行为，包括边界条件和错误处理

#### 修复问题原则

- **先理解，后修复**：
- 修复前先认真查阅相关方法、类、结构体定义及设计文档，理解问题的根本原因，分析问题并提出解决方案，与用户确认
- 修复代码要遵循语法规范、日志规范、设计模式等
- 修复后测试用例防止回归，并记录原因和方案
- 永远不要猜测，不要擅自选择方案或路线，务必暂停运行让用户确认与澄清

#### 性能硬约束
- 必须使用二进制格式存储数据（npy / bin / parquet）
- 禁止重复解析 CSV，必须做缓存
- 向量化计算优先，禁止逐行循环
- 回测必须使用预加载数据
- 内存占用 < 8GB
- 速度要求：1天回测 < 2 秒
