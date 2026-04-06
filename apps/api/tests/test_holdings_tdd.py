"""
TD Holdings API Tests - 测试持仓管理功能

遵循TDD原则编写：
1. RED - 编写失败的测试
2. GREEN - 编写最小代码通过测试
3. REFACTOR - 重构优化
"""

import pytest
import os
import sys

# 确保从 apps/api 目录运行
test_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.dirname(test_dir)  # apps/api
root_dir = os.path.dirname(api_dir)  # datastore

# 添加路径
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


TEST_PASSWORD = "aa123aaqqA@"  # 测试用密码


def get_auth_token():
    """获取测试用的认证token"""
    response = client.post(
        "/api/login", json={"username": "admin", "password": TEST_PASSWORD}
    )
    return response.json().get("token", "")


class TestHoldingsAPI:
    """持仓管理API测试"""

    def test_add_holding(self):
        """测试添加持仓"""
        token = get_auth_token()
        response = client.post(
            "/api/holdings/admin",
            json={
                "code": "SH600000",
                "name": "浦发银行",
                "quantity": 1000,
                "average_cost": 5.60,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "holding_id" in response.json()

    def test_get_holdings(self):
        """测试获取持仓列表"""
        token = get_auth_token()
        response = client.get(
            "/api/holdings/admin", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # 应该返回分页结构
        assert "items" in data
        assert isinstance(data["items"], list)
        assert "total" in data

    def test_delete_holding(self):
        """测试删除持仓"""
        token = get_auth_token()

        # 先添加持仓
        client.post(
            "/api/holdings/admin",
            json={
                "code": "SH600519",
                "name": "贵州茅台",
                "quantity": 100,
                "average_cost": 1800,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 删除持仓
        response = client.delete(
            "/api/holdings/admin/SH600519", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json().get("deleted", 0) == 1


class TestPortfolioAPI:
    """Portfolio API测试"""

    def test_get_portfolio(self):
        """测试获取组合信息"""
        token = get_auth_token()
        response = client.get(
            "/api/portfolio/admin", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # 验证返回结构
        assert "holdings_count" in data
        assert "total_cost" in data
        assert "holdings" in data


class TestSettingsAPI:
    """设置API测试"""

    def test_get_settings(self):
        """测试获取设置"""
        token = get_auth_token()
        response = client.get(
            "/api/settings/admin", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "watchlist" in data

    def test_set_settings(self):
        """测试保存设置"""
        token = get_auth_token()
        response = client.post(
            "/api/settings/admin",
            json={
                "watchlist": ["SH600000", "SH600519"],
                "interval_sec": 60,
                "days": 5,
                "cache_ttl": 60,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json().get("ok") == True


class TestAuthMiddleware:
    """认证中间件测试"""

    def test_missing_token(self):
        """测试缺少token应该返回401"""
        response = client.get("/api/holdings/admin")
        assert response.status_code == 401

    def test_invalid_token(self):
        """测试无效token应该返回401"""
        response = client.get(
            "/api/holdings/admin", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
