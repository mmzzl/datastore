"""
测试用户 API - 完全模拟 frontend/vue-admin/src/services/api_users.ts
"""

import pytest

pytestmark = pytest.mark.asyncio


class TestApiUsers:
    """测试用户 API - 完全模拟前端 api_users.ts"""

    async def test_list_users(self, api_client):
        """模拟 apiUsers.getUsers()"""
        response = await api_client.get("/api/users")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "items" in data, "Missing 'items'"
        assert "total" in data, "Missing 'total'"
        assert "page" in data, "Missing 'page'"
        assert "page_size" in data, "Missing 'page_size'"

    async def test_list_users_with_pagination(self, api_client):
        """模拟带分页的用户列表"""
        response = await api_client.get(
            "/api/users", params={"page": 1, "page_size": 10}
        )

        assert response.status_code == 200

    async def test_list_users_with_status_filter(self, api_client):
        """模拟按状态过滤用户"""
        response = await api_client.get("/api/users", params={"status": "active"})

        assert response.status_code == 200

    async def test_get_user(self, api_client):
        """模拟 apiUsers.getUser(userId)"""
        response = await api_client.get("/api/users/admin")

        # 可能返回 200 或 404
        assert response.status_code in [200, 404], (
            f"Unexpected status: {response.status_code}"
        )

        if response.status_code == 200:
            data = response.json()
            assert "username" in data or "id" in data

    async def test_create_user(self, api_client):
        """模拟 apiUsers.createUser(userData)"""
        import uuid

        test_username = f"testuser_{uuid.uuid4().hex[:8]}"
        test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"

        response = await api_client.post(
            "/api/users",
            json={
                "username": test_username,
                "password": "test123",
                "email": test_email,
                "display_name": "测试用户",
                "role_id": "role_viewer",
                "status": "active",
            },
        )

        assert response.status_code in [200, 201, 400], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_update_user(self, api_client):
        """模拟 apiUsers.updateUser(userId, userData)"""
        response = await api_client.put(
            "/api/users/admin", json={"display_name": "更新后的名称"}
        )

        assert response.status_code in [200, 404], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_delete_user(self, api_client):
        """模拟 apiUsers.deleteUser(userId)"""
        response = await api_client.delete("/api/users/testuser")

        # 200 表示删除成功，404 表示用户不存在
        assert response.status_code in [200, 404], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_reset_password(self, api_client):
        """模拟 apiUsers.resetPassword(userId)"""
        response = await api_client.post("/api/users/admin/reset-password")

        assert response.status_code in [200, 404], (
            f"Unexpected status: {response.status_code}"
        )
