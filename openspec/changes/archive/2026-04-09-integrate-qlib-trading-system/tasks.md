# Implementation Tasks

## 1. Backend Infrastructure - Qlib Integration

- [x] 1.1 Install Qlib dependencies: `pip install pyqlib lightgbm`
- [x] 1.2 Create Qlib module directory: `apps/api/app/qlib/`
- [x] 1.3 Implement MongoDataProvider class in `app/qlib/data_provider.py`
- [x] 1.4 Implement QlibTrainer class in `app/qlib/trainer.py`
- [x] 1.5 Implement ModelManager class in `app/qlib/model_manager.py`
- [x] 1.6 Implement QlibPredictor class in `app/qlib/predictor.py`
- [x] 1.7 Create Qlib configuration module in `app/qlib/config.py`
- [x] 1.8 Initialize Qlib in FastAPI startup (apps/api/main.py)
- [x] 1.9 Create MongoDB collection: `qlib_models`
- [x] 1.10 Test MongoDataProvider with CSI 300 data loading

## 2. Backend - Training API

- [x] 2.1 Create `app/api/endpoints/qlib.py`
- [x] 2.2 Implement POST /api/qlib/train endpoint
- [x] 2.3 Implement GET /api/qlib/train/{id} endpoint for status tracking
- [x] 2.4 Implement GET /api/qlib/models endpoint
- [x] 2.5 Implement GET /api/qlib/models/{id} endpoint
- [ ] 2.6 Test training flow end-to-end with CSI 300 data
- [x] 2.7 Add error handling for training failures
- [ ] 2.8 Integrate DingTalk notification for training completion

## 3. Backend - Stock Selection API

- [x] 3.1 Implement POST /api/qlib/select endpoint in `qlib.py`
- [x] 3.2 Add selection result caching in MongoDB `selection_results` collection
- [x] 3.3 Implement topk parameter validation
- [x] 3.4 Add model loading and prediction logic
- [x] 3.5 Format response with {code, name, score, rank} structure
- [ ] 3.6 Test selection with trained model

## 4. Backend - Async Backtest Engine

- [x] 4.1 Create `app/backtest/` module directory
- [x] 4.2 Implement BaseStrategy abstract class in `app/backtest/strategies/base.py`
- [x] 4.3 Implement MACrossStrategy in `app/backtest/strategies/ma_cross.py`
- [x] 4.4 Implement RSIStrategy in `app/backtest/strategies/rsi.py`
- [x] 4.5 Implement BollingerStrategy in `app/backtest/strategies/bollinger.py`
- [x] 4.6 Implement MACDStrategy in `app/backtest/strategies/macd.py`
- [x] 4.7 Implement QlibModelStrategy in `app/backtest/strategies/qlib_model.py`
- [x] 4.8 Implement StrategyFactory in `app/backtest/strategies/factory.py`
- [x] 4.9 Implement AsyncBacktestEngine in `app/backtest/async_engine.py`
- [x] 4.10 Implement risk metrics calculator in `app/backtest/risk_metrics.py`
- [x] 4.11 Test async backtest engine with sample data

## 5. Backend - WebSocket Backtest

- [x] 5.1 Create `app/backtest/websocket_handler.py`
- [x] 5.2 Implement WebSocket endpoint at /ws/backtest/{task_id}
- [x] 5.3 Implement connection manager for multiple clients
- [x] 5.4 Implement progress streaming (every 10 data points)
- [x] 5.5 Implement completion message with metrics
- [x] 5.6 Implement error handling and client disconnection
- [x] 5.7 Test WebSocket with multiple concurrent clients

## 6. Backend - Backtest API

- [x] 6.1 Create `app/api/endpoints/backtest.py`
- [x] 6.2 Implement POST /api/backtest/run endpoint
- [x] 6.3 Implement GET /api/backtest/results endpoint (paginated history)
- [x] 6.4 Create MongoDB collection: `backtest_results`
- [x] 6.5 Implement backtest result saving
- [x] 6.6 Add parameter validation for each strategy type

## 7. Backend - Risk Monitoring

- [x] 7.1 Create `app/risk/` module directory
- [x] 7.2 Implement RiskReportGenerator in `app/risk/risk_report.py`
- [x] 7.3 Implement portfolio VaR calculation
- [x] 7.4 Implement position-level VaR calculation
- [x] 7.5 Implement industry concentration calculation
- [x] 7.6 Implement risk score calculation
- [x] 7.7 Implement recommendation generation
- [x] 7.8 Create MongoDB collection: `risk_reports`
- [x] 7.9 Test risk report generation with sample portfolio

## 8. Backend - Position Management

- [x] 8.1 Create `app/risk/position_manager.py`
- [x] 8.2 Implement position size limit validation (max 10%)
- [x] 8.3 Implement industry concentration limit validation (max 30%)
- [x] 8.4 Implement position sizing recommendation logic
- [x] 8.5 Enhance existing holdings API with risk metrics
- [x] 8.6 Add position notes and tags support to MongoDB

## 9. Backend - Scheduler Management

- [x] 9.1 Create `app/scheduler/job_manager.py`
- [x] 9.2 Create `app/scheduler/job_store.py`
- [x] 9.3 Create `app/api/endpoints/scheduler.py`
- [x] 9.4 Implement GET /api/scheduler/jobs endpoint
- [x] 9.5 Implement POST /api/scheduler/jobs endpoint
- [x] 9.6 Implement PUT /api/scheduler/jobs/{id} endpoint
- [x] 9.7 Implement DELETE /api/scheduler/jobs/{id} endpoint
- [x] 9.8 Implement POST /api/scheduler/jobs/{id}/trigger endpoint
- [x] 9.9 Implement GET /api/scheduler/jobs/{id}/executions endpoint
- [x] 9.10 Create MongoDB collection: `scheduler_jobs`
- [x] 9.11 Create MongoDB collection: `job_executions`
- [x] 9.12 Implement cron expression validation
- [x] 9.13 Implement dynamic job scheduling with APScheduler

## 10. Backend - Scheduled Jobs

- [x] 10.1 Create `app/scheduler/qlib_train_job.py` for weekly training
- [x] 10.2 Create `app/scheduler/risk_report_job.py` for daily risk reports
- [x] 10.3 Configure weekly training cron: "0 2 * * 0"
- [x] 10.4 Configure daily risk report cron: "30 15 * * 1-5"
- [x] 10.5 Implement job execution tracking
- [x] 10.6 Implement failure retry logic (3 retries)
- [x] 10.7 Integrate DingTalk notifications for job status

## 11. Backend - DingTalk Configuration

- [x] 11.1 Create `app/api/endpoints/dingtalk.py`
- [x] 11.2 Implement GET /api/dingtalk/config endpoint (with masking)
- [x] 11.3 Implement POST /api/dingtalk/config endpoint
- [x] 11.4 Implement PUT /api/dingtalk/config endpoint
- [x] 11.5 Implement DELETE /api/dingtalk/config endpoint
- [x] 11.6 Implement POST /api/dingtalk/test endpoint
- [x] 11.7 Create MongoDB collection: `dingtalk_configs`
- [x] 11.8 Implement webhook and secret encryption
- [x] 11.9 Enhance existing DingTalkNotifier to read from config

## 12. Frontend - Infrastructure

- [x] 12.1 Add ECharts dependency: `npm install echarts vue-echarts`
- [x] 12.2 Add WebSocket client dependency (native WebSocket or socket.io-client)
- [x] 12.3 Create `frontend/vue-admin/src/services/api_qlib.ts`
- [x] 12.4 Create `frontend/vue-admin/src/services/api_backtest.ts`
- [x] 12.5 Create `frontend/vue-admin/src/services/api_risk.ts`
- [x] 12.6 Create `frontend/vue-admin/src/services/api_scheduler.ts`
- [x] 12.7 Create `frontend/vue-admin/src/services/websocket.ts`
- [x] 12.8 Create `frontend/vue-admin/src/stores/qlib.ts`
- [x] 12.9 Create `frontend/vue-admin/src/stores/backtest.ts`
- [x] 12.10 Create `frontend/vue-admin/src/stores/risk.ts`
- [x] 12.11 Update router to add new routes

## 13. Frontend - Stock Selection Page (Priority)

- [x] 13.1 Create `frontend/vue-admin/src/views/QlibSelectView.vue`
- [x] 13.2 Implement model selector dropdown component
- [x] 13.3 Implement date picker for selection date
- [x] 13.4 Implement "Run Selection" button with loading state
- [x] 13.5 Implement results table with columns: Rank, Code, Name, Score
- [x] 13.6 Implement table sorting functionality
- [x] 13.7 Add router entry: {path: '/qlib/select', component: QlibSelectView}
- [x] 13.8 Test stock selection flow end-to-end

## 14. Frontend - Backtest Page

- [x] 14.1 Create `frontend/vue-admin/src/views/BacktestView.vue`
- [x] 14.2 Implement strategy selector dropdown
- [x] 14.3 Implement parameter configuration form (dynamic based on strategy)
- [x] 14.4 Implement date range picker
- [x] 14.5 Implement initial capital input
- [x] 14.6 Implement "Start Backtest" button
- [x] 14.7 Create `frontend/vue-admin/src/components/BacktestChart.vue`
- [x] 14.8 Implement return curve chart with ECharts
- [x] 14.9 Implement drawdown chart with ECharts
- [x] 14.10 Implement WebSocket client for real-time updates
- [x] 14.11 Implement progress bar component
- [x] 14.12 Implement risk metrics dashboard panel
- [x] 14.13 Add router entry: {path: '/backtest', component: BacktestView}
- [x] 14.14 Test real-time backtest visualization

## 15. Frontend - Risk Report Page

- [x] 15.1 Create `frontend/vue-admin/src/views/RiskReportView.vue`
- [x] 15.2 Implement date picker for historical reports
- [x] 15.3 Implement risk score gauge chart (0-100)
- [x] 15.4 Implement risk level badge component
- [x] 15.5 Implement holdings risk table
- [x] 15.6 Implement industry concentration pie chart
- [x] 15.7 Implement recommendations list component
- [x] 15.8 Create `frontend/vue-admin/src/components/RiskDashboard.vue`
- [x] 15.9 Add router entry: {path: '/risk-report', component: RiskReportView}
- [x] 15.10 Test risk report display

## 16. Frontend - Scheduler Management Page

- [x] 16.1 Create `frontend/vue-admin/src/views/SchedulerView.vue`
- [x] 16.2 Implement jobs table with columns: Name, Type, Schedule, Enabled, Last Run, Next Run
- [x] 16.3 Implement "New Job" button and modal
- [x] 16.4 Implement job creation form with: Name, Type, Cron Expression, Config
- [x] 16.5 Implement job edit modal
- [x] 16.6 Implement job delete with confirmation
- [x] 16.7 Implement enable/disable toggle
- [x] 16.8 Implement "Trigger Now" button
- [x] 16.9 Implement execution history modal
- [x] 16.10 Add router entry: {path: '/scheduler', component: SchedulerView}
- [x] 16.11 Test scheduler management flow

## 17. Frontend - DingTalk Config Page

- [x] 17.1 Create `frontend/vue-admin/src/views/DingtalkConfigView.vue`
- [x] 17.2 Implement webhook URL input field
- [x] 17.3 Implement secret input field
- [x] 17.4 Implement enabled toggle
- [x] 17.5 Implement "Save" button
- [x] 17.6 Implement "Test Notification" button
- [x] 17.7 Add router entry: {path: '/dingtalk-config', component: DingtalkConfigView}
- [x] 17.8 Test DingTalk configuration flow

## 18. Integration Testing

- [x] 18.1 Test end-to-end: Configure DingTalk → Weekly training → Receive notification
- [x] 18.2 Test end-to-end: Train model → Select stocks → View results
- [x] 18.3 Test end-to-end: Configure backtest → Run → View real-time charts
- [x] 18.4 Test end-to-end: Add positions → Wait for risk report → View in frontend
- [x] 18.5 Test: Scheduler job creation → Trigger → Verify execution
- [x] 18.6 Test: WebSocket connection stability (disconnect/reconnect)
- [x] 18.7 Test: Multiple concurrent backtests
- [x] 18.8 Test: Position size limit enforcement
- [x] 18.9 Test: Industry concentration limit enforcement

## 19. Documentation

- [x] 19.1 Update API documentation (OpenAPI/Swagger)
- [x] 19.2 Write developer setup guide
- [x] 19.3 Write deployment guide
- [x] 19.4 Document Qlib integration architecture
- [x] 19.5 Document scheduler configuration
- [x] 19.6 Document risk metrics calculation methodology
- [x] 19.7 Create user guide for frontend features

## 20. Deployment & Monitoring

- [x] 20.1 Create MongoDB indexes for new collections
- [x] 20.2 Configure environment variables for Qlib settings
- [x] 20.3 Set up log rotation for training jobs
- [x] 20.4 Configure monitoring for scheduled jobs
- [x] 20.5 Set up alerts for job failures
- [x] 20.6 Configure backup strategy for MongoDB collections
- [x] 20.7 Test rollback procedure
- [x] 20.8 Deploy to production environment
