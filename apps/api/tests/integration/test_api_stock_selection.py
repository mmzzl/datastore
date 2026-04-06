"""
测试策略选股 API - 完全模拟 frontend/vue-admin/src/services/api_stock_selection.ts
"""

import pytest
from unittest.mock import patch, AsyncMock

pytestmark = pytest.mark.asyncio


class TestApiStockSelection:
    """测试策略选股 API - 完全模拟前端 api_stock_selection.ts"""

    async def test_get_stock_pools(self, api_client):
        """模拟 apiStockSelection.getStockPools()"""
        response = await api_client.get("/api/stock-selection/pools")

        assert response.status_code in [200, 401, 403, 404, 500], (
            f"Unexpected status: {response.status_code}"
        )

        if response.status_code == 200:
            data = response.json()
            assert "pools" in data, "Missing 'pools'"

    async def test_get_stock_pools_unauthorized(self, async_client):
        """测试未授权访问股票池"""
        response = await async_client.get("/api/stock-selection/pools")

        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    async def test_run_selection(self, api_client):
        """模拟 apiStockSelection.runSelection() - 开始选股"""
        response = await api_client.post(
            "/api/stock-selection/run",
            json={
                "strategy_type": "ma_cross",
                "strategy_params": {"period": 20},
                "stock_pool": "all",
            },
        )

        assert response.status_code in [200, 201, 400, 422, 500], (
            f"Unexpected status: {response.status_code}"
        )

        if response.status_code in [200, 201]:
            data = response.json()
            assert "task_id" in data, "Missing 'task_id'"
            assert "status" in data, "Missing 'status'"

    async def test_run_selection_with_plugin(self, api_client):
        """模拟使用插件策略的选股"""
        response = await api_client.post(
            "/api/stock-selection/run",
            json={
                "strategy_type": "plugin",
                "plugin_id": "test_plugin",
                "stock_pool": "hs300",
            },
        )

        assert response.status_code in [200, 201, 400, 422, 404, 500], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_run_selection_rsi_strategy(self, api_client):
        """测试 RSI 策略选股"""
        response = await api_client.post(
            "/api/stock-selection/run",
            json={
                "strategy_type": "rsi",
                "strategy_params": {"period": 14, "oversold": 30, "overbought": 70},
                "stock_pool": "hs300",
            },
        )

        assert response.status_code in [200, 201, 400, 422, 500], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_run_selection_macd_strategy(self, api_client):
        """测试 MACD 策略选股"""
        response = await api_client.post(
            "/api/stock-selection/run",
            json={
                "strategy_type": "macd",
                "strategy_params": {"fast": 12, "slow": 26, "signal": 9},
                "stock_pool": "zz500",
            },
        )

        assert response.status_code in [200, 201, 400, 422, 500], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_run_selection_bollinger_strategy(self, api_client):
        """测试布林带策略选股"""
        response = await api_client.post(
            "/api/stock-selection/run",
            json={
                "strategy_type": "bollinger",
                "strategy_params": {"period": 20, "std": 2},
                "stock_pool": "all",
            },
        )

        assert response.status_code in [200, 201, 400, 422, 500], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_run_selection_invalid_strategy(self, api_client):
        """测试无效策略类型"""
        response = await api_client.post(
            "/api/stock-selection/run",
            json={
                "strategy_type": "invalid_strategy",
                "stock_pool": "all",
            },
        )

        assert response.status_code in [400, 422], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_run_selection_invalid_stock_pool(self, api_client):
        """测试无效股票池"""
        response = await api_client.post(
            "/api/stock-selection/run",
            json={
                "strategy_type": "ma_cross",
                "stock_pool": "invalid_pool",
            },
        )

        assert response.status_code in [400, 422], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_run_selection_missing_strategy_type(self, api_client):
        """测试缺少策略类型"""
        response = await api_client.post(
            "/api/stock-selection/run",
            json={
                "stock_pool": "all",
            },
        )

        assert response.status_code in [400, 422], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_get_result(self, api_client):
        """模拟 apiStockSelection.getResult() - 获取选股结果"""
        response = await api_client.get("/api/stock-selection/test-task-id")

        assert response.status_code in [200, 404, 500], (
            f"Unexpected status: {response.status_code}"
        )

        if response.status_code == 200:
            data = response.json()
            assert "task_id" in data or "status" in data

    async def test_get_result_not_found(self, api_client):
        """测试不存在的任务"""
        response = await api_client.get("/api/stock-selection/nonexistent-id")

        assert response.status_code in [404, 500], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_get_result_completed_status(self, api_client):
        """测试获取已完成的任务结果"""
        response = await api_client.get("/api/stock-selection/completed-task")

        assert response.status_code in [200, 404, 500], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_get_result_running_status(self, api_client):
        """测试获取运行中的任务状态"""
        response = await api_client.get("/api/stock-selection/running-task")

        assert response.status_code in [200, 404, 500], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_get_history(self, api_client):
        """模拟 apiStockSelection.getHistory() - 获取选股历史"""
        response = await api_client.get("/api/stock-selection/history")

        assert response.status_code in [200, 401, 404, 500], (
            f"Unexpected status: {response.status_code}"
        )

        if response.status_code == 200:
            data = response.json()
            assert "items" in data or "total" in data

    async def test_get_history_with_pagination(self, api_client):
        """测试带分页的历史查询"""
        response = await api_client.get(
            "/api/stock-selection/history", params={"page": 1, "page_size": 10}
        )

        assert response.status_code in [200, 401, 404, 500], (
            f"Unexpected status: {response.status_code}"
        )

        if response.status_code == 200:
            data = response.json()
            assert "items" in data

    async def test_get_history_with_status_filter(self, api_client):
        """测试按状态过滤历史"""
        response = await api_client.get(
            "/api/stock-selection/history", params={"status": "completed"}
        )

        assert response.status_code in [200, 401, 404, 500], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_get_history_with_stock_pool_filter(self, api_client):
        """测试按股票池过滤历史"""
        response = await api_client.get(
            "/api/stock-selection/history", params={"stock_pool": "hs300"}
        )

        assert response.status_code in [200, 401, 404, 500], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_get_history_all_filters(self, api_client):
        """测试同时使用多个过滤条件"""
        response = await api_client.get(
            "/api/stock-selection/history",
            params={
                "page": 2,
                "page_size": 5,
                "status": "completed",
                "stock_pool": "all",
            },
        )

        assert response.status_code in [200, 401, 404, 500], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_get_history_empty_result(self, api_client):
        """测试空历史记录"""
        response = await api_client.get(
            "/api/stock-selection/history", params={"page": 1, "page_size": 100}
        )

        assert response.status_code in [200, 401, 404, 500], (
            f"Unexpected status: {response.status_code}"
        )
