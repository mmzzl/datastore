# Design: Integrate Qlib Trading System

## Context

### Current State
- **Backend**: FastAPI with MongoDB storage, existing technical analysis (RSI, MACD, MA), simple backtest engine, holdings management, DingTalk notifications
- **Frontend**: Vue 3 + Vite + Naive UI, existing dashboard, holdings, market watch, settings pages
- **Data Sources**: MongoDB K-line data (populated by Akshare/Baostock), real-time data via Akshare
- **Architecture**: Monolithic FastAPI application

### Stakeholders
- **Primary User**: Aggressive trader seeking ML-driven stock selection and real-time backtest visualization
- **Development Team**: Single developer (fast iteration prioritized)

### Constraints
- Single-machine deployment (no distributed training)
- MongoDB as single source of truth for K-line data
- Must integrate with existing data layer (MongoDBAdapter)
- Aggressive trading style: high risk tolerance (5% VaR), focus on momentum factors

## Goals / Non-Goals

**Goals:**
1. Enable ML-based stock selection using Qlib with MongoDB K-line data
2. Provide real-time backtest visualization via WebSocket (return curve, drawdown, risk metrics)
3. Automate weekly model training (Sunday 02:00)
4. Generate daily post-market risk reports (15:30)
5. Support both Qlib models and traditional strategies (MA, RSI, Bollinger, MACD)
6. Manage scheduled tasks via frontend
7. Configure DingTalk via frontend

**Non-Goals:**
1. Distributed training infrastructure (single-machine only)
2. Real-time risk monitoring (post-market batch calculation only)
3. Mobile app (web-only)
4. Multi-tenant user management (single user)
5. Paper trading / live trading execution (backtest and signals only)

## Decisions

### D1: Qlib Data Integration Strategy

**Decision**: Custom MongoDataProvider instead of Qlib's built-in data loaders

**Rationale**:
- MongoDB is already the system's data store (single source of truth)
- Avoids data duplication and sync issues between Qlib built-in and MongoDB
- Reuses existing MongoDBAdapter infrastructure
- Simpler operational model (one data pipeline)

**Alternatives Considered**:
1. **Qlib built-in data (yfinance, baostock)**: Rejected - would create data duplication and sync complexity
2. **Hybrid approach (Qlib historical + MongoDB real-time)**: Rejected - increases complexity, creates consistency issues

**Implementation**:
```python
class MongoDataProvider:
    """Bridges MongoDB K-line data to Qlib format"""
    def load_data(self, instruments, start, end) -> pd.DataFrame:
        # MultiIndex: (datetime, instrument)
        # Columns: open, high, low, close, volume, amount
        df = self.mongo_adapter.get_kline(...)
        return self._to_qlib_format(df)
```

### D2: WebSocket Backtest Architecture

**Decision**: Async generator pattern with connection manager

**Rationale**:
- Existing BacktestEngine is synchronous and returns complete results
- Need real-time progress without blocking HTTP connections
- Async generator allows yielding intermediate results naturally
- Connection manager handles multiple concurrent clients

**Alternatives Considered**:
1. **Server-Sent Events (SSE)**: Simpler but unidirectional; WebSocket enables future bidirectional features
2. **Polling**: Higher latency, more requests; real-time feel requires WebSocket
3. **Background thread + DB polling**: More complex; async generator is cleaner

**Implementation Pattern**:
```python
async def backtest_stream(websocket: WebSocket, task_id: str):
    async for progress in engine.run_async(data, strategy):
        await websocket.send_json(progress)
    await websocket.send_json({"type": "completed", "metrics": ...})
```

### D3: Strategy Abstraction

**Decision**: Factory pattern with base Strategy class

**Rationale**:
- Need unified interface for Qlib models and traditional strategies
- Factory enables runtime strategy selection by name
- Base class enforces consistent signal generation interface

**Alternatives Considered**:
1. **No abstraction (separate implementations)**: Code duplication, harder to test
2. **Plugin architecture**: Over-engineered for current needs

**Interface**:
```python
class BaseStrategy:
    def generate_signal(self, data: Dict) -> str:  # 'buy' | 'sell' | 'hold'
        raise NotImplementedError

class QlibModelStrategy(BaseStrategy):
    def __init__(self, model_id: str, topk: int):
        self.model = ModelManager.load(model_id)
    
    def generate_signal(self, data: Dict) -> str:
        scores = self.model.predict(data)
        top_stocks = scores.nlargest(self.topk)
        # Return signal based on current position
```

### D4: Model Versioning

**Decision**: MongoDB metadata + filesystem models

**Rationale**:
- MongoDB for fast querying (by metrics, date, status)
- Filesystem for large model files (not suitable for MongoDB)
- Simple version numbering (v1, v2, ...) with automatic rollback support

**Alternatives Considered**:
1. **MLflow**: Additional dependency, overkill for single-developer scenario
2. **MongoDB GridFS**: Slower for large models, unnecessary complexity

**Storage**:
```
MongoDB: qlib_models collection
{
    "model_id": "model_2026_03_30_001",
    "version": 3,
    "created_at": "2026-03-30T02:00:00Z",
    "metrics": {"sharpe": 1.8, "ic": 0.06},
    "file_path": "/models/model_2026_03_30_001.pkl"
}

Filesystem: ./models/
├── model_2026_03_23_001.pkl
├── model_2026_03_30_001.pkl  # latest
└── ...
```

### D5: Risk Calculation Timing

**Decision**: Post-market batch calculation (15:30 daily), not real-time

**Rationale**:
- User specified post-market summary (not real-time monitoring)
- Simpler implementation (no streaming VaR calculations)
- Sufficient for swing trading style
- Lower computational overhead during trading hours

**Alternatives Considered**:
1. **Real-time streaming VaR**: Complex, overkill for stated requirements
2. **Intraday periodic (hourly)**: Unnecessary for daily rebalancing strategy

### D6: Training Frequency & Trigger

**Decision**: Weekly cron (Sunday 02:00) + manual API trigger

**Rationale**:
- Weekly sufficient for CSI 300 (stable index composition)
- Sunday early morning: low system load, no market activity
- Manual trigger for ad-hoc experiments or after market regime changes

**Training Window**:
- Train: 2015-01-01 to recent-week - 2 weeks
- Validate: 2-week holdout
- Test: Most recent 2 weeks (for metrics reporting)

## Risks / Trade-offs

### R1: Qlib Data Freshness
- **Risk**: MongoDB K-line data may be stale if crawler fails
- **Mitigation**: Pre-training data integrity check; alert via DingTalk if data gaps detected
- **Fallback**: Skip training round, keep previous model

### R2: Training Time Blocking
- **Risk**: Model training (2-4 hours) may block other operations on single-machine deployment
- **Mitigation**: Run training in background thread; limit concurrent training jobs to 1
- **Trade-off**: Training uses significant CPU/memory; schedule for low-traffic hours

### R3: WebSocket Connection Stability
- **Risk**: Client disconnection during long backtest loses progress
- **Mitigation**: 
  1. Store intermediate progress in MongoDB (allow resume)
  2. Client-side auto-reconnect with last-seen sequence number
- **Trade-off**: Additional complexity vs. UX improvement

### R4: Model Overfitting
- **Risk**: Model performs well on backtest but fails in production
- **Mitigation**:
  1. Out-of-sample test set (never used in training)
  2. IC and ICIR monitoring across time segments
  3. Reject model if test Sharpe < validation Sharpe * 0.8
  4. Require manual approval before deploying new model

### R5: Risk Metric Accuracy
- **Risk**: VaR estimates based on historical volatility may underestimate tail risk
- **Mitigation**: 
  1. Use conservative multiplier (1.65 instead of 1.65 for 95% VaR)
  2. Monitor VaR breaches; alert if actual losses exceed VaR
- **Trade-off**: More conservative positioning vs. potential missed opportunities

### R6: Frontend Chart Performance
- **Risk**: Real-time WebSocket updates may overwhelm ECharts rendering
- **Mitigation**:
  1. Throttle updates (batch every 100ms)
  2. Use WebWorker for data processing
  3. Limit visible data points (show last N bars)
- **Trade-off**: Slight delay vs. smooth rendering

## Migration Plan

### Phase 1: Backend Infrastructure (Weeks 1-3)
1. Install Qlib dependencies
2. Implement MongoDataProvider
3. Implement QlibTrainer + ModelManager
4. Add MongoDB collections (qlib_models, etc.)
5. Create training API endpoints
6. Test training flow end-to-end

### Phase 2: Async Backtest (Weeks 4-5)
1. Refactor BacktestEngine to async generator
2. Implement WebSocket handler
3. Add strategy factory pattern
4. Test WebSocket streaming

### Phase 3: Frontend - Stock Selection (Week 6)
1. Add ECharts dependency
2. Create QlibSelectView.vue
3. Implement stock selection API service
4. Display model recommendations with scores

### Phase 4: Frontend - Backtest & Risk (Weeks 7-8)
1. Create BacktestView.vue with real-time charts
2. Create RiskReportView.vue
3. Implement WebSocket client
4. Test real-time visualization

### Phase 5: Scheduler & Config (Week 9)
1. Implement JobManager
2. Create scheduler API endpoints
3. Create SchedulerView.vue
4. Create DingTalk config page

### Rollback Strategy
- Each phase is independently deployable
- Qlib integration is isolated module (can disable if issues)
- Existing functionality remains unaffected (additive changes)
- Database migrations are additive only (no breaking schema changes)

## Open Questions

1. **Factor Customization**: Should we support custom factor definitions beyond Alpha158 in v1, or defer?
   - **Recommendation**: Defer to v2. Alpha158 is comprehensive for initial needs.

2. **Multi-Model Ensemble**: Should we support ensemble of multiple models (e.g., averaging predictions)?
   - **Recommendation**: Defer to v2. Start with single model for simplicity.

3. **Backtest History Retention**: How long to keep backtest results in MongoDB?
   - **Recommendation**: 90 days (configurable). Older results can be archived to cold storage.

4. **Model Deployment Approval**: Require manual approval before new model goes live, or auto-deploy if metrics improve?
   - **Recommendation**: Manual approval for v1. Add auto-deploy with thresholds in v2.

5. **Risk Report Delivery**: Email in addition to DingTalk?
   - **Recommendation**: Defer to v2. DingTalk sufficient for MVP.
