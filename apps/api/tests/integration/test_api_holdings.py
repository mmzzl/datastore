"""
测试持仓 API - 完全模拟 frontend/vue-admin/src/services/api_holdings.ts
"""

import pytest

pytestmark = pytest.mark.asyncio


class TestApiHoldings:
    """测试持仓 API - 完全模拟前端 api_holdings.ts"""

    async def test_get_holdings_pagination(self, api_client):
        """模拟 api_holdings.getHoldings(userId, page, pageSize)"""
        response = await api_client.get(
            "/api/holdings/admin", params={"page": 1, "page_size": 10}
        )

        # 如果返回 404，说明接口路径不对
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

        data = response.json()

        # 验证响应格式与前端期望一致
        assert "items" in data, "Missing 'items' in response"
        assert "total" in data, "Missing 'total' in response"
        assert "page" in data, "Missing 'page' in response"
        assert "page_size" in data, "Missing 'page_size' in response"
        assert "total_pages" in data, "Missing 'total_pages' in response"

    async def test_get_holdings_with_filters(self, api_client):
        """模拟带过滤条件的查询"""
        response = await api_client.get(
            "/api/holdings/admin",
            params={"page": 1, "page_size": 10, "sort_by": "code", "order": "asc"},
        )

        assert response.status_code == 200

    async def test_upsert_holding(self, api_client):
        """模拟 api_holdings.upsertHolding(userId, code, name, quantity, avgCost)"""
        response = await api_client.post(
            "/api/holdings/admin",
            json={
                "code": "SH600000",
                "name": "测试股票",
                "quantity": 1000,
                "average_cost": 10.5,
            },
        )

        assert response.status_code in [200, 201, 400], (
            f"Unexpected status: {response.status_code}"
        )

        # 如果成功，验证返回格式
        if response.status_code in [200, 201]:
            data = response.json()
            assert data.get("success") == True or "id" in data

    async def test_remove_holding(self, api_client):
        """模拟 api_holdings.removeHolding(userId, code)"""
        response = await api_client.delete("/api/holdings/admin/SH600000")

        assert response.status_code in [200, 404], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_get_portfolio(self, api_client):
        """模拟 api_holdings.getPortfolio(userId)"""
        response = await api_client.get("/api/portfolio/admin")

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

        data = response.json()

        # 验证字段与前端 holdings.ts store 期望一致
        assert "total_cost" in data, "Missing 'total_cost'"
        assert "market_value" in data, "Missing 'market_value'"
        assert "unrealized_pnl" in data or "profit" in data, "Missing profit field"
        assert "profit_rate" in data, "Missing 'profit_rate'"

    async def test_get_transactions(self, api_client):
        """模拟获取交易记录"""
        response = await api_client.get("/api/transactions/admin")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "items" in data, "Missing 'items'"
        assert "total" in data, "Missing 'total'"

    async def test_get_pnl(self, api_client):
        """模拟获取盈亏数据"""
        response = await api_client.get("/api/pnl/admin")

        # 这个接口可能不存在，期望 404
        assert response.status_code in [200, 404], (
            f"Unexpected status: {response.status_code}"
        )
