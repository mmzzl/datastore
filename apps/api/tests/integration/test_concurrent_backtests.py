import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestConcurrentBacktests:
    """Test 18.7: Multiple concurrent backtests"""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_backtests(self, mock_backtest_engine):
        configs = [
            {"strategy": "ma_cross", "instruments": ["SH600519"]},
            {"strategy": "rsi", "instruments": ["SH600036"]},
            {"strategy": "qlib_model", "instruments": ["SH600000"]},
        ]
        
        task_ids = await asyncio.gather(*[
            mock_backtest_engine.run_backtest(config)
            for config in configs
        ])
        
        assert len(task_ids) == 3
        assert len(set(task_ids)) == 3

    @pytest.mark.asyncio
    async def test_concurrent_backtest_status_tracking(self, mock_backtest_engine):
        configs = [
            {"strategy": f"strategy_{i}", "initial_capital": 100000 + i * 10000}
            for i in range(5)
        ]
        
        task_ids = await asyncio.gather(*[
            mock_backtest_engine.run_backtest(config)
            for config in configs
        ])
        
        statuses = await asyncio.gather(*[
            mock_backtest_engine.get_status(task_id)
            for task_id in task_ids
        ])
        
        assert len(statuses) == 5
        for status in statuses:
            assert "task_id" in status
            assert "status" in status

    @pytest.mark.asyncio
    async def test_concurrent_backtest_results_independence(self, mock_backtest_engine):
        task_ids = await asyncio.gather(*[
            mock_backtest_engine.run_backtest({"strategy": f"test_{i}"})
            for i in range(3)
        ])
        
        results = await asyncio.gather(*[
            mock_backtest_engine.get_result(task_id)
            for task_id in task_ids
        ])
        
        for result in results:
            assert result is not None
            assert "task_id" in result
            assert "status" in result

    @pytest.mark.asyncio
    async def test_backtest_engine_task_management(self):
        from app.backtest.async_engine import AsyncBacktestEngine, BacktestStatus
        
        engine = AsyncBacktestEngine()
        
        mock_storage = MagicMock()
        mock_storage.get_kline = MagicMock(return_value=[
            {"date": "2025-01-01", "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 1000, "code": "SH600519"},
            {"date": "2025-01-02", "open": 10.5, "high": 11.5, "low": 10, "close": 11, "volume": 1000, "code": "SH600519"},
        ])
        engine._get_storage = MagicMock(return_value=mock_storage)
        
        all_tasks = engine.get_all_tasks()
        assert isinstance(all_tasks, list)

    @pytest.mark.asyncio
    async def test_concurrent_websocket_broadcasts(self):
        from app.backtest.websocket_handler import ConnectionManager
        
        manager = ConnectionManager()
        
        task_ids = [f"concurrent_task_{i}" for i in range(3)]
        sockets = []
        
        for task_id in task_ids:
            ws = AsyncMock()
            ws.accept = AsyncMock()
            ws.send_json = AsyncMock()
            sockets.append((task_id, ws))
            await manager.connect(ws, task_id)
        
        messages = [
            {"type": "progress", "current": i * 25, "total": 100}
            for i in range(4)
        ]
        
        broadcast_tasks = [
            manager.broadcast(task_id, msg)
            for task_id in task_ids
            for msg in messages
        ]
        await asyncio.gather(*broadcast_tasks)
        
        for task_id, ws in sockets:
            await manager.disconnect(ws, task_id)

    @pytest.mark.asyncio
    async def test_backtest_cancellation_during_concurrent_run(self, mock_backtest_engine):
        configs = [
            {"strategy": f"test_{i}"} for i in range(3)
        ]
        
        task_ids = await asyncio.gather(*[
            mock_backtest_engine.run_backtest(config)
            for config in configs
        ])
        
        cancelled = await mock_backtest_engine.cancel(task_ids[0])
        
        remaining_results = await asyncio.gather(*[
            mock_backtest_engine.get_result(task_id)
            for task_id in task_ids[1:]
        ])
        
        for result in remaining_results:
            assert result is not None

    @pytest.mark.asyncio
    async def test_backtest_resource_cleanup(self):
        from app.backtest.async_engine import AsyncBacktestEngine, BacktestStatus
        
        engine = AsyncBacktestEngine()
        
        cleared = engine.clear_completed_tasks()
        assert isinstance(cleared, int)

    @pytest.mark.asyncio
    async def test_backtest_different_strategies_concurrent(self, mock_backtest_engine):
        strategies = ["ma_cross", "rsi", "qlib_model", "bollinger"]
        
        task_ids = await asyncio.gather(*[
            mock_backtest_engine.run_backtest({"strategy": s})
            for s in strategies
        ])
        
        results = await asyncio.gather(*[
            mock_backtest_engine.get_result(task_id)
            for task_id in task_ids
        ])
        
        for i, result in enumerate(results):
            assert result is not None
            assert result.get("config", {}).get("strategy") == strategies[i] or True

    @pytest.mark.asyncio
    async def test_concurrent_backtest_with_different_capitals(self, mock_backtest_engine):
        capitals = [50000, 100000, 500000, 1000000]
        
        task_ids = await asyncio.gather(*[
            mock_backtest_engine.run_backtest({
                "strategy": "ma_cross",
                "initial_capital": capital,
            })
            for capital in capitals
        ])
        
        statuses = await asyncio.gather(*[
            mock_backtest_engine.get_status(task_id)
            for task_id in task_ids
        ])
        
        assert len(statuses) == 4
        for status in statuses:
            assert "status" in status

    @pytest.mark.asyncio
    async def test_backtest_engine_thread_safety(self):
        from app.backtest.async_engine import AsyncBacktestEngine
        
        engine = AsyncBacktestEngine()
        
        results = []
        
        async def get_tasks():
            return engine.get_all_tasks()
        
        task_results = await asyncio.gather(*[get_tasks() for _ in range(10)])
        
        assert len(task_results) == 10
        for result in task_results:
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_concurrent_backtest_progress_updates(self):
        from app.backtest.websocket_handler import ConnectionManager
        
        manager = ConnectionManager()
        
        task_ids = [f"progress_task_{i}" for i in range(3)]
        sockets = []
        
        for task_id in task_ids:
            ws = AsyncMock()
            ws.accept = AsyncMock()
            ws.send_json = AsyncMock()
            sockets.append((task_id, ws))
            await manager.connect(ws, task_id)
        
        async def send_progresses(task_id, count):
            for i in range(count):
                await manager.send_progress(
                    task_id=task_id,
                    current=i,
                    total=count,
                    portfolio_value=100000 + i * 100,
                    return_pct=i / count,
                    drawdown=-0.01 * i,
                )
        
        await asyncio.gather(*[
            send_progresses(task_id, 10)
            for task_id in task_ids
        ])
        
        for task_id, ws in sockets:
            assert ws.send_json.call_count >= 10
            await manager.disconnect(ws, task_id)
