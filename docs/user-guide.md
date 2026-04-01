# User Guide

This guide explains how to use the frontend features of the quantitative trading system.

## Overview

The frontend provides the following main features:
- Stock Selection (Qlib ML-based)
- Backtesting
- Risk Reports
- Scheduler Management
- DingTalk Notifications

---

## Stock Selection Page

### Accessing the Page

Navigate to **Qlib选股** from the sidebar menu.

### Features

The Stock Selection page enables ML-based stock screening using trained Qlib models.

#### 1. Model Selection

Select a trained model from the dropdown:
- Shows all **approved** models
- Displays model creation date and Sharpe ratio
- Latest approved model is selected by default

**Example**:
```
Model: lgbm_alpha158 (2024-01-01) - Sharpe: 2.15
```

#### 2. Date Selection

Choose the prediction date:
- Select any historical date up to today
- Uses latest available data if not specified

#### 3. Running Selection

1. Select model and date
2. Click **运行筛选** button
3. Wait for results to load

#### 4. Viewing Results

Results display in a sortable table:

| Column | Description |
|--------|-------------|
| 排名 | Ranking by prediction score |
| 代码 | Stock code (e.g., SH600000) |
| 名称 | Stock name |
| 得分 | Prediction score (higher = better) |

**Features**:
- Sort by any column
- Pagination (50 stocks per page)
- Click row for stock details

#### 5. Interpreting Scores

| Score Range | Interpretation |
|-------------|----------------|
| > 0.8 | Strong buy signal |
| 0.5 - 0.8 | Moderate buy signal |
| 0 - 0.5 | Weak/neutral signal |
| < 0 | Sell signal |

**Note**: Scores are model-specific. Always consider multiple factors.

---

## Backtest Page

### Accessing the Page

Navigate to **回测** from the sidebar menu.

### Configuration

#### 1. Strategy Selection

Choose from available strategies:

| Strategy | Description | Parameters |
|----------|-------------|------------|
| MA Cross | Moving average crossover | `fast_period`, `slow_period` |
| RSI | Relative Strength Index | `period`, `oversold`, `overbought` |
| Bollinger | Bollinger Bands | `period`, `num_std` |
| MACD | Moving Average Convergence Divergence | `fast_period`, `slow_period`, `signal_period` |
| Qlib Model | ML-based strategy | `model_id`, `topk` |

#### 2. Parameter Configuration

Configure strategy-specific parameters:

**MA Cross Example**:
```
Fast Period: 5    (short-term MA)
Slow Period: 20   (long-term MA)
```

**RSI Example**:
```
Period: 14        (RSI calculation period)
Oversold: 30      (buy threshold)
Overbought: 70    (sell threshold)
```

#### 3. Date Range

Select backtest period:
- Click date picker
- Choose start and end dates
- Minimum recommended: 3 months

#### 4. Initial Capital

Set starting capital:
- Default: ¥100,000
- Minimum: ¥1,000
- Use reasonable values for meaningful metrics

### Running Backtest

1. Configure all parameters
2. Click **开始回测**
3. Monitor progress via WebSocket connection

**Progress Display**:
```
[████████████░░░░░░░░] 60%
WebSocket: Connected
```

### Viewing Results

#### Key Metrics

| Metric | Description |
|--------|-------------|
| 总收益 | Total return percentage |
| 年化收益 | Annualized return |
| 夏普比率 | Risk-adjusted return (higher is better) |
| 最大回撤 | Maximum peak-to-trough decline |
| 胜率 | Percentage of profitable trades |
| 交易次数 | Total number of trades |

#### Charts

**Return Curve**: Shows portfolio value over time
**Drawdown Curve**: Shows drawdown from peak

#### Historical Results

View past backtest runs in the history table at bottom.

### Interpreting Results

| Metric | Good | Excellent |
|--------|------|-----------|
| Sharpe Ratio | 1.0 - 2.0 | > 2.0 |
| Max Drawdown | < 15% | < 10% |
| Win Rate | > 50% | > 60% |

---

## Risk Report Page

### Accessing the Page

Navigate to **风险报告** from the sidebar menu.

### Overview

The Risk Report page provides comprehensive portfolio risk analysis.

### Risk Score Gauge

The main gauge shows composite risk score (0-100):

```
        100
        /  \
       /    \
      /      \
   Low   Medium   High
  (0-29) (30-59) (60-100)
```

**Color Coding**:
- 🟢 Green (0-29): Low risk
- 🟡 Yellow (30-59): Medium risk  
- 🔴 Red (60-100): High risk

### Risk Metrics Panel

View key risk metrics:

| Metric | Description |
|--------|-------------|
| VaR (95%) | 5% worst-case daily loss |
| VaR (99%) | 1% worst-case daily loss |
| 预期损失 | Expected Shortfall (CVaR) |
| Beta | Market correlation |
| 波动率 | Annualized volatility |
| 最大回撤 | Historical maximum drawdown |

### Holdings Risk Table

View risk metrics per position:

| Column | Description |
|--------|-------------|
| 代码 | Stock code |
| 名称 | Stock name |
| 数量 | Position size |
| 成本 | Average cost price |
| 现价 | Current price |
| 盈亏% | Profit/Loss percentage |
| VaR | Position VaR contribution |
| 风险分 | Position risk score |

**Color Coding**:
- Red rows: High risk (>60 score)
- Yellow cells: Moderate risk
- Green cells: Low risk

### Industry Concentration Pie Chart

Shows portfolio allocation by industry:
- Hover for details
- Larger slices = higher concentration
- **Warning**: Any slice > 50% triggers alert

### Recommendations

Actionable recommendations based on risk analysis:

**Priority Levels**:
1. **【高风险】**: Immediate attention required
2. **【警告】**: Important warnings
3. **【注意】**: Informational notices
4. **【提示】**: General suggestions

**Example Recommendations**:
```
【高风险】组合VaR超过5%阈值(6.2%)，建议降低仓位或分散持仓
【高风险】金融行业集中度过高(55%)，建议分散配置
【警告】SH600000亏损12%，建议止损或减仓
```

### Date Selection

View historical risk reports:
- Select date from picker
- Compare reports over time
- Track risk trends

---

## Scheduler Page

### Accessing the Page

Navigate to **调度任务** from the sidebar menu.

### Job List

View all scheduled jobs:

| Column | Description |
|--------|-------------|
| 名称 | Job name |
| 类型 | Job type |
| 调度表达式 | Cron schedule |
| 启用 | Enable/Disable toggle |
| 上次执行 | Last run time |
| 下次执行 | Next scheduled run |
| 状态 | Current status |
| 操作 | Action buttons |

### Creating a Job

1. Click **新建任务**
2. Fill in the form:
   - **任务名称**: Descriptive name
   - **任务类型**: Select job type
   - **Cron表达式**: Schedule (see below)
   - **配置**: JSON config (optional)
   - **启用**: Enable checkbox

3. Click **创建**

### Cron Expression Examples

| Expression | Description |
|------------|-------------|
| `0 9 * * 1-5` | Weekdays at 9:00 AM |
| `30 15 * * 1-5` | Weekdays at 3:30 PM |
| `0 2 * * 0` | Sundays at 2:00 AM |
| `0 0 1 * *` | First of month |

**Hints**:
- System shows human-readable description
- Validates expression in real-time

### Managing Jobs

#### Enable/Disable

Toggle the switch in **启用** column.

#### Trigger Immediately

Click **立即执行** to run job now.

#### Edit Job

1. Click **编辑**
2. Modify settings
3. Click **保存**

#### View History

1. Click **历史**
2. View execution records:
   - Start/End time
   - Status (success/failed)
   - Duration
   - Error message (if failed)

#### Delete Job

1. Click **删除**
2. Confirm deletion

### Execution History

View detailed execution records:

| Column | Description |
|--------|-------------|
| 开始时间 | Execution start |
| 完成时间 | Completion time |
| 状态 | success/failed |
| 耗时 | Duration in ms |
| 结果/错误 | Result or error message |

---

## DingTalk Configuration

### Accessing the Page

Navigate to **钉钉配置** from the sidebar menu.

### Prerequisites

Before configuring, ensure you have:
1. DingTalk group with robot access
2. Webhook URL
3. (Optional) Signing secret

### Creating DingTalk Robot

1. Open DingTalk group
2. Go to Group Settings → Smart Group Assistant
3. Add Robot → Custom
4. Security Settings:
   - Custom keywords (recommended), OR
   - Signing secret
5. Copy Webhook URL and Secret

### Configuration

#### Webhook URL

Enter the webhook URL:
```
https://oapi.dingtalk.com/robot/send?access_token=xxxx
```

**Note**: URL is stored encrypted.

#### Signing Secret (Optional)

If robot uses signing:
1. Enter secret
2. System stores encrypted

#### Keywords (Optional)

If robot uses keywords:
- Enter keywords (comma-separated)
- Messages will include these keywords

#### @手机号

Enter phone numbers to @ specific people:
- Comma-separated
- Example: `13800138000,13900139000`

### Testing Configuration

1. Click **测试通知**
2. Check DingTalk group for test message
3. Verify message appears correctly

### Managing Configuration

- **保存配置**: Save current settings
- **重置**: Reset form to saved values
- **删除配置**: Remove all settings

### Notification Examples

**Risk Alert**:
```
【风险警告】
组合风险评分: 72 (高风险)
VaR(95%): 6.2%
建议: 金融行业集中度过高(55%)，建议分散配置
```

**Training Complete**:
```
【训练完成】
模型: model_20240101
Sharpe: 2.15
IC: 0.05
状态: 等待审核
```

---

## Best Practices

### Stock Selection

1. Use multiple models for validation
2. Compare with fundamental analysis
3. Consider market conditions
4. Don't rely solely on scores

### Backtesting

1. Use sufficient date range (6+ months)
2. Test with out-of-sample data
3. Consider transaction costs
4. Validate with paper trading

### Risk Management

1. Monitor risk reports daily
2. Act on high-priority warnings
3. Maintain diversification
4. Set stop-loss limits

### Scheduler

1. Schedule training during off-hours
2. Set appropriate retry limits
3. Monitor execution history
4. Configure error notifications

### Notifications

1. Configure DingTalk for critical alerts
2. Use keywords for filtering
3. Test configuration regularly
4. Keep secrets secure

---

## Troubleshooting

### Stock Selection Issues

**No models available**:
- Train a model first
- Check model approval status

**Selection fails**:
- Verify date has available data
- Check model compatibility

### Backtest Issues

**Connection timeout**:
- Check WebSocket connection
- Reduce date range

**Invalid parameters**:
- Verify parameter types
- Check date format (YYYY-MM-DD)

### Risk Report Issues

**No data available**:
- Ensure holdings are configured
- Check price data availability

**Incorrect metrics**:
- Verify cost basis
- Check position quantities

### Scheduler Issues

**Job not running**:
- Verify cron expression
- Check if job is enabled

**Repeated failures**:
- Check error logs
- Verify job configuration

### DingTalk Issues

**Test fails**:
- Verify webhook URL format
- Check secret configuration
- Ensure keywords match

**Messages not received**:
- Check robot is active
- Verify group membership
- Check notification settings
