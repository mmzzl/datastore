# Risk Report Overhaul Design

## Problem Statement

Risk report data is not updating. Root causes identified:

1. **Risk report job not in standalone scheduler** — `scheduler_standalone.py` has no risk report job, so reports are never auto-generated
2. **Stock code format mismatch** — Holdings store codes with `SH`/`SZ` prefix, but kline collection stores without prefix, causing VaR calculations to return 0.0
3. **Fabricated metrics in API** — `var_99 = var_95 * 1.5`, `beta = 1.0`, `expected_shortfall = var_95 * 0.5` etc. are hardcoded multiples, not real calculations
4. **Frontend random data fallbacks** — `Math.random()` used when backend fields are missing, masking real data problems
5. **Daily kline scraper commented out** — Stock kline data may be stale

Additionally, the current risk report is too simplistic — it only calculates VaR 95%, basic industry concentration, and a composite risk score.

## Design: Phase 1 — Fix Existing Issues

### 1.1 Add Risk Report Job to Standalone Scheduler

In `scheduler_standalone.py`, add a new cron job after market close (15:35):

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

The job function will:
- Query MongoDB `holdings` collection to discover all distinct user IDs with active holdings
- For each user, instantiate `RiskReportGenerator` and call `generate_report()`
- Log results and errors per user
- Skip users with no holdings (with info-level log, not silent)

### 1.2 Fix Stock Code Format Mismatch

In `risk_report.py`, add a `_normalize_code()` helper:

```python
def _normalize_code(self, code: str) -> str:
    """Strip SH/SZ prefix for kline queries."""
    if code.startswith("SH") or code.startswith("SZ"):
        return code[2:]
    return code
```

Apply in `_get_kline_data()` and `_calculate_position_var()` before querying kline data. This aligns with the existing pattern in `risk_report_job.py:_fetch_latest_prices()`.

### 1.3 Remove Fabricated Metrics from API

In `app/risk/api.py`, delete all lines that fabricate metrics:
- `var_99 = var_95 * 1.5`
- `expected_shortfall = var_95 * 0.5`
- `beta = 1.0`
- `volatility = var_95 * 2.0`
- `max_drawdown = var_95 * 0.8`

Replace with reading from the stored report document. If a field is not in the report (e.g., old reports), return `null` instead of a fabricated value. The frontend will handle `null` gracefully.

### 1.4 Remove Frontend Random Data Fallbacks

In `RiskReportView.vue`, replace all `Math.random()` fallbacks with `null`/`undefined`, and display "—" in the UI for missing data. Add a data freshness indicator showing the report date, with a warning if the report is stale (>1 day old).

## Design: Phase 2 — Enhanced Risk Indicators

### 2.1 Per-Position Real Risk Metrics

Calculated from individual stock kline data (252 trading days lookback):

| Metric | Calculation | Data Source |
|--------|------------|-------------|
| VaR 95% | Historical simulation, 5th percentile of daily returns | Stock kline |
| VaR 99% | Historical simulation, 1st percentile of daily returns | Stock kline |
| Expected Shortfall (CVaR) | Mean of returns below VaR 95% threshold | Stock kline |
| Volatility | Daily return std × √252 | Stock kline |
| Max Drawdown | Rolling peak-to-trough maximum decline | Stock kline |
| Sharpe Ratio | (Annualized return - 0.03) / Annualized volatility | Stock kline |
| Beta | Cov(stock, HS300) / Var(HS300) | Stock kline + HS300 kline |
| Liquidity Days | Position value / (avg daily volume × 10%) | Stock kline volume |
| Marginal VaR | Change in portfolio VaR when position is removed | Portfolio calculation |

### 2.2 Portfolio-Level Risk Analysis

| Metric | Calculation | Description |
|--------|------------|-------------|
| Portfolio VaR 95% | Already exists | Portfolio-level value at risk |
| Portfolio VaR 99% | Same method at 1% threshold | Extreme tail risk |
| Portfolio CVaR | Mean of losses exceeding VaR | Average worst-case loss |
| Portfolio Volatility | Weighted variance with correlation | Actual portfolio vol |
| Portfolio Max Drawdown | Peak-to-trough on portfolio value series | Worst historical decline |
| Portfolio Sharpe | (Return - Rf) / Vol | Risk-adjusted return |
| Portfolio Beta | Weighted average of position betas | Market sensitivity |
| Concentration Score | HHI index: Σ(weight²) × 100 | 0=perfectly diversified, 100=single stock |
| Liquidity Risk | Max position liquidity days | Hardest-to-exit position |
| Style Exposure | Large/small cap via market cap; value/growth via PE ratio | Simple binning, not full factor model |

### 2.3 Correlation Analysis

- Calculate pairwise return correlation matrix for all holdings
- Store as `correlation_matrix: List[List[float]]` with `correlation_labels: List[str]` (stock codes)
- Flag high-correlation pairs (>0.7) in recommendations
- Used for portfolio VaR calculation (parametric method as cross-check)

### 2.4 Data Model Changes

**`PositionRisk` new fields:**

```python
var_99: float = 0.0
expected_shortfall: float = 0.0
volatility: float = 0.0
max_drawdown: float = 0.0
sharpe_ratio: float = 0.0
beta: float = 0.0
liquidity_days: float = 0.0
marginal_var: float = 0.0
```

**`PortfolioRisk` new fields:**

```python
var_99: float = 0.0
expected_shortfall: float = 0.0
volatility: float = 0.0
max_drawdown: float = 0.0
sharpe_ratio: float = 0.0
beta: float = 0.0
concentration_score: float = 0.0
liquidity_risk: Dict[str, Any] = {}
style_exposure: Dict[str, float] = {}
correlation_matrix: Optional[List[List[float]]] = None
correlation_labels: Optional[List[str]] = None
high_correlation_pairs: Optional[List[Dict[str, Any]]] = None
```

**New `StressTestResult` dataclass:**

```python
@dataclass
class StressScenario:
    name: str
    description: str
    market_shock: float  # e.g., -0.10 for 10% drop
    estimated_loss: float
    estimated_loss_pct: float

@dataclass
class StressTestResult:
    scenarios: List[StressScenario]
    industry_shock: List[StressScenario]
    liquidity_crisis: Optional[StressScenario]
```

**`RiskReport` new field:**

```python
stress_test: Optional[StressTestResult] = None
```

### 2.5 Calculation Implementation Details

All calculations use numpy/pandas vectorized operations (no row-by-row loops):

- **VaR**: `np.percentile(returns, 5)` for 95%, `np.percentile(returns, 1)` for 99%
- **CVaR**: `returns[returns <= np.percentile(returns, 5)].mean()`
- **Max Drawdown**: `((cummax - close) / cummax).max()` using pandas rolling
- **Sharpe**: `(returns.mean() * 252 - 0.03) / (returns.std() * sqrt(252))`
- **Beta**: `np.cov(stock_returns, market_returns)[0][1] / np.var(market_returns)`
- **Concentration (HHI)**: `sum(w**2 for w in weights) * 100`
- **Liquidity**: `position_value / (avg_volume_20d * close * 0.1)`
- **Marginal VaR**: `(portfolio_var - var_without_position) / position_value`

HS300 index kline data is needed for Beta calculation — fetch via baostock if not in local kline collection.

## Design: Phase 3 — Advanced Features

### 3.1 Stress Testing

Compute estimated portfolio loss under predefined scenarios:

| Scenario | Method |
|----------|--------|
| Market -10% | Each position: loss = beta × (-10%) × position_value |
| Market -20% | Same method with -20% |
| Market -30% | Same method with -30% |
| Industry Shock | Target industry -20%, others -5% |
| Liquidity Crisis | Positions with >5 day liquidity take additional 5% slippage |

Results stored in `stress_test` field of the report document.

### 3.2 Historical Scenario Analysis

Based on historical extreme events, calculate what the current portfolio would have experienced:

| Event | Period |
|-------|--------|
| 2015 Stock Crash | 2015-06-12 to 2015-08-26 |
| 2020 COVID | 2020-01-20 to 2020-03-23 |
| 2024 Policy Rally | 2024-09-24 to 2024-10-08 |

For each event, use actual stock returns during the period to estimate portfolio impact. Requires sufficient kline history (optional — skip positions without data).

### 3.3 Risk Trend API

New endpoint: `GET /risk/reports/{user_id}/trend?days=30`

Returns time series of key metrics from the last N daily reports:

```python
{
    "dates": ["2026-04-20", "2026-04-21", ...],
    "risk_score": [45, 48, ...],
    "var_95": [0.023, 0.025, ...],
    "var_99": [0.035, 0.038, ...],
    "max_drawdown": [0.08, 0.09, ...],
    "sharpe_ratio": [1.2, 1.1, ...],
    "concentration_score": [35, 33, ...],
}
```

### 3.4 Frontend Redesign

**Layout structure:**

```
┌──────────────────────────────────────────────┐
│  Risk Report Header (date, risk level badge) │
├──────────┬──────────┬──────────┬─────────────┤
│ Risk     │ VaR 95%  │ Max      │ Sharpe      │
│ Score    │          │ Drawdown │ Ratio       │
│ 45/100   │ -2.3%    │ -8.5%    │ 1.24        │
├──────────┴──────────┴──────────┴─────────────┤
│ Holdings Risk Table (sortable, all metrics)   │
├──────────────────────────────────────────────┤
│ Industry Distribution (pie chart)            │
│ Concentration Score                           │
├──────────────────────────────────────────────┤
│ Stress Test Results (scenario cards)         │
├──────────────────────────────────────────────┤
│ Risk Trend Charts (line charts, 30-day)      │
├──────────────────────────────────────────────┤
│ Recommendations                              │
└──────────────────────────────────────────────┘
```

**Component changes:**
- Top summary cards: `NStatistic` + `NCard` with color-coded risk levels
- Holdings table: `NDataTable` with all new columns, sortable
- Industry chart: existing pie chart, enhanced with concentration score
- Stress test: new section with `NCard` per scenario
- Trend charts: new section using ECharts line charts
- All `Math.random()` replaced with "—" for null values
- Stale data warning banner when report > 1 day old

**Naive UI components used:** `NStatistic`, `NCard`, `NDataTable`, `NTag`, `NProgress`, `NGrid`, `NGi`

## Files to Modify

### Phase 1
- `apps/api/scheduler_standalone.py` — Add risk report cron job
- `apps/api/app/risk/risk_report.py` — Add `_normalize_code()`, apply in kline queries
- `apps/api/app/risk/api.py` — Remove fabricated metrics, return null for missing
- `frontend/vue-admin/src/views/RiskReportView.vue` — Remove random fallbacks, add "—" display

### Phase 2
- `apps/api/app/risk/risk_report.py` — New data models, calculation methods for all metrics
- `apps/api/app/risk/api.py` — Expose new fields in API responses
- `apps/api/app/schemas/risk.py` — Update Pydantic schemas if they exist
- `frontend/vue-admin/src/views/RiskReportView.vue` — Enhanced table, new sections
- `frontend/vue-admin/src/services/api_risk.ts` — Update TypeScript interfaces

### Phase 3
- `apps/api/app/risk/risk_report.py` — Stress test and historical scenario methods
- `apps/api/app/risk/api.py` — New trend endpoint
- `frontend/vue-admin/src/views/RiskReportView.vue` — Stress test UI, trend charts
- `frontend/vue-admin/src/services/api_risk.ts` — New trend API call

## Dependencies

- **numpy** — Already used for VaR calculation
- **pandas** — Already available via akshare/baostock
- **ECharts** — Already available in frontend (via `vue-echarts` if present, or naivue-charts)
- **HS300 kline data** — Need to ensure baostock can fetch, or use existing kline collection

## Constraints

- All calculations must use vectorized numpy/pandas operations (no row-by-row loops)
- Report generation must complete in < 30 seconds for a 50-position portfolio
- Memory usage < 500MB during report generation
- Kline data fetched from MongoDB (pre-loaded by scheduler), not live API calls during generation
- Backward compatible: old reports without new fields still render (with "—" for missing metrics)
