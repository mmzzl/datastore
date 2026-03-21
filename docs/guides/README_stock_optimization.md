# MongoDB股票技术指标计算优化方案

## 问题背景
在MongoDB中存储股票全市场历史数据，计算MA、RSI等技术指标时需要几十天的历史数据，一次性返回数据量较大，影响性能。

## 解决方案

### 方案1: 优化查询（推荐用于实时查询）
**特点**: 只查询必要字段，使用索引，限制返回数量

**优势**:
- 减少数据传输量
- 利用索引加速查询
- 实现简单，立即可用

**适用场景**: 实时查询，数据量不是特别大

**实现代码**:
```javascript
const data = await db.collection('stocks')
    .find({ symbol: 'AAPL' })
    .project({ date: 1, close: 1, high: 1, low: 1 }) // 只查需要的字段
    .sort({ date: -1 })
    .limit(100) // 只取需要的天数
    .toArray();
```

### 方案2: 聚合管道计算（推荐用于复杂计算）
**特点**: 在数据库层面完成部分计算，减少数据传输

**优势**:
- 减少网络传输
- 利用MongoDB的计算能力
- 可以预先过滤和聚合数据

**适用场景**: 需要批量计算多个指标

### 方案3: 预计算并存储指标（强烈推荐）
**特点**: 定时预计算所有技术指标，存储在专门集合中

**优势**:
- 查询速度极快
- 减少实时计算压力
- 支持复杂的指标计算
- 便于历史数据分析

**适用场景**: 指标计算频繁，对性能要求高

**实现步骤**:
1. 创建专门的指标集合 `stock_indicators`
2. 定时任务预计算所有股票的MA、RSI等指标
3. 查询时直接从指标集合读取

**数据结构**:
```javascript
{
    symbol: "AAPL",
    date: ISODate("2024-01-15"),
    close: 150.25,
    ma5: 148.50,
    ma10: 147.20,
    ma20: 145.80,
    rsi14: 65.3,
    updatedAt: ISODate("2024-01-16T02:00:00Z")
}
```

### 方案4: 时间序列集合（MongoDB 5.0+）
**特点**: 使用MongoDB原生时间序列功能

**优势**:
- 自动压缩数据
- 优化时间范围查询
- 减少存储空间

**适用场景**: 大量时间序列数据，MongoDB版本>=5.0

## 性能对比

| 方案 | 查询速度 | 存储空间 | 实现难度 | 实时性 | 推荐指数 |
|------|---------|---------|---------|--------|---------|
| 方案1 | 中 | 低 | 简单 | 高 | ⭐⭐⭐⭐ |
| 方案2 | 中高 | 低 | 中等 | 高 | ⭐⭐⭐⭐ |
| 方案3 | 极快 | 中 | 中等 | 中 | ⭐⭐⭐⭐⭐ |
| 方案4 | 快 | 低 | 简单 | 高 | ⭐⭐⭐⭐ |

## 推荐实施策略

### 阶段1: 立即实施（方案1 + 索引优化）
```javascript
// 创建索引
db.collection('stocks').createIndex({ symbol: 1, date: -1 });

// 优化查询
const data = await db.collection('stocks')
    .find({ symbol: 'AAPL' })
    .project({ date: 1, close: 1, high: 1, low: 1 })
    .sort({ date: -1 })
    .limit(requiredDays)
    .toArray();
```

### 阶段2: 中期优化（方案3预计算）
```javascript
// 定时任务（每天收盘后执行）
async function dailyIndicatorUpdate() {
    const symbols = await db.collection('stocks').distinct('symbol');
    for (const symbol of symbols) {
        await preCalculateAndStoreIndicators(symbol);
    }
}
```

### 阶段3: 长期优化（方案4时间序列）
如果MongoDB版本>=5.0，迁移到时间序列集合

## 使用方法

### 安装依赖
```bash
npm install mongodb
```

### 基本使用
```javascript
const StockIndicatorOptimizer = require('./mongodb_stock_optimization');

const optimizer = new StockIndicatorOptimizer(
    'mongodb://localhost:27017',
    'stock_database'
);

await optimizer.connect();

// 创建索引
await optimizer.createIndexes();

// 预计算所有股票指标
await optimizer.batchPreCalculateAllStocks();

// 查询预计算的指标
const indicators = await optimizer.getPreCalculatedIndicators('AAPL', 100);

await optimizer.disconnect();
```

## 索引优化建议

### 必须创建的索引
```javascript
// 主查询索引
db.collection('stocks').createIndex({ symbol: 1, date: -1 });

// 指标集合索引
db.collection('stock_indicators').createIndex({ symbol: 1, date: -1 });
```

### 可选优化索引
```javascript
// 复合索引用于特定查询
db.collection('stock_indicators').createIndex(
    { symbol: 1, date: -1, indicator: 1 }
);

// 时间序列集合索引
db.collection('stock_timeseries').createIndex(
    { symbol: 1, date: -1 }
);
```

## 注意事项

1. **内存管理**: 预计算时注意内存使用，可以分批处理
2. **更新策略**: 确定指标更新频率（实时、每日、每周）
3. **数据一致性**: 新数据插入后及时更新指标
4. **监控**: 监控查询性能和存储空间使用
5. **备份**: 指标集合也需要定期备份

## 扩展功能

可以扩展支持更多技术指标:
- MACD
- 布林带
- KDJ
- 成交量指标
- ATR（平均真实波幅）

只需在预计算函数中添加相应的计算逻辑即可。

## 性能测试建议

1. 测试不同方案下的查询响应时间
2. 监控数据库CPU和内存使用
3. 比较存储空间占用
4. 测试并发查询性能

## 总结

对于股票技术指标计算场景，**强烈推荐采用方案3（预计算）**，因为它能提供最佳的查询性能，特别适合高频查询场景。结合方案1的索引优化，可以实现最优的整体性能。

如果数据量极大且MongoDB版本支持，可以考虑方案4的时间序列集合来进一步优化存储和查询性能。
