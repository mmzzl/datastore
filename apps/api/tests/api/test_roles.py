import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestRolesEndpoints:
    """Tests for role management endpoints"""

    @pytest.mark.asyncio
    async def test_list_roles_success(self, async_client: AsyncClient, auth_headers, setup_test_db):
        """Test listing roles with proper permissions"""
        response = await async_client.get(
            "/api/roles",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 4  # At least 4 default roles

    @pytest.mark.asyncio
    async def test_list_roles_without_permission(self, async_client: AsyncClient, viewer_auth_headers, setup_test_db):
        """Test listing roles without proper permissions"""
        response = await async_client.get(
            "/api/roles",
            headers=viewer_auth_headers
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_permissions_success(self, async_client: AsyncClient, auth_headers, setup_test_db):
        """Test listing all permissions"""
        response = await async_client.get(
            "/api/roles/permissions",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "permissions" in data
        assert len(data["permissions"]) > 0

    @pytest.mark.asyncio
    async def test_create_role_success(self, async_client: AsyncClient, auth_headers, setup_test_db, test_db):
        """Test creating a new role"""
        response = await async_client.post(
            "/api/roles",
            headers=auth_headers,
            json={
                "role_id": "role_new_test",
                "name": "新测试角色",
                "description": "用于测试的新角色",
                "permissions": ["user:view", "role:view"],
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["role_id"] == "role_new_test"
        assert data["name"] == "新测试角色"
        
        test_db["roles"].delete_one({"role_id": "role_new_test"})

    @pytest.mark.asyncio
    async def test_create_role_duplicate_id(self, async_client: AsyncClient, auth_headers, setup_test_db):
        """Test creating role with duplicate ID"""
        response = await async_client.post(
            "/api/roles",
            headers=auth_headers,
            json={
                "role_id": "role_admin",
                "name": "Duplicate Admin",
                "description": "Duplicate role",
                "permissions": ["*"],
            }
        )
        assert response.status_code == 400
        assert "角色ID已存在" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_role_without_permission(self, async_client: AsyncClient, viewer_auth_headers, setup_test_db):
        """Test creating role without proper permissions"""
        response = await async_client.post(
            "/api/roles",
            headers=viewer_auth_headers,
            json={
                "role_id": "role_new",
                "name": "New Role",
                "description": "New role",
                "permissions": ["user:view"],
            }
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_role_success(self, async_client: AsyncClient, auth_headers, setup_test_db):
        """Test getting role details"""
        response = await async_client.get(
            "/api/roles/role_admin",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role_id"] == "role_admin"
        assert data["name"] == "管理员"

    @pytest.mark.asyncio
    async def test_get_role_not_found(self, async_client: AsyncClient, auth_headers, setup_test_db):
        """Test getting non-existent role"""
        response = await async_client.get(
            "/api/roles/nonexistent_role",
            headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_role_success(self, async_client: AsyncClient, auth_headers, setup_test_db, test_db, test_role_data):
        """Test updating role"""
        response = await async_client.put(
            f"/api/roles/{test_role_data['role_id']}",
            headers=auth_headers,
            json={
                "name": "Updated Role Name",
                "description": "Updated description",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Role Name"
        
        test_db["roles"].update_one(
            {"role_id": test_role_data["role_id"]},
            {"$set": {"name": test_role_data["name"], "description": test_role_data["description"]}}
        )

    @pytest.mark.asyncio
    async def test_update_system_role_forbidden(self, async_client: AsyncClient, auth_headers, setup_test_db):
        """Test updating system role is forbidden"""
        response = await async_client.put(
            "/api/roles/role_admin",
            headers=auth_headers,
            json={
                "name": "Modified Admin",
                "description": "Modified",
            }
        )
        assert response.status_code == 403
        assert "系统内置角色不能修改" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_role_not_found(self, async_client: AsyncClient, auth_headers, setup_test_db):
        """Test updating non-existent role"""
        response = await async_client.put(
            "/api/roles/nonexistent_role",
            headers=auth_headers,
            json={
                "name": "New Name",
                "description": "New description",
            }
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_role_success(self, async_client: AsyncClient, auth_headers, setup_test_db, test_db):
        """Test deleting role"""
        test_db["roles"].insert_one({
            "role_id": "role_to_delete",
            "name": "To Delete",
            "description": "Role to be deleted",
            "permissions": ["user:view"],
            "is_system": False,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
        })
        
        response = await async_client.delete(
            "/api/roles/role_to_delete",
            headers=auth_headers
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_system_role_forbidden(self, async_client: AsyncClient, auth_headers, setup_test_db):
        """Test deleting system role is forbidden"""
        response = await async_client.delete(
            "/api/roles/role_admin",
            headers=auth_headers
        )
        assert response.status_code == 403
        assert "系统内置角色不能删除" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_role_in_use(self, async_client: AsyncClient, auth_headers, setup_test_db):
        """Test deleting role that is in use"""
        response = await async_client.delete(
            "/api/roles/role_viewer",
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "角色正在被" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_role_not_found(self, async_client: AsyncClient, auth_headers, setup_test_db):
        """Test deleting non-existent role"""
        response = await async_client.delete(
            "/api/roles/nonexistent_role",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestRolesPermissions:
    """Tests for role endpoint permissions"""

    @pytest.mark.asyncio
    async def test_viewer_cannot_create_role(self, async_client: AsyncClient, viewer_auth_headers, setup_test_db):
        """Test viewer cannot create roles"""
        response = await async_client.post(
            "/api/roles",
            headers=viewer_auth_headers,
            json={
                "role_id": "role_new",
                "name": "New Role",
                "description": "New role",
                "permissions": ["user:view"],
            }
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_viewer_cannot_update_role(self, async_client: AsyncClient, viewer_auth_headers, setup_test_db, test_role_data):
        """Test viewer cannot update roles"""
        response = await async_client.put(
            f"/api/roles/{test_role_data['role_id']}",
            headers=viewer_auth_headers,
            json={
                "name": "Modified Role",
                "description": "Modified",
            }
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_viewer_cannot_delete_role(self, async_client: AsyncClient, viewer_auth_headers, setup_test_db):
        """Test viewer cannot delete roles"""
        response = await async_client.delete(
            "/api/roles/role_test",
            headers=viewer_auth_headers
        )
        assert response.status_code == 403
