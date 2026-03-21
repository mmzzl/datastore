# 实时数据获取使用指南

## 问题背景

之前 `StockMonitor` 直接依赖 `StockDataFetcher` 获取数据，当 MongoDB 中没有数据时会失败。现在通过统一数据源接口，可以自动从多个数据源获取数据。

## 解决方案

### 1. 统一数据源接口

使用 `DataSourceManager` 统一管理多个数据源：

```python
from app.data_source import DataSourceManager

manager = DataSourceManager()
```

### 2. 获取实时数据

#### 自动选择数据源（推荐）

```python
# 自动从优先级最高的数据源获取实时数据
realtime_data = manager.get_realtime_data("sz.300185")

if realtime_data:
    print(f"股票: {realtime_data['name']}")
    print(f"价格: {realtime_data['price']}")
    print(f"涨跌幅: {realtime_data['change_pct']}%")
```

#### 指定数据源

```python
# 从 Akshare 获取实时数据
realtime_data = manager.get_realtime_data("sz.300185", provider="akshare")

# 从 MongoDB 获取数据（如果有缓存）
realtime_data = manager.get_realtime_data("sz.300185", provider="mongodb")
```

### 3. 数据源优先级

默认优先级（数字越小优先级越高）：
1. **Baostock** (优先级1) - 免费A股数据
2. **MongoDB** (优先级2) - 缓存的历史数据
3. **Akshare** (优先级3) - 备用数据源

### 4. 在 StockMonitor 中的使用

`StockMonitor` 已经集成了统一数据源接口：

```python
from app.monitor.stock_monitor import StockMonitor

monitor = StockMonitor(config)

# 获取股票数据（自动使用统一接口）
stock_data = monitor.get_stock_data("sz.300185")

if stock_data:
    print(f"股票: {stock_data.name}")
    print(f"当前价格: {stock_data.current_price}")
```

### 5. 工作流程

```
请求获取股票数据
    ↓
DataSourceManager.get_realtime_data()
    ↓
按优先级尝试数据源：
1. MongoDB (如果有缓存)
2. Baostock (免费数据)
3. Akshare (备用数据源)
    ↓
返回统一格式的数据
```

### 6. 错误处理

```python
try:
    realtime_data = manager.get_realtime_data("sz.300185")
    if not realtime_data:
        print("未获取到数据")
    else:
        print(f"价格: {realtime_data['price']}")
except Exception as e:
    print(f"获取数据失败: {e}")
```

### 7. 数据格式

统一的实时数据格式：

```python
{
    "code": "sz.300185",
    "name": "股票名称",
    "price": 10.5,        # 最新价
    "change": 0.5,        # 涨跌额
    "change_pct": 5.0,    # 涨跌幅%
    "volume": 1000000,    # 成交量
    "amount": 10000000.0, # 成交额
    "open": 10.0,         # 开盘价
    "high": 10.8,         # 最高价
    "low": 9.9,           # 最低价
    "close": 10.5         # 收盘价(最新价)
}
```

### 8. 实际应用示例

#### 在 Brain 系统中使用

```python
from app.monitor.brain.analyzer import BrainAnalyzer

brain = BrainAnalyzer()
decision = brain.analyze("sz.300185", technical_data, current_price=10.5)
```

#### 在监控任务中使用

```python
from app.monitor.stock_monitor import StockMonitor

monitor = StockMonitor(config)
stocks = monitor.monitor_config.get_stocks()

for stock in stocks:
    stock_code = stock.get("code")
    stock_data = monitor.get_stock_data(stock_code)
    
    if stock_data:
        # 进行分析...
        result = monitor.analyze_stock(stock)
```

### 9. 调试技巧

```python
# 查看可用数据源
manager = DataSourceManager()
print(f"可用数据源: {list(manager._adapters.keys())}")

# 查看数据源详情
for provider, adapter in manager._adapters.items():
    print(f"{provider}: {adapter.name} (优先级: {manager._get_adapter_priority(provider)})")

# 测试特定数据源
akshare_data = manager.get_realtime_data("sz.300185", provider="akshare")
print(f"Akshare数据: {akshare_data}")
```

### 10. 常见问题

**Q: 为什么有时候获取不到数据？**
A: 可能是网络问题或数据源暂时不可用，系统会自动尝试其他数据源。

**Q: 如何知道当前使用哪个数据源？**
A: 可以通过日志查看，或者调用 `manager.get_best_adapter("realtime")`。

**Q: 如何添加新的数据源？**
A: 实现 `IDataSource` 接口，然后调用 `manager.register_adapter()`。

**Q: Akshare 连接失败怎么办？**
A: 这可能是网络问题或 Akshare 服务限制，系统会自动回退到其他数据源。

## 总结

通过统一数据源接口，`StockMonitor` 现在可以：
- ✅ 自动从多个数据源获取数据
- ✅ 在主数据源失败时自动切换
- ✅ 统一数据格式，简化业务逻辑
- ✅ 灵活扩展新的数据源

即使 MongoDB 中没有数据，系统也会自动从 Akshare 或 Baostock 获取实时数据！
