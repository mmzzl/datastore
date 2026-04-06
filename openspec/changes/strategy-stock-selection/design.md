## Context

系统已有完善的策略回测框架和插件系统：
- `StrategyFactory` 支持创建内置策略（ma_cross, rsi, bollinger, macd）和插件策略
- `PluginRegistry` 管理用户上传的策略插件
- `AsyncBacktestEngine` 提供异步回测能力
- `LLMClient` 提供AI分析能力（使用DeepSeek API）
- 股票数据通过 `MongoStorage` 存储，支持K线查询

股票池数据已就绪：
- `hs300_stocks.csv` - 沪深300成分股（约300只）
- `zz500_stocks.csv` - 中证500成分股（约500只）
- `stock_industry.csv` - 证监会行业分类数据

选股功能需要：
1. 复用现有策略系统，而非重新实现
2. 对股票池中每只股票计算策略信号
3. 筛选出买入信号强的股票
4. 调用AI进行深度分析

## Goals / Non-Goals

**Goals:**
- 实现策略选股引擎，复用 `StrategyFactory` 和 `BaseStrategy`
- 支持三种股票池：沪深300、中证500、全市场
- 计算每只股票的评分、信号强度、技术指标
- 实现市场趋势判断（基于金叉比例、多头排列比例）
- AI分析输出：板块特征、风险提示、操作建议
- 选股历史保存到MongoDB，支持分页查询
- 前端提供选股弹窗、结果展示、历史记录页面

**Non-Goals:**
- 不实现实时选股推送（本次仅支持手动触发）
- 不实现选股结果的一键回测（回测功能独立使用）
- 不修改现有策略系统代码
- 不替换Qlib选股功能（两者并存）

## Decisions

### 1. 选股架构：独立服务 vs 扩展回测引擎

**Decision:** 创建独立的 `StockSelectionEngine`，不扩展 `AsyncBacktestEngine`

**Rationale:**
- 选股和回测是不同的业务场景：选股是"筛选"，回测是"验证"
- 选股需要计算全股票池的技术指标用于市场趋势分析，回测不需要
- 选股结果需要AI分析后处理，回测不需要
- 独立服务更易于维护和扩展

**Alternatives Considered:**
- 扩展回测引擎添加"selection mode"：增加复杂度，耦合两个业务场景

### 2. 技术指标计算：引擎内部计算 vs 策略输出

**Decision:** 选股引擎统一计算技术指标，不依赖策略输出

**Rationale:**
- 不同策略输出的指标不同（MA Cross输出MA，RSI输出RSI）
- 市场趋势分析需要统一的指标集（MA5/10/20、RSI、MACD）
- 前端展示需要一致的指标格式
- 避免每个策略都需要实现完整的技术指标计算

**Implementation:**
```python
class StockSelectionEngine:
    def _calculate_indicators(self, df: pd.DataFrame) -> StockIndicator:
        # 统一计算 MA, RSI, MACD, Bollinger Bands
        ...
```

### 3. AI分析触发时机：同步 vs 异步

**Decision:** AI分析在选股完成后同步执行，作为选股任务的最后一步

**Rationale:**
- 选股结果数量有限（通常少于20只），AI分析耗时可控（约5-10秒）
- 用户体验更好：一次请求完成所有处理
- 避免前端轮询或WebSocket复杂度

**Alternatives Considered:**
- 异步AI分析 + WebSocket推送：增加复杂度，对选股场景收益不大

### 4. 股票池加载：内存缓存 vs 每次查询

**Decision:** 启动时加载CSV到内存缓存，设置1小时TTL

**Rationale:**
- 成分股变化频率低（每季度调整），缓存命中率高
- 内存占用小（300+500条记录）
- 避免每次选股都读取文件

**Implementation:**
```python
class StockPoolService:
    _cache: Dict[str, List[str]] = {}
    _cache_time: Dict[str, float] = {}
    CACHE_TTL = 3600  # 1 hour
```

### 5. 行业数据查询：预加载 vs 按需查询

**Decision:** 选股时预加载行业映射表（code -> industry）

**Rationale:**
- AI分析需要知道所有选出股票的行业
- 行业数据约5000条，内存占用可接受
- 避免为每只股票单独查询

### 6. 市场趋势判断算法

**Decision:** 基于金叉比例和多头排列比例的加权判断

**Algorithm:**
```
MACD金叉比例 = MACD金叉股票数 / 股票池总数
均线金叉比例 = MA5 > MA10 的股票数 / 股票池总数
完整多头排列比例 = MA5 > MA10 > MA20 的股票数 / 股票池总数

趋势判断逻辑：
- MACD金叉 > 60% 且 多头排列 > 50% → 强势看多
- MACD金叉 40%-60% 且 多头排列 30%-50% → 震荡偏强
- MACD金叉 < 40% 或 多头排列 < 30% → 弱势震荡或看空
```

**Rationale:**
- 简单直观，易于解释
- 基于广泛使用的技术指标
- 可通过AI分析进一步解释

### 7. 前端架构：新页面 vs 弹窗

**Decision:** 主页面 + 选股弹窗模式

**Implementation:**
- `StockSelectionView.vue` - 选股主页面，展示结果和历史
- `StockSelectionDialog.vue` - 选股配置弹窗（策略、股票池、参数）
- `StockResultCard.vue` - 可展开的股票结果卡片

## Risks / Trade-offs

### Risk 1: 全市场选股性能
- **Risk:** 全市场5000+只股票，每只获取K线并计算指标，可能耗时较长
- **Mitigation:**
  - 限制全市场选股的股票池（排除ST、退市股）
  - 前端显示进度条
  - 后端使用异步处理，支持取消

### Risk 2: AI分析成本
- **Risk:** 每次选股调用LLM API，产生费用
- **Mitigation:**
  - 选股结果数量有限（通常少于20只）
  - 使用DeepSeek等成本较低的API
  - 可配置是否启用AI分析

### Risk 3: 成分股数据时效性
- **Risk:** CSV文件中的成分股可能过时
- **Mitigation:**
  - 设置缓存TTL，定期刷新
  - 后续支持从东方财富API更新成分股

### Risk 4: 策略信号单一
- **Risk:** 当前 `Signal` 只有 BUY/SELL/HOLD 三种，无法表达强度
- **Mitigation:**
  - 使用 `confidence` 字段作为评分基础
  - 结合技术指标调整评分

## Migration Plan

### Phase 1: 后端核心功能
1. 创建 `stock_selection/` 模块
2. 实现 `StockSelectionEngine`
3. 实现 `StockPoolService`
4. 实现 `AIAnalyzer`
5. 创建API端点

### Phase 2: 前端界面
1. 创建选股页面和组件
2. 实现选股弹窗
3. 实现结果展示（含AI分析）
4. 实现历史记录查询

### Phase 3: 集成测试
1. 权限配置
2. 端到端测试
3. 性能优化

### Rollback
- 后端：删除 `stock_selection/` 模块和API端点
- 前端：删除选股页面和路由
- 数据库：删除 `stock_selections` collection

## Open Questions

1. **成分股更新机制：** 是否需要在系统中提供成分股更新功能，还是手动更新CSV？
   - **Current Decision:** 手动更新CSV，后续可扩展API更新

2. **AI分析可配置：** 是否需要允许用户选择是否启用AI分析？
   - **Current Decision:** 默认启用，可在配置中关闭

3. **选股结果导出：** 是否需要支持导出选股结果？
   - **Current Decision:** 本次不实现，后续可扩展
