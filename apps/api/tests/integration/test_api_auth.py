"""
测试认证 API - 完全模拟 frontend/vue-admin/src/services/api_auth.ts
"""

import pytest

pytestmark = pytest.mark.asyncio


class TestApiAuth:
    """测试认证 API - 完全模拟前端 api_auth.ts"""

    async def test_login_success(self, async_client, test_user):
        """模拟 apiAuthNew.login(username, password)"""
        response = await async_client.post(
            "/api/auth/token",
            json={"username": test_user["username"], "password": test_user["password"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data
        assert "username" in data
        assert "display_name" in data

    async def test_login_invalid_password(self, async_client, test_user):
        """测试密码错误"""
        response = await async_client.post(
            "/api/auth/token",
            json={"username": test_user["username"], "password": "wrong_password"},
        )

        assert response.status_code == 401

    async def test_login_invalid_username(self, async_client):
        """测试用户名不存在"""
        response = await async_client.post(
            "/api/auth/token",
            json={"username": "nonexistent_user", "password": "any_password"},
        )

        assert response.status_code == 401

    async def test_logout(self, api_client):
        """模拟 apiAuthNew.logout()"""
        response = await api_client.post("/api/auth/logout")

        assert response.status_code == 200

    async def test_get_current_user(self, api_client):
        """模拟 apiAuthNew.getCurrentUser()"""
        response = await api_client.get("/api/auth/me")

        assert response.status_code == 200
        data = response.json()

        # 验证字段与前端期望一致
        assert "id" in data
        assert "username" in data
        assert "display_name" in data
        assert "role_id" in data
        assert "is_superuser" in data
