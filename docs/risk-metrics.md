# Risk Metrics Calculation Methodology

This document describes the methodology for calculating risk metrics in the quantitative trading system.

## Overview

The system calculates various risk metrics for portfolio analysis:
- Value at Risk (VaR)
- Sharpe Ratio
- Industry Concentcentration
- Risk Score

---

## Value at Risk (VaR)

### Definition

Value at Risk (VaR) estimates the maximum potential loss over a given time horizon at a specified confidence level.

### VaR (95%) Calculation

```python
def calculate_var_95(returns: List[float]) -> float:
    """
    Calculate Value at Risk at 95% confidence.
    
    VaR(95%) represents the loss that will not be exceeded
    95% of the time over the given period.
    
    Formula:
        VaR(95%) = |returns[5th_percentile]|
    
    Args:
        returns: List of daily returns
    
    Returns:
        VaR as positive decimal (e.g., 0.05 = 5%)
    """
    if len(returns) < 10:
        return 0.0
    
    sorted_returns = sorted(returns)
    var_index = int(len(sorted_returns) * 0.05)
    var_index = max(0, var_index)
    
    return abs(sorted_returns[var_index])
```

### Example

```python
# Given: 252 daily returns
returns = [-0.05, -0.03, -0.02, ..., 0.04, 0.05]

# Sort returns
sorted_returns = sorted(returns)  # Ascending

# 5th percentile index
index = int(252 * 0.05) = 12

# VaR(95%)
var_95 = abs(sorted_returns[12])  # e.g., 0.032 (3.2%)
```

### Historical VaR

The system uses **historical simulation** method:
1. Collect historical returns (252 trading days)
2. Sort returns in ascending order
3. Find 5th percentile value
4. Return absolute value as VaR

### Portfolio VaR

Portfolio VaR is calculated as value-weighted average:

```python
def calculate_portfolio_var(
    positions: List[Dict],
    price_fetcher: Callable
) -> float:
    """
    Calculate portfolio VaR.
    
    Formula:
        Portfolio_VaR = Σ(Weight_i × VaR_i)
    
    Where:
        Weight_i = Value_i / Total_Value
        VaR_i = VaR of position i
    """
    total_var = 0.0
    total_value = 0.0
    
    for pos in positions:
        value = pos.quantity * price_fetcher(pos.code)
        var = calculate_var_95(get_returns(pos.code))
        
        total_var += value * var
        total_value += value
    
    return total_var / total_value if total_value > 0 else 0.0
```

---

## Sharpe Ratio

### Definition

The Sharpe ratio measures risk-adjusted return, calculated as excess return per unit of volatility.

### Formula

```
Sharpe Ratio = (R_p - R_f) / σ_p × √252

Where:
    R_p   = Portfolio return (daily mean)
    R_f   = Risk-free rate (assumed 0)
    σ_p   = Portfolio standard deviation
    252   = Trading days per year
```

### Implementation

```python
def calculate_sharpe_ratio(returns: np.ndarray) -> float:
    """
    Calculate annualized Sharpe ratio.
    
    Assumes risk-free rate = 0.
    
    Formula:
        Sharpe = E[R] / std(R) × √252
    
    Args:
        returns: Array of daily returns
    
    Returns:
        Annualized Sharpe ratio
    """
    if len(returns) < 2:
        return 0.0
    
    mean_return = np.mean(returns)
    std_return = np.std(returns, ddof=1)
    
    if std_return == 0:
        return 0.0
    
    # Annualize
    sharpe = mean_return / std_return * np.sqrt(252)
    
    return sharpe if np.isfinite(sharpe) else 0.0
```

### Example

```python
# Given: Daily returns with mean 0.001, std 0.02
mean_return = 0.001  # 0.1% daily
std_return = 0.02    # 2% daily

# Sharpe calculation
sharpe = 0.001 / 0.02 * np.sqrt(252)
       = 0.05 * 15.87
       = 0.79

# Interpretation: 
# < 1.0 = Sub-optimal
# 1.0 - 2.0 = Good
# > 2.0 = Excellent
```

### In Backtest Context

```python
class RiskMetricsCalculator:
    TRADING_DAYS_PER_YEAR = 252
    
    @classmethod
    def _calculate_annual_return(cls, returns: np.ndarray) -> float:
        """Calculate annualized return."""
        if len(returns) == 0:
            return 0.0
        
        # Compound returns
        total_return = np.prod(1 + returns) - 1
        years = len(returns) / cls.TRADING_DAYS_PER_YEAR
        
        if years <= 0:
            return total_return
        
        # CAGR formula
        annual_return = (1 + total_return) ** (1 / years) - 1
        return annual_return if np.isfinite(annual_return) else 0.0
```

---

## Industry Concentration

### Definition

Industry concentration measures how portfolio value is distributed across industries.

### Calculation

```python
@dataclass
class IndustryConcentration:
    industry: str
    allocation_pct: float  # Percentage of portfolio
    position_count: int    # Number of positions
    value: float           # Total value in industry

def calculate_industry_concentrations(
    positions: List[Dict],
    price_fetcher: Callable
) -> List[IndustryConcentration]:
    """
    Calculate industry allocation.
    
    Steps:
        1. Get industry for each position
        2. Calculate value by industry
        3. Compute allocation percentages
    """
    industry_values = {}
    total_value = 0.0
    
    for pos in positions:
        value = pos.quantity * price_fetcher(pos.code)
        if value <= 0:
            continue
            
        total_value += value
        industry = get_industry(pos.code) or "未知"
        industry_values[industry] = industry_values.get(industry, 0) + value
    
    # Calculate allocations
    concentrations = []
    for industry, value in industry_values.items():
        concentrations.append(IndustryConcentration(
            industry=industry,
            allocation_pct=value / total_value,
            position_count=count_positions(industry),
            value=value
        ))
    
    return sorted(concentrations, key=lambda x: x.allocation_pct, reverse=True)
```

### Concentration Risk Threshold

```python
INDUSTRY_CONCENTRATION_THRESHOLD = 0.50  # 50%

def check_concentration_warning(concentrations: List[IndustryConcentration]) -> bool:
    """Check if any industry exceeds threshold."""
    return any(c.allocation_pct > INDUSTRY_CONCENTRATION_THRESHOLD 
               for c in concentrations)
```

### Example

```
Portfolio Allocation:
  金融行业: 35% (¥350,000)
  科技行业: 25% (¥250,000)
  医药行业: 20% (¥200,000)
  消费行业: 15% (¥150,000)
  其他:     5%  (¥50,000)

Concentration Risk:
  - 金融行业 (35%) < 50%: OK
  - No warnings
```

---

## Risk Score

### Definition

The risk score is a composite metric (0-100) that combines multiple risk factors.

### Components

```python
def calculate_risk_score(
    portfolio_var: float,
    concentrations: List[IndustryConcentration],
    positions_risk: List[PositionRisk],
) -> int:
    """
    Calculate composite risk score (0-100).
    
    Components:
        1. VaR Component (0-30 points)
        2. Concentration Component (0-30 points)
        3. Loss Ratio Component (0-40 points)
    """
    score = 0
    
    # 1. VaR Score (max 30)
    var_score = min(30, int(portfolio_var * 500))
    score += var_score
    
    # 2. Concentration Score (max 30)
    max_concentration = max((c.allocation_pct for c in concentrations), default=0)
    concentration_score = min(30, int(max_concentration * 50))
    score += concentration_score
    
    # 3. Loss Ratio Score (max 40)
    loss_count = sum(1 for p in positions_risk if p.pnl_pct < 0)
    total_count = len(positions_risk)
    if total_count > 0:
        loss_ratio = loss_count / total_count
        loss_score = min(40, int(loss_ratio * 80))
        score += loss_score
    
    return min(100, score)
```

### Scoring Breakdown

| Component | Formula | Max Score |
|-----------|---------|-----------|
| VaR | `min(30, var × 500)` | 30 |
| Concentration | `min(30, max_concentration × 50)` | 30 |
| Loss Ratio | `min(40, loss_ratio × 80)` | 40 |

### Example Calculation

```python
# Given:
portfolio_var = 0.04          # 4% VaR
max_concentration = 0.40      # 40% in one industry
loss_count = 3                # 3 losing positions
total_positions = 10

# Calculate:
var_score = min(30, 0.04 * 500) = min(30, 20) = 20
concentration_score = min(30, 0.40 * 50) = min(30, 20) = 20
loss_ratio = 3/10 = 0.30
loss_score = min(40, 0.30 * 80) = min(40, 24) = 24

# Total:
risk_score = 20 + 20 + 24 = 64  # Medium-High risk
```

### Risk Levels

```python
def get_risk_level(score: int) -> str:
    """Map score to risk level."""
    if score < 30:
        return "low"
    elif score < 60:
        return "medium"
    else:
        return "high"
```

| Score | Level | Description |
|-------|-------|-------------|
| 0-29 | Low | Conservative risk profile |
| 30-59 | Medium | Moderate risk profile |
| 60-100 | High | Aggressive risk profile |

---

## Position Risk Score

### Individual Position Scoring

```python
def calculate_position_risk_score(
    pnl_pct: float,
    var_95: float,
    var_contribution: float
) -> int:
    """
    Calculate risk score for individual position.
    
    Components:
        1. PnL Component (based on loss percentage)
        2. VaR Component (based on VaR threshold)
        3. VaR Contribution (position's contribution to portfolio VaR)
    """
    score = 0
    
    # PnL Component
    PNL_WARNING_THRESHOLD = -0.08  # -8%
    
    if pnl_pct < PNL_WARNING_THRESHOLD:
        score += 40  # Heavy loss warning
    elif pnl_pct < 0:
        score += int(abs(pnl_pct) * 250)  # Proportional to loss
    
    # VaR Component
    VAR_THRESHOLD = 0.05  # 5%
    
    if var_95 > VAR_THRESHOLD:
        score += 30  # High volatility warning
    elif var_95 > 0.03:
        score += int(var_95 * 500)
    
    # VaR Contribution Component
    if var_contribution > 0.2:
        score += 20  # Concentrated risk
    
    return min(100, max(0, score))
```

---

## Additional Metrics

### Maximum Drawdown

```python
def calculate_max_drawdown(values: np.ndarray) -> float:
    """
    Calculate maximum drawdown from peak.
    
    Formula:
        Max_Drawdown = max((Peak - Value) / Peak)
    
    Returns:
        Maximum drawdown as positive decimal
    """
    if len(values) < 2:
        return 0.0
    
    # Running maximum (peak)
    peak = np.maximum.accumulate(values)
    
    # Drawdown at each point
    drawdowns = (peak - values) / peak
    drawdowns = np.where(np.isfinite(drawdowns), drawdowns, 0)
    
    return np.max(drawdowns)
```

### Win Rate

```python
def calculate_win_rate(trades: List[Dict]) -> float:
    """
    Calculate percentage of profitable trades.
    
    Formula:
        Win_Rate = Profitable_Trades / Total_Trades
    """
    if not trades:
        return 0.0
    
    pnls = [t.get("pnl", 0) for t in trades if "pnl" in t]
    if not pnls:
        return 0.0
    
    profitable = sum(1 for pnl in pnls if pnl > 0)
    return profitable / len(pnls)
```

### Profit Factor

```python
def calculate_profit_factor(trades: List[Dict]) -> float:
    """
    Calculate profit factor.
    
    Formula:
        Profit_Factor = Gross_Profit / Gross_Loss
    
    Interpretation:
        > 1.0 = Profitable system
        > 2.0 = Good system
    """
    pnls = [t.get("pnl", 0) for t in trades]
    
    profits = sum(p for p in pnls if p > 0)
    losses = sum(abs(p) for p in pnls if p < 0)
    
    return profits / losses if losses > 0 else 0.0
```

---

## Risk Report Generation

### Full Report Structure

```python
@dataclass
class RiskReport:
    report_id: str
    user_id: str
    date: str
    risk_score: int              # Composite score (0-100)
    risk_level: str              # "low", "medium", "high"
    holdings_risk: List[PositionRisk]
    portfolio_risk: PortfolioRisk
    recommendations: List[str]
    created_at: datetime

@dataclass
class PortfolioRisk:
    total_value: float
    total_cost: float
    portfolio_var_95: float
    industry_concentrations: List[IndustryConcentration]
    var_warning: bool
    concentration_warning: bool
```

### Recommendations Generation

```python
def generate_recommendations(
    portfolio_risk: PortfolioRisk,
    positions_risk: List[PositionRisk],
    risk_level: str
) -> List[str]:
    """Generate actionable risk recommendations."""
    recommendations = []
    
    # VaR warning
    if portfolio_risk.var_warning:
        recommendations.append(
            f"【高风险】组合VaR超过5%阈值"
            f"({portfolio_risk.portfolio_var_95:.2%})，"
            f"建议降低仓位或分散持仓"
        )
    
    # Concentration warnings
    for conc in portfolio_risk.industry_concentrations:
        if conc.allocation_pct > INDUSTRY_CONCENTRATION_THRESHOLD:
            recommendations.append(
                f"【高风险】{conc.industry}行业集中度过高"
                f"({conc.allocation_pct:.1%})，建议分散配置"
            )
    
    # Position-specific warnings
    for pos in positions_risk:
        if pos.pnl_pct < PNL_WARNING_THRESHOLD:
            recommendations.append(
                f"【警告】{pos.name or pos.code}亏损"
                f"{abs(pos.pnl_pct):.1%}，建议止损或减仓"
            )
    
    return recommendations
```

---

## Thresholds Reference

| Metric | Threshold | Action |
|--------|-----------|--------|
| VaR (95%) | > 5% | High risk warning |
| PnL Loss | < -8% | Position warning |
| Concentration | > 50% | Diversification needed |
| Risk Score | ≥ 60 | High risk level |

---

## Data Requirements

### For VaR Calculation
- Minimum 10 days of returns
- Recommended 252 trading days (1 year)

### For Sharpe Ratio
- Minimum 2 days of returns
- Recommended 30+ days for meaningful result

### For Concentration
- Position quantities and prices
- Industry classification data
