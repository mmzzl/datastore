# 策略选股 API 文档

## 概述

策略选股 API 提供基于策略的股票筛选功能，支持内置策略和用户上传的插件策略。

## 基础路径

```
/api/stock-selection
```

## 认证

所有端点需要 JWT 认证，在请求头中添加：

```
Authorization: Bearer <token>
```

## 权限

- `selection:run` - 执行选股任务
- `selection:view` - 查看选股结果和历史

---

## 端点

### 1. 启动选股任务

**POST** `/api/stock-selection/run`

启动一个新的策略选股任务。

#### 请求体

```json
{
  "strategy_type": "ma_cross",
  "strategy_params": {
    "fast_period": 5,
    "slow_period": 20
  },
  "stock_pool": "hs300",
  "plugin_id": null
}
```

#### 参数说明

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `strategy_type` | string | 是 | 策略类型：`ma_cross`、`rsi`、`bollinger`、`macd`、`plugin` |
| `strategy_params` | object | 否 | 策略参数，根据策略类型不同 |
| `stock_pool` | string | 否 | 股票池：`hs300`（默认）、`zz500`、`all` |
| `plugin_id` | string | 否 | 插件ID，使用插件策略时必填 |

#### 策略参数

**MA Cross 策略**
```json
{
  "fast_period": 5,
  "slow_period": 20
}
```

**RSI 策略**
```json
{
  "period": 14,
  "oversold": 30,
  "overbought": 70
}
```

**Bollinger 策略**
```json
{
  "period": 20,
  "num_std": 2
}
```

**MACD 策略**
```json
{
  "fast_period": 12,
  "slow_period": 26,
  "signal_period": 9
}
```

#### 响应

```json
{
  "task_id": "uuid-string",
  "status": "pending",
  "message": "Selection task started successfully"
}
```

#### 错误响应

| 状态码 | 描述 |
|--------|------|
| 400 | 无效的策略类型或股票池 |
| 403 | 缺少 `selection:run` 权限 |

---

### 2. 获取选股结果

**GET** `/api/stock-selection/{task_id}`

获取指定选股任务的详细结果。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `task_id` | string | 选股任务ID |

#### 响应

```json
{
  "id": "uuid-string",
  "task_id": "uuid-string",
  "strategy_type": "ma_cross",
  "stock_pool": "hs300",
  "status": "completed",
  "created_at": "2024-01-01T10:00:00",
  "completed_at": "2024-01-01T10:01:30",
  "total_stocks": 300,
  "selected_count": 8,
  "results": [
    {
      "code": "600519",
      "name": "贵州茅台",
      "score": 85.0,
      "signal_type": "buy",
      "signal_strength": "强",
      "confidence": 0.85,
      "industry": "白酒",
      "indicators": {
        "ma5": 1856.2,
        "ma10": 1832.5,
        "ma20": 1798.8,
        "rsi": 58.2,
        "macd": 12.3,
        "macd_hist": 5.6
      },
      "ai_analysis": {
        "sector": "白酒",
        "sector_features": "白酒板块近期受春节备货预期提振",
        "risk_factors": ["估值偏高", "技术压力位"],
        "operation_suggestion": "回调至1830可轻仓介入，止损1780",
        "brief_analysis": "MACD金叉运行中，均线多头排列"
      }
    }
  ],
  "market_trend": {
    "total_stocks": 300,
    "macd_golden_cross_count": 156,
    "macd_golden_cross_ratio": 52.0,
    "ma_golden_cross_count": 142,
    "ma_golden_cross_ratio": 47.3,
    "full_bullish_alignment_count": 98,
    "full_bullish_alignment_ratio": 32.7,
    "trend_direction": "震荡",
    "trend_strength": "中",
    "rsi_oversold_count": 45,
    "rsi_overbought_count": 45,
    "rsi_neutral_count": 210
  },
  "ai_summary": "本次选股选出8只股票，主要集中在白酒板块",
  "sector_overview": "白酒板块近期表现强势，北向资金持续流入",
  "market_risk": "市场震荡，需关注成交量配合",
  "error": null
}
```

#### 任务状态

| 状态 | 描述 |
|------|------|
| `pending` | 任务等待执行 |
| `running` | 正在执行选股 |
| `analyzing` | 正在进行AI分析 |
| `completed` | 任务完成 |
| `failed` | 任务失败 |

---

### 3. 获取选股历史

**GET** `/api/stock-selection/history`

获取选股历史记录，支持分页和过滤。

#### 查询参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `page` | integer | 1 | 页码 |
| `page_size` | integer | 20 | 每页数量（最大100） |
| `status` | string | - | 按状态过滤 |
| `stock_pool` | string | - | 按股票池过滤 |

#### 响应

```json
{
  "items": [
    {
      "id": "uuid-string",
      "task_id": "uuid-string",
      "strategy_type": "ma_cross",
      "stock_pool": "hs300",
      "created_at": "2024-01-01T10:00:00",
      "selected_count": 8,
      "status": "completed"
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 20
}
```

---

### 4. 获取股票池列表

**GET** `/api/stock-selection/pools`

获取可用的股票池列表。

#### 响应

```json
{
  "pools": [
    {
      "id": "hs300",
      "name": "沪深300",
      "count": 300,
      "description": "沪深两市市值最大的300只股票"
    },
    {
      "id": "zz500",
      "name": "中证500",
      "count": 500,
      "description": "沪深两市中盘代表性500只股票"
    },
    {
      "id": "all",
      "name": "全市场",
      "count": 800,
      "description": "沪深300+中证500 (排除ST)"
    }
  ]
}
```

---

## 数据模型

### StockResultItem

| 字段 | 类型 | 描述 |
|------|------|------|
| `code` | string | 股票代码 |
| `name` | string | 股票名称 |
| `score` | number | 综合评分 (0-100) |
| `signal_type` | string | 信号类型 (buy) |
| `signal_strength` | string | 信号强度 (强/中/弱) |
| `confidence` | number | 策略置信度 (0-1) |
| `industry` | string | 所属行业 |
| `indicators` | object | 技术指标 |
| `ai_analysis` | object | AI分析结果 |

### MarketTrendData

| 字段 | 类型 | 描述 |
|------|------|------|
| `total_stocks` | number | 股票池总数 |
| `macd_golden_cross_count` | number | MACD金叉数量 |
| `macd_golden_cross_ratio` | number | MACD金叉比例 (%) |
| `trend_direction` | string | 趋势方向 (看多/看空/震荡) |
| `trend_strength` | string | 趋势强度 (强/中/弱) |

### AIAnalysis

| 字段 | 类型 | 描述 |
|------|------|------|
| `sector` | string | 所属板块 |
| `sector_features` | string | 板块特征描述 |
| `risk_factors` | array | 风险因素列表 |
| `operation_suggestion` | string | 操作建议 |
| `brief_analysis` | string | 技术面分析 |

---

## 使用示例

### Python 示例

```python
import requests

API_URL = "http://localhost:8000"
TOKEN = "your-jwt-token"

headers = {"Authorization": f"Bearer {TOKEN}"}

# 启动选股任务
response = requests.post(
    f"{API_URL}/api/stock-selection/run",
    headers=headers,
    json={
        "strategy_type": "ma_cross",
        "strategy_params": {"fast_period": 5, "slow_period": 20},
        "stock_pool": "hs300"
    }
)
task_id = response.json()["task_id"]

# 获取结果
result = requests.get(
    f"{API_URL}/api/stock-selection/{task_id}",
    headers=headers
)
print(result.json())
```

### cURL 示例

```bash
# 启动选股
curl -X POST "http://localhost:8000/api/stock-selection/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"strategy_type": "ma_cross", "stock_pool": "hs300"}'

# 获取结果
curl "http://localhost:8000/api/stock-selection/{task_id}" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 错误处理

### 常见错误码

| 状态码 | 错误类型 | 描述 |
|--------|----------|------|
| 400 | Bad Request | 请求参数无效 |
| 401 | Unauthorized | 未认证 |
| 403 | Forbidden | 无权限 |
| 404 | Not Found | 任务不存在 |
| 500 | Internal Error | 服务器错误 |

### 错误响应格式

```json
{
  "detail": "Invalid strategy type: invalid. Valid types: ['ma_cross', 'rsi', 'bollinger', 'macd', 'plugin']"
}
```
