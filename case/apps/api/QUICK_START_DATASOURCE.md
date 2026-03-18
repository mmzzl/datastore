# 统一数据源接口快速入门

## 1. 基本使用

```python
from app.data_source import DataSourceManager

# 创建数据源管理器
manager = DataSourceManager()

# 获取K线数据（自动选择最佳数据源）
klines = manager.get_kline(
    code="sh.600000",
    start_date="2026-01-01",
    end_date="2026-03-17"
)

# 获取股票列表
stocks = manager.get_stock_list()

# 获取实时数据
realtime = manager.get_realtime_data("sh.600000")
```

## 2. 指定数据源

```python
# 使用Baostock
klines = manager.get_kline(
    "sh.600000", "2026-01-01", "2026-03-17",
    provider="baostock"
)

# 使用MongoDB
klines = manager.get_kline(
    "sh.600000", "2026-01-01", "2026-03-17",
    provider="mongodb"
)
```

## 3. 在Brain系统中使用

```python
from app.monitor.brain.analyzer import BrainAnalyzer
from app.data_source import DataSourceManager

# Brain分析器会自动使用统一数据源接口
brain = BrainAnalyzer()
decision = brain.analyze("sh.600000", technical_data, current_price=10.0)
```

## 4. 添加新数据源

```python
from app.data_source.interface import IDataSource
from app.data_source.models import StockKLine, StockInfo

class MyAdapter(IDataSource):
    @property
    def name(self):
        return "MyData"
    
    @property
    def provider(self):
        return "mydata"
    
    def get_kline(self, code, start_date, end_date, frequency="d", adjust_flag="3"):
        # 实现你的数据获取逻辑
        return []
    
    def get_stock_info(self, code):
        return StockInfo(code=code, name="MyStock", exchange="SH")
    
    def get_stock_list(self):
        return []
    
    def get_realtime_data(self, code):
        return {}
    
    def get_capital_flow(self, code, days=5):
        return []
    
    def close(self):
        pass

# 注册适配器
manager = DataSourceManager()
manager.register_adapter("mydata", MyAdapter())

# 使用新数据源
klines = manager.get_kline("sh.600000", "2026-01-01", "2026-03-17", provider="mydata")
```

## 5. 数据模型

### StockKLine (K线数据)
```python
kline = StockKLine(
    code="sh.600000",
    date="2026-03-17",
    open=10.0,
    high=10.5,
    low=9.8,
    close=10.2,
    volume=1000000,
    amount=10000000.0,
    turnover_rate=0.5,  # 可选
    change_pct=2.0      # 可选
)
```

### StockInfo (股票信息)
```python
info = StockInfo(
    code="sh.600000",
    name="浦发银行",
    exchange="SH",
    industry="银行",      # 可选
    market_value=1000000000.0  # 可选
)
```

## 6. 配置数据源优先级

```python
from app.data_source.models import DataSourceConfig

config = [
    DataSourceConfig(
        provider="baostock",
        name="Baostock免费数据源",
        enabled=True,
        priority=1  # 优先级最高
    ),
    DataSourceConfig(
        provider="mongodb",
        name="MongoDB缓存",
        enabled=True,
        priority=2
    )
]

manager = DataSourceManager(config)
```

## 7. 上下文管理器

```python
with DataSourceManager().get_connection() as manager:
    klines = manager.get_kline("sh.600000", "2026-01-01", "2026-03-17")
    # 自动关闭所有连接
```

## 8. 错误处理

```python
try:
    klines = manager.get_kline("sh.600000", "2026-01-01", "2026-03-17")
    if not klines:
        print("未获取到数据")
except Exception as e:
    print(f"获取数据失败: {e}")
```

## 9. 实际应用示例

### 在Brain分析器中使用

```python
from app.monitor.brain.capital_flow import CapitalFlowAnalyzer
from app.data_source import DataSourceManager

# 创建分析器
data_manager = DataSourceManager()
analyzer = CapitalFlowAnalyzer(data_manager)

# 分析资金流向
result = analyzer.analyze("sh.600000", days=5)
print(f"主力动向: {result['主力动向']}")
```

### 在回测系统中使用

```python
from app.monitor.brain.backtest import BacktestEngine
from app.data_source import DataSourceManager

# 获取历史数据
manager = DataSourceManager()
klines = manager.get_kline("sh.600000", "2026-01-01", "2026-03-17")

# 转换为回测格式
data = [{
    "date": k.date,
    "close": k.close,
    "open": k.open,
    "high": k.high,
    "low": k.low,
    "volume": k.volume
} for k in klines]

# 运行回测
engine = BacktestEngine()
result = engine.run(data, "moving_average", fast_period=5, slow_period=20)
```

## 10. 调试技巧

```python
# 查看可用数据源
manager = DataSourceManager()
print(f"可用数据源: {list(manager._adapters.keys())}")

# 查看数据源详情
for provider, adapter in manager._adapters.items():
    print(f"{provider}: {adapter.name}")

# 强制使用特定数据源
klines = manager.get_kline(
    "sh.600000", "2026-01-01", "2026-03-17",
    provider="baostock"  # 明确指定
)
```

## 常见问题

**Q: 如何知道当前使用哪个数据源？**
A: 可以通过 `manager.get_best_adapter("kline")` 查看当前选择的数据源

**Q: 数据源失败怎么办？**
A: 管理器会自动尝试下一个优先级的数据源

**Q: 如何添加新的数据源？**
A: 实现 `IDataSource` 接口，然后调用 `manager.register_adapter()`

**Q: 如何调试数据源问题？**
A: 查看日志输出，数据源初始化和调用都有详细日志
