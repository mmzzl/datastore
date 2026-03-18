# 资金流向功能使用指南

## 概述

资金流向分析是股票交易中的重要指标，可以帮助判断主力资金的动向。系统现在支持通过 Akshare 获取个股历史资金流向数据。

## 数据来源

使用 Akshare 的 `stock_individual_fund_flow` 函数获取资金流向数据：

```python
import akshare as ak
df = ak.stock_individual_fund_flow(stock="600519")
```

## 数据字段

获取到的资金流向数据包含以下字段：

| 字段 | 说明 |
|------|------|
| 日期 | 交易日期 |
| 收盘价 | 当日收盘价 |
| 涨跌幅 | 当日涨跌幅 |
| 主力净流入-净额 | 主力资金净流入金额 |
| 主力净流入-净占比 | 主力资金净流入占比 |
| 超大单净流入-净额 | 超大单资金净流入金额 |
| 超大单净流入-净占比 | 超大单资金净流入占比 |
| 大单净流入-净额 | 大单资金净流入金额 |
| 大单净流入-净占比 | 大单资金净流入占比 |
| 中单净流入-净额 | 中单资金净流入金额 |
| 中单净流入-净占比 | 中单资金净流入占比 |
| 小单净流入-净额 | 小单资金净流入金额 |
| 小单净流入-净占比 | 小单资金净流入占比 |

## 使用方法

### 1. 通过统一接口获取资金流向

```python
from app.data_source import DataSourceManager

manager = DataSourceManager()

# 获取个股资金流向（最近5天）
capital_flow = manager.get_capital_flow("sh.600519", days=5, provider="akshare")

if capital_flow:
    for data in capital_flow:
        print(f"{data['date']}: 主力净流入 {data['主力净流入_净额']:.2f}")
```

### 2. 在 Brain 系统中使用

```python
from app.monitor.brain.capital_flow import CapitalFlowAnalyzer

analyzer = CapitalFlowAnalyzer()
result = analyzer.analyze("sh.600519", days=5)

print(f"主力动向: {result['主力动向']}")
print(f"净流入: {result['net_inflow']:.2f}")
print(f"趋势评分: {result['trend_score']:.2f}")
```

### 3. 在 StockMonitor 中使用

```python
from app.monitor.stock_monitor import StockMonitor

monitor = StockMonitor(config)

# 分析股票时会自动使用资金流向数据
result = monitor.analyze_stock({"code": "sh.600519"})
```

## 返回数据格式

```python
[
    {
        "date": "2026-03-17",
        "code": "sh.600519",
        "close": 1499.54,
        "change_pct": 0.10,
        "主力净流入_净额": 198632512.00,
        "主力净流入_净占比": 3.52,
        "net_inflow": 198632512.00
    },
    # ... 更多日期的数据
]
```

## 实际应用示例

### 判断主力动向

```python
def analyze主力动向(stock_code):
    manager = DataSourceManager()
    capital_flow = manager.get_capital_flow(stock_code, days=5)
    
    if not capital_flow:
        return "无数据"
    
    # 计算最近5天的平均净流入
    total_inflow = sum(d['net_inflow'] for d in capital_flow)
    avg_inflow = total_inflow / len(capital_flow)
    
    if avg_inflow > 0:
        return "主力流入"
    elif avg_inflow < 0:
        return "主力流出"
    else:
        return "平衡"
```

### 结合技术指标

```python
def 综合分析(stock_code):
    # 获取技术指标
    technical_data = get_technical_data(stock_code)
    
    # 获取资金流向
    manager = DataSourceManager()
    capital_flow = manager.get_capital_flow(stock_code, days=5)
    
    # 综合判断
    if technical_data['rsi'] < 30 and capital_flow[0]['net_inflow'] > 0:
        return "超卖且主力流入，买入信号"
    elif technical_data['rsi'] > 70 and capital_flow[0]['net_inflow'] < 0:
        return "超买且主力流出，卖出信号"
    else:
        return "观望"
```

## 资金流向分析策略

### 主力资金流向判断

1. **主力净流入 > 0**: 主力在买入，可能是上涨信号
2. **主力净流入 < 0**: 主力在卖出，可能是下跌信号
3. **连续多日流入**: 主力持续看好，上涨概率大
4. **连续多日流出**: 主力持续看空，下跌概率大

### 大单分析

- **超大单净流入**: 机构资金动向
- **大单净流入**: 游资动向
- **中单/小单**: 散户动向

### 实际应用

```python
def 判断主力意图(stock_code):
    manager = DataSourceManager()
    capital_flow = manager.get_capital_flow(stock_code, days=3)
    
    if len(capital_flow) < 3:
        return "数据不足"
    
    # 检查连续性
    inflows = [d['net_inflow'] for d in capital_flow]
    
    if all(i > 0 for i in inflows):
        return "主力持续流入，看涨"
    elif all(i < 0 for i in inflows):
        return "主力持续流出，看跌"
    else:
        return "主力分歧，观望"
```

## 注意事项

1. **数据延迟**: 资金流向数据通常有1天延迟
2. **数据完整性**: 部分股票可能没有完整的资金流向数据
3. **主力定义**: 不同数据源对"主力"的定义可能不同
4. **仅供参考**: 资金流向只是参考指标，需要结合其他分析

## 常见问题

**Q: 为什么获取不到资金流向数据？**
A: 可能是股票代码格式不对，或者该股票没有资金流向数据。

**Q: 主力净流入占比是什么意思？**
A: 主力净流入占当日成交额的百分比，数值越大说明主力参与度越高。

**Q: 如何判断主力是否在吸筹？**
A: 连续多日主力净流入且股价相对稳定，可能是主力在吸筹。

**Q: 资金流向数据准确吗？**
A: 资金流向数据是估算值，仅供参考，不能作为唯一交易依据。

## 总结

资金流向功能已经集成到统一数据源接口中，可以：
- ✅ 通过 Akshare 获取个股历史资金流向
- ✅ 自动集成到 Brain 系统进行分析
- ✅ 支持多日数据获取
- ✅ 统一的数据格式

使用资金流向可以帮助判断主力动向，辅助交易决策！
