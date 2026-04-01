import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch, Mock
from datetime import datetime


class TestBacktestWebSocketIntegration:
    """Test 18.3: Configure backtest → Run → View real-time charts"""

    @pytest.mark.asyncio
    async def test_backtest_configuration_and_run(self, mock_backtest_engine):
        config = {
            "strategy": "ma_cross",
            "params": {"short_window": 5, "long_window": 20},
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_capital": 100000,
            "instruments": ["SH600519", "SH600036"],
        }

        task_id = await mock_backtest_engine.run_backtest(config)
        assert task_id == "backtest_test_001"

        status = await mock_backtest_engine.get_status(task_id)
        assert "status" in status
        assert status["status"] in ["pending", "running", "completed"]

    @pytest.mark.asyncio
    async def test_backtest_progress_updates(self, mock_backtest_engine):
        from app.backtest.async_engine import BacktestStatus
        
        task_id = await mock_backtest_engine.run_backtest({})
        
        for _ in range(5):
            status = await mock_backtest_engine.get_status(task_id)
            if status.get("status") == BacktestStatus.RUNNING.value:
                assert "progress" in status
                assert 0 <= status.get("progress", 0) <= 1.0
            await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_websocket_connection_and_messages(self):
        from app.backtest.websocket_handler import ConnectionManager
        
        manager = ConnectionManager()
        
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_json = AsyncMock()
        
        task_id = "test_task_001"
        await manager.connect(mock_websocket, task_id)
        
        assert task_id in manager._connections
        assert mock_websocket in manager._connections[task_id]

        message = {"type": "progress", "current": 10, "total": 100}
        await manager.send_message(mock_websocket, message)
        mock_websocket.send_json.assert_called_once_with(message)

        await manager.disconnect(mock_websocket, task_id)
        assert mock_websocket not in manager._connections.get(task_id, set())

    @pytest.mark.asyncio
    async def test_websocket_progress_broadcast(self):
        from app.backtest.websocket_handler import ConnectionManager
        
        manager = ConnectionManager()
        
        mock_ws1 = AsyncMock()
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_json = AsyncMock()
        
        mock_ws2 = AsyncMock()
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_json = AsyncMock()

        task_id = "broadcast_test"
        
        await manager.connect(mock_ws1, task_id)
        await manager.connect(mock_ws2, task_id)

        progress_msg = {
            "type": "progress",
            "current": 50,
            "total": 100,
            "portfolio_value": 105000,
            "return_pct": 5.0,
            "drawdown": -2.0,
        }
        await manager.broadcast(task_id, progress_msg)

        mock_ws1.send_json.assert_called_with(progress_msg)
        mock_ws2.send_json.assert_called_with(progress_msg)

    @pytest.mark.asyncio
    async def test_websocket_completed_message(self):
        from app.backtest.websocket_handler import ConnectionManager
        
        manager = ConnectionManager()
        
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_json = AsyncMock()
        
        task_id = "completion_test"
        await manager.connect(mock_websocket, task_id)

        metrics = {
            "total_return": 0.15,
            "sharpe_ratio": 1.8,
            "max_drawdown": -0.08,
        }
        await manager.send_completed(task_id, metrics)

        sent_message = mock_websocket.send_json.call_args[0][0]
        assert sent_message["type"] == "completed"
        assert sent_message["metrics"] == metrics

    @pytest.mark.asyncio
    async def test_websocket_error_message(self):
        from app.backtest.websocket_handler import ConnectionManager
        
        manager = ConnectionManager()
        
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_json = AsyncMock()
        
        task_id = "error_test"
        await manager.connect(mock_websocket, task_id)

        error_msg = "Backtest failed: Invalid strategy"
        await manager.send_error(task_id, error_msg)

        sent_message = mock_websocket.send_json.call_args[0][0]
        assert sent_message["type"] == "error"
        assert sent_message["message"] == error_msg

    @pytest.mark.asyncio
    async def test_backtest_result_retrieval(self, mock_backtest_engine):
        task_id = await mock_backtest_engine.run_backtest({})
        
        result = await mock_backtest_engine.get_result(task_id)
        
        assert result is not None
        assert "task_id" in result
        assert "status" in result
        assert "portfolio_values" in result
        assert "metrics" in result

        metrics = result.get("metrics", {})
        assert "total_return" in metrics or "sharpe_ratio" in metrics

    @pytest.mark.asyncio
    async def test_backtest_metrics_calculation(self):
        from app.backtest.risk_metrics import RiskMetricsCalculator

        portfolio_values = [100000, 101000, 102500, 101500, 103000]
        trades = [
            {"pnl": 1000, "action": "buy"},
            {"pnl": 500, "action": "sell"},
        ]

        metrics = RiskMetricsCalculator.calculate(portfolio_values, trades=trades)

        assert metrics is not None
        assert hasattr(metrics, 'total_return') or hasattr(metrics, 'sharpe_ratio')

    @pytest.mark.asyncio
    async def test_backtest_with_multiple_strategies(self, mock_backtest_engine):
        strategies = ["ma_cross", "rsi", "qlib_model"]
        
        task_ids = []
        for strategy in strategies:
            config = {"strategy": strategy}
            task_id = await mock_backtest_engine.run_backtest(config)
            task_ids.append(task_id)

        assert len(task_ids) == 3
        assert len(set(task_ids)) == 3

    @pytest.mark.asyncio
    async def test_backtest_storage_and_retrieval(self, test_db):
        collection = test_db["backtest_results"]
        
        result_doc = {
            "task_id": "backtest_test_001",
            "config": {
                "strategy": "ma_cross",
                "initial_capital": 100000,
            },
            "portfolio_values": [100000, 101000, 102500],
            "metrics": {
                "total_return": 0.025,
                "sharpe_ratio": 1.8,
            },
            "status": "completed",
            "created_at": datetime.now(),
        }
        
        collection.insert_one(result_doc)
        
        stored = collection.find_one({"task_id": "backtest_test_001"})
        assert stored is not None
        assert stored["status"] == "completed"
        
        collection.delete_many({"task_id": "backtest_test_001"})
