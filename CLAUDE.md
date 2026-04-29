# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A 股量化交易系统 — FastAPI + MongoDB 后端，Vue 3 + Naive UI 前端。功能包括行情数据采集、持仓管理、信号监控、Qlib ML 选股、回测、风险报告。

## 常用命令

### 后端 (Python 3.12)

```bash
# 安装依赖
py -3.12 -m pip install -r apps/api/requirements.txt

# 开发服务器
py -3.12 -m uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

# Celery Worker（Qlib 训练用，需 Redis）
celery -A app.celery_app worker --loglevel=info --pool=solo --concurrency=1

# 独立调度器
py -3.12 apps/api/scheduler_standalone.py

# 数据采集
py -3.12 apps/api/stock_kline_scraper.py

# Qlib 训练 + 回测
py -3.12 apps/api/scripts/train_eval.py
py -3.12 apps/api/scripts/train_eval.py --model lgbm --factor alpha158 --instruments csi300
py -3.12 apps/api/scripts/train_eval.py --model lgbm --target-sharpe 2.0

# 运行测试
py -3.12 -m pytest apps/api/tests/ -v
py -3.12 -m pytest apps/api/tests/test_file.py::TestClass::test_method -v
```

### 前端 (Vue 3 + Vite)

```bash
cd frontend/vue-admin
npm install
npm run dev          # 开发服务器 (port 3000, 代理 /api -> localhost:8000)
npm run build         # 生产构建
npm run test          # Vitest
npm run test:coverage # 覆盖率
```

### Docker

```bash
docker-compose up -d    # 启动 MongoDB + API + 前端
```

## 架构

```
Vue 3 SPA (Vite, port 3000)
    │  HTTP proxy /api -> localhost:8000
    ▼
FastAPI (port 8000)
    ├── MongoDB          # 主数据存储
    ├── Redis            # Celery 消息队列
    ├── Akshare/Baostock # A 股行情数据源
    ├── DeepSeek LLM     # AI 分析
    └── DingTalk         # 消息推送
```

### 后端模块 (apps/api/app/)

| 模块 | 职责 |
|------|------|
| `core/` | 配置 (pydantic-settings)、JWT 认证、RBAC 权限 |
| `storage/` | MongoDB 客户端 (MongoStorage) 和数据模型 |
| `api/endpoints/` | REST API 路由处理 |
| `qlib/` | Qlib ML 引擎：训练、预测、数据转换、模型管理 |
| `backtest/` | 回测引擎、策略插件、WebSocket 进度推送 |
| `monitor/` | 实时监控：信号、看板宽度、Brain 多维分析 |
| `stock_selection/` | 策略选股引擎 + AI 分析器 |
| `data_source/` | 统一数据源接口，适配 baostock/akshare/TDX |
| `risk/` | VaR/ES/Beta、压力测试、相关性分析 |
| `scheduler/` | APScheduler 任务调度，MongoDB 持久化 |
| `collector/` | 数据采集、LLM 客户端、技术指标 |
| `notify/` | 钉钉通知（带去重过滤） |

### 前端结构 (frontend/vue-admin/src/)

- `views/` — 页面组件 (15 个路由)
- `stores/` — Pinia stores (Composition API, `defineStore` + `setup`)
- `services/` — Axios API 服务模块 + WebSocket 管理器
- `router/` — Vue Router，`beforeEach` 鉴权守卫
- `components/` — 共享组件 (ChartCard, StockResultCard, StockSelectionDialog)

## 关键约定

### Python

- 始终使用 `py -3.12`，不要用 `python` 或 `python3`
- 配置通过 `app.core.config.settings` 访问，从 `config/config.yaml` 加载
- MongoDB 操作使用 `MongoStorage` 类，不要直接操作 pymongo
- 错误处理使用 `HTTPException`，日志使用 `logging` 模块
- API 端点中 I/O 操作使用 async/await
- imports 顺序：标准库 → 第三方 → 本地（模块内用相对导入）
- pandas 3.0+ 兼容：需要时使用 `app.core.pandas_compat` 补丁

### TypeScript / Vue

- 所有组件使用 `<script setup lang="ts">`
- Stores 使用 Pinia Composition API 模式：`reactive()` 状态 + 普通函数 action
- API 调用统一使用 `services/api.ts` 的 Axios 实例（自动附带 Bearer token）
- UI 组件库：Naive UI；图表：ECharts via vue-echarts

### 认证

- 双 token 系统：配置文件超级用户 (SHA1) + 数据库用户 (bcrypt)
- JWT (HS256)，前端存 localStorage (`auth_token`)
- RBAC 四角色：superuser、admin、trader、viewer
- 权限格式：`resource:action`，支持通配符

### 数据库

- 仅 MongoDB，无 SQL 迁移
- 索引通过代码创建（`MongoStorage._create_*_indexes()`）
- 启动时自动初始化默认角色和管理员账号

## 常见坑

1. **Python 版本**：项目使用 Windows，必须用 `py -3.12`，不用 `python`
2. **异步混用**：不要在同一个端点中混合 sync 和 async 操作
3. **Qlib 数据格式**：使用二进制格式 (bin/npy)，禁止重复解析 CSV
4. **回测性能**：1 天回测 < 2 秒，内存 < 8GB
5. **APScheduler vs Celery**：APScheduler 跟随 API 进程，Celery 用于重型 ML 任务
6. **CORS**：开发环境允许所有来源，生产环境需检查

## 测试原则

- 不为通过测试而简化业务逻辑或伪造数据
- 业务代码保持完整，使用 Mock 隔离外部依赖
- 测试应验证真实行为，包括边界条件和错误处理

## 修复问题原则

- 先理解后修复：查阅相关方法、类、结构体定义，分析根本原因
- 修复前与用户确认方案，不要擅自选择路线
- 修复后添加测试用例防止回归

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)
