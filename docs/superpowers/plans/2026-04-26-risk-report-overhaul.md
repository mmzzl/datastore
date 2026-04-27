# Risk Report Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix broken risk report auto-generation and overhaul with real risk metrics, portfolio analysis, stress testing, and trend visualization.

**Architecture:** Three-phase incremental approach — Phase 1 fixes core bugs (scheduler, code format, fabricated data), Phase 2 adds real risk indicator calculations, Phase 3 adds stress testing, historical scenarios, and trend visualization. Each phase produces working, testable software.

**Tech Stack:** Python 3.12, FastAPI, MongoDB, numpy, pandas, Vue 3, Naive UI, ECharts

---

## Phase 1: Fix Existing Issues

### Task 1: Fix Stock Code Format Mismatch in risk_report.py

**Files:**
- Modify: `apps/api/app/risk/risk_report.py:86-92` (add `_normalize_code` and apply in `_get_kline_data`)
- Modify: `apps/api/app/risk/risk_report.py:114-117` (apply in `_calculate_position_var`)

- [ ] **Step 1: Add `_normalize_code` method to `RiskReportGenerator`**

Insert after line 84 (after `_get_risk_collection` method):

```python
def _normalize_code(self, code: str) -> str:
    if code.startswith("SH") or code.startswith("SZ"):
        return code[2:]
    return code
```

- [ ] **Step 2: Apply `_normalize_code` in `_get_kline_data`**

Change line 92 from:
```python
return storage.get_kline(code, start_date=start_date, end_date=end_date, limit=days + 30)
```
to:
```python
normalized = self._normalize_code(code)
return storage.get_kline(normalized, start_date=start_date, end_date=end_date, limit=days + 30)
```

- [ ] **Step 3: Apply `_normalize_code` in `_calculate_position_var`**

Change line 115 from:
```python
kline_data = await asyncio.to_thread(self._get_kline_data, code, self.LOOKBACK_DAYS)
```
to:
```python
kline_data = await asyncio.to_thread(self._get_kline_data, self._normalize_code(code), self.LOOKBACK_DAYS)
```

- [ ] **Step 4: Verify by running the backend**

Run: `py -3.12 -c "from apps.api.app.risk.risk_report import RiskReportGenerator; g = RiskReportGenerator(); print(g._normalize_code('SH600000')); print(g._normalize_code('600000'))"`

Expected output: `600000` then `600000`

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/risk/risk_report.py
git commit -m "fix: normalize stock code format (strip SH/SZ prefix) for kline queries"
```

### Task 2: Fix Double Industry Lookup and Add Caching in risk_report.py

**Files:**
- Modify: `apps/api/app/risk/risk_report.py:135-179` (optimize `_get_industry` calls with cache)

- [ ] **Step 1: Add industry cache to `__init__`**

Change the `__init__` method (line 64-66) from:
```python
def __init__(self, storage: Optional[MongoStorage] = None):
    self._storage = storage
    self._risk_collection = None
```
to:
```python
def __init__(self, storage: Optional[MongoStorage] = None):
    self._storage = storage
    self._risk_collection = None
    self._industry_cache: Dict[str, Optional[str]] = {}
```

- [ ] **Step 2: Add caching to `_get_industry`**

Change the `_get_industry` method (lines 135-144) to:
```python
async def _get_industry(self, code: str) -> Optional[str]:
    normalized = self._normalize_code(code)
    if normalized in self._industry_cache:
        return self._industry_cache[normalized]
    storage = self._get_storage()
    try:
        stock_info_coll = storage.db.get_collection("stock_info")
        doc = await asyncio.to_thread(stock_info_coll.find_one, {"code": normalized})
        industry = doc.get("industry") if doc else None
    except Exception as e:
        logger.warning(f"Failed to get industry for {code}: {e}")
        industry = None
    self._industry_cache[normalized] = industry
    return industry
```

- [ ] **Step 3: Simplify `_calculate_industry_concentrations` to avoid double lookup**

Replace the entire `_calculate_industry_concentrations` method (lines 146-180) with:
```python
async def _calculate_industry_concentrations(
    self, positions: List[Dict[str, Any]], price_fetcher: Callable[[str], float]
) -> List[IndustryConcentration]:
    industry_values: Dict[str, float] = {}
    industry_counts: Dict[str, int] = {}
    total_value = 0.0
    for pos in positions:
        code = pos.get("code", "")
        quantity = pos.get("quantity", 0)
        price = price_fetcher(code) if quantity > 0 else 0
        value = quantity * price
        if value <= 0:
            continue
        total_value += value
        industry = await self._get_industry(code) or "未知"
        industry_values[industry] = industry_values.get(industry, 0) + value
        industry_counts[industry] = industry_counts.get(industry, 0) + 1
    if total_value <= 0:
        return []
    concentrations = []
    for industry, value in industry_values.items():
        pct = value / total_value
        concentrations.append(
            IndustryConcentration(
                industry=industry,
                allocation_pct=pct,
                position_count=industry_counts.get(industry, 0),
                value=value,
            )
        )
    return sorted(concentrations, key=lambda x: x.allocation_pct, reverse=True)
```

- [ ] **Step 4: Commit**

```bash
git add apps/api/app/risk/risk_report.py
git commit -m "fix: add industry cache and eliminate double lookup in risk report"
```

### Task 3: Remove Fabricated Metrics from API

**Files:**
- Modify: `apps/api/app/risk/api.py:167-180` (list endpoint fabricated metrics)
- Modify: `apps/api/app/risk/api.py:283-298` (detail endpoint fabricated metrics)

- [ ] **Step 1: Replace fabricated metrics in `get_risk_reports` list endpoint**

Replace lines 167-180 (the `metrics = {...}` block) with:
```python
metrics = {
    "var_95": portfolio_risk.get("portfolio_var_95"),
    "var_99": portfolio_risk.get("var_99") or portfolio_risk.get("portfolio_var_99"),
    "expected_shortfall": portfolio_risk.get("expected_shortfall"),
    "beta": portfolio_risk.get("beta"),
    "volatility": portfolio_risk.get("volatility"),
    "max_drawdown": portfolio_risk.get("max_drawdown"),
    "concentration_risk": max(
        (c.get("allocation_pct", 0) for c in portfolio_risk.get("industry_concentrations", [])),
        default=0
    ),
}
```

- [ ] **Step 2: Replace fabricated metrics in `get_risk_report` detail endpoint**

Replace lines 283-298 (the `if "metrics" not in doc:` block) with:
```python
if "metrics" not in doc:
    portfolio_risk = doc.get("portfolio_risk", {})
    doc["metrics"] = {
        "var_95": portfolio_risk.get("portfolio_var_95"),
        "var_99": portfolio_risk.get("var_99") or portfolio_risk.get("portfolio_var_99"),
        "expected_shortfall": portfolio_risk.get("expected_shortfall"),
        "beta": portfolio_risk.get("beta"),
        "volatility": portfolio_risk.get("volatility"),
        "max_drawdown": portfolio_risk.get("max_drawdown"),
        "concentration_risk": max(
            (c.get("allocation_pct", 0) for c in portfolio_risk.get("industry_concentrations", [])),
            default=0
        ),
    }
```

- [ ] **Step 3: Commit**

```bash
git add apps/api/app/risk/api.py
git commit -m "fix: remove fabricated risk metrics from API, use real data from report"
```

### Task 4: Remove Frontend Random Data Fallbacks

**Files:**
- Modify: `frontend/vue-admin/src/views/RiskReportView.vue:181-193` (holdingsRiskData computed)
- Modify: `frontend/vue-admin/src/views/RiskReportView.vue:32-45` (riskScore computed fallback)

- [ ] **Step 1: Replace random fallbacks in `holdingsRiskData`**

Replace lines 181-193 with:
```typescript
const holdingsRiskData = computed(() => {
  if (!currentReport.value?.holdings_risk) return []
  return currentReport.value.holdings_risk.map((h: any, idx: number) => ({
    ...h,
    key: h.code || idx,
    pnl_percent: h.pnl_percent ?? null,
    current_price: h.current_price ?? null,
    quantity: h.quantity ?? null,
    average_cost: h.average_cost ?? null,
    risk_score: h.risk_score ?? null,
    var_value: h.var_contribution ?? null,
  }))
})
```

- [ ] **Step 2: Update table column renderers to handle null values**

Replace `holdingsColumns` (lines 195-245) with:
```typescript
const holdingsColumns: DataTableColumns = [
  { title: '代码', key: 'code', width: 100 },
  { title: '名称', key: 'name', width: 100 },
  {
    title: '盈亏%',
    key: 'pnl_percent',
    width: 80,
    render: (row: any) => {
      const pnl = row.pnl_percent
      if (pnl === null || pnl === undefined) return h('span', { style: { color: '#999' } }, '—')
      const color = pnl >= 0 ? '#10b981' : '#ef4444'
      return h('span', { style: { color } }, `${pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}%`)
    }
  },
  {
    title: '风险分',
    key: 'risk_score',
    width: 80,
    sorter: (a: any, b: any) => (a.risk_score ?? 0) - (b.risk_score ?? 0),
    render: (row: any) => {
      const score = row.risk_score
      if (score === null || score === undefined) return h('span', { style: { color: '#999' } }, '—')
      let type: 'success' | 'warning' | 'error' = 'success'
      if (score > 60) type = 'error'
      else if (score > 30) type = 'warning'
      return h(NTag, { type, size: 'small' }, () => score)
    }
  },
  {
    title: '数量',
    key: 'quantity',
    width: 80,
    render: (row: any) => row.quantity !== null ? row.quantity?.toLocaleString() : '—'
  },
  {
    title: '成本',
    key: 'average_cost',
    width: 80,
    render: (row: any) => row.average_cost !== null ? `¥${row.average_cost.toFixed(2)}` : '—'
  },
  {
    title: '现价',
    key: 'current_price',
    width: 80,
    render: (row: any) => row.current_price !== null ? `¥${row.current_price.toFixed(2)}` : '—'
  },
  {
    title: 'VaR',
    key: 'var_value',
    width: 80,
    render: (row: any) => row.var_value !== null ? `¥${row.var_value.toFixed(0)}` : '—'
  }
]
```

- [ ] **Step 3: Update riskScore computed to not use fabricated fallback**

Replace lines 32-45 with:
```typescript
const riskScore = computed(() => {
  if (currentReport.value?.risk_score !== undefined && currentReport.value?.risk_score !== null) {
    return currentReport.value.risk_score
  }
  return null
})
```

- [ ] **Step 4: Add stale data warning indicator**

After the `<NSpin>` opening tag (line 354), add before the `<template v-if="currentReport">`:
```html
<NAlert v-if="isStale" type="warning" class="mb-4">
  报告数据可能已过时（报告日期：{{ reportDate }}），请确认调度器正常运行
</NAlert>
```

Add these computed properties in the `<script setup>` after `riskLevel`:
```typescript
const reportDate = computed(() => currentReport.value?.date || currentReport.value?.created_at?.split('T')[0] || '')

const isStale = computed(() => {
  if (!reportDate.value) return true
  const reportDay = new Date(reportDate.value)
  const today = new Date()
  const diffDays = Math.floor((today.getTime() - reportDay.getTime()) / (1000 * 60 * 60 * 24))
  return diffDays > 1
})
```

- [ ] **Step 5: Commit**

```bash
git add frontend/vue-admin/src/views/RiskReportView.vue
git commit -m "fix: remove Math.random() fallbacks, show dash for missing data, add stale warning"
```

### Task 5: Add Risk Report Job to Standalone Scheduler

**Files:**
- Modify: `apps/api/scheduler_standalone.py:200-302` (add job function and scheduler entry)

- [ ] **Step 1: Add `run_risk_report_job` function**

Insert after `run_qlib_top_stocks_job` function (after line 199):

```python
def run_risk_report_job():
    if datetime.now().weekday() >= 5:
        logging.info("Skipping risk report job: weekend")
        return
    try:
        import asyncio
        from app.scheduler.risk_report_job import RiskReportJob
        from app.storage.mongo_client import MongoStorage

        storage = MongoStorage(
            host=settings.mongodb_host,
            port=settings.mongodb_port,
            db_name=settings.mongodb_database,
            username=settings.mongodb_username,
            password=settings.mongodb_password,
        )
        storage.connect()
        holdings_coll = storage.db.get_collection("holdings")
        user_ids = holdings_coll.distinct("user_id")
        storage.close()

        if not user_ids:
            logging.info("No users with holdings found, skipping risk report")
            return

        config = build_config()
        config["user_ids"] = user_ids
        job = RiskReportJob(config)
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(job.run(config))
            logging.info(f"Risk report job result: {result}")
        finally:
            loop.close()
    except Exception as e:
        logging.error(f"Risk report job failed: {e}")
        logging.error(traceback.format_exc())
```

- [ ] **Step 2: Add scheduler entry in `setup_scheduler`**

Insert after the `qlib_top_stocks_job` scheduler entry (after line 302, before line 304):

```python
scheduler.add_job(
    run_risk_report_job,
    "cron",
    hour=15,
    minute=35,
    timezone=timezone,
    id="risk_report_job",
    misfire_grace_time=3600,
    coalesce=True,
)
```

- [ ] **Step 3: Verify scheduler loads without errors**

Run: `py -3.12 -c "import sys; sys.path.insert(0, 'apps/api'); from scheduler_standalone import setup_scheduler; print('OK')"`

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add apps/api/scheduler_standalone.py
git commit -m "feat: add risk report job to standalone scheduler (daily 15:35)"
```

### Task 6: Fix run_risk_report.py Default User

**Files:**
- Modify: `apps/api/run_risk_report.py:27-28` (remove hardcoded "admin")

- [ ] **Step 1: Replace hardcoded user_ids with auto-discovery**

Replace lines 26-31 with:
```python
async def main():
    logger.info("Starting manual risk report generation...")

    from app.storage.mongo_client import MongoStorage
    storage = MongoStorage(
        host=settings.mongodb_host,
        port=settings.mongodb_port,
        db_name=settings.mongodb_database,
        username=settings.mongodb_username,
        password=settings.mongodb_password,
    )
    storage.connect()
    holdings_coll = storage.db.get_collection("holdings")
    user_ids = holdings_coll.distinct("user_id")
    storage.close()

    if not user_ids:
        logger.warning("No users with holdings found")
        return

    config = {
        "user_ids": user_ids,
        "dingtalk_webhook": settings.after_market_dingtalk_webhook,
        "dingtalk_secret": settings.after_market_dingtalk_secret,
    }
```

- [ ] **Step 2: Commit**

```bash
git add apps/api/run_risk_report.py
git commit -m "fix: auto-discover user IDs from holdings instead of hardcoding admin"
```

---

## Phase 2: Enhanced Risk Indicators

### Task 7: Extend PositionRisk and PortfolioRisk Data Models

**Files:**
- Modify: `apps/api/app/risk/risk_report.py:14-43` (add new fields to dataclasses)

- [ ] **Step 1: Add new fields to `PositionRisk`**

Replace the `PositionRisk` dataclass (lines 14-24) with:
```python
@dataclass
class PositionRisk:
    code: str
    name: Optional[str]
    quantity: float
    cost_price: float
    current_price: float
    pnl_pct: float
    var_95: float
    risk_score: int
    industry: Optional[str] = None
    var_99: float = 0.0
    expected_shortfall: float = 0.0
    volatility: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    beta: float = 0.0
    liquidity_days: float = 0.0
    marginal_var: float = 0.0
```

- [ ] **Step 2: Add new fields to `PortfolioRisk`**

Replace the `PortfolioRisk` dataclass (lines 35-42) with:
```python
@dataclass
class PortfolioRisk:
    total_value: float
    total_cost: float
    portfolio_var_95: float
    industry_concentrations: List[IndustryConcentration] = field(default_factory=list)
    var_warning: bool = False
    concentration_warning: bool = False
    var_99: float = 0.0
    expected_shortfall: float = 0.0
    volatility: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    beta: float = 0.0
    concentration_score: float = 0.0
    liquidity_risk: Dict[str, Any] = field(default_factory=dict)
    style_exposure: Dict[str, float] = field(default_factory=dict)
    correlation_matrix: Optional[List[List[float]]] = None
    correlation_labels: Optional[List[str]] = None
    high_correlation_pairs: Optional[List[Dict[str, Any]]] = None
```

- [ ] **Step 3: Add `StressScenario` and `StressTestResult` dataclasses**

Insert after the `PortfolioRisk` dataclass, before `RiskReport`:
```python
@dataclass
class StressScenario:
    name: str
    description: str
    market_shock: float
    estimated_loss: float
    estimated_loss_pct: float

@dataclass
class StressTestResult:
    scenarios: List[StressScenario] = field(default_factory=list)
    industry_shock: List[StressScenario] = field(default_factory=list)
    liquidity_crisis: Optional[StressScenario] = None
```

- [ ] **Step 4: Add `stress_test` field to `RiskReport`**

Add after `recommendations` field in the `RiskReport` dataclass:
```python
    stress_test: Optional[StressTestResult] = None
```

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/risk/risk_report.py
git commit -m "feat: extend risk data models with VaR99, CVaR, volatility, drawdown, sharpe, beta, stress test"
```

### Task 8: Implement Real Risk Calculation Methods

**Files:**
- Modify: `apps/api/app/risk/risk_report.py:58-200` (add calculation methods to RiskReportGenerator)

- [ ] **Step 1: Add import for numpy**

Add `import numpy as np` after the existing imports (line 7).

- [ ] **Step 1b: Update `_calculate_var_95` to use `np.percentile` for consistency**

Replace the `_calculate_var_95` method (lines 94-100) with:
```python
def _calculate_var_95(self, returns: List[float]) -> float:
    if not returns or len(returns) < 10:
        return 0.0
    arr = np.array(returns)
    return float(abs(np.percentile(arr, 5)))
```

- [ ] **Step 2: Add `_calculate_var_99` method**

Insert after `_calculate_var_95` method (after line 100):
```python
def _calculate_var_99(self, returns: List[float]) -> float:
    if not returns or len(returns) < 10:
        return 0.0
    arr = np.array(returns)
    return float(abs(np.percentile(arr, 1)))
```

- [ ] **Step 3: Add `_calculate_expected_shortfall` method**

```python
def _calculate_expected_shortfall(self, returns: List[float]) -> float:
    if not returns or len(returns) < 10:
        return 0.0
    arr = np.array(returns)
    threshold = np.percentile(arr, 5)
    tail = arr[arr <= threshold]
    if len(tail) == 0:
        return self._calculate_var_95(returns)
    return abs(float(np.mean(tail)))
```

- [ ] **Step 4: Add `_calculate_volatility` method**

```python
def _calculate_volatility(self, returns: List[float]) -> float:
    if not returns or len(returns) < 10:
        return 0.0
    return float(np.std(returns, ddof=1) * np.sqrt(252))
```

- [ ] **Step 5: Add `_calculate_max_drawdown` method**

```python
def _calculate_max_drawdown(self, kline_data: List[Dict[str, Any]]) -> float:
    if not kline_data or len(kline_data) < 2:
        return 0.0
    sorted_data = sorted(kline_data, key=lambda x: x.get("date", ""))
    closes = np.array([d.get("close", 0) for d in sorted_data], dtype=float)
    if len(closes) < 2 or np.any(closes <= 0):
        return 0.0
    cummax = np.maximum.accumulate(closes)
    drawdowns = (cummax - closes) / cummax
    return float(np.max(drawdowns))
```

- [ ] **Step 6: Add `_calculate_sharpe_ratio` method**

```python
def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
    if not returns or len(returns) < 10:
        return 0.0
    arr = np.array(returns)
    annualized_return = float(np.mean(arr) * 252)
    annualized_vol = float(np.std(arr, ddof=1) * np.sqrt(252))
    if annualized_vol <= 0:
        return 0.0
    return (annualized_return - 0.03) / annualized_vol
```

- [ ] **Step 7: Add `_calculate_beta` method**

```python
async def _calculate_beta(self, code: str) -> float:
    kline_data = await asyncio.to_thread(
        self._get_kline_data, self._normalize_code(code), self.LOOKBACK_DAYS
    )
    returns = self._calculate_returns(kline_data)
    if not returns or len(returns) < 30:
        return 0.0
    market_kline = await asyncio.to_thread(
        self._get_kline_data, "sh.000300", self.LOOKBACK_DAYS
    )
    market_returns = self._calculate_returns(market_kline)
    if not market_returns or len(market_returns) < 30:
        return 0.0
    min_len = min(len(returns), len(market_returns))
    stock_arr = np.array(returns[:min_len])
    market_arr = np.array(market_returns[:min_len])
    cov_matrix = np.cov(stock_arr, market_arr)
    market_var = np.var(market_arr, ddof=1)
    if market_var <= 0:
        return 0.0
    return float(cov_matrix[0][1] / market_var)
```

- [ ] **Step 8: Add `_calculate_liquidity_days` method**

```python
def _calculate_liquidity_days(self, kline_data: List[Dict[str, Any]], position_value: float) -> float:
    if not kline_data or position_value <= 0:
        return 0.0
    sorted_data = sorted(kline_data, key=lambda x: x.get("date", ""))
    recent = sorted_data[-20:] if len(sorted_data) >= 20 else sorted_data
    volumes = [d.get("volume", 0) for d in recent]
    closes = [d.get("close", 0) for d in recent]
    daily_values = [v * c for v, c in zip(volumes, closes) if v > 0 and c > 0]
    if not daily_values:
        return 0.0
    avg_daily_value = float(np.mean(daily_values))
    if avg_daily_value <= 0:
        return 0.0
    return position_value / (avg_daily_value * 0.1)
```

- [ ] **Step 9: Add `_calculate_concentration_score` (HHI) method**

```python
def _calculate_concentration_score(self, positions_risk: List[PositionRisk]) -> float:
    total_value = sum(p.quantity * p.current_price for p in positions_risk)
    if total_value <= 0:
        return 0.0
    weights = [(p.quantity * p.current_price) / total_value for p in positions_risk]
    return sum(w * w for w in weights) * 100
```

- [ ] **Step 10: Add `_calculate_correlation_matrix` method**

```python
async def _calculate_correlation_matrix(
    self, positions: List[Dict[str, Any]]
) -> tuple:
    codes = [p.get("code", "") for p in positions if p.get("quantity", 0) > 0]
    if len(codes) < 2:
        return None, None, []
    returns_dict = {}
    for code in codes:
        kline_data = await asyncio.to_thread(
            self._get_kline_data, self._normalize_code(code), self.LOOKBACK_DAYS
        )
        returns = self._calculate_returns(kline_data)
        if len(returns) >= 30:
            returns_dict[code] = returns
    if len(returns_dict) < 2:
        return None, None, []
    min_len = min(len(r) for r in returns_dict.values())
    aligned = {code: r[-min_len:] for code, r in returns_dict.items()}
    codes_ordered = list(aligned.keys())
    matrix = np.corrcoef([aligned[c] for c in codes_ordered])
    high_pairs = []
    for i in range(len(codes_ordered)):
        for j in range(i + 1, len(codes_ordered)):
            corr = float(matrix[i][j])
            if abs(corr) > 0.7:
                high_pairs.append({
                    "code_1": codes_ordered[i],
                    "code_2": codes_ordered[j],
                    "correlation": round(corr, 3),
                })
    return matrix.tolist(), codes_ordered, high_pairs
```

- [ ] **Step 11: Commit**

```bash
git add apps/api/app/risk/risk_report.py
git commit -m "feat: add real risk calculation methods (VaR99, CVaR, vol, MDD, sharpe, beta, liquidity, HHI, correlation)"
```

### Task 9: Integrate New Calculations into generate_report

**Files:**
- Modify: `apps/api/app/risk/risk_report.py:264-344` (update `generate_report` method)
- Modify: `apps/api/app/risk/risk_report.py:346-393` (update `save_report` to persist new fields)

- [ ] **Step 1: Update `generate_report` to calculate per-position new metrics**

Replace the position risk creation block inside the `for holding in holdings:` loop (lines 282-308) with:
```python
        var_95 = await self._calculate_position_var(code)
        var_99 = await self._calculate_position_var_99(code)
        kline_data = await asyncio.to_thread(
            self._get_kline_data, self._normalize_code(code), self.LOOKBACK_DAYS
        )
        returns = self._calculate_returns(kline_data)
        expected_shortfall = self._calculate_expected_shortfall(returns)
        volatility = self._calculate_volatility(returns)
        max_drawdown = self._calculate_max_drawdown(kline_data)
        sharpe_ratio = self._calculate_sharpe_ratio(returns)
        beta = await self._calculate_beta(code)
        position_value = quantity * current_price
        liquidity_days = self._calculate_liquidity_days(kline_data, position_value)
        total_value = sum(
            h.get("quantity", 0) * price_fetcher(h.get("code", ""))
            for h in holdings
            if h.get("quantity", 0) > 0
        )
        var_contribution = (
            position_value * var_95 / total_value if total_value > 0 else 0
        )
        risk_score = self._calculate_position_risk_score(
            pnl_pct, var_95, var_contribution
        )
        industry = await self._get_industry(code)
        positions_risk.append(
            PositionRisk(
                code=code,
                name=name,
                quantity=quantity,
                cost_price=cost_price,
                current_price=current_price,
                pnl_pct=pnl_pct,
                var_95=var_95,
                risk_score=risk_score,
                industry=industry,
                var_99=var_99,
                expected_shortfall=expected_shortfall,
                volatility=volatility,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                beta=beta,
                liquidity_days=liquidity_days,
                marginal_var=0.0,
            )
        )
```

- [ ] **Step 2: Add `_calculate_position_var_99` helper method**

Insert after `_calculate_position_var`:
```python
async def _calculate_position_var_99(self, code: str) -> float:
    kline_data = await asyncio.to_thread(
        self._get_kline_data, self._normalize_code(code), self.LOOKBACK_DAYS
    )
    returns = self._calculate_returns(kline_data)
    return self._calculate_var_99(returns)
```

- [ ] **Step 3: Update portfolio risk creation with new fields**

Replace the portfolio risk creation block (lines 309-325) with:
```python
    concentrations = await self._calculate_industry_concentrations(holdings, price_fetcher)
    portfolio_var = await self._calculate_portfolio_var(holdings, price_fetcher)
    portfolio_var_99 = await self._calculate_portfolio_var_99(holdings, price_fetcher)
    total_value = sum(p.quantity * p.current_price for p in positions_risk)
    total_cost = sum(p.quantity * p.cost_price for p in positions_risk)
    var_warning = portfolio_var > self.VAR_THRESHOLD
    concentration_warning = any(
        c.allocation_pct > self.INDUSTRY_CONCENTRATION_THRESHOLD
        for c in concentrations
    )
    concentration_score = self._calculate_concentration_score(positions_risk)
    corr_matrix, corr_labels, high_corr_pairs = await self._calculate_correlation_matrix(holdings)
    portfolio_returns = self._calculate_portfolio_returns(positions_risk)
    portfolio_es = self._calculate_expected_shortfall(portfolio_returns)
    portfolio_vol = self._calculate_volatility(portfolio_returns)
    portfolio_mdd = self._calculate_portfolio_max_drawdown(positions_risk)
    portfolio_sharpe = self._calculate_sharpe_ratio(portfolio_returns)
    portfolio_beta = self._calculate_weighted_beta(positions_risk)
    liquidity_risk = self._calculate_portfolio_liquidity_risk(positions_risk)
    portfolio_risk = PortfolioRisk(
        total_value=total_value,
        total_cost=total_cost,
        portfolio_var_95=portfolio_var,
        industry_concentrations=concentrations,
        var_warning=var_warning,
        concentration_warning=concentration_warning,
        var_99=portfolio_var_99,
        expected_shortfall=portfolio_es,
        volatility=portfolio_vol,
        max_drawdown=portfolio_mdd,
        sharpe_ratio=portfolio_sharpe,
        beta=portfolio_beta,
        concentration_score=concentration_score,
        liquidity_risk=liquidity_risk,
        style_exposure={},
        correlation_matrix=corr_matrix,
        correlation_labels=corr_labels,
        high_correlation_pairs=high_corr_pairs,
    )
```

- [ ] **Step 4: Add helper methods for portfolio-level calculations**

Insert before `generate_report`:
```python
async def _calculate_portfolio_var_99(
    self, positions: List[Dict[str, Any]], price_fetcher: Callable[[str], float]
) -> float:
    total_var = 0.0
    total_value = 0.0
    for pos in positions:
        code = pos.get("code", "")
        quantity = pos.get("quantity", 0)
        if quantity <= 0:
            continue
        price = price_fetcher(code)
        value = quantity * price
        var = await self._calculate_position_var_99(code)
        total_var += value * var
        total_value += value
    if total_value <= 0:
        return 0.0
    return total_var / total_value

def _calculate_portfolio_returns(self, positions_risk: List[PositionRisk]) -> List[float]:
    if not positions_risk:
        return []
    total_value = sum(p.quantity * p.current_price for p in positions_risk)
    if total_value <= 0:
        return []
    weights = [(p.quantity * p.current_price) / total_value for p in positions_risk]
    min_len = min(
        (len(self._calculate_returns(
            self._get_kline_data(self._normalize_code(p.code), self.LOOKBACK_DAYS)
        )) for p in positions_risk if p.current_price > 0),
        default=0
    )
    if min_len < 2:
        return []
    portfolio_returns = [0.0] * min_len
    for i, pos in enumerate(positions_risk):
        if pos.current_price <= 0 or weights[i] <= 0:
            continue
        kline_data = self._get_kline_data(self._normalize_code(pos.code), self.LOOKBACK_DAYS)
        returns = self._calculate_returns(kline_data)
        for j in range(min_len):
            offset = len(returns) - min_len
            portfolio_returns[j] += weights[i] * returns[offset + j]
    return portfolio_returns

def _calculate_portfolio_max_drawdown(self, positions_risk: List[PositionRisk]) -> float:
    returns = self._calculate_portfolio_returns(positions_risk)
    if not returns:
        return 0.0
    cum_returns = np.cumprod(np.array(returns) + 1)
    cummax = np.maximum.accumulate(cum_returns)
    drawdowns = (cummax - cum_returns) / cummax
    return float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

def _calculate_weighted_beta(self, positions_risk: List[PositionRisk]) -> float:
    total_value = sum(p.quantity * p.current_price for p in positions_risk if p.beta > 0)
    if total_value <= 0:
        return 0.0
    return sum(
        (p.quantity * p.current_price) * p.beta / total_value
        for p in positions_risk if p.beta > 0
    )

def _calculate_portfolio_liquidity_risk(self, positions_risk: List[PositionRisk]) -> Dict[str, Any]:
    if not positions_risk:
        return {}
    max_days = max((p.liquidity_days for p in positions_risk), default=0)
    high_liquidity = [p.code for p in positions_risk if p.liquidity_days > 5]
    return {
        "max_liquidity_days": round(max_days, 1),
        "high_liquidity_positions": high_liquidity,
    }
```

- [ ] **Step 5: Add high-correlation recommendations**

Add after the existing recommendation generation in `_generate_recommendations` (before the `if risk_level == "high"` block):
```python
    if hasattr(portfolio_risk, 'high_correlation_pairs') and portfolio_risk.high_correlation_pairs:
        for pair in portfolio_risk.high_correlation_pairs[:3]:
            recommendations.append(
                f"【注意】{pair['code_1']}与{pair['code_2']}相关性较高({pair['correlation']:.2f})，分散化效果有限"
            )
```

- [ ] **Step 6: Update `save_report` to persist new fields**

Replace the `holdings_risk` serialization in `save_report` (lines 355-367) with:
```python
        "holdings_risk": [
            {
                "code": p.code,
                "name": p.name,
                "quantity": p.quantity,
                "cost_price": p.cost_price,
                "current_price": p.current_price,
                "pnl_pct": p.pnl_pct,
                "var_95": p.var_95,
                "risk_score": p.risk_score,
                "industry": p.industry,
                "var_99": p.var_99,
                "expected_shortfall": p.expected_shortfall,
                "volatility": p.volatility,
                "max_drawdown": p.max_drawdown,
                "sharpe_ratio": p.sharpe_ratio,
                "beta": p.beta,
                "liquidity_days": p.liquidity_days,
                "marginal_var": p.marginal_var,
            }
            for p in report.holdings_risk
        ],
```

Replace the `portfolio_risk` serialization in `save_report` (lines 369-384) with:
```python
        "portfolio_risk": {
            "total_value": report.portfolio_risk.total_value,
            "total_cost": report.portfolio_risk.total_cost,
            "portfolio_var_95": report.portfolio_risk.portfolio_var_95,
            "industry_concentrations": [
                {
                    "industry": c.industry,
                    "allocation_pct": c.allocation_pct,
                    "position_count": c.position_count,
                    "value": c.value,
                }
                for c in report.portfolio_risk.industry_concentrations
            ],
            "var_warning": report.portfolio_risk.var_warning,
            "concentration_warning": report.portfolio_risk.concentration_warning,
            "var_99": report.portfolio_risk.var_99,
            "expected_shortfall": report.portfolio_risk.expected_shortfall,
            "volatility": report.portfolio_risk.volatility,
            "max_drawdown": report.portfolio_risk.max_drawdown,
            "sharpe_ratio": report.portfolio_risk.sharpe_ratio,
            "beta": report.portfolio_risk.beta,
            "concentration_score": report.portfolio_risk.concentration_score,
            "liquidity_risk": report.portfolio_risk.liquidity_risk,
            "style_exposure": report.portfolio_risk.style_exposure,
            "correlation_matrix": report.portfolio_risk.correlation_matrix,
            "correlation_labels": report.portfolio_risk.correlation_labels,
            "high_correlation_pairs": report.portfolio_risk.high_correlation_pairs,
        },
```

Add after `"recommendations": report.recommendations,`:
```python
        "stress_test": None,
```

- [ ] **Step 7: Commit**

```bash
git add apps/api/app/risk/risk_report.py
git commit -m "feat: integrate real risk calculations into report generation and persistence"
```

### Task 10: Update API to Expose New Fields

**Files:**
- Modify: `apps/api/app/risk/api.py:167-210` (list endpoint)
- Modify: `apps/api/app/risk/api.py:264-298` (detail endpoint)

- [ ] **Step 1: Update list endpoint holdings_risk mapping**

Replace the holdings_risk construction in list endpoint (lines 198-210) with:
```python
        holdings_risk.append({
            "code": code,
            "name": name,
            "industry": industry,
            "weight": weight,
            "contribution_to_risk": h.get("var_95", 0),
            "var_contribution": h.get("var_95", 0),
            "average_cost": h.get("cost_price", 0),
            "current_price": current_price,
            "quantity": quantity,
            "pnl_percent": h.get("pnl_pct", 0) * 100 if h.get("pnl_pct") is not None else None,
            "risk_score": h.get("risk_score"),
            "var_99": h.get("var_99"),
            "expected_shortfall": h.get("expected_shortfall"),
            "volatility": h.get("volatility"),
            "max_drawdown": h.get("max_drawdown"),
            "sharpe_ratio": h.get("sharpe_ratio"),
            "beta": h.get("beta"),
            "liquidity_days": h.get("liquidity_days"),
            "marginal_var": h.get("marginal_var"),
        })
```

- [ ] **Step 2: Update list endpoint metrics to use real data**

The metrics block was already updated in Task 3. Verify it now reads:
```python
metrics = {
    "var_95": portfolio_risk.get("portfolio_var_95"),
    "var_99": portfolio_risk.get("var_99"),
    "expected_shortfall": portfolio_risk.get("expected_shortfall"),
    "beta": portfolio_risk.get("beta"),
    "volatility": portfolio_risk.get("volatility"),
    "max_drawdown": portfolio_risk.get("max_drawdown"),
    "concentration_risk": max(
        (c.get("allocation_pct", 0) for c in portfolio_risk.get("industry_concentrations", [])),
        default=0
    ),
    "concentration_score": portfolio_risk.get("concentration_score"),
    "sharpe_ratio": portfolio_risk.get("sharpe_ratio"),
}
```

Add `concentration_score` and `sharpe_ratio` fields if not present.

- [ ] **Step 3: Update detail endpoint to include portfolio_risk top-level fields**

After the metrics block in the detail endpoint, add:
```python
    doc["portfolio_risk"]["var_99"] = doc["portfolio_risk"].get("var_99")
    doc["portfolio_risk"]["expected_shortfall"] = doc["portfolio_risk"].get("expected_shortfall")
    doc["portfolio_risk"]["volatility"] = doc["portfolio_risk"].get("volatility")
    doc["portfolio_risk"]["max_drawdown"] = doc["portfolio_risk"].get("max_drawdown")
    doc["portfolio_risk"]["sharpe_ratio"] = doc["portfolio_risk"].get("sharpe_ratio")
    doc["portfolio_risk"]["beta"] = doc["portfolio_risk"].get("beta")
    doc["portfolio_risk"]["concentration_score"] = doc["portfolio_risk"].get("concentration_score")
    doc["portfolio_risk"]["liquidity_risk"] = doc["portfolio_risk"].get("liquidity_risk", {})
    doc["portfolio_risk"]["high_correlation_pairs"] = doc["portfolio_risk"].get("high_correlation_pairs", [])
```

- [ ] **Step 4: Commit**

```bash
git add apps/api/app/risk/api.py
git commit -m "feat: expose new risk metrics in API responses"
```

### Task 11: Update Frontend TypeScript Interfaces

**Files:**
- Modify: `frontend/vue-admin/src/services/api_risk.ts:3-50` (update interfaces and add trend API)

- [ ] **Step 1: Update `RiskReport` interface**

Replace the entire `RiskReport` interface (lines 3-26) with:
```typescript
interface RiskReport {
  id: string
  name: string
  type: 'daily' | 'weekly' | 'monthly'
  date: string
  portfolio_value: number
  risk_score?: number
  risk_level?: string
  metrics: {
    var_95: number | null
    var_99: number | null
    expected_shortfall: number | null
    beta: number | null
    volatility: number | null
    max_drawdown: number | null
    concentration_risk: number
    concentration_score?: number | null
    sharpe_ratio?: number | null
  }
  holdings_risk?: Array<{
    code: string
    name: string
    industry?: string
    weight: number
    contribution_to_risk: number
    var_contribution: number
    pnl_percent?: number | null
    current_price?: number | null
    quantity?: number | null
    average_cost?: number | null
    risk_score?: number | null
    var_99?: number | null
    expected_shortfall?: number | null
    volatility?: number | null
    max_drawdown?: number | null
    sharpe_ratio?: number | null
    beta?: number | null
    liquidity_days?: number | null
    marginal_var?: number | null
  }>
  portfolio_risk?: {
    total_value: number
    total_cost: number
    portfolio_var_95: number
    var_99?: number | null
    expected_shortfall?: number | null
    volatility?: number | null
    max_drawdown?: number | null
    sharpe_ratio?: number | null
    beta?: number | null
    concentration_score?: number | null
    liquidity_risk?: Record<string, any>
    high_correlation_pairs?: Array<{ code_1: string; code_2: string; correlation: number }>
    industry_concentrations?: Array<{
      industry: string
      allocation_pct: number
      position_count: number
      value: number
    }>
  }
  recommendations?: string[]
  created_at: string
}
```

- [ ] **Step 2: Add trend API interface and method**

Add after `RiskReport` interface:
```typescript
interface RiskTrend {
  dates: string[]
  risk_score: number[]
  var_95: number[]
  var_99: number[]
  max_drawdown: number[]
  sharpe_ratio: number[]
  concentration_score: number[]
}
```

Add to `apiRisk` object before closing:
```typescript
  async getTrend(userId: string, days: number = 30): Promise<RiskTrend> {
    const res = await api.get(`/risk/reports/${userId}/trend`, { params: { days } })
    return res.data
  },
```

Add `RiskTrend` to the export type line:
```typescript
export type { RiskReport, PaginatedReports, RiskTrend }
```

- [ ] **Step 3: Commit**

```bash
git add frontend/vue-admin/src/services/api_risk.ts
git commit -m "feat: update TypeScript interfaces with new risk metrics and trend API"
```

### Task 12: Redesign Frontend Risk Report Page

**Files:**
- Modify: `frontend/vue-admin/src/views/RiskReportView.vue` (full redesign)

- [ ] **Step 1: Add ECharts LineChart import**

Update the ECharts imports at the top of `<script setup>` to include `LineChart`:
```typescript
import { GaugeChart, PieChart, LineChart } from 'echarts/charts'
```

Add to the `use()` call:
```typescript
use([CanvasRenderer, GaugeChart, PieChart, LineChart, TitleComponent, TooltipComponent, LegendComponent])
```

- [ ] **Step 2: Add summary metrics cards computed**

Add after `riskLevel` computed:
```typescript
const summaryMetrics = computed(() => {
  const m = currentReport.value?.metrics
  const pr = currentReport.value?.portfolio_risk
  return {
    var95: m?.var_95 ?? pr?.portfolio_var_95 ?? null,
    var99: m?.var_99 ?? pr?.var_99 ?? null,
    maxDrawdown: m?.max_drawdown ?? pr?.max_drawdown ?? null,
    sharpeRatio: m?.sharpe_ratio ?? pr?.sharpe_ratio ?? null,
    beta: m?.beta ?? pr?.beta ?? null,
    volatility: m?.volatility ?? pr?.volatility ?? null,
    concentrationScore: m?.concentration_score ?? pr?.concentration_score ?? null,
  }
})

function formatPercent(val: number | null | undefined): string {
  if (val === null || val === undefined) return '—'
  return `${(val * 100).toFixed(2)}%`
}

function formatNumber(val: number | null | undefined, decimals: number = 2): string {
  if (val === null || val === undefined) return '—'
  return val.toFixed(decimals)
}
```

- [ ] **Step 3: Update the template with new layout**

Replace the entire `<template>` section with the new layout including summary cards, enhanced table, stress test section placeholder, and trend chart placeholder:
```html
<template>
  <div class="risk-report-view">
    <NCard title="风险报告">
      <template #header-extra>
        <NDatePicker
          v-model:value="selectedDate"
          type="date"
          placeholder="选择报告日期"
          :is-date-disabled="(ts: number) => ts > Date.now()"
        />
      </template>

      <NAlert v-if="store.state.error" type="error" class="mb-4">
        {{ store.state.error }}
      </NAlert>

      <NAlert v-if="isStale" type="warning" class="mb-4">
        报告数据可能已过时（报告日期：{{ reportDate }}），请确认调度器正常运行
      </NAlert>

      <NSpin :show="store.state.loading">
        <template v-if="currentReport">
          <NGrid :cols="24" :x-gap="16">
            <NGi :span="6">
              <NCard title="风险评分" class="gauge-card" :bordered="false">
                <div class="gauge-container">
                  <VChart v-if="riskScore !== null" :option="gaugeOption" autoresize style="height: 240px" />
                  <NEmpty v-else description="无数据" />
                </div>
                <div class="risk-badge" v-if="riskScore !== null">
                  <NTag :type="riskLevel.type" size="small">{{ riskLevel.text }}</NTag>
                </div>
              </NCard>
            </NGi>
            <NGi :span="18">
              <NGrid :cols="3" :x-gap="12" :y-gap="12">
                <NGi>
                  <NCard size="small" :bordered="false" class="metrics-card">
                    <NStatistic label="VaR 95%" :value="formatPercent(summaryMetrics.var95)" />
                  </NCard>
                </NGi>
                <NGi>
                  <NCard size="small" :bordered="false" class="metrics-card">
                    <NStatistic label="VaR 99%" :value="formatPercent(summaryMetrics.var99)" />
                  </NCard>
                </NGi>
                <NGi>
                  <NCard size="small" :bordered="false" class="metrics-card">
                    <NStatistic label="最大回撤" :value="formatPercent(summaryMetrics.maxDrawdown)" />
                  </NCard>
                </NGi>
                <NGi>
                  <NCard size="small" :bordered="false" class="metrics-card">
                    <NStatistic label="夏普比率" :value="formatNumber(summaryMetrics.sharpeRatio)" />
                  </NCard>
                </NGi>
                <NGi>
                  <NCard size="small" :bordered="false" class="metrics-card">
                    <NStatistic label="Beta" :value="formatNumber(summaryMetrics.beta)" />
                  </NCard>
                </NGi>
                <NGi>
                  <NCard size="small" :bordered="false" class="metrics-card">
                    <NStatistic label="波动率" :value="formatPercent(summaryMetrics.volatility)" />
                  </NCard>
                </NGi>
              </NGrid>
            </NGi>
          </NGrid>

          <NGrid :cols="24" :x-gap="16" style="margin-top: 16px;">
            <NGi :span="24">
              <NCard title="持仓风险明细" class="table-card">
                <NDataTable
                  :columns="holdingsColumns"
                  :data="holdingsRiskData"
                  :bordered="false"
                  :row-class-name="rowClassName"
                  :max-height="400"
                />
              </NCard>
            </NGi>
          </NGrid>

          <NGrid :cols="24" :x-gap="16" style="margin-top: 16px;">
            <NGi :span="8">
              <NCard title="行业集中度" class="pie-card">
                <VChart v-if="industryData.length > 0" :option="pieOption" autoresize style="height: 280px" />
                <NEmpty v-else description="暂无行业分布数据" />
                <div v-if="summaryMetrics.concentrationScore !== null" style="text-align: center; margin-top: 8px;">
                  <NTag :type="summaryMetrics.concentrationScore > 30 ? 'warning' : 'success'" size="small">
                    集中度评分: {{ summaryMetrics.concentrationScore?.toFixed(1) }}
                  </NTag>
                </div>
              </NCard>
            </NGi>
            <NGi :span="16">
              <NCard title="高相关性持仓" class="correlation-card">
                <template v-if="currentReport?.portfolio_risk?.high_correlation_pairs?.length">
                  <NList bordered>
                    <NListItem v-for="(pair, idx) in currentReport.portfolio_risk.high_correlation_pairs" :key="idx">
                      <NThing>
                        <template #header>
                          {{ pair.code_1 }} / {{ pair.code_2 }}
                        </template>
                        <template #description>
                          相关系数: <span :style="{ color: pair.correlation > 0.8 ? '#ef4444' : '#f59e0b' }">{{ pair.correlation?.toFixed(3) }}</span>
                        </template>
                      </NThing>
                    </NListItem>
                  </NList>
                </template>
                <NEmpty v-else description="无高相关性持仓（相关性阈值 > 0.7）" />
              </NCard>
            </NGi>
          </NGrid>

          <NDivider />

          <NCard title="风险建议" class="recommendations-card" :bordered="false">
            <NList bordered>
              <NListItem v-for="(rec, idx) in recommendations" :key="idx">
                <NThing>
                  <template #avatar>
                    <NTag :type="typeof rec === 'object' ? rec.severity : (rec.includes('高风险') || rec.includes('警告') ? 'warning' : 'info')" size="small" round>
                      {{ typeof rec === 'object' ? (rec.severity === 'warning' ? '警告' : '提示') : (rec.includes('高风险') || rec.includes('警告') ? '警告' : '提示') }}
                    </NTag>
                  </template>
                  <template #header v-if="typeof rec === 'object'">
                    <span class="rec-priority">优先级 {{ rec.priority }}</span>
                  </template>
                  <template #description>
                    {{ typeof rec === 'object' ? rec.text : rec }}
                  </template>
                </NThing>
              </NListItem>
            </NList>
          </NCard>
        </template>

        <NEmpty v-else-if="!store.state.loading" description="暂无风险报告数据" />
      </NSpin>
    </NCard>
  </div>
</template>
```

- [ ] **Step 4: Add CSS for new metrics cards**

Add to `<style scoped>`:
```css
.metrics-card {
  text-align: center;
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.correlation-card {
  height: 100%;
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/vue-admin/src/views/RiskReportView.vue
git commit -m "feat: redesign risk report page with summary cards, enhanced table, correlation display"
```

---

## Phase 3: Advanced Features

### Task 13: Implement Stress Testing

**Files:**
- Modify: `apps/api/app/risk/risk_report.py` (add stress test methods and integrate into generate_report)

- [ ] **Step 1: Add `_calculate_stress_test` method to RiskReportGenerator**

Insert after `_calculate_correlation_matrix`:
```python
def _calculate_stress_test(
    self, positions_risk: List[PositionRisk], concentrations: List[IndustryConcentration]
) -> StressTestResult:
    total_value = sum(p.quantity * p.current_price for p in positions_risk)
    if total_value <= 0:
        return StressTestResult()

    market_scenarios = []
    for shock_pct, name in [(-0.10, "市场下跌10%"), (-0.20, "市场下跌20%"), (-0.30, "市场下跌30%")]:
        estimated_loss = sum(
            p.quantity * p.current_price * p.beta * abs(shock_pct)
            for p in positions_risk if p.beta > 0
        )
        if estimated_loss == 0:
            estimated_loss = total_value * abs(shock_pct)
        market_scenarios.append(StressScenario(
            name=name,
            description=f"假设沪深300{shock_pct:.0%}，按Beta估算组合损失",
            market_shock=shock_pct,
            estimated_loss=estimated_loss,
            estimated_loss_pct=estimated_loss / total_value,
        ))

    industry_scenarios = []
    top_industries = sorted(concentrations, key=lambda c: c.allocation_pct, reverse=True)[:3]
    for conc in top_industries:
        if conc.allocation_pct < 0.15:
            continue
        industry_loss = sum(
            p.quantity * p.current_price * 0.20
            for p in positions_risk
            if (p.industry or "未知") == conc.industry
        )
        other_loss = sum(
            p.quantity * p.current_price * 0.05
            for p in positions_risk
            if (p.industry or "未知") != conc.industry
        )
        total_loss = industry_loss + other_loss
        industry_scenarios.append(StressScenario(
            name=f"{conc.industry}行业冲击",
            description=f"假设{conc.industry}行业下跌20%，其他行业下跌5%",
            market_shock=-0.20,
            estimated_loss=total_loss,
            estimated_loss_pct=total_loss / total_value,
        ))

    liquidity_crisis = None
    high_liquidity = [p for p in positions_risk if p.liquidity_days > 5]
    if high_liquidity:
        slippage_loss = sum(p.quantity * p.current_price * 0.05 for p in high_liquidity)
        liquidity_crisis = StressScenario(
            name="流动性危机",
            description=f"{len(high_liquidity)}只持仓流动性不足(>5天)，假设5%滑点损失",
            market_shock=-0.05,
            estimated_loss=slippage_loss,
            estimated_loss_pct=slippage_loss / total_value,
        )

    return StressTestResult(
        scenarios=market_scenarios,
        industry_shock=industry_scenarios,
        liquidity_crisis=liquidity_crisis,
    )
```

- [ ] **Step 2: Integrate stress test into `generate_report`**

Before `report = RiskReport(...)` in `generate_report`, add:
```python
    stress_test = self._calculate_stress_test(positions_risk, concentrations)
```

Update the `RiskReport` constructor to include:
```python
    stress_test=stress_test,
```

- [ ] **Step 3: Update `save_report` to persist stress_test**

In `save_report`, replace `"stress_test": None,` (added in Task 9) with:
```python
        "stress_test": {
            "scenarios": [
                {
                    "name": s.name,
                    "description": s.description,
                    "market_shock": s.market_shock,
                    "estimated_loss": s.estimated_loss,
                    "estimated_loss_pct": s.estimated_loss_pct,
                }
                for s in report.stress_test.scenarios
            ] if report.stress_test else [],
            "industry_shock": [
                {
                    "name": s.name,
                    "description": s.description,
                    "market_shock": s.market_shock,
                    "estimated_loss": s.estimated_loss,
                    "estimated_loss_pct": s.estimated_loss_pct,
                }
                for s in report.stress_test.industry_shock
            ] if report.stress_test else [],
            "liquidity_crisis": {
                "name": report.stress_test.liquidity_crisis.name,
                "description": report.stress_test.liquidity_crisis.description,
                "market_shock": report.stress_test.liquidity_crisis.market_shock,
                "estimated_loss": report.stress_test.liquidity_crisis.estimated_loss,
                "estimated_loss_pct": report.stress_test.liquidity_crisis.estimated_loss_pct,
            } if report.stress_test and report.stress_test.liquidity_crisis else None,
        } if report.stress_test else None,
```

- [ ] **Step 4: Commit**

```bash
git add apps/api/app/risk/risk_report.py
git commit -m "feat: add stress testing (market shock, industry shock, liquidity crisis)"
```

### Task 14: Add Stress Test Display to Frontend

**Files:**
- Modify: `frontend/vue-admin/src/views/RiskReportView.vue` (add stress test section)

- [ ] **Step 1: Add stress test data computed**

Add in `<script setup>` after `recommendations`:
```typescript
const stressTest = computed(() => {
  const st = (currentReport.value as any)?.stress_test
  if (!st) return null
  const allScenarios = [
    ...(st.scenarios || []),
    ...(st.industry_shock || []),
  ]
  if (st.liquidity_crisis) allScenarios.push(st.liquidity_crisis)
  return allScenarios
})
```

- [ ] **Step 2: Add stress test section to template**

Insert before `<NDivider />` in the template:
```html
<NGrid :cols="24" :x-gap="16" style="margin-top: 16px;" v-if="stressTest && stressTest.length > 0">
  <NGi :span="24">
    <NCard title="压力测试" class="stress-card">
      <NGrid :cols="3" :x-gap="12" :y-gap="12">
        <NGi v-for="(scenario, idx) in stressTest" :key="idx">
          <NCard size="small" :bordered="true">
            <template #header>
              <NTag :type="scenario.estimated_loss_pct > 0.15 ? 'error' : 'warning'" size="small">
                {{ scenario.name }}
              </NTag>
            </template>
            <NStatistic
              label="预估损失"
              :value="formatPercent(scenario.estimated_loss_pct)"
            />
            <div style="font-size: 12px; color: #64748b; margin-top: 8px;">
              ¥{{ Math.round(scenario.estimated_loss || 0).toLocaleString() }}
            </div>
            <div style="font-size: 12px; color: #999; margin-top: 4px;">
              {{ scenario.description }}
            </div>
          </NCard>
        </NGi>
      </NGrid>
    </NCard>
  </NGi>
</NGrid>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/vue-admin/src/views/RiskReportView.vue
git commit -m "feat: add stress test section to risk report page"
```

### Task 15: Add Risk Trend API Endpoint

**Files:**
- Modify: `apps/api/app/risk/api.py` (add trend endpoint)
- Modify: `apps/api/app/risk/risk_report.py` (add trend query method)

- [ ] **Step 1: Add `get_trend_data` method to RiskReportGenerator**

Insert after `get_reports_by_date`:
```python
async def get_trend_data(self, user_id: str, days: int = 30) -> Dict[str, Any]:
    try:
        collection = self._get_risk_collection()
        from_date = (datetime.now() - timedelta(days=days + 5)).strftime("%Y-%m-%d")
        cursor = await asyncio.to_thread(
            lambda: list(
                collection.find({"user_id": user_id, "date": {"$gte": from_date}})
                .sort("date", 1)
            )
        )
        result = {
            "dates": [],
            "risk_score": [],
            "var_95": [],
            "var_99": [],
            "max_drawdown": [],
            "sharpe_ratio": [],
            "concentration_score": [],
        }
        for doc in cursor:
            result["dates"].append(doc.get("date", ""))
            result["risk_score"].append(doc.get("risk_score", 0))
            pr = doc.get("portfolio_risk", {})
            result["var_95"].append(pr.get("portfolio_var_95", 0))
            result["var_99"].append(pr.get("var_99", 0))
            result["max_drawdown"].append(pr.get("max_drawdown", 0))
            result["sharpe_ratio"].append(pr.get("sharpe_ratio", 0))
            result["concentration_score"].append(pr.get("concentration_score", 0))
        return result
    except Exception as e:
        logger.error(f"Failed to get trend data: {e}")
        return {"dates": [], "risk_score": [], "var_95": [], "var_99": [], "max_drawdown": [], "sharpe_ratio": [], "concentration_score": []}
```

- [ ] **Step 2: Add trend endpoint in api.py**

Add after the `get_risk_report` endpoint:
```python
@router.get("/reports/{user_id}/trend")
async def get_risk_trend(
    user_id: str,
    days: int = Query(default=30, ge=7, le=365, description="Number of days"),
    current_user: AuthenticatedUser = Depends(require_permission("risk:view")),
):
    """Get risk trend data for a user."""
    generator = RiskReportGenerator()
    try:
        return await generator.get_trend_data(user_id, days)
    except Exception as e:
        logger.error(f"Failed to get risk trend: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trend: {str(e)}")
    finally:
        generator.close()
```

- [ ] **Step 3: Commit**

```bash
git add apps/api/app/risk/risk_report.py apps/api/app/risk/api.py
git commit -m "feat: add risk trend API endpoint for historical metrics time series"
```

### Task 16: Add Risk Trend Charts to Frontend

**Files:**
- Modify: `frontend/vue-admin/src/views/RiskReportView.vue` (add trend charts)
- Modify: `frontend/vue-admin/src/stores/risk.ts` (add trend fetch action)

- [ ] **Step 1: Add trend data to risk store**

In `stores/risk.ts`, add to the state:
```typescript
trendData: null as any | null,
```

Add action:
```typescript
async function fetchTrend(userId: string, days: number = 30) {
  try {
    state.trendData = await apiRisk.getTrend(userId, days)
  } catch (e: any) {
    console.error('Failed to fetch trend data:', e)
  }
}
```

Add to return: `fetchTrend`

- [ ] **Step 2: Add trend chart computed in RiskReportView.vue**

```typescript
const trendOption = computed(() => {
  const trend = store.state.trendData
  if (!trend || !trend.dates?.length) return null
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['风险评分', 'VaR 95%', '最大回撤', '夏普比率'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: trend.dates },
    yAxis: [
      { type: 'value', name: '评分/比率', axisLabel: { formatter: '{value}' } },
    ],
    series: [
      { name: '风险评分', type: 'line', data: trend.risk_score, smooth: true },
      { name: 'VaR 95%', type: 'line', data: trend.var_95?.map((v: number) => +(v * 100).toFixed(2)), smooth: true },
      { name: '最大回撤', type: 'line', data: trend.max_drawdown?.map((v: number) => +(v * 100).toFixed(2)), smooth: true },
      { name: '夏普比率', type: 'line', data: trend.sharpe_ratio, smooth: true },
    ],
  }
})
```

- [ ] **Step 3: Add trend fetch on mount**

In `onMounted`, add after fetching report:
```typescript
if (currentReport.value?.user_id || currentReport.value?.id) {
  const userId = (currentReport.value as any)?.user_id || 'default'
  await store.fetchTrend(userId)
}
```

- [ ] **Step 4: Add trend chart to template**

Insert after the stress test section (before `<NDivider />`):
```html
<NGrid :cols="24" :x-gap="16" style="margin-top: 16px;" v-if="trendOption">
  <NGi :span="24">
    <NCard title="风险趋势 (近30天)">
      <VChart :option="trendOption" autoresize style="height: 300px" />
    </NCard>
  </NGi>
</NGrid>
```

- [ ] **Step 5: Commit**

```bash
git add frontend/vue-admin/src/views/RiskReportView.vue frontend/vue-admin/src/stores/risk.ts
git commit -m "feat: add risk trend charts with 30-day historical metrics"
```

### Task 17: Update risk_report_job.py to Use Enhanced Generator

**Files:**
- Modify: `apps/api/app/scheduler/risk_report_job.py:182-213` (update price fetcher to include volume data)

- [ ] **Step 1: Update `_fetch_latest_prices` to also fetch volume data**

Replace the `_fetch_latest_prices` method (lines 182-213) with:
```python
async def _fetch_latest_prices(self, codes: List[str]) -> Dict[str, Dict[str, float]]:
    storage = self._get_storage()
    today = datetime.now().strftime("%Y-%m-%d")
    prices = {}

    for code in codes:
        try:
            query_code = code
            if code.startswith("SH"):
                query_code = code[2:]
            elif code.startswith("SZ"):
                query_code = code[2:]

            klines = await asyncio.to_thread(
                storage.get_kline,
                query_code,
                start_date=None,
                end_date=today,
                limit=5,
            )
            if klines:
                latest = klines[0]
                prices[code] = {
                    "close": latest.get("close", 0.0),
                    "volume": latest.get("volume", 0),
                    "date": latest.get("date", ""),
                }
        except Exception as e:
            logger.warning(f"Failed to fetch price for {code}: {e}")
            prices[code] = {"close": 0.0, "volume": 0, "date": ""}

    return prices
```

- [ ] **Step 2: Commit**

```bash
git add apps/api/app/scheduler/risk_report_job.py
git commit -m "feat: include volume data in price fetcher for liquidity calculations"
```

### Task 18: Final Integration Verification

**Files:** None (verification only)

- [ ] **Step 1: Verify backend starts without import errors**

Run: `py -3.12 -c "import sys; sys.path.insert(0, 'apps/api'); from app.risk.risk_report import RiskReportGenerator, PositionRisk, PortfolioRisk, StressTestResult, StressScenario; print('Backend OK')"`

Expected: `Backend OK`

- [ ] **Step 2: Verify API router loads**

Run: `py -3.12 -c "import sys; sys.path.insert(0, 'apps/api'); from app.risk.api import router; print(f'API routes: {len(router.routes)}')" 2>&1`

Expected: Route count printed

- [ ] **Step 3: Verify scheduler configures**

Run: `py -3.12 -c "import sys; sys.path.insert(0, 'apps/api'); from scheduler_standalone import setup_scheduler; print('Scheduler OK')" 2>&1`

Expected: `Scheduler OK`

- [ ] **Step 4: Verify frontend builds**

Run: `cd frontend/vue-admin && npm run build`

Expected: Build succeeds with no TypeScript errors

- [ ] **Step 5: Commit if any fixes needed**

```bash
git add -A
git commit -m "fix: address integration issues found during verification"
```
