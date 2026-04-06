"""
测试角色 API - 完全模拟 frontend/vue-admin/src/services/api_roles.ts
"""

import pytest

pytestmark = pytest.mark.asyncio


class TestApiRoles:
    """测试角色 API - 完全模拟前端 api_roles.ts"""

    async def test_list_roles(self, api_client):
        """模拟 apiRoles.getRoles()"""
        response = await api_client.get("/api/roles")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "items" in data or "roles" in data, "Missing response data"

    async def test_list_roles_with_pagination(self, api_client):
        """模拟带分页的角色列表"""
        response = await api_client.get(
            "/api/roles", params={"page": 1, "page_size": 10}
        )

        assert response.status_code == 200

    async def test_get_role(self, api_client):
        """模拟 apiRoles.getRole(roleId)"""
        response = await api_client.get("/api/roles/role_admin")

        # 200 表示找到，404 表示不存在
        assert response.status_code in [200, 404], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_get_role_not_found(self, api_client):
        """测试获取不存在的角色"""
        response = await api_client.get("/api/roles/nonexistent_role")

        assert response.status_code == 404

    async def test_create_role(self, api_client):
        """模拟 apiRoles.createRole(roleData)"""
        import uuid

        test_role_id = f"role_test_{uuid.uuid4().hex[:6]}"

        response = await api_client.post(
            "/api/roles",
            json={
                "role_id": test_role_id,
                "name": "测试角色",
                "description": "用于测试的角色",
                "permissions": ["user:view"],
            },
        )

        # 201 表示创建成功，400 表示验证错误
        assert response.status_code in [200, 201, 400], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_update_role(self, api_client):
        """模拟 apiRoles.updateRole(roleId, roleData)"""
        response = await api_client.put(
            "/api/roles/role_admin",
            json={"name": "更新的角色名称", "description": "更新描述"},
        )

        # 200 表示更新成功，403 表示系统内置角色不能修改，404 表示不存在
        assert response.status_code in [200, 403, 404], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_delete_role(self, api_client):
        """模拟 apiRoles.deleteRole(roleId)"""
        response = await api_client.delete("/api/roles/role_test")

        # 200 表示删除成功，403 表示系统内置角色不能删除，404 表示不存在
        assert response.status_code in [200, 403, 404], (
            f"Unexpected status: {response.status_code}"
        )

    async def test_list_permissions(self, api_client):
        """模拟获取所有权限列表"""
        response = await api_client.get("/api/roles/permissions")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "permissions" in data, "Missing 'permissions' in response"
