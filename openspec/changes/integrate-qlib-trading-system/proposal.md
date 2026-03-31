# Integrate Qlib Trading System

## Why

The current system lacks advanced ML-based stock selection capabilities and real-time backtest visualization. Manual trading decisions based solely on technical indicators are insufficient for generating consistent alpha in aggressive trading strategies. Integrating Qlib (Microsoft's quantitative investment platform) will enable ML-driven stock selection, while WebSocket-based backtest visualization will provide real-time feedback on strategy performance.

**Business Goal**: Build a profitable trading system that can generate buy/sell signals using ML models, manage positions with proper risk controls, and visualize backtest results in real-time.

## What Changes

### Backend (FastAPI)
- **NEW**: Qlib integration module (`app/qlib/`) - train ML models using MongoDB K-line data
- **NEW**: Async backtest engine with WebSocket real-time push
- **NEW**: Multi-strategy support (Qlib models + traditional: MA, RSI, Bollinger, MACD)
- **NEW**: Weekly automated model training job (every Sunday 02:00)
- **NEW**: Daily post-market risk summary job (every trading day 15:30)
- **NEW**: Position management with risk controls (VaR limits, industry concentration)
- **NEW**: Scheduler job management APIs (CRUD for dynamic task configuration)
- **NEW**: DingTalk configuration management APIs

### Frontend (Vue 3)
- **NEW**: Qlib stock selection page - display model-recommended stocks with scores
- **NEW**: Backtest page with real-time visualization (return curve, drawdown, risk metrics dashboard)
- **NEW**: Risk report page - post-market risk summary display
- **NEW**: Scheduler management page - configure and monitor scheduled tasks
- **NEW**: DingTalk configuration page
- **NEW**: ECharts integration for financial charts

### Data Layer
- **NEW**: MongoDB collections: `qlib_models`, `backtest_results`, `risk_reports`, `scheduler_jobs`, `dingtalk_configs`
- **NEW**: Custom Qlib DataProvider reading from MongoDB K-line data

### Configuration
- Stock pool: CSI 300 (沪深300)
- Model evaluation criteria: Sharpe ratio > 1.5
- Risk tolerance: Portfolio VaR 5% (95% confidence)
- Training frequency: Weekly

## Capabilities

### New Capabilities

- `qlib-integration`: ML model training and inference using MongoDB K-line data, weekly automated training, model version management
- `ml-stock-selection`: Use trained Qlib models to score and select top stocks from CSI 300
- `async-backtest`: WebSocket-based real-time backtest with progress updates, supports both traditional strategies and Qlib models
- `risk-monitoring`: Post-market risk report generation with VaR, industry concentration, and position-level risk metrics
- `position-management`: Position sizing with risk controls (VaR limits, max single position, industry concentration limits)
- `scheduler-management`: Dynamic scheduler job CRUD APIs for managing training, backtest, and risk report tasks
- `dingtalk-config`: DingTalk webhook and secret configuration management

### Modified Capabilities

- `holdings-management`: Enhanced with position-level risk metrics and VaR calculations (existing holdings API extended)
- `market-monitoring`: Extended to support ML model signals alongside technical indicators

## Impact

### Code Structure
```
apps/api/app/
├── qlib/                    # NEW
├── backtest/                # NEW (enhanced from existing)
├── risk/                    # NEW
├── scheduler/               # ENHANCED
└── api/endpoints/           # NEW endpoints

frontend/vue-admin/src/
├── views/
│   ├── QlibSelectView.vue   # NEW (priority)
│   ├── BacktestView.vue     # NEW
│   ├── RiskReportView.vue   # NEW
│   └── SchedulerView.vue    # NEW
└── components/
    ├── BacktestChart.vue    # NEW
    └── RiskDashboard.vue    # NEW
```

### Dependencies
- **NEW**: `pyqlib` (Microsoft Qlib)
- **NEW**: `lightgbm` (ML model)
- **NEW**: `echarts` (frontend charts)
- **EXISTING**: MongoDB, FastAPI, Vue 3, Naive UI, Akshare, Baostock

### API Endpoints
- `POST /api/qlib/train` - Start model training
- `GET /api/qlib/train/{id}` - Query training status
- `GET /api/qlib/models` - List trained models
- `POST /api/qlib/select` - Execute stock selection
- `POST /api/backtest/run` - Start backtest
- `WebSocket /ws/backtest/{task_id}` - Real-time backtest stream
- `CRUD /api/scheduler/jobs` - Scheduler job management
- `CRUD /api/dingtalk/config` - DingTalk configuration

### MongoDB Collections
- `qlib_models` - Model metadata and metrics
- `backtest_results` - Backtest history and results
- `risk_reports` - Daily risk summaries
- `scheduler_jobs` - Job configurations
- `dingtalk_configs` - DingTalk webhook settings

### Breaking Changes
None - all changes are additive.
