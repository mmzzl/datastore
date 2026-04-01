import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestWebSocketStability:
    """Test 18.6: WebSocket connection stability (disconnect/reconnect)"""

    @pytest.mark.asyncio
    async def test_websocket_connect_disconnect(self):
        from app.backtest.websocket_handler import ConnectionManager
        
        manager = ConnectionManager()
        
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_json = AsyncMock()
        
        task_id = "stability_test_001"
        
        await manager.connect(mock_websocket, task_id)
        assert task_id in manager._connections
        
        await manager.disconnect(mock_websocket, task_id)
        assert task_id not in manager._connections

    @pytest.mark.asyncio
    async def test_websocket_auto_reconnect_simulation(self):
        from app.backtest.websocket_handler import ConnectionManager
        
        manager = ConnectionManager()
        task_id = "reconnect_test"
        
        first_socket = AsyncMock()
        first_socket.accept = AsyncMock()
        first_socket.send_json = AsyncMock(side_effect=Exception("Connection lost"))
        
        second_socket = AsyncMock()
        second_socket.accept = AsyncMock()
        second_socket.send_json = AsyncMock()
        
        await manager.connect(first_socket, task_id)
        
        message = {"type": "progress", "current": 50}
        result = await manager.send_message(first_socket, message)
        assert result is False
        
        await manager.disconnect(first_socket, task_id)
        
        await manager.connect(second_socket, task_id)
        
        result = await manager.send_message(second_socket, message)
        assert result is True
        
        await manager.disconnect(second_socket, task_id)

    @pytest.mark.asyncio
    async def test_websocket_multiple_clients_same_task(self):
        from app.backtest.websocket_handler import ConnectionManager
        
        manager = ConnectionManager()
        task_id = "multi_client_test"
        
        sockets = []
        for i in range(3):
            ws = AsyncMock()
            ws.accept = AsyncMock()
            ws.send_json = AsyncMock()
            sockets.append(ws)
            await manager.connect(ws, task_id)
        
        assert len(manager._connections.get(task_id, set())) == 3
        
        message = {"type": "progress", "current": 100}
        await manager.broadcast(task_id, message)
        
        for ws in sockets:
            ws.send_json.assert_called_with(message)
        
        for ws in sockets:
            await manager.disconnect(ws, task_id)

    @pytest.mark.asyncio
    async def test_websocket_message_queue_on_disconnect(self):
        from app.backtest.websocket_handler import ConnectionManager
        
        manager = ConnectionManager()
        task_id = "queue_test"
        
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        
        await manager.connect(mock_ws, task_id)
        
        message = {"type": "progress", "current": 50}
        await manager.send_message(mock_ws, message)
        
        mock_ws.send_json.assert_called_once()
        
        await manager.disconnect(mock_ws, task_id)

    @pytest.mark.asyncio
    async def test_websocket_dead_connection_cleanup(self):
        from app.backtest.websocket_handler import ConnectionManager
        
        manager = ConnectionManager()
        task_id = "cleanup_test"
        
        dead_ws = AsyncMock()
        dead_ws.accept = AsyncMock()
        dead_ws.send_json = AsyncMock(side_effect=Exception("Dead connection"))
        
        alive_ws = AsyncMock()
        alive_ws.accept = AsyncMock()
        alive_ws.send_json = AsyncMock()
        
        await manager.connect(dead_ws, task_id)
        await manager.connect(alive_ws, task_id)
        
        message = {"type": "progress", "current": 50}
        await manager.broadcast(task_id, message)
        
        assert dead_ws not in manager._connections.get(task_id, set())
        assert alive_ws in manager._connections.get(task_id, set())
        
        await manager.disconnect(alive_ws, task_id)

    @pytest.mark.asyncio
    async def test_websocket_concurrent_connections(self):
        from app.backtest.websocket_handler import ConnectionManager
        
        manager = ConnectionManager()
        
        tasks = []
        for i in range(10):
            task_id = f"concurrent_task_{i}"
            mock_ws = AsyncMock()
            mock_ws.accept = AsyncMock()
            mock_ws.send_json = AsyncMock()
            tasks.append((task_id, mock_ws))
        
        connect_tasks = [
            manager.connect(ws, task_id) 
            for task_id, ws in tasks
        ]
        await asyncio.gather(*connect_tasks)
        
        for task_id, _ in tasks:
            assert task_id in manager._connections
        
        disconnect_tasks = [
            manager.disconnect(ws, task_id) 
            for task_id, ws in tasks
        ]
        await asyncio.gather(*disconnect_tasks)

    @pytest.mark.asyncio
    async def test_websocket_connection_manager_singleton(self):
        from app.backtest.websocket_handler import get_connection_manager, manager
        
        retrieved_manager = get_connection_manager()
        
        assert retrieved_manager is manager
        assert isinstance(retrieved_manager.__class__, type)

    @pytest.mark.asyncio
    async def test_websocket_send_progress_message(self):
        from app.backtest.websocket_handler import ConnectionManager
        
        manager = ConnectionManager()
        task_id = "progress_test"
        
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        
        await manager.connect(mock_ws, task_id)
        
        await manager.send_progress(
            task_id=task_id,
            current=50,
            total=100,
            portfolio_value=105000,
            return_pct=5.0,
            drawdown=-2.0,
        )
        
        sent_message = mock_ws.send_json.call_args[0][0]
        assert sent_message["type"] == "progress"
        assert sent_message["current"] == 50
        assert sent_message["total"] == 100
        assert sent_message["portfolio_value"] == 105000
        
        await manager.disconnect(mock_ws, task_id)

    @pytest.mark.asyncio
    async def test_websocket_message_format(self):
        from app.backtest.websocket_handler import ConnectionManager
        
        manager = ConnectionManager()
        task_id = "format_test"
        
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        
        await manager.connect(mock_ws, task_id)

        await manager.send_progress(task_id, 10, 100, 100000, 0, 0)
        progress_msg = mock_ws.send_json.call_args[0][0]
        assert all(k in progress_msg for k in ["type", "current", "total", "portfolio_value", "return_pct", "drawdown"])

        mock_ws.send_json.reset_mock()
        await manager.send_completed(task_id, {"sharpe_ratio": 1.5})
        completed_msg = mock_ws.send_json.call_args[0][0]
        assert completed_msg["type"] == "completed"
        assert "metrics" in completed_msg

        mock_ws.send_json.reset_mock()
        await manager.send_error(task_id, "Test error")
        error_msg = mock_ws.send_json.call_args[0][0]
        assert error_msg["type"] == "error"
        assert error_msg["message"] == "Test error"
        
        await manager.disconnect(mock_ws, task_id)

    @pytest.mark.asyncio
    async def test_websocket_task_isolation(self):
        from app.backtest.websocket_handler import ConnectionManager
        
        manager = ConnectionManager()
        
        task_1 = "isolation_test_1"
        task_2 = "isolation_test_2"
        
        ws_1 = AsyncMock()
        ws_1.accept = AsyncMock()
        ws_1.send_json = AsyncMock()
        
        ws_2 = AsyncMock()
        ws_2.accept = AsyncMock()
        ws_2.send_json = AsyncMock()
        
        await manager.connect(ws_1, task_1)
        await manager.connect(ws_2, task_2)
        
        await manager.broadcast(task_1, {"type": "progress", "current": 50})
        
        ws_1.send_json.assert_called_once()
        ws_2.send_json.assert_not_called()
        
        await manager.disconnect(ws_1, task_1)
        await manager.disconnect(ws_2, task_2)
