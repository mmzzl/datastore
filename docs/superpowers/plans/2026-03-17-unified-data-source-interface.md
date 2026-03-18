# Unified Data Source Interface Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a unified data source interface that abstracts away different data providers (Baostock, Akshare, MongoDB, etc.) behind a consistent API, allowing easy switching between data sources.

**Architecture:** Use Adapter Pattern with an abstract base class defining the interface, and concrete adapters for each data provider. A Data Source Manager will handle provider selection and configuration.

**Tech Stack:** Python, Pydantic (for data models), ABC (Abstract Base Classes), existing data providers (Baostock, Akshare, MongoDB)

---

### Task 1: Define Unified Data Models

**Files:**
- Create: `case/apps/api/app/data_source/models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/data_source/test_models.py
import pytest
from app.data_source.models import StockKLine, StockInfo, DataSourceConfig

def test_stock_kline_model():
    """测试K线数据模型"""
    kline = StockKLine(
        code="sh.600000",
        date="2026-03-17",
        open=10.0,
        high=10.5,
        low=9.8,
        close=10.2,
        volume=1000000,
        amount=10000000.0
    )
    assert kline.code == "sh.600000"
    assert kline.close == 10.2

def test_stock_info_model():
    """测试股票信息模型"""
    info = StockInfo(
        code="sh.600000",
        name="浦发银行",
        exchange="SH"
    )
    assert info.code == "sh.600000"
    assert info.name == "浦发银行"

def test_data_source_config():
    """测试数据源配置模型"""
    config = DataSourceConfig(
        provider="baostock",
        name="Baostock免费数据源"
    )
    assert config.provider == "baostock"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.12 -m pytest tests/data_source/test_models.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# case/apps/api/app/data_source/models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DataSourceType(Enum):
    """数据源类型"""
    BAOSTOCK = "baostock"
    AKSHARE = "akshare"
    MONGODB = "mongodb"
    CUSTOM = "custom"

class StockKLine(BaseModel):
    """统一K线数据模型"""
    code: str = Field(..., description="股票代码")
    date: str = Field(..., description="日期 YYYY-MM-DD")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: int = Field(..., description="成交量")
    amount: float = Field(..., description="成交额")
    turnover_rate: Optional[float] = Field(None, description="换手率")
    change_pct: Optional[float] = Field(None, description="涨跌幅")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "sh.600000",
                "date": "2026-03-17",
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": 1000000,
                "amount": 10000000.0
            }
        }

class StockInfo(BaseModel):
    """统一股票信息模型"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    exchange: str = Field(..., description="交易所 SH/SZ")
    industry: Optional[str] = Field(None, description="行业")
    market_value: Optional[float] = Field(None, description="市值")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "sh.600000",
                "name": "浦发银行",
                "exchange": "SH"
            }
        }

class DataSourceConfig(BaseModel):
    """数据源配置模型"""
    provider: str = Field(..., description="数据源提供商")
    name: str = Field(..., description="数据源名称")
    enabled: bool = Field(True, description="是否启用")
    priority: int = Field(1, description="优先级，数字越小优先级越高")
    config: Dict[str, Any] = Field(default_factory=dict, description=" provider-specific配置")
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "baostock",
                "name": "Baostock免费数据源",
                "enabled": True,
                "priority": 1
            }
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3.12 -m pytest tests/data_source/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add case/apps/api/app/data_source/models.py tests/data_source/test_models.py
git commit -m "feat: define unified data source models"
```

### Task 2: Define Abstract Data Source Interface

**Files:**
- Create: `case/apps/api/app/data_source/interface.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/data_source/test_interface.py
import pytest
from app.data_source.interface import IDataSource
from app.data_source.models import StockKLine, StockInfo

def test_interface_methods():
    """测试接口定义的方法"""
    # 检查接口是否定义了必要的方法
    assert hasattr(IDataSource, 'get_kline')
    assert hasattr(IDataSource, 'get_stock_info')
    assert hasattr(IDataSource, 'get_stock_list')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.12 -m pytest tests/data_source/test_interface.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# case/apps/api/app/data_source/interface.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .models import StockKLine, StockInfo

class IDataSource(ABC):
    """
    数据源统一接口
    所有数据源必须实现此接口
    """
    
    @abstractmethod
    def get_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d",
        adjust_flag: str = "3"
    ) -> List[StockKLine]:
        """
        获取K线数据
        
        Args:
            code: 股票代码
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            frequency: 数据频率 d=日, w=周, m=月
            adjust_flag: 复权类型 1=后复权, 2=前复权, 3=不复权
        
        Returns:
            K线数据列表
        """
        pass
    
    @abstractmethod
    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        """
        获取股票基本信息
        
        Args:
            code: 股票代码
        
        Returns:
            股票信息
        """
        pass
    
    @abstractmethod
    def get_stock_list(self) -> List[StockInfo]:
        """
        获取股票列表
        
        Returns:
            股票信息列表
        """
        pass
    
    @abstractmethod
    def get_realtime_data(self, code: str) -> Dict[str, Any]:
        """
        获取实时数据
        
        Args:
            code: 股票代码
        
        Returns:
            实时数据字典
        """
        pass
    
    @abstractmethod
    def get_capital_flow(self, code: str, days: int = 5) -> List[Dict[str, Any]]:
        """
        获取资金流向数据
        
        Args:
            code: 股票代码
            days: 获取天数
        
        Returns:
            资金流向数据列表
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """数据源名称"""
        pass
    
    @property
    @abstractmethod
    def provider(self) -> str:
        """数据源提供商"""
        pass
    
    @abstractmethod
    def close(self):
        """关闭连接/清理资源"""
        pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3.12 -m pytest tests/data_source/test_interface.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add case/apps/api/app/data_source/interface.py tests/data_source/test_interface.py
git commit -m "feat: define unified data source interface"
```

### Task 3: Implement Baostock Adapter

**Files:**
- Create: `case/apps/api/app/data_source/adapters/baostock_adapter.py`
- Modify: `case/apps/api/app/data_source/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/data_source/test_baostock_adapter.py
import pytest
from app.data_source.adapters.baostock_adapter import BaostockAdapter
from app.data_source.models import StockKLine, StockInfo

def test_baostock_adapter_creation():
    """测试Baostock适配器创建"""
    adapter = BaostockAdapter()
    assert adapter.name == "Baostock"
    assert adapter.provider == "baostock"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.12 -m pytest tests/data_source/test_baostock_adapter.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# case/apps/api/app/data_source/adapters/baostock_adapter.py
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import baostock as bs

from ..interface import IDataSource
from ..models import StockKLine, StockInfo

logger = logging.getLogger(__name__)

class BaostockAdapter(IDataSource):
    """Baostock数据源适配器"""
    
    def __init__(self):
        self._connected = False
        self._name = "Baostock"
        self._provider = "baostock"
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def provider(self) -> str:
        return self._provider
    
    def _ensure_connected(self):
        """确保已连接到baostock"""
        if not self._connected:
            lg = bs.login()
            if lg.error_code != '0':
                raise Exception(f"Baostock登录失败: {lg.error_msg}")
            self._connected = True
            logger.info("Baostock登录成功")
    
    def get_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d",
        adjust_flag: str = "3"
    ) -> List[StockKLine]:
        try:
            self._ensure_connected()
            
            rs = bs.query_history_k_data_plus(
                code,
                "date,code,open,high,low,close,volume,amount,adjustflag,turn,tradestatus,pctChg",
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                adjustflag=adjust_flag
            )
            
            if rs.error_code != '0':
                logger.error(f"获取 {code} K线数据失败: {rs.error_msg}")
                return []
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                row = rs.get_row_data()
                kline = StockKLine(
                    code=row[1],
                    date=row[0],
                    open=float(row[2]),
                    high=float(row[3]),
                    low=float(row[4]),
                    close=float(row[5]),
                    volume=int(row[6]),
                    amount=float(row[7]),
                    turnover_rate=float(row[9]) if row[9] else None,
                    change_pct=float(row[11]) if row[11] else None
                )
                data_list.append(kline)
            
            return data_list
            
        except Exception as e:
            logger.error(f"获取K线数据异常: {e}")
            return []
    
    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        try:
            self._ensure_connected()
            
            rs = bs.query_stock_basic(code)
            if rs.error_code != '0':
                return None
            
            if rs.next():
                row = rs.get_row_data()
                return StockInfo(
                    code=row[0],
                    name=row[1],
                    exchange=row[2][:2] if row[2] else "SH"
                )
            return None
            
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            return None
    
    def get_stock_list(self) -> List[StockInfo]:
        try:
            self._ensure_connected()
            
            rs = bs.query_all_stock()
            stock_list = []
            
            while rs.next():
                row = rs.get_row_data()
                if row[1] == "1":  # 交易状态正常
                    stock_list.append(StockInfo(
                        code=row[0],
                        name=row[2],
                        exchange=row[0][:2]
                    ))
            
            return stock_list
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    def get_realtime_data(self, code: str) -> Dict[str, Any]:
        """Baostock不提供实时数据，返回空字典"""
        return {}
    
    def get_capital_flow(self, code: str, days: int = 5) -> List[Dict[str, Any]]:
        """Baostock不提供资金流向数据，返回空列表"""
        return []
    
    def close(self):
        """关闭Baostock连接"""
        if self._connected:
            bs.logout()
            self._connected = False
            logger.info("Baostock连接已关闭")
    
    def __del__(self):
        """析构函数中关闭连接"""
        self.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3.12 -m pytest tests/data_source/test_baostock_adapter.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add case/apps/api/app/data_source/adapters/baostock_adapter.py tests/data_source/test_baostock_adapter.py
git commit -m "feat: implement Baostock data source adapter"
```

### Task 4: Implement Akshare Adapter

**Files:**
- Create: `case/apps/api/app/data_source/adapters/akshare_adapter.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/data_source/test_akshare_adapter.py
import pytest
from app.data_source.adapters.akshare_adapter import AkshareAdapter

def test_akshare_adapter_creation():
    """测试Akshare适配器创建"""
    adapter = AkshareAdapter()
    assert adapter.name == "Akshare"
    assert adapter.provider == "akshare"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.12 -m pytest tests/data_source/test_akshare_adapter.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# case/apps/api/app/data_source/adapters/akshare_adapter.py
import logging
from typing import List, Optional, Dict, Any
import akshare as ak

from ..interface import IDataSource
from ..models import StockKLine, StockInfo

logger = logging.getLogger(__name__)

class AkshareAdapter(IDataSource):
    """Akshare数据源适配器"""
    
    def __init__(self):
        self._name = "Akshare"
        self._provider = "akshare"
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def provider(self) -> str:
        return self._provider
    
    def get_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d",
        adjust_flag: str = "3"
    ) -> List[StockKLine]:
        try:
            # 转换代码格式 sh.600000 -> 600000
            stock_code = code.split('.')[-1] if '.' in code else code
            
            # 获取K线数据
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                adjust=frequency
            )
            
            data_list = []
            for _, row in df.iterrows():
                kline = StockKLine(
                    code=code,
                    date=row['日期'],
                    open=float(row['开盘']),
                    high=float(row['最高']),
                    low=float(row['最低']),
                    close=float(row['收盘']),
                    volume=int(row['成交量']),
                    amount=float(row['成交额']),
                    change_pct=float(row['涨跌幅'])
                )
                data_list.append(kline)
            
            return data_list
            
        except Exception as e:
            logger.error(f"获取K线数据异常: {e}")
            return []
    
    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        try:
            # Akshare获取股票信息
            stock_code = code.split('.')[-1] if '.' in code else code
            
            # 从实时数据获取基本信息
            df = ak.stock_zh_a_spot_em()
            stock_data = df[df['代码'] == stock_code]
            
            if not stock_data.empty:
                return StockInfo(
                    code=code,
                    name=stock_data.iloc[0]['名称'],
                    exchange=code[:2] if '.' in code else "SH"
                )
            return None
            
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            return None
    
    def get_stock_list(self) -> List[StockInfo]:
        try:
            df = ak.stock_zh_a_spot_em()
            stock_list = []
            
            for _, row in df.iterrows():
                code = row['代码']
                exchange = "SH" if code.startswith('6') else "SZ"
                stock_list.append(StockInfo(
                    code=f"{exchange}.{code}",
                    name=row['名称'],
                    exchange=exchange
                ))
            
            return stock_list
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    def get_realtime_data(self, code: str) -> Dict[str, Any]:
        try:
            stock_code = code.split('.')[-1] if '.' in code else code
            
            df = ak.stock_zh_a_spot_em()
            stock_data = df[df['代码'] == stock_code]
            
            if not stock_data.empty:
                row = stock_data.iloc[0]
                return {
                    "code": code,
                    "name": row['名称'],
                    "price": row['最新价'],
                    "change": row['涨跌额'],
                    "change_pct": row['涨跌幅'],
                    "volume": row['成交量'],
                    "amount': row['成交额']
                }
            return {}
            
        except Exception as e:
            logger.error(f"获取实时数据失败: {e}")
            return {}
    
    def get_capital_flow(self, code: str, days: int = 5) -> List[Dict[str, Any]]:
        """Akshare资金流向数据"""
        try:
            stock_code = code.split('.')[-1] if '.' in code else code
            
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=(datetime.now() - timedelta(days=days)).strftime('%Y%m%d'),
                end_date=datetime.now().strftime('%Y%m%d')
            )
            
            # 简化处理，返回基本的资金流向信息
            return [{
                "date": row['日期'],
                "net_inflow": 0,  # Akshare不直接提供，需要计算
                "code": code
            } for _, row in df.iterrows()]
            
        except Exception as e:
            logger.error(f"获取资金流向失败: {e}")
            return []
    
    def close(self):
        """Akshare不需要关闭连接"""
        pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3.12 -m pytest tests/data_source/test_akshare_adapter.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add case/apps/api/app/data_source/adapters/akshare_adapter.py tests/data_source/test_akshare_adapter.py
git commit -m "feat: implement Akshare data source adapter"
```

### Task 5: Implement MongoDB Adapter

**Files:**
- Create: `case/apps/api/app/data_source/adapters/mongodb_adapter.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/data_source/test_mongodb_adapter.py
import pytest
from app.data_source.adapters.mongodb_adapter import MongoDBAdapter

def test_mongodb_adapter_creation():
    """测试MongoDB适配器创建"""
    adapter = MongoDBAdapter()
    assert adapter.name == "MongoDB"
    assert adapter.provider == "mongodb"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.12 -m pytest tests/data_source/test_mongodb_adapter.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# case/apps/api/app/data_source/adapters/mongodb_adapter.py
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..interface import IDataSource
from ..models import StockKLine, StockInfo
from ...storage.mongo_client import MongoStorage
from ...core.config import settings

logger = logging.getLogger(__name__)

class MongoDBAdapter(IDataSource):
    """MongoDB数据源适配器"""
    
    def __init__(self):
        self._name = "MongoDB"
        self._provider = "mongodb"
        self.storage = None
        self._init_storage()
    
    def _init_storage(self):
        """初始化存储连接"""
        try:
            self.storage = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_database,
                username=settings.mongodb_username,
                password=settings.mongodb_password
            )
            self.storage.connect()
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB: {e}")
            self.storage = None
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def provider(self) -> str:
        return self._provider
    
    def get_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d",
        adjust_flag: str = "3"
    ) -> List[StockKLine]:
        if not self.storage:
            return []
        
        try:
            kline_data = self.storage.get_kline(
                code=code,
                start_date=start_date,
                end_date=end_date,
                limit=1000
            )
            
            data_list = []
            for item in kline_data:
                kline = StockKLine(
                    code=item.get('code', code),
                    date=item.get('date', ''),
                    open=float(item.get('open', 0)),
                    high=float(item.get('high', 0)),
                    low=float(item.get('low', 0)),
                    close=float(item.get('close', 0)),
                    volume=int(item.get('volume', 0)),
                    amount=float(item.get('amount', 0)),
                    turnover_rate=float(item.get('turnover', 0)) if item.get('turnover') else None,
                    change_pct=float(item.get('pct_chg', 0)) if item.get('pct_chg') else None
                )
                data_list.append(kline)
            
            return data_list
            
        except Exception as e:
            logger.error(f"获取MongoDB K线数据失败: {e}")
            return []
    
    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        # MongoDB通常存储K线数据，股票基本信息可以从其他数据源获取
        # 这里返回基本信息
        return StockInfo(
            code=code,
            name=code,
            exchange=code[:2] if '.' in code else "SH"
        )
    
    def get_stock_list(self) -> List[StockInfo]:
        """从K线数据中提取股票列表"""
        if not self.storage:
            return []
        
        try:
            # 获取所有股票的最新数据
            kline_data = self.storage.get_all_klines(limit=10000)
            
            # 去重获取股票列表
            stock_dict = {}
            for item in kline_data:
                code = item.get('code')
                if code and code not in stock_dict:
                    stock_dict[code] = StockInfo(
                        code=code,
                        name=item.get('name', code),
                        exchange=code[:2] if '.' in code else "SH"
                    )
            
            return list(stock_dict.values())
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    def get_realtime_data(self, code: str) -> Dict[str, Any]:
        """MongoDB不提供实时数据"""
        return {}
    
    def get_capital_flow(self, code: str, days: int = 5) -> List[Dict[str, Any]]:
        """从MongoDB获取资金流向数据"""
        if not self.storage:
            return []
        
        try:
            # 获取资金流向数据
            capital_data = self.storage.get_capital_flow(
                name=code,
                limit=days
            )
            return capital_data
            
        except Exception as e:
            logger.error(f"获取资金流向失败: {e}")
            return []
    
    def close(self):
        """关闭MongoDB连接"""
        if self.storage:
            self.storage.close()
            logger.info("MongoDB连接已关闭")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3.12 -m pytest tests/data_source/test_mongodb_adapter.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add case/apps/api/app/data_source/adapters/mongodb_adapter.py tests/data_source/test_mongodb_adapter.py
git commit -m "feat: implement MongoDB data source adapter"
```

### Task 6: Implement Data Source Manager

**Files:**
- Create: `case/apps/api/app/data_source/manager.py`
- Modify: `case/apps/api/app/data_source/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/data_source/test_manager.py
import pytest
from app.data_source.manager import DataSourceManager
from app.data_source.models import DataSourceConfig

def test_manager_creation():
    """测试数据源管理器创建"""
    manager = DataSourceManager()
    assert manager is not None

def test_manager_register_adapter():
    """测试注册数据源适配器"""
    manager = DataSourceManager()
    
    # 注册模拟适配器
    class MockAdapter:
        def __init__(self):
            self.name = "Mock"
            self.provider = "mock"
    
    manager.register_adapter("mock", MockAdapter())
    assert "mock" in manager._adapters
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.12 -m pytest tests/data_source/test_manager.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# case/apps/api/app/data_source/manager.py
import logging
from typing import Dict, Optional, List, Any
from contextlib import contextmanager

from .interface import IDataSource
from .models import DataSourceConfig, StockKLine, StockInfo
from .adapters.baostock_adapter import BaostockAdapter
from .adapters.akshare_adapter import AkshareAdapter
from .adapters.mongodb_adapter import MongoDBAdapter

logger = logging.getLogger(__name__)

class DataSourceManager:
    """
    数据源管理器
    负责管理多个数据源适配器，提供统一的数据访问接口
    """
    
    def __init__(self, config: List[DataSourceConfig] = None):
        self._adapters: Dict[str, IDataSource] = {}
        self._config = config or self._get_default_config()
        self._initialize_adapters()
    
    def _get_default_config(self) -> List[DataSourceConfig]:
        """获取默认数据源配置"""
        return [
            DataSourceConfig(
                provider="baostock",
                name="Baostock免费数据源",
                enabled=True,
                priority=1,
                config={}
            ),
            DataSourceConfig(
                provider="mongodb",
                name="MongoDB缓存数据源",
                enabled=True,
                priority=2,
                config={}
            ),
            DataSourceConfig(
                provider="akshare",
                name="Akshare数据源",
                enabled=True,
                priority=3,
                config={}
            )
        ]
    
    def _initialize_adapters(self):
        """初始化数据源适配器"""
        for config in self._config:
            if not config.enabled:
                continue
            
            try:
                if config.provider == "baostock":
                    adapter = BaostockAdapter()
                elif config.provider == "akshare":
                    adapter = AkshareAdapter()
                elif config.provider == "mongodb":
                    adapter = MongoDBAdapter()
                else:
                    logger.warning(f"未知的数据源提供商: {config.provider}")
                    continue
                
                self._adapters[config.provider] = adapter
                logger.info(f"初始化数据源: {adapter.name} (优先级: {config.priority})")
                
            except Exception as e:
                logger.error(f"初始化数据源 {config.provider} 失败: {e}")
    
    def register_adapter(self, provider: str, adapter: IDataSource):
        """注册自定义数据源适配器"""
        self._adapters[provider] = adapter
        logger.info(f"注册自定义数据源: {provider}")
    
    def get_adapter(self, provider: str) -> Optional[IDataSource]:
        """获取指定的数据源适配器"""
        return self._adapters.get(provider)
    
    def get_best_adapter(self, data_type: str = "kline") -> Optional[IDataSource]:
        """
        获取最适合的数据源适配器
        根据优先级和数据类型选择
        """
        # 按优先级排序
        sorted_adapters = sorted(
            self._adapters.items(),
            key=lambda x: self._get_adapter_priority(x[0])
        )
        
        for provider, adapter in sorted_adapters:
            # 根据数据类型选择合适的数据源
            if data_type == "kline" and hasattr(adapter, 'get_kline'):
                return adapter
            elif data_type == "realtime" and hasattr(adapter, 'get_realtime_data'):
                return adapter
            elif data_type == "capital_flow" and hasattr(adapter, 'get_capital_flow'):
                return adapter
        
        return None
    
    def _get_adapter_priority(self, provider: str) -> int:
        """获取适配器优先级"""
        for config in self._config:
            if config.provider == provider:
                return config.priority
        return 999
    
    # 统一数据访问接口
    
    def get_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d",
        adjust_flag: str = "3",
        provider: str = None
    ) -> List[StockKLine]:
        """
        获取K线数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
            adjust_flag: 复权类型
            provider: 指定数据源，None则自动选择
        
        Returns:
            K线数据列表
        """
        if provider:
            adapter = self._adapters.get(provider)
            if adapter:
                return adapter.get_kline(code, start_date, end_date, frequency, adjust_flag)
        else:
            # 自动选择最佳数据源
            adapter = self.get_best_adapter("kline")
            if adapter:
                return adapter.get_kline(code, start_date, end_date, frequency, adjust_flag)
        
        return []
    
    def get_stock_info(self, code: str, provider: str = None) -> Optional[StockInfo]:
        """获取股票信息"""
        if provider:
            adapter = self._adapters.get(provider)
            if adapter:
                return adapter.get_stock_info(code)
        else:
            for adapter in self._adapters.values():
                info = adapter.get_stock_info(code)
                if info:
                    return info
        return None
    
    def get_stock_list(self, provider: str = None) -> List[StockInfo]:
        """获取股票列表"""
        if provider:
            adapter = self._adapters.get(provider)
            if adapter:
                return adapter.get_stock_list()
        else:
            # 合并所有数据源的股票列表
            all_stocks = {}
            for adapter in self._adapters.values():
                stocks = adapter.get_stock_list()
                for stock in stocks:
                    all_stocks[stock.code] = stock
            return list(all_stocks.values())
        return []
    
    def get_realtime_data(self, code: str, provider: str = None) -> Dict[str, Any]:
        """获取实时数据"""
        if provider:
            adapter = self._adapters.get(provider)
            if adapter:
                return adapter.get_realtime_data(code)
        else:
            for adapter in self._adapters.values():
                data = adapter.get_realtime_data(code)
                if data:
                    return data
        return {}
    
    def get_capital_flow(self, code: str, days: int = 5, provider: str = None) -> List[Dict[str, Any]]:
        """获取资金流向数据"""
        if provider:
            adapter = self._adapters.get(provider)
            if adapter:
                return adapter.get_capital_flow(code, days)
        else:
            for adapter in self._adapters.values():
                data = adapter.get_capital_flow(code, days)
                if data:
                    return data
        return []
    
    def close_all(self):
        """关闭所有数据源连接"""
        for provider, adapter in self._adapters.items():
            try:
                adapter.close()
                logger.info(f"关闭数据源连接: {provider}")
            except Exception as e:
                logger.error(f"关闭数据源 {provider} 失败: {e}")
    
    @contextmanager
    def get_connection(self):
        """上下文管理器"""
        try:
            yield self
        finally:
            self.close_all()
```

- [ ] **Step 4: Update __init__.py**

```python
# case/apps/api/app/data_source/__init__.py
from .interface import IDataSource
from .models import StockKLine, StockInfo, DataSourceConfig, DataSourceType
from .manager import DataSourceManager

__all__ = [
    "IDataSource",
    "StockKLine",
    "StockInfo",
    "DataSourceConfig",
    "DataSourceType",
    "DataSourceManager"
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `py -3.12 -m pytest tests/data_source/test_manager.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add case/apps/api/app/data_source/manager.py case/apps/api/app/data_source/__init__.py tests/data_source/test_manager.py
git commit -m "feat: implement data source manager with unified interface"
```

### Task 7: Integration with Existing Code

**Files:**
- Modify: `case/apps/api/app/monitor/brain/capital_flow.py`
- Modify: `case/apps/api/app/monitor/brain/sentiment.py`

- [ ] **Step 1: Update capital flow analyzer to use unified interface**

```python
# case/apps/api/app/monitor/brain/capital_flow.py (modified)
import logging
from typing import Dict, Any
from datetime import datetime, timedelta

from app.data_source import DataSourceManager

logger = logging.getLogger(__name__)

class CapitalFlowAnalyzer:
    """主力资金流向分析器 - 使用统一数据源接口"""
    
    def __init__(self, data_manager: DataSourceManager = None):
        self.data_manager = data_manager or DataSourceManager()
    
    def analyze(self, code: str, days: int = 5) -> Dict[str, Any]:
        """
        分析股票资金流向
        
        Args:
            code: 股票代码
            days: 分析天数
        
        Returns:
            资金流向分析结果
        """
        try:
            # 使用统一接口获取资金流向数据
            capital_flow_data = self.data_manager.get_capital_flow(
                code=code,
                days=days
            )
            
            if not capital_flow_data:
                logger.warning(f"No capital flow data found for {code}")
                return self._get_mock_data(code)
            
            # 计算统计指标
            net_inflows = [d.get('net_inflow', 0) for d in capital_flow_data]
            
            avg_net_inflow = sum(net_inflows) / len(net_inflows) if net_inflows else 0
            
            # 判断主力动向
            if avg_net_inflow > 0:
                trend = "流入"
                trend_score = min(0.8, avg_net_inflow / 1000000)
            else:
                trend = "流出"
                trend_score = max(0.2, 1 - abs(avg_net_inflow) / 1000000)
            
            return {
                "net_inflow": avg_net_inflow,
                "主力动向": trend,
                "trend_score": trend_score,
                "data_points": len(capital_flow_data)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing capital flow for {code}: {e}")
            return self._get_mock_data(code)
    
    def _get_mock_data(self, code: str) -> Dict[str, Any]:
        """获取模拟数据"""
        return {
            "net_inflow": 0.0,
            "主力动向": "未知",
            "trend_score": 0.5,
            "data_points": 0,
            "is_mock": True
        }
```

- [ ] **Step 2: Commit integration changes**

```bash
git add case/apps/api/app/monitor/brain/capital_flow.py
git commit -m "refactor: integrate unified data source interface into capital flow analyzer"
```

### Task 8: Documentation and Testing

**Files:**
- Create: `case/apps/api/DATASOURCE_README.md`

- [ ] **Step 1: Create documentation**

```markdown
# 统一数据源接口文档

## 概述

统一数据源接口提供了一致的数据访问API，支持多种数据源（Baostock、Akshare、MongoDB等），可通过配置轻松切换。

## 使用示例

### 基本使用

```python
from app.data_source import DataSourceManager

# 创建管理器（使用默认配置）
manager = DataSourceManager()

# 获取K线数据
klines = manager.get_kline("sh.600000", "2026-01-01", "2026-03-17")

# 获取股票列表
stocks = manager.get_stock_list()

# 获取实时数据
realtime = manager.get_realtime_data("sh.600000")
```

### 指定数据源

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

### 自定义数据源

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

## 配置

### 默认配置

默认按优先级使用数据源：
1. Baostock (优先级1)
2. MongoDB (优先级2)
3. Akshare (优先级3)

### 自定义配置

```python
from app.data_source.models import DataSourceConfig

config = [
    DataSourceConfig(
        provider="baostock",
        name="Baostock免费数据源",
        enabled=True,
        priority=1
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

## 接口方法

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `get_kline` | 获取K线数据 | code, start_date, end_date, frequency, adjust_flag, provider | List[StockKLine] |
| `get_stock_info` | 获取股票信息 | code, provider | Optional[StockInfo] |
| `get_stock_list` | 获取股票列表 | provider | List[StockInfo] |
| `get_realtime_data` | 获取实时数据 | code, provider | Dict |
| `get_capital_flow` | 获取资金流向 | code, days, provider | List[Dict] |

## 扩展性

### 添加新数据源

1. 创建适配器类实现 `IDataSource` 接口
2. 在 `DataSourceManager._initialize_adapters` 中添加初始化逻辑
3. 更新默认配置

### 数据源优先级

通过 `DataSourceConfig.priority` 控制数据源优先级，数字越小优先级越高。
```

- [ ] **Step 2: Commit documentation**

```bash
git add case/apps/api/DATASOURCE_README.md
git commit -m "docs: add unified data source interface documentation"
```

---

## Plan Review Loop

After saving the plan:

1. Dispatch a single plan-document-reviewer subagent with:
   - Plan path: `docs/superpowers/plans/2026-03-17-unified-data-source-interface.md`
   - Spec path: `case/Trading_Strategy_Platform_Requirements.md`

2. If Issues Found: fix issues, re-dispatch.
3. If Approved: proceed to execution.

I will now dispatch the subagent.<tool_call>
<function=task>
<parameter=description>Review data source plan