# 盯盘系统增强规格文档

**日期**: 2026-03-22
**版本**: v1.0
**状态**: 已批准

---

## 1. 背景与目标

现有盯盘系统（MarketWatcher + StockMonitor）存在以下不足：
- 仅支持日线级别的技术指标（RSI/MACD/KDJ/布林带）
- 缺少市场广度数据（涨跌家数比、板块轮动、北向资金、VIX）
- 缺少关联资产监控（A50期货、离岸人民币、美元指数）
- 预警机制单一（仅钉钉推送，无优先级/策略分层）
- 无事件驱动（新闻/政策）监控能力
- 无日内高频（分钟K线）盯盘支持

本次重构目标是构建一个**分层预警引擎**，支持日内高频、波段趋势、事件驱动三种策略，覆盖价格/成交量/技术指标/新闻/市场广度五类预警，统一经分级推送机制触达用户。

---

## 2. 架构设计

### 2.1 整体架构

```
MarketWatcher (总调度 / AlertOrchestrator)
├── MarketBreadthWatcher     # 市场广度层
├── CorrelatedAssetWatcher   # 关联资产层
├── StockAlertWatcher        # 个股预警层
├── NewsEventWatcher         # 事件驱动层
├── MinuteKlineWatcher       # 分钟K线层 (新增)
└── AlertAggregator          # 信号聚合器
```

- **MarketBreadthWatcher**: 监控涨跌家数比、板块涨跌幅排名、北向资金实时流向、VIX恐慌指数
- **CorrelatedAssetWatcher**: 监控 A50 期货、离岸人民币汇率（USDCNH）、美元指数（DXY）
- **StockAlertWatcher**: 监控个股的价格预警、量比异动、技术指标突破
- **NewsEventWatcher**: 监控新闻/政策关键词订阅，生成事件驱动信号
- **MinuteKlineWatcher**: 支持 1/5/15/30/60 分钟K线数据，用于日内高频策略
- **AlertAggregator**: 接收所有Watcher信号，按策略类型加权评分，触发预警

### 2.2 分层权重设计

| 策略类型 | 技术指标 | 盘口/量价 | 市场情绪 | 关联资产 | 事件 |
|---------|---------|---------|---------|---------|------|
| 日内高频 | 30% | 25% | 25% | 10% | 10% |
| 波段趋势 | 20% | 15% | 20% | 20% | 25% |
| 事件驱动 | 10% | 10% | 10% | 30% | 40% |

---

## 3. 数据层扩展

### 3.1 DataSourceManager 新增方法

| 方法 | 返回类型 | 说明 |
|------|---------|------|
| `get_market_breadth()` | `Dict[str, Any]` | 涨跌家数比、板块排名、北向资金、VIX |
| `get_correlated_assets()` | `Dict[str, Any]` | A50期货、离岸人民币、美元指数 |
| `get_minute_kline(code, frequency)` | `List[StockKLine]` | 分钟K线，frequency=1/5/15/30/60 |

### 3.2 数据源适配

- **get_market_breadth()**: 优先通过 akshare 适配器实现（`akshare.stock_zh_a_spot_em` + 北向资金接口）
- **get_correlated_assets()**: 通过 akshare 适配器获取期货/汇率数据
- **get_minute_kline()**: 扩展现有 `get_kline` 接口，增加 `frequency` 参数支持

---

## 4. 预警配置模型

### 4.1 AlertRule 配置结构

```python
AlertRule:
  code: str                          # 股票代码
  name: str                          # 股票名称
  alert_type: AlertType              # price | volume | technical | news | breadth
  condition: AlertCondition          # 条件表达式
  strategy_type: StrategyType        # intraday | swing | event | all
  priority: AlertPriority            # low | medium | high | critical
  notification: NotifyConfig         # 推送方式+频率
  enabled: bool                      # 是否启用

AlertType:
  - price: 价格突破/跌破指定价位
  - volume: 量比放大/缩量
  - technical: RSI/MACD/KDJ/布林带突破
  - news: 新闻/公告关键词触发
  - breadth: 市场广度异动

AlertPriority:
  - low: 仅记录日志+仪表盘
  - medium: 钉钉推送+仪表盘
  - high: 钉钉高亮推送+仪表盘高亮
  - critical: 钉钉@所有人+每30s重复确认

StrategyType:
  - intraday: 日内高频（使用分钟K线）
  - swing: 波段趋势（使用日线/60分钟线）
  - event: 事件驱动（新闻+关联资产）
  - all: 所有策略
```

### 4.2 预警条件表达式

```python
AlertCondition:
  operator: str    # > | < | >= | <= | == | cross_up | cross_down | in_range
  value: float     # 阈值
  reference: str   # reference字段名（如 price, rsi, volume_ratio, north_flow）
  period: int       # 指标周期（用于技术指标）
```

---

## 5. 信号聚合与评分

### 5.1 综合评分算法

```
total_score = (
    tech_score * tech_weight +
    volume_score * volume_weight +
    sentiment_score * sentiment_weight +
    correlation_score * correlation_weight +
    event_score * event_weight
)
```

权重由 `strategy_type` 决定（见 2.2 节）。

### 5.2 动作判定

| 条件 | 动作 |
|------|------|
| `total_score > 0.75` 或 `rsi < 25` | buy |
| `total_score < 0.25` 或 `rsi > 75` 或触发止损/止盈 | sell |
| 否则 | hold |

---

## 6. 分级推送机制

### 6.1 推送规则

| 优先级 | 触发场景 | 推送方式 | 频率 |
|--------|---------|---------|------|
| `critical` | 止损触发、止盈触发、板块黑天鹅事件 | 钉钉@所有人 + 仪表盘弹窗 | 每30s重复至用户确认 |
| `high` | buy/sell 信号、量比突放倍量 | 钉钉普通推送 + 仪表盘高亮 | 单次 |
| `medium` | 政策/公告关键词命中、板块轮动信号 | 钉钉 + 仪表盘实时推送 | 单次 |
| `low` | 量比轻微异动、均线收敛交叉 | 仅记录日志 + 仪表盘 | 无推送 |

### 6.2 推送去重

- 同一只股票的同一类型预警，5分钟内不重复推送
- `critical` 级别强制推送（不参与去重）

---

## 7. 文件结构

```
apps/api/app/monitor/
├── __init__.py
├── market_watcher.py          # 重构：AlertOrchestrator 总调度
├── stock_monitor.py           # 重构：移除重复逻辑，统一走 AlertOrchestrator
├── config.py                  # 扩展：AlertRule 配置管理
├── analysis/
│   ├── technical.py           # 扩展：新增分钟K线指标计算
│   ├── signal.py              # 重构：支持策略分层信号生成
│   └── aggregator.py          # 新增：AlertAggregator 信号聚合器
├── watchers/
│   ├── __init__.py            # 新增
│   ├── breadth.py             # 新增：MarketBreadthWatcher
│   ├── correlated.py          # 新增：CorrelatedAssetWatcher
│   ├── stock_alert.py         # 新增：StockAlertWatcher
│   ├── news_event.py          # 新增：NewsEventWatcher
│   └── minute_kline.py        # 新增：MinuteKlineWatcher
├── models/
│   ├── __init__.py
│   ├── alert_rule.py          # 新增：AlertRule 数据模型
│   ├── alert_signal.py        # 新增：AlertSignal 信号模型
│   └── notification.py        # 新增：NotificationConfig 模型
└── notification/
    ├── __init__.py
    ├── dingtalk.py            # 扩展：支持分级推送
    └── dashboard.py           # 新增：仪表盘推送

apps/api/app/data_source/
├── manager.py                 # 扩展：get_market_breadth / get_correlated_assets / get_minute_kline
└── adapters/
    └── akshare_adapter.py     # 扩展：实现市场广度和关联资产数据获取
```

---

## 8. 回退策略

- 如果 akshare 的市场广度/关联资产接口不可用，回退到 `baostock` 或返回默认值
- 如果分钟K线数据不可用，降级为日线数据，并在日志中记录降级原因
- 钉钉推送失败时，仅记录日志，不阻塞主流程

---

## 9. 测试策略

- 单元测试：每个 Watcher 类独立测试，覆盖正常/异常/边界数据
- 集成测试：AlertAggregator 接收多源信号，验证加权评分正确性
- 回测验证：使用 `backtest()` 方法对历史分钟K线数据验证日内高频策略
- 预警配置验证：测试 AlertRule 序列化/反序列化正确性

---

## 10. 下一步

本规格批准后，进入实施计划阶段（writing-plans）。
