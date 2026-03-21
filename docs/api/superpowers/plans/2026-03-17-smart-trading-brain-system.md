# Smart Trading Brain System Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a "Brain" system for intelligent stock trading decisions, including multi-dimensional analysis, target price prediction, and unhooking strategies, built upon the existing monitoring framework.

**Architecture:** The system will extend the existing `StockMonitor` class with a new `BrainAnalyzer` module. This module will aggregate data from technical analysis, capital flow, sentiment, and fundamentals to produce a comprehensive decision score and specific recommendations (entry price, target price, unhooking plan). Backtesting will be performed using a new `BacktestEngine`.

**Tech Stack:** Python, Pandas, NumPy, Baostock (data), MongoDB (storage), FastAPI (existing).

---

### Task 1: Define Brain Models and Schemas

**Files:**
- Create: `case/apps/api/app/monitor/brain/models.py`
- Modify: `case/apps/api/app/monitor/models.py` (add imports)

- [ ] **Step 1: Write the failing test (Schema validation)**

```python
# tests/monitor/test_brain_models.py
import pytest
from case.apps.api.app.monitor.brain.models import BrainDecision, UnhookStrategy

def test_brain_decision_creation():
    decision = BrainDecision(
        code="sh.600000",
        action="buy",
        confidence=0.85,
        target_price=10.5,
        entry_price=10.0,
        stop_loss=9.5
    )
    assert decision.code == "sh.600000"
    assert decision.confidence == 0.85

def test_unhook_strategy_creation():
    strategy = UnhookStrategy(
        code="sh.600000",
        current_price=8.0,
        cost_price=10.0,
        suggestion="补仓摊平",
        details={"action": "buy", "price": 8.5, "percent": 0.5}
    )
    assert strategy.suggestion == "补仓摊平"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/monitor/test_brain_models.py -v`
Expected: FAIL with "ModuleNotFoundError" or similar.

- [ ] **Step 3: Write minimal implementation**

```python
# case/apps/api/app/monitor/brain/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class BrainDecision(BaseModel):
    """大脑决策模型"""
    code: str = Field(..., description="股票代码")
    action: str = Field(..., description="操作类型: buy/sell/hold")
    confidence: float = Field(..., description="置信度 0-1")
    target_price: float = Field(..., description="目标价格")
    entry_price: float = Field(..., description="建议入场价格")
    stop_loss: float = Field(..., description="止损价格")
    reasons: List[str] = Field(default_factory=list, description="决策原因")

class UnhookStrategy(BaseModel):
    """解套策略模型"""
    code: str = Field(..., description="股票代码")
    current_price: float = Field(..., description="当前价格")
    cost_price: float = Field(..., description="持仓成本")
    suggestion: str = Field(..., description="策略建议")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细操作")
    expected_recovery_time: str = Field(default="未知", description="预计解套时间")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/monitor/test_brain_models.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add case/apps/api/app/monitor/brain/models.py tests/monitor/test_brain_models.py
git commit -m "feat: add brain decision and unhook strategy models"
```

### Task 2: Implement Capital Flow Analyzer

**Files:**
- Create: `case/apps/api/app/monitor/brain/capital_flow.py`
- Test: `tests/monitor/test_capital_flow.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/monitor/test_capital_flow.py
import pytest
from case.apps.api.app.monitor.brain.capital_flow import CapitalFlowAnalyzer

def test_capital_flow_analysis():
    analyzer = CapitalFlowAnalyzer()
    # Mock data or use real data if available
    result = analyzer.analyze("sh.600000")
    assert "net_inflow" in result
    assert "large_order_ratio" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/monitor/test_capital_flow.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# case/apps/api/app/monitor/brain/capital_flow.py
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class CapitalFlowAnalyzer:
    """主力资金流向分析器"""
    
    def analyze(self, code: str) -> Dict[str, Any]:
        """
        分析股票资金流向
        Args:
            code: 股票代码
        Returns:
            资金流向分析结果
        """
        # TODO: Integrate with existing data sources or API
        # For now, return mock data to satisfy interface
        logger.info(f"Analyzing capital flow for {code}")
        return {
            "net_inflow": 0.0,  # 净流入
            "large_order_ratio": 0.0,  # 大单占比
            "主力动向": "未知"
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/monitor/test_capital_flow.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add case/apps/api/app/monitor/brain/capital_flow.py tests/monitor/test_capital_flow.py
git commit -m "feat: add capital flow analyzer skeleton"
```

### Task 3: Implement Sentiment Analyzer

**Files:**
- Create: `case/apps/api/app/monitor/brain/sentiment.py`
- Test: `tests/monitor/test_sentiment.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/monitor/test_sentiment.py
import pytest
from case.apps.api.app.monitor.brain.sentiment import SentimentAnalyzer

def test_sentiment_analysis():
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze("sh.600000")
    assert "score" in result
    assert "news_count" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/monitor/test_sentiment.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# case/apps/api/app/monitor/brain/sentiment.py
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """情绪分析器"""
    
    def analyze(self, code: str) -> Dict[str, Any]:
        """
        分析股票情绪
        Args:
            code: 股票代码
        Returns:
            情绪分析结果
        """
        logger.info(f"Analyzing sentiment for {code}")
        # Mock implementation
        return {
            "score": 0.5,  # 0-1, 1 is positive
            "news_count": 10,
            "trend": "neutral"
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/monitor/test_sentiment.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add case/apps/api/app/monitor/brain/sentiment.py tests/monitor/test_sentiment.py
git commit -m "feat: add sentiment analyzer skeleton"
```

### Task 4: Implement Brain Analyzer (Core Logic)

**Files:**
- Create: `case/apps/api/app/monitor/brain/analyzer.py`
- Modify: `case/apps/api/app/monitor/stock_monitor.py` (integrate brain)
- Test: `tests/monitor/test_brain_analyzer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/monitor/test_brain_analyzer.py
import pytest
from case.apps.api.app.monitor.brain.analyzer import BrainAnalyzer
from case.apps.api.app.monitor.brain.models import BrainDecision

def test_brain_analysis():
    analyzer = BrainAnalyzer()
    # Mock technical data
    technical_data = {
        "rsi": 30.0,
        "macd": {"macd": -0.1, "signal": -0.05, "histogram": -0.05},
        "close": [10.0, 10.1, 10.2]
    }
    decision = analyzer.analyze("sh.600000", technical_data)
    assert isinstance(decision, BrainDecision)
    assert decision.code == "sh.600000"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/monitor/test_brain_analyzer.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# case/apps/api/app/monitor/brain/analyzer.py
import logging
from typing import Dict, Any
from .models import BrainDecision
from .capital_flow import CapitalFlowAnalyzer
from .sentiment import SentimentAnalyzer

logger = logging.getLogger(__name__)

class BrainAnalyzer:
    """大脑分析器 - 综合多维度分析"""
    
    def __init__(self):
        self.capital_analyzer = CapitalFlowAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def analyze(self, code: str, technical_data: Dict[str, Any]) -> BrainDecision:
        """
        综合分析股票
        Args:
            code: 股票代码
            technical_data: 技术指标数据
        Returns:
            大脑决策
        """
        # 1. 获取多维度数据
        capital_data = self.capital_analyzer.analyze(code)
        sentiment_data = self.sentiment_analyzer.analyze(code)
        
        # 2. 计算综合评分 (简单加权)
        technical_score = self._calculate_technical_score(technical_data)
        capital_score = capital_data.get("net_inflow", 0) > 0 ? 0.8 : 0.2
        sentiment_score = sentiment_data.get("score", 0.5)
        
        total_score = (technical_score * 0.5 + capital_score * 0.3 + sentiment_score * 0.2)
        
        # 3. 确定操作和价格
        action = "buy" if total_score > 0.6 else "sell" if total_score < 0.4 else "hold"
        
        # 简单的价格预测 (基于最近收盘价)
        close_prices = technical_data.get("close", [])
        current_price = close_prices[-1] if close_prices else 0.0
        
        return BrainDecision(
            code=code,
            action=action,
            confidence=abs(total_score - 0.5) * 2,
            target_price=current_price * 1.1,  # 预测上涨10%
            entry_price=current_price * 0.95,   # 建议入场价低5%
            stop_loss=current_price * 0.9,      # 止损低10%
            reasons=[f"综合评分: {total_score:.2f}"]
        )
    
    def _calculate_technical_score(self, technical_data: Dict[str, Any]) -> float:
        """计算技术指标得分"""
        rsi = technical_data.get("rsi", 50.0)
        if rsi < 30: return 0.8
        elif rsi > 70: return 0.2
        else: return 0.5
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/monitor/test_brain_analyzer.py -v`
Expected: PASS.

- [ ] **Step 5: Modify StockMonitor to integrate Brain**

```python
# case/apps/api/app/monitor/stock_monitor.py (add import and usage)
from .brain.analyzer import BrainAnalyzer
# ... in __init__ ...
self.brain_analyzer = BrainAnalyzer()
# ... in analyze_stock ...
# After technical analysis
brain_decision = self.brain_analyzer.analyze(stock_code, history_data)
# Use brain_decision to enhance signal or replace signal generation
```

- [ ] **Step 6: Commit**

```bash
git add case/apps/api/app/monitor/brain/analyzer.py tests/monitor/test_brain_analyzer.py
git commit -m "feat: implement core brain analyzer"
```

### Task 5: Implement Unhook Strategy Engine

**Files:**
- Create: `case/apps/api/app/monitor/brain/unhook.py`
- Test: `tests/monitor/test_unhook.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/monitor/test_unhook.py
import pytest
from case.apps.api.app.monitor.brain.unhook import UnhookEngine

def test_unhook_strategy():
    engine = UnhookEngine()
    # Holding stock at 10.0, current price 8.0
    strategy = engine.calculate_strategy("sh.600000", 8.0, 10.0)
    assert strategy.suggestion in ["补仓摊平", "止损离场", "长期持有"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/monitor/test_unhook.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# case/apps/api/app/monitor/brain/unhook.py
import logging
from typing import Dict, Any
from .models import UnhookStrategy

logger = logging.getLogger(__name__)

class UnhookEngine:
    """解套策略引擎"""
    
    def calculate_strategy(self, code: str, current_price: float, cost_price: float) -> UnhookStrategy:
        """
        计算解套策略
        Args:
            code: 股票代码
            current_price: 当前价格
            cost_price: 持仓成本
        Returns:
            解套策略
        """
        loss_rate = (cost_price - current_price) / cost_price
        
        if loss_rate < 0.05:
            suggestion = "持有观察"
            details = {"action": "hold"}
        elif loss_rate < 0.15:
            suggestion = "高抛低吸做T"
            details = {"action": "trade_t", "buy_price": current_price * 0.98, "sell_price": current_price * 1.02}
        elif loss_rate < 0.30:
            suggestion = "补仓摊平"
            details = {"action": "buy", "price": current_price * 0.95, "percent": 0.5}
        elif loss_rate < 0.50:
            suggestion = "分析基本面，考虑换股"
            details = {"action": "research"}
        else:
            suggestion = "止损离场或长期持有"
            details = {"action": "stop_loss_or_hold"}
        
        return UnhookStrategy(
            code=code,
            current_price=current_price,
            cost_price=cost_price,
            suggestion=suggestion,
            details=details
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/monitor/test_unhook.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add case/apps/api/app/monitor/brain/unhook.py tests/monitor/test_unhook.py
git commit -m "feat: implement unhook strategy engine"
```

### Task 6: Implement Backtest Engine

**Files:**
- Create: `case/apps/api/app/monitor/brain/backtest.py`
- Test: `tests/monitor/test_backtest.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/monitor/test_backtest.py
import pytest
from case.apps.api.app.monitor.brain.backtest import BacktestEngine

def test_backtest():
    engine = BacktestEngine()
    # Mock data
    data = [{"close": 10.0}, {"close": 10.1}, {"close": 10.2}]
    result = engine.run(data, "buy_and_hold")
    assert "total_return" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/monitor/test_backtest.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# case/apps/api/app/monitor/brain/backtest.py
import logging
import pandas as pd
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class BacktestEngine:
    """回测引擎"""
    
    def run(self, data: List[Dict[str, Any]], strategy: str) -> Dict[str, Any]:
        """
        运行回测
        Args:
            data: 历史数据
            strategy: 策略名称
        Returns:
            回测结果
        """
        df = pd.DataFrame(data)
        if df.empty:
            return {"total_return": 0.0, "sharpe_ratio": 0.0}
        
        # 简单的买入持有策略回测
        initial_price = df['close'].iloc[0]
        final_price = df['close'].iloc[-1]
        total_return = (final_price - initial_price) / initial_price
        
        logger.info(f"Backtest {strategy}: Total Return {total_return:.2%}")
        
        return {
            "total_return": total_return,
            "sharpe_ratio": 0.0, # Placeholder
            "max_drawdown": 0.0  # Placeholder
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/monitor/test_backtest.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add case/apps/api/app/monitor/brain/backtest.py tests/monitor/test_backtest.py
git commit -m "feat: implement backtest engine skeleton"
```

---

## Plan Review Loop

After saving the plan:

1. Dispatch a single plan-document-reviewer subagent with:
   - Plan path: `docs/superpowers/plans/2026-03-17-smart-trading-brain-system.md`
   - Spec path: `case/Trading_Strategy_Platform_Requirements.md` (or relevant spec if exists)

2. If Issues Found: fix issues, re-dispatch.
3. If Approved: proceed to execution.

I will now dispatch the subagent.<tool_call>
<function=task>
<parameter=description>Review brain system plan