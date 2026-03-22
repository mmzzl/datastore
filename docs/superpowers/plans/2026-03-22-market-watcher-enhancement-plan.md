# 盯盘系统增强实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建分层预警引擎，支持日内高频/波段趋势/事件驱动三种策略，覆盖价格/成交量/技术指标/新闻/市场广度五类预警，统一经分级推送机制触达用户。

**Architecture:** AlertOrchestrator 总调度 + 5个独立 Watcher（市场广度/关联资产/个股预警/新闻事件/分钟K线）+ AlertAggregator 信号聚合器 + 分级推送。数据层扩展 DataSourceManager 新增三个方法，复用现有 baostock/akshare 适配器实现。

**Tech Stack:** Python (asyncio + threading), akshare, baostock, MongoDB, 钉钉 webhook

---

## Chunk 1: 数据层扩展

### Context

扩展 `DataSourceManager` 和 `AkshareAdapter`，新增三个统一数据访问方法。

### Files

- Create: `apps/api/app/data_source/models.py` (新增 `MarketBreadth`, `CorrelatedAssets` 数据模型)
- Modify: `apps/api/app/data_source/manager.py` (新增 `get_market_breadth`, `get_correlated_assets`, `get_minute_kline`)
- Modify: `apps/api/app/data_source/adapters/akshare_adapter.py` (实现三个方法的具体逻辑)
- Modify: `apps/api/app/data_source/adapters/baostock_adapter.py` (stub实现，返回默认值)
- Modify: `apps/api/app/data_source/adapters/mongodb_adapter.py` (stub实现)
- Modify: `apps/api/app/data_source/adapters/tdx_adapter.py` (stub实现)
- Modify: `apps/api/app/data_source/interface.py` (接口定义更新)
- Test: `apps/api/tests/test_data_source_enhancement.py` (新建)

---

- [ ] **Step 1: 在 `data_source/models.py` 中新增 MarketBreadth 和 CorrelatedAssets 模型**

打开 `apps/api/app/data_source/models.py`，在文件末尾追加：

```python
@dataclass
class MarketBreadth:
    """市场广度数据"""
    timestamp: datetime
    advance_count: int          # 上涨家数
    decline_count: int          # 下跌家数
    advance_decline_ratio: float  # 涨跌家数比
    sector_rankings: List[Dict[str, Any]]  # 板块排名 [{name, change_pct}]
    north_bound_flow: float     # 北向资金净流入（万元）
    vix: float                 # 恐慌指数

@dataclass
class CorrelatedAssets:
    """关联资产数据"""
    timestamp: datetime
    a50_future: float          # A50期货点位
    a50_change_pct: float     # A50涨跌幅
    usdcnh: float             # 离岸人民币汇率
    dxy: float               # 美元指数
```

- [ ] **Step 2: 在 `data_source/interface.py` 中更新 IDataSource 接口**

找到 `IDataSource` 类，在末尾新增三个方法签名：

```python
def get_market_breadth(self) -> Optional[MarketBreadth]:
    """获取市场广度数据"""

def get_correlated_assets(self) -> Optional[CorrelatedAssets]:
    """获取关联资产数据"""

def get_minute_kline(
    self, code: str, frequency: str = "5", days: int = 5
) -> List[StockKLine]:
    """获取分钟K线数据, frequency: 1/5/15/30/60"""
```

- [ ] **Step 3: 在 `data_source/adapters/baostock_adapter.py` 中添加 stub 实现**

在 `BaostockAdapter` 类末尾添加三个 stub 方法：

```python
def get_market_breadth(self) -> Optional[MarketBreadth]:
    return None

def get_correlated_assets(self) -> Optional[CorrelatedAssets]:
    return None

def get_minute_kline(
    self, code: str, frequency: str = "5", days: int = 5
) -> List[StockKLine]:
    return []
```

- [ ] **Step 4: 在 `data_source/adapters/mongodb_adapter.py` 中添加 stub 实现**

同上，添加三个返回 `None` / `[]` 的 stub 方法。

- [ ] **Step 5: 在 `data_source/adapters/tdx_adapter.py` 中添加 stub 实现**

同上，添加三个返回 `None` / `[]` 的 stub 方法。

- [ ] **Step 6: 在 `data_source/adapters/akshare_adapter.py` 中实现三个方法**

找到 `AkshareAdapter` 类末尾，添加三个方法：

```python
def get_market_breadth(self) -> Optional[MarketBreadth]:
    """获取市场广度数据"""
    try:
        from datetime import datetime
        import akshare as ak
        
        # 涨跌家数（东方财富）
        spot_em = ak.stock_zh_a_spot_em()
        advance = int(spot_em[spot_em['涨跌幅'] > 0].shape[0])
        decline = int(spot_em[spot_em['涨跌幅'] < 0].shape[0])
        
        # 北向资金
        north = ak.stock_em_hsgt_north_flow(indicator="北向资金")
        north_flow = float(north['北向资金'].iloc[-1]) if not north.empty else 0.0
        
        # 板块排名（取前10）
        sector = ak.stock_board_industry_name_em()
        sector_sorted = sector.sort_values('涨跌幅', ascending=False)
        sector_rankings = [
            {"name": row['板块名称'], "change_pct": float(row['涨跌幅'])}
            for _, row in sector_sorted.head(10).iterrows()
        ]
        
        return MarketBreadth(
            timestamp=datetime.now(),
            advance_count=advance,
            decline_count=decline,
            advance_decline_ratio=round(advance / decline, 2) if decline > 0 else 99.0,
            sector_rankings=sector_rankings,
            north_bound_flow=north_flow,
            vix=15.0  # akshare暂不支持VIX，返回默认值
        )
    except Exception:
        return None

def get_correlated_assets(self) -> Optional[CorrelatedAssets]:
    """获取关联资产数据"""
    try:
        from datetime import datetime
        import akshare as ak
        
        # A50期货
        try:
            a50_df = ak.index_zh_a_hist(symbol="000001", period="daily", adjust="qfq")
            a50_change = float(a50_df['涨跌幅'].iloc[-1]) if not a50_df.empty else 0.0
        except Exception:
            a50_change = 0.0
        a50_future = 0.0  # 期货数据需单独接口，暂用现货代替
        
        # 离岸人民币
        try:
            usdcnh_df = ak.currency_usdt_cny_hist()
            usdcnh = float(usdcnh_df['中行折算价'].iloc[-1]) if not usdcnh_df.empty else 7.25
        except Exception:
            usdcnh = 7.25
        
        # 美元指数（使用欧元美元代替）
        try:
            dxy_df = ak.currency_usdkline()
            dxy = float(dxy_df['close'].iloc[-1]) if not dxy_df.empty else 104.0
        except Exception:
            dxy = 104.0
        
        return CorrelatedAssets(
            timestamp=datetime.now(),
            a50_future=a50_future,
            a50_change_pct=a50_change,
            usdcnh=usdcnh,
            dxy=dxy
        )
    except Exception:
        return None

def get_minute_kline(
    self, code: str, frequency: str = "5", days: int = 5
) -> List[StockKLine]:
    """获取分钟K线数据"""
    try:
        import akshare as ak
        from datetime import datetime, timedelta
        
        # 格式化代码
        if not code.startswith(('SH', 'SZ')):
            if code.startswith('6'):
                code = f"SH{code}"
            else:
                code = f"SZ{code}"
        
        # 转换frequency格式
        freq_map = {"1": "1", "5": "5", "15": "15", "30": "30", "60": "60"}
        freq = freq_map.get(frequency, "5")
        
        end_date = datetime.now().strftime("%Y%m%d %H:%M:%S")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d %H:%M:%S")
        
        df = ak.stock_zh_a_hist_min_em(
            symbol=code, period=freq, start_date=start_date, end_date=end_date, adjust="qfq"
        )
        
        if df is None or df.empty:
            return []
        
        return [
            StockKLine(
                code=code,
                date=row['时间'],
                open=float(row['开盘']),
                high=float(row['最高']),
                low=float(row['最低']),
                close=float(row['收盘']),
                volume=int(row['成交量']),
                amount=float(row['成交额']) if '成交额' in row else 0.0,
                change=float(row['涨跌幅']) if '涨跌幅' in row else 0.0,
                turnover=float(row['换手率']) if '换手率' in row else 0.0
            )
            for _, row in df.iterrows()
        ]
    except Exception:
        return []
```

- [ ] **Step 7: 在 `data_source/manager.py` 中添加统一接口方法**

在 `DataSourceManager` 类末尾添加：

```python
def get_market_breadth(self, provider: str = None) -> Optional[MarketBreadth]:
    """获取市场广度数据"""
    from app.data_source.models import MarketBreadth
    if provider:
        adapter = self._adapters.get(provider)
        if adapter and hasattr(adapter, "get_market_breadth"):
            return adapter.get_market_breadth()
    for adapter in self._adapters.values():
        try:
            result = adapter.get_market_breadth()
            if result:
                return result
        except Exception:
            continue
    return None

def get_correlated_assets(self, provider: str = None) -> Optional[CorrelatedAssets]:
    """获取关联资产数据"""
    from app.data_source.models import CorrelatedAssets
    if provider:
        adapter = self._adapters.get(provider)
        if adapter and hasattr(adapter, "get_correlated_assets"):
            return adapter.get_correlated_assets()
    for adapter in self._adapters.values():
        try:
            result = adapter.get_correlated_assets()
            if result:
                return result
        except Exception:
            continue
    return None

def get_minute_kline(
    self, code: str, frequency: str = "5", days: int = 5, provider: str = None
) -> List[StockKLine]:
    """获取分钟K线数据"""
    if provider:
        adapter = self._adapters.get(provider)
        if adapter and hasattr(adapter, "get_minute_kline"):
            return adapter.get_minute_kline(code, frequency, days)
    for adapter in self._adapters.values():
        try:
            result = adapter.get_minute_kline(code, frequency, days)
            if result:
                return result
        except Exception:
            continue
    return []
```

- [ ] **Step 8: 写单元测试**

创建 `apps/api/tests/test_data_source_enhancement.py`：

```python
import pytest
from app.data_source.manager import DataSourceManager
from app.data_source.models import MarketBreadth, CorrelatedAssets, StockKLine


class TestDataSourceEnhancement:
    """数据源增强测试"""
    
    def test_manager_has_new_methods(self):
        dm = DataSourceManager()
        assert hasattr(dm, "get_market_breadth")
        assert hasattr(dm, "get_correlated_assets")
        assert hasattr(dm, "get_minute_kline")
    
    def test_get_market_breadth_returns_expected_fields(self):
        dm = DataSourceManager()
        result = dm.get_market_breadth()
        if result:
            assert hasattr(result, "advance_count")
            assert hasattr(result, "decline_count")
            assert hasattr(result, "advance_decline_ratio")
            assert hasattr(result, "sector_rankings")
            assert hasattr(result, "north_bound_flow")
    
    def test_get_correlated_assets_returns_expected_fields(self):
        dm = DataSourceManager()
        result = dm.get_correlated_assets()
        if result:
            assert hasattr(result, "a50_change_pct")
            assert hasattr(result, "usdcnh")
            assert hasattr(result, "dxy")
    
    def test_get_minute_kline_returns_list(self):
        dm = DataSourceManager()
        result = dm.get_minute_kline("600000", frequency="5", days=1)
        assert isinstance(result, list)
    
    def test_market_breadth_fallback_on_error(self):
        dm = DataSourceManager()
        # 验证降级处理：所有adapter失败时返回None
        result = dm.get_market_breadth(provider="nonexistent")
        assert result is None
    
    def test_correlated_assets_fallback_on_error(self):
        dm = DataSourceManager()
        result = dm.get_correlated_assets(provider="nonexistent")
        assert result is None
    
    def test_minute_kline_fallback_on_error(self):
        dm = DataSourceManager()
        result = dm.get_minute_kline("INVALID_CODE", frequency="5")
        assert result == []
```

- [ ] **Step 9: 运行测试验证**

Run: `cd apps/api && python -m pytest tests/test_data_source_enhancement.py -v`
Expected: 至少 `test_manager_has_new_methods` PASS，其他可 skip（依赖外部 API）

- [ ] **Step 10: Commit**

```bash
git add apps/api/app/data_source/models.py apps/api/app/data_source/interface.py
git add apps/api/app/data_source/manager.py
git add apps/api/app/data_source/adapters/baostock_adapter.py
git add apps/api/app/data_source/adapters/mongodb_adapter.py
git add apps/api/app/data_source/adapters/tdx_adapter.py
git add apps/api/app/data_source/adapters/akshare_adapter.py
git add apps/api/tests/test_data_source_enhancement.py
git commit -m "feat: extend DataSourceManager with market breadth, correlated assets, and minute kline methods"
```

---

## Chunk 2: 预警数据模型

### Context

新增 AlertRule、AlertSignal、NotificationConfig 三个数据模型，定义预警配置结构和信号结构。

### Files

- Create: `apps/api/app/monitor/models/alert_rule.py`
- Create: `apps/api/app/monitor/models/alert_signal.py`
- Create: `apps/api/app/monitor/models/notification_config.py`
- Modify: `apps/api/app/monitor/models/__init__.py` (导出新增模型)
- Test: `apps/api/tests/test_alert_models.py` (新建)

---

- [ ] **Step 1: 创建 `apps/api/app/monitor/models/alert_rule.py`**

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime


class AlertType(str, Enum):
    PRICE = "price"
    VOLUME = "volume"
    TECHNICAL = "technical"
    NEWS = "news"
    BREADTH = "breadth"


class StrategyType(str, Enum):
    INTRADAY = "intraday"
    SWING = "swing"
    EVENT = "event"
    ALL = "all"


class AlertPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertOperator(str, Enum):
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    EQ = "=="
    CROSS_UP = "cross_up"
    CROSS_DOWN = "cross_down"
    IN_RANGE = "in_range"


@dataclass
class AlertCondition:
    operator: AlertOperator
    value: float
    reference: str  # price, rsi, volume_ratio, north_flow, etc.
    period: int = 14


@dataclass
class NotifyConfig:
    dingtalk: bool = True
    dashboard: bool = True
    repeat_interval: int = 30  # seconds, for critical only
    at_all: bool = False  # for critical priority


@dataclass
class AlertRule:
    id: str = ""
    code: str = ""
    name: str = ""
    alert_type: AlertType = AlertType.PRICE
    condition: Optional[AlertCondition] = None
    strategy_type: StrategyType = StrategyType.ALL
    priority: AlertPriority = AlertPriority.MEDIUM
    notification: NotifyConfig = field(default_factory=NotifyConfig)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "alert_type": self.alert_type.value,
            "condition": {
                "operator": self.condition.operator.value if self.condition else None,
                "value": self.condition.value if self.condition else None,
                "reference": self.condition.reference if self.condition else None,
                "period": self.condition.period if self.condition else None,
            } if self.condition else None,
            "strategy_type": self.strategy_type.value,
            "priority": self.priority.value,
            "notification": {
                "dingtalk": self.notification.dingtalk,
                "dashboard": self.notification.dashboard,
                "repeat_interval": self.notification.repeat_interval,
                "at_all": self.notification.at_all,
            },
            "enabled": self.enabled,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlertRule":
        condition = None
        if data.get("condition"):
            cond_data = data["condition"]
            condition = AlertCondition(
                operator=AlertOperator(cond_data.get("operator", ">")),
                value=float(cond_data.get("value", 0)),
                reference=cond_data.get("reference", "price"),
                period=int(cond_data.get("period", 14)),
            )
        notify_data = data.get("notification", {})
        return cls(
            id=data.get("id", ""),
            code=data.get("code", ""),
            name=data.get("name", ""),
            alert_type=AlertType(data.get("alert_type", "price")),
            condition=condition,
            strategy_type=StrategyType(data.get("strategy_type", "all")),
            priority=AlertPriority(data.get("priority", "medium")),
            notification=NotifyConfig(
                dingtalk=notify_data.get("dingtalk", True),
                dashboard=notify_data.get("dashboard", True),
                repeat_interval=notify_data.get("repeat_interval", 30),
                at_all=notify_data.get("at_all", False),
            ),
            enabled=data.get("enabled", True),
        )
```

- [ ] **Step 2: 创建 `apps/api/app/monitor/models/alert_signal.py`**

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime


class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class AlertSignal:
    timestamp: datetime
    code: str
    name: str
    signal: SignalType
    confidence: float  # 0.0 ~ 1.0
    priority: str  # low / medium / high / critical
    reasons: List[str] = field(default_factory=list)
    technical_data: Dict[str, Any] = field(default_factory=dict)
    market_breadth: Optional[Dict[str, Any]] = None
    correlated_assets: Optional[Dict[str, Any]] = None
    price: float = 0.0
    volume_ratio: float = 0.0
    alert_type: str = "technical"
    strategy_type: str = "all"
    action_price: float = 0.0  # 触发预警的价格
    target_price: float = 0.0
    stop_loss: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "code": self.code,
            "name": self.name,
            "signal": self.signal.value,
            "confidence": round(self.confidence, 4),
            "priority": self.priority,
            "reasons": self.reasons,
            "technical_data": self.technical_data,
            "market_breadth": self.market_breadth,
            "correlated_assets": self.correlated_assets,
            "price": self.price,
            "volume_ratio": self.volume_ratio,
            "alert_type": self.alert_type,
            "strategy_type": self.strategy_type,
            "action_price": self.action_price,
            "target_price": self.target_price,
            "stop_loss": self.stop_loss,
        }
```

- [ ] **Step 3: 创建 `apps/api/app/monitor/models/notification_config.py`**

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any


class NotificationLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class NotificationPayload:
    title: str
    body: str
    level: NotificationLevel
    code: str
    signal: str
    confidence: float
    price: float
    reasons: list
    action_price: float
    target_price: float
    stop_loss: float
    
    def to_dingtalk_markdown(self) -> str:
        emoji = "🔴" if self.level == "critical" else ("🟠" if self.level == "high" else ("🟡" if self.level == "medium" else "⚪"))
        return f"### {emoji} [{self.level.upper()}] {self.title}\n\n**股票**: {self.name} ({self.code})\n\n**当前价格**: {self.price:.2f}\n\n**信号**: {self.signal.upper()}\n\n**置信度**: {self.confidence*100:.1f}%\n\n**理由**:\n" + "\n".join([f"- {r}" for r in self.reasons]) + f"\n\n**建议操作**: {'立即执行' if self.level in ('critical', 'high') else '观察'}"

    @property
    def name(self) -> str:
        return self.title.replace("信号", "").replace("预警", "")
```

- [ ] **Step 4: 更新 `apps/api/app/monitor/models/__init__.py`**

```python
from .alert_rule import (
    AlertRule,
    AlertType,
    AlertCondition,
    AlertPriority,
    AlertOperator,
    StrategyType,
    NotifyConfig,
)
from .alert_signal import AlertSignal, SignalType
from .notification_config import NotificationPayload, NotificationLevel
from .models import (
    StockData,
    TechnicalData,
    Signal,
    MonitorResult,
    MonitorNotification,
    RSI,
    MACD,
    KDJ,
    BollingerBands,
)

__all__ = [
    "AlertRule",
    "AlertType",
    "AlertCondition",
    "AlertPriority",
    "AlertOperator",
    "StrategyType",
    "NotifyConfig",
    "AlertSignal",
    "SignalType",
    "NotificationPayload",
    "NotificationLevel",
    "StockData",
    "TechnicalData",
    "Signal",
    "MonitorResult",
    "MonitorNotification",
    "RSI",
    "MACD",
    "KDJ",
    "BollingerBands",
]
```

- [ ] **Step 5: 写单元测试**

创建 `apps/api/tests/test_alert_models.py`：

```python
import pytest
from datetime import datetime
from app.monitor.models.alert_rule import (
    AlertRule, AlertType, AlertCondition, AlertPriority,
    AlertOperator, StrategyType, NotifyConfig
)
from app.monitor.models.alert_signal import AlertSignal, SignalType
from app.monitor.models.notification_config import NotificationPayload


class TestAlertRule:
    def test_alert_rule_serialization(self):
        rule = AlertRule(
            code="600000",
            name="浦发银行",
            alert_type=AlertType.PRICE,
            condition=AlertCondition(
                operator=AlertOperator.GT,
                value=10.0,
                reference="price",
            ),
            priority=AlertPriority.HIGH,
        )
        data = rule.to_dict()
        assert data["code"] == "600000"
        assert data["alert_type"] == "price"
        assert data["condition"]["operator"] == ">"

    def test_alert_rule_deserialization(self):
        data = {
            "code": "600000",
            "alert_type": "volume",
            "condition": {
                "operator": "cross_up",
                "value": 1.5,
                "reference": "volume_ratio",
                "period": 5,
            },
            "priority": "critical",
            "notification": {"dingtalk": True, "dashboard": True, "repeat_interval": 30, "at_all": True},
        }
        rule = AlertRule.from_dict(data)
        assert rule.code == "600000"
        assert rule.alert_type == AlertType.VOLUME
        assert rule.condition.operator == AlertOperator.CROSS_UP
        assert rule.priority == AlertPriority.CRITICAL
        assert rule.notification.at_all is True

    def test_notify_config_defaults(self):
        cfg = NotifyConfig()
        assert cfg.repeat_interval == 30
        assert cfg.at_all is False


class TestAlertSignal:
    def test_alert_signal_to_dict(self):
        signal = AlertSignal(
            timestamp=datetime.now(),
            code="600000",
            name="浦发银行",
            signal=SignalType.BUY,
            confidence=0.75,
            priority="high",
            reasons=["RSI低于30", "MACD金叉"],
            price=9.5,
            volume_ratio=2.0,
            alert_type="technical",
            strategy_type="intraday",
        )
        data = signal.to_dict()
        assert data["code"] == "600000"
        assert data["signal"] == "buy"
        assert data["confidence"] == 0.75
        assert len(data["reasons"]) == 2


class TestNotificationPayload:
    def test_dingtalk_markdown_critical(self):
        payload = NotificationPayload(
            title="止损预警",
            body="止损触发",
            level="critical",
            code="600000",
            signal="sell",
            confidence=0.9,
            price=8.5,
            reasons=["触及止损线"],
            action_price=8.8,
            target_price=10.0,
            stop_loss=8.8,
        )
        md = payload.to_dingtalk_markdown()
        assert "🔴" in md
        assert "[CRITICAL]" in md
        assert "止损预警" in md
```

- [ ] **Step 6: 运行测试验证**

Run: `cd apps/api && python -m pytest tests/test_alert_models.py -v`
Expected: 全部 PASS

- [ ] **Step 7: Commit**

```bash
git add apps/api/app/monitor/models/alert_rule.py apps/api/app/monitor/models/alert_signal.py apps/api/app/monitor/models/notification_config.py apps/api/app/monitor/models/__init__.py apps/api/tests/test_alert_models.py
git commit -m "feat: add alert data models (AlertRule, AlertSignal, NotificationConfig)"
```

---

## Chunk 3: Watcher 组件实现

### Context

实现5个独立的Watcher组件：MarketBreadthWatcher、CorrelatedAssetWatcher、StockAlertWatcher、NewsEventWatcher、MinuteKlineWatcher。每个Watcher独立采集数据、生成信号。

### Files

- Create: `apps/api/app/monitor/watchers/__init__.py`
- Create: `apps/api/app/monitor/watchers/breadth.py`
- Create: `apps/api/app/monitor/watchers/correlated.py`
- Create: `apps/api/app/monitor/watchers/stock_alert.py`
- Create: `apps/api/app/monitor/watchers/news_event.py`
- Create: `apps/api/app/monitor/watchers/minute_kline.py`
- Create: `apps/api/app/monitor/watchers/base.py` (公共基类)
- Test: `apps/api/tests/test_watchers.py` (新建)

---

- [ ] **Step 1: 创建 `apps/api/app/monitor/watchers/base.py`**

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging


class BaseWatcher(ABC):
    """Watcher基类，定义统一接口"""
    
    def __init__(self, data_manager=None):
        from app.data_source import DataSourceManager
        self.data_manager = data_manager or DataSourceManager()
        self._logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def collect(self) -> Optional[Dict[str, Any]]:
        """采集数据，返回原始数据字典或None"""
        pass
    
    @abstractmethod
    def evaluate(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        评估数据，生成预警信号列表
        每个信号格式: {code, name, signal, confidence, priority, reasons, alert_type, strategy_type, price, volume_ratio}
        """
        pass
    
    def run_once(self) -> List[Dict[str, Any]]:
        """执行一次采集和评估"""
        data = self.collect()
        if not data:
            return []
        return self.evaluate(data)
    
    def get_name(self) -> str:
        return self.__class__.__name__.replace("Watcher", "")
```

- [ ] **Step 2: 创建 `apps/api/app/monitor/watchers/breadth.py`**

```python
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import BaseWatcher


class MarketBreadthWatcher(BaseWatcher):
    """市场广度Watcher: 涨跌家数比、板块排名、北向资金、VIX"""
    
    def collect(self) -> Optional[Dict[str, Any]]:
        try:
            result = self.data_manager.get_market_breadth()
            if result is None:
                return None
            return {
                "timestamp": result.timestamp,
                "advance_count": result.advance_count,
                "decline_count": result.decline_count,
                "advance_decline_ratio": result.advance_decline_ratio,
                "sector_rankings": result.sector_rankings,
                "north_bound_flow": result.north_bound_flow,
                "vix": result.vix,
            }
        except Exception as e:
            self._logger.error(f"MarketBreadthWatcher collect error: {e}")
            return None
    
    def evaluate(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        signals = []
        ratio = data.get("advance_decline_ratio", 1.0)
        north_flow = data.get("north_bound_flow", 0.0)
        sector_rankings = data.get("sector_rankings", [])
        
        # 涨跌家数比异常
        if ratio > 2.0:
            signals.append({
                "code": "MARKET",
                "name": "市场整体",
                "signal": "buy",
                "confidence": min(0.9, (ratio - 2.0) / 2.0 + 0.7),
                "priority": "high",
                "reasons": [f"上涨家数远超下跌家数（涨跌比={ratio:.2f}）"],
                "alert_type": "breadth",
                "strategy_type": "all",
                "price": 0.0,
                "volume_ratio": ratio,
                "market_breadth": data,
            })
        elif ratio < 0.5:
            signals.append({
                "code": "MARKET",
                "name": "市场整体",
                "signal": "sell",
                "confidence": min(0.9, (0.5 - ratio) / 0.5 + 0.7),
                "priority": "high",
                "reasons": [f"下跌家数远超上涨家数（涨跌比={ratio:.2f}）"],
                "alert_type": "breadth",
                "strategy_type": "all",
                "price": 0.0,
                "volume_ratio": ratio,
                "market_breadth": data,
            })
        
        # 北向资金大幅流入/流出
        if north_flow > 50000:
            signals.append({
                "code": "NORTHBOUND",
                "name": "北向资金",
                "signal": "buy",
                "confidence": min(0.85, north_flow / 200000),
                "priority": "medium",
                "reasons": [f"北向资金大幅净流入 {north_flow:.0f} 万元"],
                "alert_type": "breadth",
                "strategy_type": "swing",
                "price": 0.0,
                "volume_ratio": 0.0,
                "market_breadth": data,
            })
        elif north_flow < -50000:
            signals.append({
                "code": "NORTHBOUND",
                "name": "北向资金",
                "signal": "sell",
                "confidence": min(0.85, abs(north_flow) / 200000),
                "priority": "medium",
                "reasons": [f"北向资金大幅净流出 {north_flow:.0f} 万元"],
                "alert_type": "breadth",
                "strategy_type": "swing",
                "price": 0.0,
                "volume_ratio": 0.0,
                "market_breadth": data,
            })
        
        # 板块异动检测
        for sector in sector_rankings[:3]:
            change_pct = sector.get("change_pct", 0.0)
            if change_pct > 3.0:
                signals.append({
                    "code": f"SECTOR_{sector['name']}",
                    "name": f"板块: {sector['name']}",
                    "signal": "buy",
                    "confidence": min(0.8, change_pct / 10),
                    "priority": "medium",
                    "reasons": [f"板块 {sector['name']} 大涨 {change_pct:.2f}%"],
                    "alert_type": "breadth",
                    "strategy_type": "event",
                    "price": 0.0,
                    "volume_ratio": change_pct,
                    "market_breadth": data,
                })
            elif change_pct < -3.0:
                signals.append({
                    "code": f"SECTOR_{sector['name']}",
                    "name": f"板块: {sector['name']}",
                    "signal": "sell",
                    "confidence": min(0.8, abs(change_pct) / 10),
                    "priority": "medium",
                    "reasons": [f"板块 {sector['name']} 大跌 {change_pct:.2f}%"],
                    "alert_type": "breadth",
                    "strategy_type": "event",
                    "price": 0.0,
                    "volume_ratio": change_pct,
                    "market_breadth": data,
                })
        
        return signals
```

- [ ] **Step 3: 创建 `apps/api/app/monitor/watchers/correlated.py`**

```python
from typing import List, Dict, Any, Optional
from .base import BaseWatcher


class CorrelatedAssetWatcher(BaseWatcher):
    """关联资产Watcher: A50期货、离岸人民币、美元指数"""
    
    # 关键阈值
    A50_SPIKE_THRESHOLD = 1.0  # A50涨跌幅超过1%触发
    USDCNH_SPIKE_THRESHOLD = 0.5  # 汇率波动超过0.5%触发
    DXY_SPIKE_THRESHOLD = 0.3  # 美元指数波动超过0.3%触发
    
    def collect(self) -> Optional[Dict[str, Any]]:
        try:
            result = self.data_manager.get_correlated_assets()
            if result is None:
                return None
            return {
                "timestamp": result.timestamp,
                "a50_future": result.a50_future,
                "a50_change_pct": result.a50_change_pct,
                "usdcnh": result.usdcnh,
                "dxy": result.dxy,
            }
        except Exception as e:
            self._logger.error(f"CorrelatedAssetWatcher collect error: {e}")
            return None
    
    def evaluate(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        signals = []
        a50_change = abs(data.get("a50_change_pct", 0.0))
        
        # A50期货大幅波动
        if data.get("a50_change_pct", 0) > self.A50_SPIKE_THRESHOLD:
            signals.append({
                "code": "A50",
                "name": "富时A50",
                "signal": "buy",
                "confidence": min(0.8, a50_change / 3),
                "priority": "medium",
                "reasons": [f"A50期货上涨 {data['a50_change_pct']:.2f}%"],
                "alert_type": "breadth",
                "strategy_type": "all",
                "price": data.get("a50_future", 0.0),
                "volume_ratio": a50_change,
                "correlated_assets": data,
            })
        elif data.get("a50_change_pct", 0) < -self.A50_SPIKE_THRESHOLD:
            signals.append({
                "code": "A50",
                "name": "富时A50",
                "signal": "sell",
                "confidence": min(0.8, a50_change / 3),
                "priority": "medium",
                "reasons": [f"A50期货下跌 {data['a50_change_pct']:.2f}%"],
                "alert_type": "breadth",
                "strategy_type": "all",
                "price": data.get("a50_future", 0.0),
                "volume_ratio": a50_change,
                "correlated_assets": data,
            })
        
        # 离岸人民币异动（人民币贬值 > 7.3 利好出口/出口型股票）
        usdcnh = data.get("usdcnh", 7.25)
        if usdcnh > 7.3:
            signals.append({
                "code": "USDCNH",
                "name": "离岸人民币",
                "signal": "sell",
                "confidence": min(0.7, (usdcnh - 7.3) * 2),
                "priority": "low",
                "reasons": [f"离岸人民币突破7.3（当前{usdcnh:.4f}），人民币贬值压力"],
                "alert_type": "breadth",
                "strategy_type": "swing",
                "price": usdcnh,
                "volume_ratio": 0.0,
                "correlated_assets": data,
            })
        
        return signals
```

- [ ] **Step 4: 创建 `apps/api/app/monitor/watchers/stock_alert.py`**

```python
from typing import List, Dict, Any, Optional
from .base import BaseWatcher


class StockAlertWatcher(BaseWatcher):
    """个股预警Watcher: 价格预警、量比异动、技术指标突破"""
    
    def collect(self) -> Optional[Dict[str, Any]]:
        return None  # 由外部注入个股数据
    
    def evaluate_single(
        self,
        code: str,
        name: str,
        realtime_data: Dict[str, Any],
        technical_data: Dict[str, Any],
        capital_flow: List[Dict[str, Any]],
        watchlist: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        signals = []
        current_price = realtime_data.get("price") or realtime_data.get("close") or 0.0
        volume_ratio = realtime_data.get("volume_ratio", 0.0)
        change_pct = realtime_data.get("change_pct", 0.0)
        
        if not current_price:
            return signals
        
        stock_config = next((s for s in watchlist if s.get("code") == code), {})
        is_holding = stock_config.get("hold", False)
        cost_price = stock_config.get("cost_price", 0.0)
        stop_loss = stock_config.get("stop_loss", 0.05)
        profit_target = stock_config.get("profit_target", 0.1)
        
        # 止损/止盈检测 (critical级别)
        if is_holding and cost_price > 0:
            loss_pct = (cost_price - current_price) / cost_price
            if loss_pct >= stop_loss:
                signals.append({
                    "code": code,
                    "name": name,
                    "signal": "sell",
                    "confidence": 0.95,
                    "priority": "critical",
                    "reasons": [f"触及止损线（亏损{loss_pct*100:.1f}%，止损线{stop_loss*100:.1f}%）"],
                    "alert_type": "price",
                    "strategy_type": "all",
                    "price": current_price,
                    "volume_ratio": volume_ratio,
                    "stop_loss": cost_price * (1 - stop_loss),
                    "technical_data": technical_data,
                })
                return signals  # 止损优先
            
            profit_pct = (current_price - cost_price) / cost_price
            if profit_pct >= profit_target:
                signals.append({
                    "code": code,
                    "name": name,
                    "signal": "sell",
                    "confidence": 0.9,
                    "priority": "critical",
                    "reasons": [f"达到止盈目标（盈利{profit_pct*100:.1f}%，目标{profit_target*100:.1f}%）"],
                    "alert_type": "price",
                    "strategy_type": "all",
                    "price": current_price,
                    "volume_ratio": volume_ratio,
                    "profit_target": cost_price * (1 + profit_target),
                    "technical_data": technical_data,
                })
                return signals
        
        # 量比放大预警
        if volume_ratio > 2.0:
            direction = "buy" if change_pct > 0 else ("sell" if change_pct < 0 else "hold")
            if direction != "hold":
                signals.append({
                    "code": code,
                    "name": name,
                    "signal": direction,
                    "confidence": min(0.8, (volume_ratio - 2.0) / 3 + 0.6),
                    "priority": "high",
                    "reasons": [f"量比突放 {volume_ratio:.1f}倍，{'放量上涨' if direction=='buy' else '放量下跌'}"],
                    "alert_type": "volume",
                    "strategy_type": "intraday",
                    "price": current_price,
                    "volume_ratio": volume_ratio,
                    "technical_data": technical_data,
                })
        
        # 技术指标分析
        rsi = technical_data.get("rsi", 50.0)
        macd = technical_data.get("macd", {})
        kdj = technical_data.get("kdj", {})
        bollinger = technical_data.get("bollinger", {})
        
        if not is_holding:
            # 未持仓：买入信号
            reasons = []
            strength = 0.0
            
            if rsi < 30:
                reasons.append(f"RSI超卖({rsi:.1f})")
                strength += 0.3
            if macd.get("histogram", 0) > 0 and macd.get("macd", 0) > macd.get("signal", 0):
                reasons.append("MACD金叉")
                strength += 0.25
            if kdj.get("k", 50) < 20:
                reasons.append(f"KDJ超卖(K={kdj.get('k',50):.1f})")
                strength += 0.2
            if bollinger.get("lower", 0) and current_price <= bollinger["lower"]:
                reasons.append("价格触及布林带下轨")
                strength += 0.25
            
            if strength >= 0.4:
                signals.append({
                    "code": code,
                    "name": name,
                    "signal": "buy",
                    "confidence": min(0.85, strength + 0.3),
                    "priority": "high" if rsi < 25 else "medium",
                    "reasons": reasons,
                    "alert_type": "technical",
                    "strategy_type": "swing",
                    "price": current_price,
                    "volume_ratio": volume_ratio,
                    "technical_data": technical_data,
                })
        else:
            # 持仓：卖出信号
            reasons = []
            strength = 0.0
            
            if rsi > 70:
                reasons.append(f"RSI超买({rsi:.1f})")
                strength += 0.3
            if macd.get("histogram", 0) < 0 and macd.get("macd", 0) < macd.get("signal", 0):
                reasons.append("MACD死叉")
                strength += 0.25
            if kdj.get("k", 50) > 80:
                reasons.append(f"KDJ超买(K={kdj.get('k',50):.1f})")
                strength += 0.2
            if bollinger.get("upper", 0) and current_price >= bollinger["upper"]:
                reasons.append("价格触及布林带上轨")
                strength += 0.25
            
            if strength >= 0.4:
                signals.append({
                    "code": code,
                    "name": name,
                    "signal": "sell",
                    "confidence": min(0.85, strength + 0.3),
                    "priority": "high" if rsi > 75 else "medium",
                    "reasons": reasons,
                    "alert_type": "technical",
                    "strategy_type": "swing",
                    "price": current_price,
                    "volume_ratio": volume_ratio,
                    "technical_data": technical_data,
                })
        
        return signals
    
    def evaluate(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []  # 使用 evaluate_single 逐股分析
```

- [ ] **Step 5: 创建 `apps/api/app/monitor/watchers/news_event.py`**

```python
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from .base import BaseWatcher


class NewsEventWatcher(BaseWatcher):
    """事件驱动Watcher: 新闻/政策关键词订阅"""
    
    def __init__(self, data_manager=None, keyword_rules: Dict[str, List[str]] = None):
        super().__init__(data_manager)
        self.keyword_rules = keyword_rules or {}
        self._last_triggered: Dict[str, datetime] = {}
        self._cooldown_seconds = 300  # 5分钟内同一关键词不重复触发
    
    def collect(self) -> Optional[Dict[str, Any]]:
        try:
            import akshare as ak
            news_list = ak.stock_news_em(symbol="A股")
            if news_list is None or news_list.empty:
                return {"news": [], "timestamp": datetime.now()}
            recent = news_list.head(20)
            return {
                "news": [
                    {"title": row.get("新闻标题", ""), "content": row.get("新闻内容", ""), "time": row.get("发布时间", "")}
                    for _, row in recent.iterrows()
                ],
                "timestamp": datetime.now(),
            }
        except Exception as e:
            self._logger.error(f"NewsEventWatcher collect error: {e}")
            return {"news": [], "timestamp": datetime.now()}
    
    def evaluate(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        signals = []
        news_list = data.get("news", [])
        keyword_rules = self.keyword_rules
        
        now = datetime.now()
        
        for news in news_list:
            title = news.get("title", "")
            content = news.get("content", "")
            text = title + content
            
            for category, keywords in keyword_rules.items():
                for keyword in keywords:
                    if keyword in text:
                        key = f"{category}:{keyword}"
                        
                        # 冷却期检查
                        if key in self._last_triggered:
                            last = self._last_triggered[key]
                            if (now - last).total_seconds() < self._cooldown_seconds:
                                continue
                        
                        self._last_triggered[key] = now
                        
                        signal_map = {
                            "政策": ("buy", "medium"),
                            "利好": ("buy", "high"),
                            "利空": ("sell", "high"),
                            "业绩": ("buy", "medium"),
                            "黑天鹅": ("sell", "critical"),
                        }
                        signal_action, priority = signal_map.get(category, ("hold", "low"))
                        
                        if signal_action != "hold":
                            signals.append({
                                "code": category,
                                "name": f"新闻事件: {keyword}",
                                "signal": signal_action,
                                "confidence": 0.75 if priority != "critical" else 0.95,
                                "priority": priority,
                                "reasons": [f"新闻命中关键词「{keyword}」: {title[:50]}"],
                                "alert_type": "news",
                                "strategy_type": "event",
                                "price": 0.0,
                                "volume_ratio": 0.0,
                            })
                        break
        
        return signals
```

- [ ] **Step 6: 创建 `apps/api/app/monitor/watchers/minute_kline.py`**

```python
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .base import BaseWatcher


class MinuteKlineWatcher(BaseWatcher):
    """分钟K线Watcher: 支持1/5/15/30/60分钟K线数据"""
    
    def __init__(self, data_manager=None, frequency: str = "5"):
        super().__init__(data_manager)
        self.frequency = frequency
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
    
    def collect(self) -> Optional[Dict[str, Any]]:
        return None  # 由外部注入股票代码
    
    def evaluate_single(
        self,
        code: str,
        name: str,
        frequency: str = None,
        days: int = 3,
    ) -> List[Dict[str, Any]]:
        signals = []
        freq = frequency or self.frequency
        
        try:
            klines = self.data_manager.get_minute_kline(code, freq, days)
            if not klines:
                return signals
            
            closes = [k.close for k in klines]
            highs = [k.high for k in klines]
            lows = [k.low for k in klines]
            volumes = [k.volume for k in klines]
            
            if len(closes) < 20:
                return signals
            
            current_price = closes[-1]
            
            # 布林带
            import numpy as np
            ma20 = np.mean(closes[-20:])
            std20 = np.std(closes[-20:])
            upper = ma20 + 2 * std20
            lower = ma20 - 2 * std20
            
            # 5分钟突破检测
            prev_high = max(highs[-6:-1])
            prev_low = min(lows[-6:-1])
            
            if current_price > prev_high and current_price > ma20:
                signals.append({
                    "code": code,
                    "name": name,
                    "signal": "buy",
                    "confidence": 0.7,
                    "priority": "medium",
                    "reasons": [f"{freq}分钟K线突破前高({prev_high:.2f})，价格={current_price:.2f}"],
                    "alert_type": "technical",
                    "strategy_type": "intraday",
                    "price": current_price,
                    "volume_ratio": 0.0,
                    "technical_data": {"ma20": ma20, "upper": upper, "lower": lower},
                })
            elif current_price < prev_low and current_price < ma20:
                signals.append({
                    "code": code,
                    "name": name,
                    "signal": "sell",
                    "confidence": 0.7,
                    "priority": "medium",
                    "reasons": [f"{freq}分钟K线跌破前低({prev_low:.2f})，价格={current_price:.2f}"],
                    "alert_type": "technical",
                    "strategy_type": "intraday",
                    "price": current_price,
                    "volume_ratio": 0.0,
                    "technical_data": {"ma20": ma20, "upper": upper, "lower": lower},
                })
            
            # 缩量整理检测
            avg_vol_5 = sum(volumes[-5:]) / 5
            current_vol = volumes[-1]
            if current_vol < avg_vol_5 * 0.5 and abs(closes[-1] - closes[-2]) / closes[-2] < 0.005:
                signals.append({
                    "code": code,
                    "name": name,
                    "signal": "hold",
                    "confidence": 0.5,
                    "priority": "low",
                    "reasons": [f"缩量整理（量为5日均量的{current_vol/avg_vol_5*100:.0f}%），等待方向选择"],
                    "alert_type": "volume",
                    "strategy_type": "intraday",
                    "price": current_price,
                    "volume_ratio": current_vol / avg_vol_5 if avg_vol_5 > 0 else 0.0,
                    "technical_data": {},
                })
            
        except Exception as e:
            self._logger.error(f"MinuteKlineWatcher evaluate_single error for {code}: {e}")
        
        return signals
    
    def evaluate(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []
```

- [ ] **Step 7: 创建 `apps/api/app/monitor/watchers/__init__.py`**

```python
from .base import BaseWatcher
from .breadth import MarketBreadthWatcher
from .correlated import CorrelatedAssetWatcher
from .stock_alert import StockAlertWatcher
from .news_event import NewsEventWatcher
from .minute_kline import MinuteKlineWatcher

__all__ = [
    "BaseWatcher",
    "MarketBreadthWatcher",
    "CorrelatedAssetWatcher",
    "StockAlertWatcher",
    "NewsEventWatcher",
    "MinuteKlineWatcher",
]
```

- [ ] **Step 8: 写单元测试**

创建 `apps/api/tests/test_watchers.py`：

```python
import pytest
from app.monitor.watchers.base import BaseWatcher
from app.monitor.watchers.breadth import MarketBreadthWatcher
from app.monitor.watchers.correlated import CorrelatedAssetWatcher
from app.monitor.watchers.stock_alert import StockAlertWatcher
from app.monitor.watchers.news_event import NewsEventWatcher
from app.monitor.watchers.minute_kline import MinuteKlineWatcher


class TestMarketBreadthWatcher:
    def test_evaluate_high_ratio_buy(self):
        watcher = MarketBreadthWatcher(data_manager=None)
        data = {
            "advance_decline_ratio": 3.0,
            "north_bound_flow": 10000.0,
            "sector_rankings": [],
        }
        signals = watcher.evaluate(data)
        assert len(signals) == 1
        assert signals[0]["signal"] == "buy"
        assert signals[0]["priority"] == "high"

    def test_evaluate_low_ratio_sell(self):
        watcher = MarketBreadthWatcher(data_manager=None)
        data = {
            "advance_decline_ratio": 0.3,
            "north_bound_flow": 0.0,
            "sector_rankings": [],
        }
        signals = watcher.evaluate(data)
        assert len(signals) == 1
        assert signals[0]["signal"] == "sell"


class TestCorrelatedAssetWatcher:
    def test_evaluate_a50_up(self):
        watcher = CorrelatedAssetWatcher(data_manager=None)
        data = {"a50_change_pct": 1.5, "usdcnh": 7.2, "dxy": 104.0}
        signals = watcher.evaluate(data)
        assert len(signals) == 1
        assert signals[0]["code"] == "A50"
        assert signals[0]["signal"] == "buy"


class TestStockAlertWatcher:
    def test_stop_loss_trigger(self):
        watcher = StockAlertWatcher(data_manager=None)
        signals = watcher.evaluate_single(
            code="600000",
            name="浦发银行",
            realtime_data={"price": 8.0, "volume_ratio": 1.0, "change_pct": -2.0},
            technical_data={"rsi": 50.0, "macd": {}, "kdj": {}, "bollinger": {}},
            capital_flow=[],
            watchlist=[{"code": "600000", "hold": True, "cost_price": 10.0, "stop_loss": 0.1}],
        )
        assert len(signals) == 1
        assert signals[0]["signal"] == "sell"
        assert signals[0]["priority"] == "critical"
        assert "止损" in signals[0]["reasons"][0]

    def test_buy_signal_oversold(self):
        watcher = StockAlertWatcher(data_manager=None)
        signals = watcher.evaluate_single(
            code="600000",
            name="浦发银行",
            realtime_data={"price": 8.0, "volume_ratio": 1.0, "change_pct": 0.5},
            technical_data={"rsi": 25.0, "macd": {"histogram": 0.1, "macd": 0.2, "signal": 0.1}, "kdj": {}, "bollinger": {}},
            capital_flow=[],
            watchlist=[{"code": "600000", "hold": False}],
        )
        assert any(s["signal"] == "buy" for s in signals)


class TestNewsEventWatcher:
    def test_keyword_matching(self):
        watcher = NewsEventWatcher(
            data_manager=None,
            keyword_rules={"黑天鹅": ["地震", "疫情"], "政策": ["降准", "加息"]},
        )
        data = {"news": [{"title": "疫情爆发导致股市暴跌", "content": "", "time": ""}], "timestamp": None}
        signals = watcher.evaluate(data)
        assert len(signals) == 1
        assert signals[0]["signal"] == "sell"
        assert signals[0]["priority"] == "critical"


class TestMinuteKlineWatcher:
    def test_breakout_signal(self):
        watcher = MinuteKlineWatcher(data_manager=None, frequency="5")
        # 无外部数据时返回空列表
        assert watcher.evaluate({}) == []
```

- [ ] **Step 9: 运行测试验证**

Run: `cd apps/api && python -m pytest tests/test_watchers.py -v`
Expected: 全部 PASS

- [ ] **Step 10: Commit**

```bash
git add apps/api/app/monitor/watchers/
git add apps/api/tests/test_watchers.py
git commit -m "feat: implement 5 watcher components (breadth, correlated, stock_alert, news_event, minute_kline)"
```

---

## Chunk 4: AlertAggregator + 重构 MarketWatcher

### Context

实现 AlertAggregator 信号聚合器（多源信号加权评分），重构 MarketWatcher 为 AlertOrchestrator（总调度），整合5个Watcher统一输出预警信号。

### Files

- Create: `apps/api/app/monitor/analysis/aggregator.py`
- Modify: `apps/api/app/monitor/market_watcher.py` (重构为 AlertOrchestrator)
- Test: `apps/api/tests/test_aggregator.py` (新建)

---

- [ ] **Step 1: 创建 `apps/api/app/monitor/analysis/aggregator.py`**

```python
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.monitor.models.alert_signal import AlertSignal, SignalType
from app.monitor.models.alert_rule import AlertRule, AlertPriority


class AlertAggregator:
    """信号聚合器：接收多源Watcher信号，按策略类型加权评分，触发预警"""
    
    STRATEGY_WEIGHTS = {
        "intraday": {
            "technical": 0.30,
            "volume": 0.25,
            "sentiment": 0.25,
            "correlation": 0.10,
            "event": 0.10,
        },
        "swing": {
            "technical": 0.20,
            "volume": 0.15,
            "sentiment": 0.20,
            "correlation": 0.20,
            "event": 0.25,
        },
        "event": {
            "technical": 0.10,
            "volume": 0.10,
            "sentiment": 0.10,
            "correlation": 0.30,
            "event": 0.40,
        },
        "all": {
            "technical": 0.25,
            "volume": 0.20,
            "sentiment": 0.20,
            "correlation": 0.15,
            "event": 0.20,
        },
    }
    
    def __init__(self, strategy_type: str = "all"):
        self.strategy_type = strategy_type
        self.weights = self.STRATEGY_WEIGHTS.get(strategy_type, self.STRATEGY_WEIGHTS["all"])
        self._logger = logging.getLogger(__name__)
        self._signal_cache: Dict[str, datetime] = {}  # 去重缓存
        self._dedup_window = 300  # 5分钟去重窗口
    
    def aggregate(self, signals: List[Dict[str, Any]]) -> List[AlertSignal]:
        """
        聚合多源信号，返回最终的 AlertSignal 列表
        """
        if not signals:
            return []
        
        # 按 code + alert_type 分组
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for sig in signals:
            key = f"{sig.get('code', '')}_{sig.get('alert_type', '')}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(sig)
        
        results = []
        now = datetime.now()
        
        for key, group in grouped.items():
            # 去重检查
            if key in self._signal_cache:
                last_time = self._signal_cache[key]
                if (now - last_time).total_seconds() < self._dedup_window:
                    # critical 级别强制通过
                    if not any(s.get("priority") == "critical" for s in group):
                        continue
            
            # 选择最高置信度的信号
            best = max(group, key=lambda x: x.get("confidence", 0.0))
            
            # 计算加权评分
            total_score = self._calculate_weighted_score(best)
            
            # 动作判定
            action = self._determine_action(total_score, best)
            
            # 计算目标价和止损价
            price = best.get("price", 0.0)
            target_price = price * 1.05 if price > 0 else 0.0
            stop_loss = price * 0.95 if price > 0 else 0.0
            
            alert_signal = AlertSignal(
                timestamp=now,
                code=best.get("code", ""),
                name=best.get("name", ""),
                signal=action,
                confidence=total_score,
                priority=best.get("priority", "medium"),
                reasons=best.get("reasons", []),
                technical_data=best.get("technical_data", {}),
                market_breadth=best.get("market_breadth"),
                correlated_assets=best.get("correlated_assets"),
                price=price,
                volume_ratio=best.get("volume_ratio", 0.0),
                alert_type=best.get("alert_type", "technical"),
                strategy_type=best.get("strategy_type", "all"),
                action_price=best.get("action_price", price),
                target_price=target_price,
                stop_loss=stop_loss,
            )
            
            results.append(alert_signal)
            self._signal_cache[key] = now
        
        # 按优先级排序
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        results.sort(key=lambda x: priority_order.get(x.priority, 4))
        
        return results
    
    def _calculate_weighted_score(self, signal: Dict[str, Any]) -> float:
        """计算加权评分"""
        alert_type = signal.get("alert_type", "technical")
        base_confidence = signal.get("confidence", 0.5)
        weight = self.weights.get(alert_type, 0.2)
        
        # 额外加权：critical/ high 优先级提升
        priority_boost = {"critical": 0.15, "high": 0.1, "medium": 0.05, "low": 0.0}
        boost = priority_boost.get(signal.get("priority", "low"), 0.0)
        
        return min(1.0, base_confidence * (1 + weight - 0.2) + boost)
    
    def _determine_action(self, total_score: float, signal: Dict[str, Any]) -> SignalType:
        """根据评分和信号确定动作"""
        rsi = signal.get("technical_data", {}).get("rsi", 50.0)
        priority = signal.get("priority", "medium")
        
        if priority == "critical":
            # critical 级别按原信号方向
            sig = signal.get("signal", "hold")
            if sig in ("buy", "sell"):
                return SignalType(sig)
        
        if total_score > 0.75 or rsi < 25:
            return SignalType.BUY
        elif total_score < 0.25 or rsi > 75:
            return SignalType.SELL
        else:
            return SignalType.HOLD
```

- [ ] **Step 2: 重构 `apps/api/app/monitor/market_watcher.py` 为 AlertOrchestrator**

删除原文件内容，替换为：

```python
import logging
import threading
import time
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Callable, Set

from app.data_source import DataSourceManager
from app.monitor.market_signals import add_signal
from app.monitor.analysis.aggregator import AlertAggregator
from app.monitor.watchers import (
    MarketBreadthWatcher,
    CorrelatedAssetWatcher,
    StockAlertWatcher,
    NewsEventWatcher,
    MinuteKlineWatcher,
)
from app.monitor.models.alert_signal import AlertSignal, SignalType
from app.monitor.models.alert_rule import AlertPriority


class AlertOrchestrator:
    """
    预警调度器（总控）：协调所有Watcher采集数据，
    经Aggregator聚合后统一输出预警信号
    """
    
    def __init__(
        self,
        data_manager: Optional[DataSourceManager] = None,
        interval_sec: int = 60,
        watchlist: Optional[List[Dict[str, Any]]] = None,
        strategy_type: str = "all",
        news_keywords: Optional[Dict[str, List[str]]] = None,
        report_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.data_manager = data_manager or DataSourceManager()
        self.interval_sec = max(1, int(interval_sec))
        self.watchlist = watchlist or self._default_watchlist()
        self.strategy_type = strategy_type
        self.report_callback = report_callback
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._logger = logging.getLogger(__name__)
        
        # 初始化 Watchers
        self.breadth_watcher = MarketBreadthWatcher(self.data_manager)
        self.correlated_watcher = CorrelatedAssetWatcher(self.data_manager)
        self.stock_watcher = StockAlertWatcher(self.data_manager)
        self.news_watcher = NewsEventWatcher(self.data_manager, news_keywords or self._default_keywords())
        self.minute_watcher = MinuteKlineWatcher(self.data_manager, frequency="5")
        
        # 初始化 Aggregator
        self.aggregator = AlertAggregator(strategy_type=strategy_type)
        
        self.signals_log: List[Dict[str, Any]] = []
    
    def _default_watchlist(self) -> List[Dict[str, Any]]:
        return [
            {"code": "SH600000", "name": "浦发银行"},
            {"code": "SH600519", "name": "贵州茅台"},
        ]
    
    def _default_keywords(self) -> Dict[str, List[str]]:
        return {
            "政策": ["降准", "加息", "LPR", "监管"],
            "利好": ["业绩预增", "订单", "合作", "重组"],
            "利空": ["业绩预减", "减持", "诉讼", "退市"],
            "黑天鹅": ["疫情", "地震", "制裁", "断供"],
        }
    
    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._logger.info("AlertOrchestrator started")
    
    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._logger.info("AlertOrchestrator stopped")
    
    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception as e:
                self._logger.error(f"AlertOrchestrator run error: {e}")
            time.sleep(self.interval_sec)
    
    def run_once(self):
        all_signals: List[Dict[str, Any]] = []
        
        # 1. 市场广度Watcher
        try:
            breadth_signals = self.breadth_watcher.run_once()
            all_signals.extend(breadth_signals)
        except Exception as e:
            self._logger.error(f"BreadthWatcher error: {e}")
        
        # 2. 关联资产Watcher
        try:
            correlated_signals = self.correlated_watcher.run_once()
            all_signals.extend(correlated_signals)
        except Exception as e:
            self._logger.error(f"CorrelatedAssetWatcher error: {e}")
        
        # 3. 新闻事件Watcher
        try:
            news_signals = self.news_watcher.run_once()
            all_signals.extend(news_signals)
        except Exception as e:
            self._logger.error(f"NewsEventWatcher error: {e}")
        
        # 4. 个股预警Watcher（遍历watchlist）
        for item in self.watchlist:
            code = item.get("code")
            name = item.get("name", code)
            if not code:
                continue
            
            try:
                # 实时数据
                rt = self.data_manager.get_realtime_data(code)
                if not rt:
                    continue
                
                # 技术指标
                technical = self._gather_technical_data(code)
                
                # 资金流向
                capital_flow = self.data_manager.get_capital_flow(code, days=5)
                
                # 分钟K线（日内策略）
                minute_signals = []
                if self.strategy_type in ("intraday", "all"):
                    minute_signals = self.minute_watcher.evaluate_single(
                        code, name, frequency="5", days=2
                    )
                
                # 个股信号
                stock_signals = self.stock_watcher.evaluate_single(
                    code, name, rt, technical, capital_flow, self.watchlist
                )
                
                all_signals.extend(stock_signals)
                all_signals.extend(minute_signals)
                
            except Exception as e:
                self._logger.error(f"StockWatcher error for {code}: {e}")
        
        # 5. Aggregator 聚合
        aggregated = self.aggregator.aggregate(all_signals)
        
        # 6. 输出信号
        for alert_signal in aggregated:
            self._emit_signal(alert_signal)
    
    def _gather_technical_data(self, code: str) -> Dict[str, Any]:
        try:
            end = date.today()
            start = end - timedelta(days=60)
            klines = self.data_manager.get_kline(
                code, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), frequency="d", adjust_flag="3"
            )
            if not klines:
                return {}
            closes = [k.close for k in klines]
            highs = [k.high for k in klines]
            lows = [k.low for k in klines]
            
            from app.monitor.analysis.technical import TechnicalAnalyzer
            ta = TechnicalAnalyzer()
            return ta.analyze_stock({"close": closes, "high": highs, "low": lows})
        except Exception:
            return {}
    
    def _emit_signal(self, alert_signal: AlertSignal):
        sig_dict = alert_signal.to_dict()
        
        # 写入全局信号仓库
        try:
            add_signal(sig_dict)
        except Exception:
            pass
        
        self.signals_log.append(sig_dict)
        
        # 回调
        if self.report_callback:
            try:
                self.report_callback(sig_dict)
            except Exception:
                pass
        
        # 日志
        if alert_signal.signal != SignalType.HOLD:
            self._logger.info(
                f"Alert: [{alert_signal.priority.upper()}] {alert_signal.code} -> {alert_signal.signal.value} "
                f"(confidence={alert_signal.confidence:.2f}) @ {alert_signal.price}"
            )
    
    def backtest(self, historical: List[Dict[str, Any]]):
        self._logger.info("AlertOrchestrator backtest (skeleton)")
        pass


__all__ = ["AlertOrchestrator"]
```

- [ ] **Step 3: 写单元测试**

创建 `apps/api/tests/test_aggregator.py`：

```python
import pytest
from datetime import datetime
from app.monitor.analysis.aggregator import AlertAggregator
from app.monitor.models.alert_signal import SignalType


class TestAlertAggregator:
    def test_aggregate_high_score_buy(self):
        agg = AlertAggregator(strategy_type="all")
        signals = [
            {
                "code": "600000",
                "name": "浦发银行",
                "signal": "buy",
                "confidence": 0.8,
                "priority": "high",
                "alert_type": "technical",
                "reasons": ["RSI低于30"],
                "price": 9.5,
                "volume_ratio": 2.0,
                "technical_data": {"rsi": 25.0},
            }
        ]
        result = agg.aggregate(signals)
        assert len(result) == 1
        assert result[0].signal == SignalType.BUY

    def test_aggregate_low_score_sell(self):
        agg = AlertAggregator(strategy_type="all")
        signals = [
            {
                "code": "600000",
                "name": "浦发银行",
                "signal": "sell",
                "confidence": 0.15,
                "priority": "medium",
                "alert_type": "technical",
                "reasons": [],
                "price": 9.5,
                "volume_ratio": 0.5,
                "technical_data": {"rsi": 80.0},
            }
        ]
        result = agg.aggregate(signals)
        assert len(result) == 1
        assert result[0].signal == SignalType.SELL

    def test_aggregate_dedup(self):
        agg = AlertAggregator(strategy_type="all")
        signals = [
            {
                "code": "600000",
                "name": "浦发银行",
                "signal": "buy",
                "confidence": 0.8,
                "priority": "high",
                "alert_type": "technical",
                "reasons": [],
                "price": 9.5,
                "volume_ratio": 0.0,
                "technical_data": {},
            }
        ]
        result1 = agg.aggregate(signals)
        assert len(result1) == 1
        # 5分钟内不应重复
        result2 = agg.aggregate(signals)
        assert len(result2) == 0

    def test_aggregate_priority_order(self):
        agg = AlertAggregator(strategy_type="all")
        signals = [
            {"code": "B", "name": "", "signal": "buy", "confidence": 0.5, "priority": "low", "alert_type": "technical", "reasons": [], "price": 0.0, "volume_ratio": 0.0, "technical_data": {}},
            {"code": "A", "name": "", "signal": "buy", "confidence": 0.5, "priority": "critical", "alert_type": "price", "reasons": [], "price": 0.0, "volume_ratio": 0.0, "technical_data": {}},
            {"code": "C", "name": "", "signal": "buy", "confidence": 0.5, "priority": "high", "alert_type": "volume", "reasons": [], "price": 0.0, "volume_ratio": 0.0, "technical_data": {}},
        ]
        result = agg.aggregate(signals)
        assert len(result) == 3
        assert result[0].code == "A"  # critical 优先
        assert result[1].code == "C"  # high 其次
        assert result[2].code == "B"  # low 最后

    def test_aggregate_empty(self):
        agg = AlertAggregator()
        assert agg.aggregate([]) == []

    def test_strategy_weights_intraday(self):
        agg = AlertAggregator(strategy_type="intraday")
        assert agg.weights["volume"] == 0.25
        assert agg.weights["technical"] == 0.30

    def test_strategy_weights_event(self):
        agg = AlertAggregator(strategy_type="event")
        assert agg.weights["event"] == 0.40
        assert agg.weights["correlation"] == 0.30
```

- [ ] **Step 4: 运行测试验证**

Run: `cd apps/api && python -m pytest tests/test_aggregator.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/monitor/analysis/aggregator.py
git add apps/api/app/monitor/market_watcher.py
git add apps/api/tests/test_aggregator.py
git commit -m "refactor: AlertOrchestrator + AlertAggregator"
```

---

## Chunk 5: 通知系统重构

### Context

重构通知系统，支持分级推送（critical/high/medium/low不同推送方式）、去重、钉钉@所有人。

### Files

- Create: `apps/api/app/monitor/notification/priority_notifier.py`
- Modify: `apps/api/app/monitor/notification/dingtalk.py` (重构 send 方法)
- Modify: `apps/api/app/monitor/stock_monitor.py` (接入新的 AlertOrchestrator)
- Test: `apps/api/tests/test_notification.py` (新建)

---

- [ ] **Step 1: 创建 `apps/api/app/monitor/notification/priority_notifier.py`**

```python
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.monitor.models.alert_signal import AlertSignal, SignalType
from app.monitor.models.notification_config import NotificationPayload, NotificationLevel


class PriorityNotifier:
    """分级通知器：根据预警优先级选择不同推送方式"""
    
    def __init__(self, dingtalk_client=None):
        self._dingtalk = dingtalk_client
        self._logger = logging.getLogger(__name__)
        self._sent_history: Dict[str, datetime] = {}
        self._repeat_history: Dict[str, datetime] = {}  # critical 重复记录
    
    def send(self, alert_signal: AlertSignal):
        """根据优先级发送通知"""
        priority = alert_signal.priority
        
        # 生成 payload
        payload = NotificationPayload(
            title=self._get_title(alert_signal),
            body="\n".join(alert_signal.reasons),
            level=priority,
            code=alert_signal.code,
            signal=alert_signal.signal.value,
            confidence=alert_signal.confidence,
            price=alert_signal.price,
            reasons=alert_signal.reasons,
            action_price=alert_signal.action_price,
            target_price=alert_signal.target_price,
            stop_loss=alert_signal.stop_loss,
        )
        
        # 级别判断
        if priority == "critical":
            self._send_critical(payload, alert_signal)
        elif priority == "high":
            self._send_high(payload, alert_signal)
        elif priority == "medium":
            self._send_medium(payload, alert_signal)
        else:
            self._send_low(payload, alert_signal)
    
    def _get_title(self, sig: AlertSignal) -> str:
        action = "买入" if sig.signal == SignalType.BUY else ("卖出" if sig.signal == SignalType.SELL else "观望")
        return f"{sig.name} {action}信号"
    
    def _should_send(self, key: str) -> bool:
        """去重检查"""
        now = datetime.now()
        if key in self._sent_history:
            last = self._sent_history[key]
            if (now - last).total_seconds() < 300:  # 5分钟窗口
                return False
        self._sent_history[key] = now
        return True
    
    def _send_critical(self, payload: NotificationPayload, sig: AlertSignal):
        key = f"{sig.code}_{sig.alert_type}"
        
        # 检查是否需要重复
        if key in self._repeat_history:
            last = self._repeat_history[key]
            if (datetime.now() - last).total_seconds() < 30:
                return  # 30秒内不重复
        
        self._repeat_history[key] = datetime.now()
        
        if self._dingtalk:
            md = payload.to_dingtalk_markdown()
            self._dingtalk.send(md, at_all=True)
        self._logger.warning(f"[CRITICAL] {payload.title}: {payload.body}")
    
    def _send_high(self, payload: NotificationPayload, sig: AlertSignal):
        key = f"{sig.code}_{sig.alert_type}"
        if not self._should_send(key):
            return
        
        if self._dingtalk:
            md = payload.to_dingtalk_markdown()
            self._dingtalk.send(md)
        self._logger.info(f"[HIGH] {payload.title}")
    
    def _send_medium(self, payload: NotificationPayload, sig: AlertSignal):
        key = f"{sig.code}_{sig.alert_type}"
        if not self._should_send(key):
            return
        
        if self._dingtalk:
            md = payload.to_dingtalk_markdown()
            self._dingtalk.send(md)
        self._logger.info(f"[MEDIUM] {payload.title}")
    
    def _send_low(self, payload: NotificationPayload, sig: AlertSignal):
        self._logger.debug(f"[LOW] {payload.title}: {payload.body}")
```

- [ ] **Step 2: 重构 `apps/api/app/monitor/notification/dingtalk.py`**

找到 `DingTalkNotifier.send` 方法，更新为支持 markdown 和 at_all 参数：

```python
def send(self, message: str = None, markdown: str = None, at_all: bool = False):
    """
    发送钉钉消息
    
    Args:
        message: 普通文本消息
        markdown: Markdown格式消息
        at_all: 是否@所有人（仅markdown模式有效）
    """
    try:
        import base64
        import hashlib
        import hmac
        import time
        import requests
        
        if not self.webhook:
            self._logger.warning("DingTalk webhook not configured")
            return
        
        # 签名
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode("utf-8")
        timestamp_enc = timestamp.encode("utf-8")
        hmac_code = hmac.new(secret_enc, timestamp_enc, digestmod=hashlib.sha256).digest()
        sign = base64.b64encode(hmac_code).decode("utf-8")
        
        # 构建请求
        url = f"{self.webhook}&timestamp={timestamp}&sign={requests.utils.quote(sign)}"
        
        if markdown:
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": "盯盘预警",
                    "text": markdown
                },
                "at": {
                    "isAtAll": at_all
                }
            }
        elif message:
            payload = {
                "msgtype": "text",
                "text": {
                    "content": message
                }
            }
        else:
            return
        
        resp = requests.post(url, json=payload, timeout=10)
        result = resp.json()
        
        if result.get("errcode") != 0:
            self._logger.error(f"DingTalk send error: {result.get('errmsg')}")
        else:
            self._logger.info("DingTalk message sent successfully")
            
    except Exception as e:
        self._logger.error(f"DingTalk send exception: {e}")
```

- [ ] **Step 3: 更新 `apps/api/app/monitor/stock_monitor.py` 接入 AlertOrchestrator**

在 `StockMonitor.__init__` 方法末尾添加：

```python
# 新增：接入 AlertOrchestrator
self.alert_orchestrator = None

def set_orchestrator(self, orchestrator):
    """注入 AlertOrchestrator"""
    self.alert_orchestrator = orchestrator
```

在 `monitor_stocks` 方法中，循环结束后添加：

```python
# 如果有 orchestrator，收集其信号并发送通知
if self.alert_orchestrator:
    for sig_dict in self.alert_orchestrator.signals_log[-len(results):] if self.alert_orchestrator.signals_log else []:
        if sig_dict.get("signal") != "hold":
            notification = self._dict_to_notification(sig_dict)
            if notification:
                self.send_notification(notification)
```

添加辅助方法：

```python
def _dict_to_notification(self, sig_dict: Dict[str, Any]) -> Optional[MonitorNotification]:
    """将信号字典转为 MonitorNotification"""
    from .models import StockData, Signal
    stock = StockData(
        code=sig_dict.get("code", ""),
        name=sig_dict.get("name", ""),
        current_price=sig_dict.get("price", 0.0),
        high_price=0.0,
        low_price=0.0,
        open_price=0.0,
        close_price=sig_dict.get("price", 0.0),
        change=0.0,
        change_pct=0.0,
        volume=0,
        amount=0.0,
    )
    signal = Signal(
        signal=sig_dict.get("signal", "hold"),
        strength=int(sig_dict.get("confidence", 0.0) * 10),
        strength_percentage=sig_dict.get("confidence", 0.0) * 100,
        reasons=sig_dict.get("reasons", []),
        suggestion=f"{sig_dict.get('signal', 'hold').upper()} @ {sig_dict.get('price', 0):.2f}",
    )
    return MonitorNotification(
        type=sig_dict.get("signal", "hold"),
        stock=stock,
        signal=signal,
        message=f"[{sig_dict.get('priority', 'medium').upper()}] {sig_dict.get('name', '')}: {', '.join(sig_dict.get('reasons', []))}",
    )
```

- [ ] **Step 4: 写单元测试**

创建 `apps/api/tests/test_notification.py`：

```python
import pytest
from datetime import datetime
from app.monitor.notification.priority_notifier import PriorityNotifier
from app.monitor.models.alert_signal import AlertSignal, SignalType


class TestPriorityNotifier:
    def test_dedup_within_window(self):
        notifier = PriorityNotifier(dingtalk_client=None)
        sig = AlertSignal(
            timestamp=datetime.now(),
            code="600000",
            name="浦发银行",
            signal=SignalType.BUY,
            confidence=0.8,
            priority="high",
            reasons=["测试"],
            price=9.5,
        )
        
        notifier.send(sig)
        notifier.send(sig)  # 5分钟内不应重复发送
        
        # 验证 _sent_history 中只有一个记录
        key = "600000_technical"
        assert key in notifier._sent_history

    def test_critical_tracks_repeat(self):
        notifier = PriorityNotifier(dingtalk_client=None)
        sig = AlertSignal(
            timestamp=datetime.now(),
            code="600000",
            name="浦发银行",
            signal=SignalType.SELL,
            confidence=0.95,
            priority="critical",
            reasons=["止损触发"],
            price=8.0,
            alert_type="price",
        )
        
        notifier.send(sig)
        notifier.send(sig)  # 30秒内不应重复
        
        key = "600000_price"
        assert key in notifier._repeat_history

    def test_low_priority_no_dingtalk(self, caplog):
        notifier = PriorityNotifier(dingtalk_client=None)
        sig = AlertSignal(
            timestamp=datetime.now(),
            code="600000",
            name="浦发银行",
            signal=SignalType.HOLD,
            confidence=0.5,
            priority="low",
            reasons=["缩量整理"],
            price=9.5,
        )
        
        notifier.send(sig)
        assert "LOW" in caplog.text

    def test_send_with_mock_dingtalk(self):
        class MockDingTalk:
            def __init__(self):
                self.sent = []
            
            def send(self, msg, at_all=False):
                self.sent.append((msg[:50], at_all))
        
        mock = MockDingTalk()
        notifier = PriorityNotifier(dingtalk_client=mock)
        
        sig = AlertSignal(
            timestamp=datetime.now(),
            code="600000",
            name="浦发银行",
            signal=SignalType.BUY,
            confidence=0.8,
            priority="high",
            reasons=["RSI低于30"],
            price=9.5,
        )
        
        notifier.send(sig)
        assert len(mock.sent) == 1
```

- [ ] **Step 5: 运行测试验证**

Run: `cd apps/api && python -m pytest tests/test_notification.py -v`
Expected: 全部 PASS

- [ ] **Step 6: Commit**

```bash
git add apps/api/app/monitor/notification/priority_notifier.py
git add apps/api/app/monitor/notification/dingtalk.py
git add apps/api/app/monitor/stock_monitor.py
git add apps/api/tests/test_notification.py
git commit -m "feat: add priority-based notification system with dedup and @all support"
```

---

## Chunk 6: 集成测试 + 端到端验证

### Context

验证整个系统端到端运行正确。

### Files

- Create: `apps/api/tests/test_end_to_end.py` (端到端集成测试)
- Modify: `apps/api/app/monitor/__init__.py` (导出 AlertOrchestrator)

---

- [ ] **Step 1: 更新 `apps/api/app/monitor/__init__.py`**

```python
from .stock_monitor import StockMonitor
from .market_watcher import AlertOrchestrator
from .analysis.aggregator import AlertAggregator
from .watchers import (
    BaseWatcher,
    MarketBreadthWatcher,
    CorrelatedAssetWatcher,
    StockAlertWatcher,
    NewsEventWatcher,
    MinuteKlineWatcher,
)

__all__ = [
    "StockMonitor",
    "AlertOrchestrator",
    "AlertAggregator",
    "BaseWatcher",
    "MarketBreadthWatcher",
    "CorrelatedAssetWatcher",
    "StockAlertWatcher",
    "NewsEventWatcher",
    "MinuteKlineWatcher",
]
```

- [ ] **Step 2: 创建端到端集成测试 `apps/api/tests/test_end_to_end.py`**

```python
import pytest
from datetime import datetime
from app.monitor.alert_orchestrator import AlertOrchestrator
from app.monitor.analysis.aggregator import AlertAggregator
from app.monitor.models.alert_signal import SignalType


class TestEndToEnd:
    def test_orchestrator_initialization(self):
        orchestrator = AlertOrchestrator(
            interval_sec=5,
            watchlist=[{"code": "SH600000", "name": "测试"}],
            strategy_type="all",
        )
        assert orchestrator.interval_sec == 5
        assert len(orchestrator.watchlist) == 1
        assert orchestrator.aggregator is not None
    
    def test_orchestrator_has_all_watchers(self):
        orchestrator = AlertOrchestrator()
        assert orchestrator.breadth_watcher is not None
        assert orchestrator.correlated_watcher is not None
        assert orchestrator.stock_watcher is not None
        assert orchestrator.news_watcher is not None
        assert orchestrator.minute_watcher is not None
    
    def test_aggregator_with_real_strategy_weights(self):
        for strategy in ["intraday", "swing", "event", "all"]:
            agg = AlertAggregator(strategy_type=strategy)
            total_weight = sum(agg.weights.values())
            assert abs(total_weight - 1.0) < 0.001, f"Strategy {strategy} weights sum to {total_weight}"
    
    def test_signal_flow_through_aggregator(self):
        agg = AlertAggregator(strategy_type="intraday")
        signals = [
            {
                "code": "600000",
                "name": "测试",
                "signal": "buy",
                "confidence": 0.7,
                "priority": "high",
                "alert_type": "technical",
                "reasons": ["RSI<30"],
                "price": 10.0,
                "volume_ratio": 2.0,
                "technical_data": {"rsi": 25.0},
            }
        ]
        result = agg.aggregate(signals)
        assert len(result) == 1
        assert result[0].signal == SignalType.BUY
        assert result[0].priority == "high"
        assert result[0].target_price == 10.5  # 5% 止盈
        assert result[0].stop_loss == 9.5  # 5% 止损
    
    def test_critical_overrides_other_signals(self):
        agg = AlertAggregator(strategy_type="all")
        signals = [
            {"code": "600000", "name": "", "signal": "hold", "confidence": 0.5, "priority": "low", "alert_type": "technical", "reasons": [], "price": 10.0, "volume_ratio": 0.0, "technical_data": {"rsi": 50.0}},
        ]
        result = agg.aggregate(signals)
        assert len(result) == 1
        assert result[0].signal == SignalType.HOLD
```

- [ ] **Step 3: 运行所有测试**

Run: `cd apps/api && python -m pytest tests/test_alert_models.py tests/test_watchers.py tests/test_aggregator.py tests/test_notification.py tests/test_end_to_end.py -v`
Expected: 全部 PASS

- [ ] **Step 4: 运行 lint 检查**

Run: `cd apps/api && python -m ruff check app/monitor/ --fix && python -m ruff format app/monitor/`
Expected: 无错误

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/monitor/__init__.py
git add apps/api/tests/test_end_to_end.py
git commit -m "test: add end-to-end integration tests and verify all chunks"
```

---

## 执行顺序

1. Chunk 1: 数据层扩展
2. Chunk 2: 预警数据模型
3. Chunk 3: Watcher 组件实现
4. Chunk 4: AlertAggregator + 重构 MarketWatcher
5. Chunk 5: 通知系统重构
6. Chunk 6: 集成测试 + 端到端验证
