"""
Integration Tests for Quantitative Trading System

This package contains end-to-end integration tests covering:
- DingTalk notifications with training jobs (18.1)
- Model training and stock selection flow (18.2)
- Backtest WebSocket real-time updates (18.3)
- Position risk report generation (18.4)
- Scheduler job execution (18.5)
- WebSocket stability and reconnection (18.6)
- Multiple concurrent backtests (18.7)
- Position size limit enforcement (18.8)
- Industry concentration limit enforcement (18.9)

Test files:
- test_qlib_integration.py: Qlib training and DingTalk notification tests
- test_backtest_websocket.py: Model training and backtest WebSocket tests
- test_risk_report_integration.py: Position and risk report tests
- test_scheduler_integration.py: Scheduler job execution tests
- test_websocket_stability.py: WebSocket connection stability tests
- test_concurrent_backtests.py: Concurrent backtest execution tests
- test_position_limits.py: Position size and industry concentration tests

Run tests with:
    py -3.12 -m pytest apps/api/tests/integration -v

Run specific test class:
    py -3.12 -m pytest apps/api/tests/integration/test_qlib_integration.py::TestDingTalkTrainingNotification -v

Run with markers:
    py -3.12 -m pytest apps/api/tests/integration -m asyncio -v
"""
