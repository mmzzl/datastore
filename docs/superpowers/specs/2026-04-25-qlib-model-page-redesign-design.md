# Qlib 模型页面重构设计

## 目标

重构 Qlib 模型页面，增加三个核心功能：
1. 展示训练历史记录和评分（从 MongoDB experiments 集合读取）
2. 展示最优模型信息（按 backtest Sharpe 选取）
3. 展示最优模型选出的 Top10 股票推荐（每日自动更新，支持日期范围筛选）

## 页面布局

三个 Tab 切换：

### Tab 1: 训练历史

- 精简列表，NDataTable 分页
- 列：实验ID、模型名、参数摘要、IC、Rank IC、ICIR、Sharpe、状态（pending/completed/failed）、创建时间
- 支持勾选多个实验 → 点击「对比」按钮 → 抽屉中并排展示指标
- 支持按 tag、status 过滤

### Tab 2: 最优模型

- 自动选择 `backtest_result.sharpe_ratio` 最高的实验对应的模型
- 卡片展示：
  - 模型基本信息：model_id、模型类型(lgbm/mlp)、因子配置(alpha158/alpha360)、版本
  - 训练指标：IC、Rank IC、ICIR、预测数量
  - 回测指标：Sharpe Ratio、长期收益率、最大回撤
  - 训练时间、实验ID
- 提供「手动选择」下拉框，可切换为其他实验的模型

### Tab 3: Top10 推荐

- 日期范围选择器（默认当天）
- NDataTable 展示：排名、代码、名称、评分、日期
- 日期范围内每天一组结果，按日期倒序排列
- 「刷新」按钮手动触发重新预测
- 显示预测模型信息（model_id + 预测日期）

## 后端 API

### 新增端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/qlib/experiments` | GET | 分页查询训练历史，支持 `tag`、`status`、`page`、`page_size` 参数 |
| `/qlib/experiments/compare` | GET | 多实验对比，参数 `ids=a,b,c`，返回并排指标 |
| `/qlib/best-model` | GET | 返回 Sharpe 最高的实验及模型信息 |
| `/qlib/top-stocks` | GET | 查询 Top10 股票推荐，支持 `start_date`、`end_date` 参数，默认当天 |
| `/qlib/top-stocks/refresh` | POST | 手动触发：用最优模型预测当天 Top10 并写入 MongoDB |

### 已有端点（无需改动）

- `GET /qlib/models` — 模型列表
- `POST /qlib/select` — 手动股票筛选（保留，与 Top10 独立）

## MongoDB 集合

### 已有：`experiments`

ExperimentTracker 已写入，文档结构：
```json
{
  "experiment_id": "exp_20260425_lgbm_alpha158",
  "tag": "weekly_training",
  "config": { "model_type": "lgbm", "factor": "alpha158", ... },
  "training_metrics": { "ic": 0.05, "rank_ic": 0.06, "icir": 0.8, ... },
  "backtest_result": { "sharpe_ratio": 1.5, "long_short_return": 0.08, ... },
  "model_id": "lgbm_alpha158_20260425",
  "status": "completed",
  "created_at": "2026-04-25T10:00:00",
  "error": null
}
```

### 新增：`qlib_top_stocks`

每日 Top10 股票推荐缓存：
```json
{
  "date": "2026-04-25",
  "model_id": "lgbm_alpha158_20260425",
  "model_type": "lgbm",
  "factor": "alpha158",
  "stocks": [
    { "rank": 1, "code": "SH600000", "name": "浦发银行", "score": 0.85 },
    { "rank": 2, "code": "SH600016", "name": "民生银行", "score": 0.82 },
    ...
  ],
  "created_at": "2026-04-25T15:30:00"
}
```

索引：`{ "date": -1 }`、`{ "model_id": 1, "date": -1 }`

## 定时任务

### `QlibTopStocksJob`

- 每个交易日收盘后（15:30）自动运行
- 流程：
  1. 从 experiments 集合查找 Sharpe 最高的已完成实验
  2. 加载对应模型
  3. 用 `QlibPredictor.predict()` 预测当天 Top10
  4. 写入 `qlib_top_stocks` 集合
  5. 预测失败时发送 DingTalk 通知

## 数据流

```
训练脚本 (train_eval.py)
  → ExperimentTracker.record_experiment()
  → MongoDB experiments 集合

GET /qlib/experiments → 前端训练历史 Tab
GET /qlib/best-model  → 前端最优模型 Tab

QlibTopStocksJob (定时 15:30) 或 POST /qlib/top-stocks/refresh (手动)
  → ExperimentTracker.get_best("backtest_result.sharpe_ratio")
  → QlibPredictor.predict(best_model_id, instruments, today, topk=10)
  → MongoDB qlib_top_stocks 集合

GET /qlib/top-stocks?start_date=&end_date= → 前端 Top10 推荐 Tab
```

## 前端改动

### 新增/修改文件

| 文件 | 改动 |
|------|------|
| `QlibSelectView.vue` | 重构为 3 个 Tab：训练历史、最优模型、Top10推荐 |
| `api_qlib.ts` | 新增 5 个 API 调用方法 + TypeScript 接口定义 |
| `qlib.ts` (store) | 新增 experiments、bestModel、topStocks 状态和 actions |

### 组件拆分

- `QlibSelectView.vue` — 主页面，Tab 容器
- `QlibTrainHistory.vue` — 训练历史表格 + 对比抽屉
- `QlibBestModel.vue` — 最优模型卡片 + 手动选择
- `QlibTopStocks.vue` — 日期筛选 + Top10 表格 + 刷新按钮

## 错误处理

- 无训练记录时：训练历史 Tab 显示空状态提示「暂无训练记录，请先运行训练」
- 无最优模型时：最优模型/Top10 Tab 显示「暂无已完成的训练实验」
- 定时任务失败：DingTalk 通知 + 记录日志，不阻塞其他任务
- 手动刷新重复点击：loading 状态防抖
