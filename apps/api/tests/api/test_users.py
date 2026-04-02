import pytest
from unittest.mock import MagicMock, patch
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestUsersEndpoints:
    """Tests for user management endpoints"""

    @pytest.mark.asyncio
    async def test_list_users_success(self, async_client: AsyncClient, auth_headers, setup_test_db):
        """Test listing users with proper permissions"""
        response = await async_client.get(
            "/api/users",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    @pytest.mark.asyncio
    async def test_list_users_with_filters(self, async_client: AsyncClient, auth_headers, setup_test_db):
        """Test listing users with filters"""
        response = await async_client.get(
            "/api/users?status=active&page=1&page_size=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    @pytest.mark.asyncio
    async def test_list_users_search(self, async_client: AsyncClient, auth_headers, setup_test_db):
        """Test listing users with search"""
        response = await async_client.get(
            "/api/users?search=test",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_list_users_without_permission(self, async_client: AsyncClient, viewer_auth_headers, setup_test_db):
        """Test listing users without proper permissions"""
        response = await async_client.get(
            "/api/users",
            headers=viewer_auth_headers
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_user_success(self, async_client: AsyncClient, auth_headers, setup_test_db, test_db):
        """Test creating a new user"""
        response = await async_client.post(
            "/api/users",
            headers=auth_headers,
            json={
                "username": "newtestuser",
                "password": "newpassword123",
                "display_name": "New Test User",
                "role_id": "role_viewer",
                "status": "active",
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newtestuser"
        assert data["display_name"] == "New Test User"
        
        test_db["users"].delete_one({"username": "newtestuser"})

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, async_client: AsyncClient, auth_headers, setup_test_db, test_admin_data):
        """Test creating user with duplicate username"""
        response = await async_client.post(
            "/api/users",
            headers=auth_headers,
            json={
                "username": test_admin_data["username"],
                "password": "password123",
                "display_name": "Duplicate User",
                "role_id": "role_viewer",
                "status": "active",
            }
        )
        assert response.status_code == 400
        assert "用户名已存在" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_user_invalid_role(self, async_client: AsyncClient, auth_headers, setup_test_db):
        """Test creating user with invalid role"""
        response = await async_client.post(
            "/api/users",
            headers=auth_headers,
            json={
                "username": "newuser",
                "password": "password123",
                "display_name": "New User",
                "role_id": "nonexistent_role",
                "status": "active",
            }
        )
        assert response.status_code == 400
        assert "角色不存在" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_user_without_permission(self, async_client: AsyncClient, viewer_auth_headers, setup_test_db):
        """Test creating user without proper permissions"""
        response = await async_client.post(
            "/api/users",
            headers=viewer_auth_headers,
            json={
                "username": "newuser",
                "password": "password123",
                "display_name": "New User",
                "role_id": "role_viewer",
                "status": "active",
            }
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_user_success(self, async_client: AsyncClient, auth_headers, setup_test_db, test_db):
        """Test getting user details"""
        users = list(test_db["users"].find({"username": "testadmin"}))
        if users:
            user_id = str(users[0]["_id"])
            response = await async_client.get(
                f"/api/users/{user_id}",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == "testadmin"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, async_client: AsyncClient, auth_headers, setup_test_db):
        """Test getting non-existent user"""
        from bson import ObjectId
        fake_id = str(ObjectId())
        response = await async_client.get(
            f"/api/users/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_user_success(self, async_client: AsyncClient, auth_headers, setup_test_db, test_db):
        """Test updating user"""
        users = list(test_db["users"].find({"username": "testuser"}))
        if users:
            user_id = str(users[0]["_id"])
            response = await async_client.put(
                f"/api/users/{user_id}",
                headers=auth_headers,
                json={
                    "display_name": "Updated Display Name",
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["display_name"] == "Updated Display Name"
            
            test_db["users"].update_one(
                {"_id": users[0]["_id"]},
                {"$set": {"display_name": "Test User"}}
            )

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, async_client: AsyncClient, auth_headers, setup_test_db):
        """Test updating non-existent user"""
        from bson import ObjectId
        fake_id = str(ObjectId())
        response = await async_client.put(
            f"/api/users/{fake_id}",
            headers=auth_headers,
            json={"display_name": "New Name"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_user_invalid_role(self, async_client: AsyncClient, auth_headers, setup_test_db, test_db):
        """Test updating user with invalid role"""
        users = list(test_db["users"].find({"username": "testuser"}))
        if users:
            user_id = str(users[0]["_id"])
            response = await async_client.put(
                f"/api/users/{user_id}",
                headers=auth_headers,
                json={"role_id": "nonexistent_role"}
            )
            assert response.status_code == 400
            assert "角色不存在" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_user_success(self, async_client: AsyncClient, auth_headers, setup_test_db, test_db):
        """Test deleting user"""
        test_db["users"].insert_one({
            "username": "to_delete",
            "password_hash": "hash",
            "display_name": "To Delete",
            "role_id": "role_viewer",
            "status": "active",
            "is_superuser": False,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "login_count": 0,
        })
        
        users = list(test_db["users"].find({"username": "to_delete"}))
        if users:
            user_id = str(users[0]["_id"])
            response = await async_client.delete(
                f"/api/users/{user_id}",
                headers=auth_headers
            )
            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, async_client: AsyncClient, auth_headers, setup_test_db):
        """Test deleting non-existent user"""
        from bson import ObjectId
        fake_id = str(ObjectId())
        response = await async_client.delete(
            f"/api/users/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_superuser_forbidden(self, async_client: AsyncClient, auth_headers, setup_test_db, test_db):
        """Test deleting superuser is forbidden"""
        users = list(test_db["users"].find({"username": "testadmin"}))
        if users:
            user_id = str(users[0]["_id"])
            response = await async_client.delete(
                f"/api/users/{user_id}",
                headers=auth_headers
            )
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_reset_password_success(self, async_client: AsyncClient, auth_headers, setup_test_db, test_db):
        """Test resetting user password"""
        users = list(test_db["users"].find({"username": "testuser"}))
        if users:
            user_id = str(users[0]["_id"])
            response = await async_client.post(
                f"/api/users/{user_id}/reset-password",
                headers=auth_headers
            )
            assert response.status_code == 200
            assert "密码已重置" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_reset_password_not_found(self, async_client: AsyncClient, auth_headers, setup_test_db):
        """Test resetting password for non-existent user"""
        from bson import ObjectId
        fake_id = str(ObjectId())
        response = await async_client.post(
            f"/api/users/{fake_id}/reset-password",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestUsersPermissions:
    """Tests for user endpoint permissions"""

    @pytest.mark.asyncio
    async def test_viewer_cannot_create_user(self, async_client: AsyncClient, viewer_auth_headers, setup_test_db):
        """Test viewer cannot create users"""
        response = await async_client.post(
            "/api/users",
            headers=viewer_auth_headers,
            json={
                "username": "newuser",
                "password": "password123",
                "display_name": "New User",
                "role_id": "role_viewer",
                "status": "active",
            }
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_viewer_cannot_delete_user(self, async_client: AsyncClient, viewer_auth_headers, setup_test_db, test_db):
        """Test viewer cannot delete users"""
        users = list(test_db["users"].find({"username": "testuser"}))
        if users:
            user_id = str(users[0]["_id"])
            response = await async_client.delete(
                f"/api/users/{user_id}",
                headers=viewer_auth_headers
            )
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_viewer_cannot_reset_password(self, async_client: AsyncClient, viewer_auth_headers, setup_test_db, test_db):
        """Test viewer cannot reset passwords"""
        users = list(test_db["users"].find({"username": "testadmin"}))
        if users:
            user_id = str(users[0]["_id"])
            response = await async_client.post(
                f"/api/users/{user_id}/reset-password",
                headers=viewer_auth_headers
            )
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_cannot_delete_self(self, async_client: AsyncClient, auth_headers, setup_test_db, test_db):
        """Test user cannot delete themselves"""
        users = list(test_db["users"].find({"username": "testadmin"}))
        if users:
            user_id = str(users[0]["_id"])
            response = await async_client.delete(
                f"/api/users/{user_id}",
                headers=auth_headers
            )
            assert response.status_code == 400
            assert "不能删除自己" in response.json()["detail"]
