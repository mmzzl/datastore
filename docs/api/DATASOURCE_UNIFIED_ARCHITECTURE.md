# 统一数据源架构设计

## 问题背景

在股票交易系统中，我们面临多种数据源：
- **Baostock**: 免费的A股数据源
- **Akshare**: 另一个免费数据源
- **MongoDB**: 缓存的历史数据
- **券商API**: 实盘交易数据

每种数据源的接口、数据格式、调用方式都不一样，导致：
1. 代码耦合度高，难以维护
2. 切换数据源需要修改大量代码
3. 新增数据源工作量大
4. 测试困难

## 解决方案：统一数据源接口

### 设计模式：适配器模式 (Adapter Pattern)

```
┌─────────────────────────────────────────────────────────────┐
│                    统一数据源管理器                         │
│                  DataSourceManager                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Baostock    │  │   MongoDB    │  │   Akshare    │     │
│  │  Adapter     │  │   Adapter    │  │   Adapter    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                 │                 │              │
│         └─────────────────┴─────────────────┘              │
│                        │                                    │
│              ┌─────────▼──────────┐                        │
│              │  IDataSource接口   │                        │
│              └────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. 统一接口 (IDataSource)

```python
class IDataSource(ABC):
    @abstractmethod
    def get_kline(code, start_date, end_date, frequency, adjust_flag) -> List[StockKLine]:
        """获取K线数据"""
    
    @abstractmethod
    def get_stock_info(code) -> Optional[StockInfo]:
        """获取股票信息"""
    
    @abstractmethod
    def get_stock_list() -> List[StockInfo]:
        """获取股票列表"""
    
    @abstractmethod
    def get_realtime_data(code) -> Dict[str, Any]:
        """获取实时数据"""
    
    @abstractmethod
    def get_capital_flow(code, days) -> List[Dict[str, Any]]:
        """获取资金流向"""
```

#### 2. 统一数据模型

```python
class StockKLine(BaseModel):
    """统一K线数据模型"""
    code: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
    turnover_rate: Optional[float]
    change_pct: Optional[float]

class StockInfo(BaseModel):
    """统一股票信息模型"""
    code: str
    name: str
    exchange: str
    industry: Optional[str]
    market_value: Optional[float]
```

#### 3. 数据源管理器

```python
class DataSourceManager:
    """负责管理多个数据源适配器"""
    
    def get_kline(code, start_date, end_date, provider=None):
        """获取K线数据，自动选择最佳数据源"""
    
    def get_stock_list(provider=None):
        """获取股票列表"""
    
    def get_realtime_data(code, provider=None):
        """获取实时数据"""
    
    def get_capital_flow(code, days, provider=None):
        """获取资金流向"""
```

### 使用示例

#### 基本使用（自动选择数据源）

```python
from app.data_source import DataSourceManager

manager = DataSourceManager()

# 自动选择最佳数据源获取K线数据
klines = manager.get_kline("sh.600000", "2026-01-01", "2026-03-17")

# 获取股票列表
stocks = manager.get_stock_list()
```

#### 指定数据源

```python
# 指定使用Baostock
klines = manager.get_kline(
    "sh.600000", 
    "2026-01-01", 
    "2026-03-17",
    provider="baostock"
)

# 指定使用MongoDB
klines = manager.get_kline(
    "sh.600000", 
    "2026-01-01", 
    "2026-03-17",
    provider="mongodb"
)
```

#### 添加新数据源

```python
from app.data_source.interface import IDataSource
from app.data_source.models import StockKLine, StockInfo

class CustomAdapter(IDataSource):
    """自定义数据源适配器"""
    
    @property
    def name(self):
        return "Custom"
    
    @property
    def provider(self):
        return "custom"
    
    def get_kline(self, code, start_date, end_date, frequency="d", adjust_flag="3"):
        # 实现自定义数据获取逻辑
        return []
    
    # 实现其他接口方法...

# 注册自定义适配器
manager = DataSourceManager()
manager.register_adapter("custom", CustomAdapter())
```

### 数据源优先级

默认按优先级使用数据源：
1. **Baostock** (优先级1) - 免费A股数据
2. **MongoDB** (优先级2) - 缓存的历史数据
3. **Akshare** (优先级3) - 备用数据源

可以通过配置调整优先级：

```python
from app.data_source.models import DataSourceConfig

config = [
    DataSourceConfig(provider="baostock", name="Baostock", enabled=True, priority=1),
    DataSourceConfig(provider="mongodb", name="MongoDB", enabled=True, priority=2),
]

manager = DataSourceManager(config)
```

### 集成到现有系统

#### Brain系统集成

已更新 `CapitalFlowAnalyzer` 和 `SentimentAnalyzer` 使用统一接口：

```python
from app.data_source import DataSourceManager

class CapitalFlowAnalyzer:
    def __init__(self, data_manager: DataSourceManager = None):
        self.data_manager = data_manager or DataSourceManager()
    
    def analyze(self, code: str, days: int = 5):
        # 使用统一接口获取资金流向
        capital_flow_data = self.data_manager.get_capital_flow(code, days)
        # ... 分析逻辑
```

### 优势

1. **解耦**: 业务逻辑与数据源实现分离
2. **可扩展**: 新增数据源只需实现接口
3. **可测试**: 可以轻松mock数据源进行测试
4. **灵活性**: 运行时切换数据源
5. **一致性**: 所有数据源返回统一格式

### 未来扩展

1. **Akshare适配器**: 实现Akshare数据源
2. **券商API适配器**: 集成实盘交易数据
3. **缓存策略**: 在管理器中添加缓存层
4. **故障转移**: 主数据源失败时自动切换备用源
5. **配置管理**: 通过配置文件管理数据源

### 文件结构

```
app/data_source/
├── __init__.py                 # 模块导出
├── interface.py                # 统一接口定义
├── models.py                   # 统一数据模型
├── manager.py                  # 数据源管理器
└── adapters/
    ├── baostock_adapter.py     # Baostock适配器
    ├── akshare_adapter.py      # Akshare适配器（待实现）
    └── mongodb_adapter.py      # MongoDB适配器
```

## 总结

通过统一数据源接口，我们实现了：
- ✅ 多数据源统一管理
- ✅ 业务逻辑与数据源解耦
- ✅ 灵活的数据源切换
- ✅ 易于扩展和测试

现在添加新数据源只需实现 `IDataSource` 接口，无需修改现有业务代码！
