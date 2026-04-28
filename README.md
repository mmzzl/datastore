# Datastore

量化交易系统，提供行情数据采集、技术指标分析、信号监控、Qlib 机器学习选股、风险报告生成和组合管理功能。

## 架构

```
┌─────────────────────────────────────────────────────┐
│                     Frontend                         │
│              Vue 3 + Naive UI + Vite                │
├─────────────────────────────────────────────────────┤
│                     Backend API                      │
│              FastAPI + MongoDB + Celery              │
├────────────┬────────────┬────────────┬──────────────┤
│ 行情数据    │ 策略信号    │ ML 选股    │ 风险报告     │
│ Akshare    │ 新闻事件    │ Qlib       │ VaR/ES/β    │
│ Baostock   │ 技术指标    │ LightGBM   │ 压力测试     │
│ TDX        │ 盘口监控    │ Alpha158   │ 相关性分析   │
└────────────┴────────────┴────────────┴──────────────┘
```

## 功能

| 模块 | 说明 |
|------|------|
| **行情数据** | A 股日/周/月 K 线、5 分钟 K 线、实时行情，多数据源（Akshare / Baostock / TDX） |
| **持仓管理** | 多账户持仓、交易记录、已实现盈亏计算（加权平均成本法） |
| **组合分析** | 市值、盈亏、收益率、持仓分布 |
| **信号监控** | 新闻关键词匹配、技术指标信号、自定义监控规则，支持钉钉推送 |
| **去重过滤** | 24 小时去重窗口、退市关键词过滤、每日每只股票仅推送一次 |
| **Qlib 选股** | LightGBM/MLP 模型训练（Alpha158/360 因子），CSI300/500 股票池，回测评估，异步 Celery Worker |
| **风险报告** | VaR(95%/99%)、Expected Shortfall、波动率、最大回撤、夏普比率、Beta、相关性矩阵、压力测试（-10%/-20%/-30% 市场冲击、行业冲击、流动性危机） |
| **数据看板** | Dashboard 首页展示持仓概况、最新信号、关键指标 |
| **调度任务** | APScheduler + Celery 混合调度，支持定时任务、立即执行、执行历史查看 |
| **用户管理** | JWT 认证、角色权限、多用户隔离 |

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- MongoDB
- Redis（Celery 任务队列，可选）

### 启动后端

```bash
cd apps/api
pip install -r requirements.txt

# 开发模式
py -3.12 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Celery Worker（Qlib 训练用）
celery -A app.celery_app worker --loglevel=info --pool=solo --concurrency=1
```

### 启动前端

```bash
cd frontend/vue-admin
npm install
npm run dev
```

### 数据采集

```bash
# 采集日 K 线
py -3.12 apps/api/stock_kline_scraper.py

# 启动独立调度器（数据同步 + 信号监控 + 风险报告）
py -3.12 apps/api/scheduler_standalone.py

# Qlib 训练 + 回测（独立脚本）
py -3.12 apps/api/scripts/train_eval.py --model lgbm --factor alpha158 --instruments csi300
```

## 配置

编辑 `apps/api/config/config.yaml`：

```yaml
mongodb:
  host: "localhost"
  port: 27017
  database: "eastmoney_news"

redis:
  host: "localhost"
  port: 6379
```

## 项目结构

```
apps/api/                     # FastAPI 后端
├── main.py                   # 应用入口
├── app/
│   ├── api/endpoints/        # API 路由
│   ├── core/                 # 配置、认证
│   ├── storage/              # MongoDB 客户端
│   ├── data_source/          # 数据适配器
│   ├── monitor/              # 信号监控
│   ├── notify/               # 钉钉通知
│   ├── qlib/                 # Qlib ML 引擎
│   ├── risk/                 # 风险报告
│   └── scheduler/            # 调度任务
├── scheduler_standalone.py   # 独立调度器
├── config/config.yaml        # 配置文件
└── scripts/train_eval.py     # 训练回测脚本

frontend/vue-admin/           # Vue 3 前端
├── src/
│   ├── views/                # 页面组件
│   ├── stores/               # Pinia 状态
│   ├── services/             # API 服务
│   └── router/               # 路由配置
```

## 许可证

MIT
