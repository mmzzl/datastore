# 通达信（TDX）数据源使用指南

## 概述

通达信（Tongdaxin）是一个非常流行的实时股票数据源，通过 `mootdx` 库可以访问通达信的实时数据。

## 安装 mootdx

### 1. 安装 mootdx 库

```bash
pip install mootdx
```

### 2. 配置 mootdx

mootdx 会自动创建配置文件：

```
/root/.mootdx/config.json  # Linux
C:\Users\用户名\.mootdx\config.json  # Windows
```

配置文件内容示例：
```json
{
    "version": "1.0.0",
    "market": "std",
    "servers": {
        "std": [
            "218.108.47.69:7709",
            "218.108.98.231:7709",
            "114.80.148.28:7709"
        ]
    }
}
```

## 使用通达信数据源

### 1. 基本使用

```python
from app.data_source import DataSourceManager

manager = DataSourceManager()

# 获取实时数据（会自动使用通达信）
realtime_data = manager.get_realtime_data("sh.600519")

if realtime_data:
    print(f"股票: {realtime_data['name']}")
    print(f"价格: {realtime_data['price']}")
    print(f"涨跌幅: {realtime_data['change_pct']:.2f}%")
```

### 2. 指定使用通达信

```python
# 明确指定使用通达信
realtime_data = manager.get_realtime_data("sh.600519", provider="tdx")
```

### 3. 数据源优先级

默认优先级（数字越小优先级越高）：
1. **通达信 (TDX)** (优先级1) - 实时数据
2. **Baostock** (优先级2) - 免费A股数据
3. **MongoDB** (优先级3) - 缓存的历史数据
4. **Akshare** (优先级4) - 备用数据源

## 数据格式

### 实时数据格式

```python
{
    "code": "sh.600519",
    "name": "600519",  # 通达信不提供股票名称
    "price": 1474.98,      # 最新价
    "change": -10.02,      # 涨跌额
    "change_pct": -0.67,   # 涨跌幅%
    "volume": 19616,       # 成交量
    "amount": 0,           # 成交额（通达信可能不提供）
    "open": 1489.0,        # 开盘价
    "high": 1489.0,        # 最高价
    "low": 1474.98,        # 最低价
    "close": 1474.98,      # 收盘价(最新价)
    "last_close": 1485.0   # 昨收盘
}
```

### K线数据格式

```python
[
    {
        "code": "sh.600519",
        "date": "2026-03-17",
        "open": 1489.0,
        "high": 1490.0,
        "low": 1474.98,
        "close": 1474.98,
        "volume": 19616,
        "amount": 0.0
    },
    # ... 更多K线数据
]
```

## 实际应用示例

### 在 StockMonitor 中使用

```python
from app.monitor.stock_monitor import StockMonitor

monitor = StockMonitor(config)

# 获取股票数据（会自动使用通达信获取实时数据）
stock_data = monitor.get_stock_data("sh.600519")

if stock_data:
    print(f"股票: {stock_data.name}")
    print(f"当前价格: {stock_data.current_price}")
    print(f"涨跌幅: {stock_data.change_pct:.2f}%")
```

### 在 Brain 系统中使用

```python
from app.monitor.brain.analyzer import BrainAnalyzer

brain = BrainAnalyzer()

# Brain分析器会自动使用统一接口获取数据
decision = brain.analyze("sh.600519", technical_data, current_price=1474.98)
```

## 调试技巧

```python
# 查看可用数据源
manager = DataSourceManager()
print(f"可用数据源: {list(manager._adapters.keys())}")

# 查看数据源详情
for provider, adapter in manager._adapters.items():
    print(f"{provider}: {adapter.name} (优先级: {manager._get_adapter_priority(provider)})")

# 测试通达信连接
tdx_adapter = manager.get_adapter("tdx")
if tdx_adapter:
    realtime_data = tdx_adapter.get_realtime_data("sh.600519")
    print(f"通达信数据: {realtime_data}")
```

## 常见问题

### Q: mootdx 安装失败怎么办？

**A:** 可能是网络问题，尝试：

```bash
# 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple mootdx

# 或者使用其他镜像
pip install -i https://pypi.douban.com/simple mootdx
```

### Q: 通达信连接失败怎么办？

**A:** 可能是网络问题或通达信服务器限制：

1. 检查网络连接
2. 尝试更换通达信服务器
3. 系统会自动回退到其他数据源

### Q: 通达信不提供股票名称怎么办？

**A:** 通达信实时数据确实不提供股票名称，可以：

1. 从其他数据源获取股票名称
2. 使用股票代码作为名称
3. 从本地数据库缓存股票名称

### Q: 如何知道当前使用哪个数据源？

**A:** 通过日志查看，或者：

```python
# 查看当前选择的数据源
best_adapter = manager.get_best_adapter("realtime")
print(f"当前数据源: {best_adapter.name if best_adapter else '无'}")
```

## 优势

1. **实时性强** - 通达信提供实时行情数据
2. **连接稳定** - 通达信服务器分布广泛
3. **自动回退** - 失败时自动切换到其他数据源
4. **统一接口** - 与其他数据源使用相同的接口
5. **K线数据** - 支持获取历史K线数据（日线、周线、月线、分钟线）

## 支持的K线周期

- **日线 (D)** - 最常用
- **周线 (W)** - 周级别分析
- **月线 (M)** - 月级别分析
- **5分钟线 (5)** - 短期交易
- **1分钟线 (1)** - 超短期交易

## 注意事项

1. **需要安装 mootdx** - 使用前必须安装 mootdx 库
2. **网络依赖** - 需要稳定的网络连接
3. **数据格式** - 通达信数据格式与其他源略有不同
4. **名称缺失** - 通达信不提供股票名称

## 总结

通达信适配器为系统提供了实时数据源，当 MongoDB 中没有数据时，系统会自动使用通达信获取实时行情，确保监控系统正常运行！
