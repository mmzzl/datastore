# Smart Trading Decision System - Data Ingestion & Management Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the data ingestion and storage layer for the Smart Trading Decision System, fetching data from Baostock (free source) and storing it in a cloud-ready database.

**Architecture:** The system will fetch stock lists and historical K-line data from Baostock, process it (cleaning, feature extraction), and store it in a PostgreSQL database hosted on a cloud server. The data layer will expose a clean API for the backtesting and decision engines.

**Tech Stack:** Python, Baostock, PostgreSQL, SQLAlchemy, Pandas.

---

### Task 1: Setup Project Structure and Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `src/data/__init__.py`
- Create: `src/data/ingestion/__init__.py`
- Create: `src/data/processing/__init__.py`
- Create: `src/data/storage/__init__.py`
- Create: `tests/data/__init__.py`
- Create: `tests/data/test_baostock_client.py` (empty)
- Create: `tests/data/test_kline_processor.py` (empty)

- [ ] **Step 1: Create requirements.txt**

```text
baostock==0.8.8
pandas==2.0.3
numpy==1.24.3
SQLAlchemy==2.0.19
psycopg2-binary==2.9.7
python-dotenv==1.0.0
pytest==7.4.2
```

- [ ] **Step 2: Create directory structure**

Run: `mkdir -p src/data/ingestion src/data/processing src/data/storage tests/data`
Run: `touch src/data/__init__.py src/data/ingestion/__init__.py src/data/processing/__init__.py src/data/storage/__init__.py tests/data/__init__.py tests/data/test_baostock_client.py tests/data/test_kline_processor.py`

- [ ] **Step 3: Verify structure**

Run: `tree src tests`
Expected: Directory tree showing the created files.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt src/ tests/
git commit -m "feat: setup project structure and dependencies for data ingestion"
```

### Task 2: Implement Baostock Client

**Files:**
- Create: `src/data/ingestion/baostock_client.py`
- Modify: `tests/data/test_baostock_client.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/data/test_baostock_client.py
import pytest
from src.data.ingestion.baostock_client import BaostockClient

def test_fetch_stock_list():
    client = BaostockClient()
    stocks = client.fetch_stock_list()
    assert isinstance(stocks, list)
    assert len(stocks) > 0
    assert 'code' in stocks[0]
    assert 'code_name' in stocks[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/data/test_baostock_client.py::test_fetch_stock_list -v`
Expected: FAIL with "BaostockClient not found" or import error.

- [ ] **Step 3: Write minimal implementation**

```python
# src/data/ingestion/baostock_client.py
import baostock as bs
import pandas as pd

class BaostockClient:
    def __init__(self):
        bs.login()

    def __del__(self):
        bs.logout()

    def fetch_stock_list(self):
        rs = bs.query_all_stock(day="2026-03-17")
        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        result = pd.DataFrame(data_list, columns=rs.fields)
        return result.to_dict('records')
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/data/test_baostock_client.py::test_fetch_stock_list -v`
Expected: PASS

- [ ] **Step 5: Add test for fetching K-line data**

```python
# tests/data/test_baostock_client.py
def test_fetch_kline_data():
    client = BaostockClient()
    kline = client.fetch_kline_data("sh.600000", "2026-01-01", "2026-03-17")
    assert isinstance(kline, pd.DataFrame)
    assert not kline.empty
    assert 'date' in kline.columns
    assert 'close' in kline.columns
```

- [ ] **Step 6: Implement K-line fetch method**

```python
# src/data/ingestion/baostock_client.py
    def fetch_kline_data(self, code, start_date, end_date):
        rs = bs.query_history_k_data(code,
            "date,code,open,high,low,close,volume,amount,adjustflag",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="3")
        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        result = pd.DataFrame(data_list, columns=rs.fields)
        return result
```

- [ ] **Step 7: Run test to verify it passes**

Run: `pytest tests/data/test_baostock_client.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/data/ingestion/baostock_client.py tests/data/test_baostock_client.py
git commit -m "feat: implement Baostock client for stock list and K-line data"
```

### Task 3: Implement Database Schema and Storage

**Files:**
- Create: `src/data/storage/database.py`
- Create: `src/data/storage/models.py`

- [ ] **Step 1: Define database models**

```python
# src/data/storage/models.py
from sqlalchemy import Column, Integer, String, Float, Date, create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Stock(Base):
    __tablename__ = 'stocks'
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, index=True)
    name = Column(String(50))
    trade_status = Column(Integer)

class KLine(Base):
    __tablename__ = 'kline_data'
    id = Column(Integer, primary_key=True)
    code = Column(String(20), index=True)
    date = Column(Date, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    amount = Column(Float)
    adjust_flag = Column(String(10))
```

- [ ] **Step 2: Implement database connection manager**

```python
# src/data/storage/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.data.storage.models import Base

class DatabaseManager:
    def __init__(self, db_url=None):
        if db_url is None:
            db_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/trading_db")
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        return self.SessionLocal()
```

- [ ] **Step 3: Commit**

```bash
git add src/data/storage/
git commit -m "feat: implement database models and connection manager"
```

### Task 4: Implement Data Processing

**Files:**
- Create: `src/data/processing/kline_processor.py`
- Modify: `tests/data/test_kline_processor.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/data/test_kline_processor.py
import pandas as pd
from src.data.processing.kline_processor import calculate_ma

def test_calculate_ma():
    data = pd.DataFrame({
        'close': [10, 12, 11, 13, 14, 15]
    })
    result = calculate_ma(data, 3)
    assert 'MA_3' in result.columns
    assert pd.isna(result['MA_3'].iloc[0])
    assert result['MA_3'].iloc[2] == 11.0  # (10+12+11)/3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/data/test_kline_processor.py::test_calculate_ma -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# src/data/processing/kline_processor.py
import pandas as pd

def calculate_ma(df, period):
    df[f'MA_{period}'] = df['close'].rolling(window=period).mean()
    return df
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/data/test_kline_processor.py::test_calculate_ma -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/data/processing/kline_processor.py tests/data/test_kline_processor.py
git commit -m "feat: implement basic data processing (MA calculation)"
```

### Task 5: Integration Test (Ingestion Flow)

**Files:**
- Create: `tests/data/test_ingestion_flow.py`

- [ ] **Step 1: Write integration test**

```python
# tests/data/test_ingestion_flow.py
import pytest
from src.data.ingestion.baostock_client import BaostockClient
from src.data.storage.database import DatabaseManager
from src.data.storage.models import Stock, KLine

def test_full_ingestion_flow():
    # 1. Fetch data
    client = BaostockClient()
    stocks = client.fetch_stock_list()
    kline = client.fetch_kline_data("sh.600000", "2026-03-01", "2026-03-10")
    
    # 2. Connect to DB (using in-memory SQLite for test)
    db_manager = DatabaseManager("sqlite:///:memory:")
    db_manager.create_tables()
    
    # 3. Store data
    session = db_manager.get_session()
    
    # Store stock
    stock = Stock(code="sh.600000", name="浦发银行", trade_status=1)
    session.add(stock)
    
    # Store K-line
    for _, row in kline.iterrows():
        kline_record = KLine(
            code=row['code'],
            date=row['date'],
            open=float(row['open']),
            high=float(row['high']),
            low=float(row['low']),
            close=float(row['close']),
            volume=float(row['volume']),
            amount=float(row['amount']),
            adjust_flag=row['adjustflag']
        )
        session.add(kline_record)
    
    session.commit()
    
    # 4. Verify
    stored_kline = session.query(KLine).filter_by(code="sh.600000").first()
    assert stored_kline is not None
    assert stored_kline.close > 0
```

- [ ] **Step 2: Run integration test**

Run: `pytest tests/data/test_ingestion_flow.py -v`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/data/test_ingestion_flow.py
git commit -m "test: add integration test for data ingestion flow"
```

### Task 6: Documentation

**Files:**
- Create: `docs/data-ingestion-readme.md`

- [ ] **Step 1: Write README**

```markdown
# Data Ingestion Module

This module handles fetching stock data from Baostock and storing it in PostgreSQL.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variable: `DATABASE_URL=postgresql://user:pass@host/db`
3. Run ingestion script (to be implemented in next phase).
```

- [ ] **Step 2: Commit**

```bash
git add docs/data-ingestion-readme.md
git commit -m "docs: add data ingestion readme"
```

---

## Plan Review Loop

After saving the plan:

1.  Dispatch a single plan-document-reviewer subagent with the path to this plan and the spec document (`case/Trading_Strategy_Platform_Requirements.md`).
2.  If Issues Found: fix the issues, re-dispatch reviewer for the whole plan.
3.  If Approved: proceed to execution handoff.

**Review context:**
- Plan path: `docs/superpowers/plans/2026-03-17-smart-trading-data-ingestion.md`
- Spec path: `case/Trading_Strategy_Platform_Requirements.md`

I will now dispatch the subagent.<tool_call>
<function=task>
<parameter=description>Review data ingestion plan