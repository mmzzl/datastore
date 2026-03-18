# 智能交易大脑系统 (Smart Trading Brain System)

## 概述

本系统实现了一个智能交易决策系统，由"盯盘系统"（感官）+ "大脑"（分析决策）+ "操盘手"（执行）组成。

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     智能交易决策系统                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   盯盘系统   │───▶│   大脑系统   │───▶│  输出系统   │     │
│  │  (感官层)   │    │  (决策层)   │    │  (执行层)   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. Brain Models (`app/monitor/brain/models.py`)
- `BrainDecision`: 大脑决策模型（操作类型、置信度、价格目标等）
- `UnhookStrategy`: 解套策略模型

### 2. Capital Flow Analyzer (`app/monitor/brain/capital_flow.py`)
- 分析主力资金流向
- 判断资金流入/流出趋势

### 3. Sentiment Analyzer (`app/monitor/brain/sentiment.py`)
- 分析市场情绪
- 评估新闻舆情影响

### 4. Brain Analyzer (`app/monitor/brain/analyzer.py`)
- **核心决策引擎**
- 多维度综合评分：
  - 技术指标 (50%)
  - 资金流向 (30%)
  - 市场情绪 (20%)
- 生成买入/卖出/持有信号
- 计算目标价、入场价、止损价

### 5. Unhook Engine (`app/monitor/brain/unhook.py`)
- 针对持仓股票的解套策略
- 根据亏损程度制定不同策略：
  - < 5%: 持有观察
  - 5-15%: 高抛低吸做T
  - 15-30%: 补仓摊平
  - 30-50%: 分析基本面，考虑换股
  - > 50%: 止损离场或长期持有

### 6. Backtest Engine (`app/monitor/brain/backtest.py`)
- 策略回测验证
- 支持多种策略：
  - 买入持有策略
  - 移动平均线策略
  - RSI策略

## 使用方法

### 基本使用

```python
from app.monitor.brain.analyzer import BrainAnalyzer
from app.monitor.brain.unhook import UnhookEngine

# 初始化大脑分析器
brain = BrainAnalyzer()

# 分析股票
technical_data = {
    "rsi": 30.0,
    "macd": {"macd": -0.1, "signal": -0.05, "histogram": -0.05},
    "kdj": {"k": 20.0, "d": 30.0, "j": 10.0},
    "bollinger": {"upper": 11.0, "middle": 10.0, "lower": 9.0},
    "close": [10.0, 10.1, 10.2]
}

decision = brain.analyze("sh.600000", technical_data, current_price=10.0)
print(f"操作建议: {decision.action}, 置信度: {decision.confidence:.2f}")

# 解套策略
unhook = UnhookEngine()
strategy = unhook.calculate_strategy("sh.600000", current_price=8.0, cost_price=10.0)
print(f"解套建议: {strategy.suggestion}")
```

### 与现有监控系统集成

Brain系统已集成到 `StockMonitor` 中，自动在股票分析时使用：

```python
from app.monitor.stock_monitor import StockMonitor

monitor = StockMonitor(config)
result = monitor.analyze_stock(stock_config)

# result.signal 包含Brain系统生成的信号
# 如果是持仓股票，还会生成解套策略
```

## 测试

运行测试：

```bash
# 使用 Python 3.12
cd case/apps/api
py -3.12 -m pytest tests/monitor/test_brain_system.py -v
```

测试覆盖：
- ✅ Brain模型创建
- ✅ Brain分析器功能
- ✅ 解套策略计算
- ✅ 解套概率计算
- ✅ 回测引擎功能

## 配置

### 数据源
- 技术指标：从现有技术分析模块获取
- 资金流向：从MongoDB获取（`capital_flow` 集合）
- 市场情绪：从MongoDB获取（`news_stocks` 集合）

### 权重配置
可在 `BrainAnalyzer` 中调整各维度权重：
```python
total_score = (technical_score * 0.5 + capital_score * 0.3 + sentiment_score * 0.2)
```

## 扩展性

### 添加新的分析维度
1. 在 `brain/` 目录下创建新的分析器
2. 实现 `analyze(code: str) -> Dict[str, Any]` 方法
3. 在 `BrainAnalyzer` 中集成
4. 调整权重分配

### 添加新的解套策略
1. 在 `UnhookEngine.calculate_strategy` 中添加新的亏损区间
2. 定义相应的策略建议和详细操作

### 添加新的回测策略
1. 在 `BacktestEngine` 中添加新的回测方法
2. 在 `run` 方法中注册新策略

## 注意事项

1. **数据依赖**：资金流向和情绪分析依赖MongoDB数据，如果没有数据会返回模拟数据
2. **性能考虑**：Brain分析涉及多维度数据获取，建议异步处理
3. **风险控制**：所有决策建议仅供参考，实际交易需结合个人判断

## 更新日志

### 2026-03-17
- ✅ 实现Brain系统核心组件
- ✅ 集成到StockMonitor
- ✅ 添加完整测试套件
- ✅ 通过所有测试
