import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestAuthEndpoints:
    """Tests for authentication endpoints"""

    @pytest.mark.asyncio
    async def test_login_success(self, async_client: AsyncClient, setup_test_db, test_admin_data):
        """Test successful login"""
        response = await async_client.post(
            "/api/auth/token",
            json={
                "username": test_admin_data["username"],
                "password": test_admin_data["password"],
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data
        assert data["username"] == test_admin_data["username"]

    @pytest.mark.asyncio
    async def test_login_invalid_username(self, async_client: AsyncClient, setup_test_db):
        """Test login with invalid username"""
        response = await async_client.post(
            "/api/auth/token",
            json={
                "username": "nonexistent",
                "password": "anypassword",
            }
        )
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, async_client: AsyncClient, setup_test_db, test_admin_data):
        """Test login with invalid password"""
        response = await async_client.post(
            "/api/auth/token",
            json={
                "username": test_admin_data["username"],
                "password": "wrongpassword",
            }
        )
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_disabled_user(self, async_client: AsyncClient, test_db, setup_test_db):
        """Test login with disabled user"""
        users_coll = test_db["users"]
        users_coll.update_one(
            {"username": "testadmin"},
            {"$set": {"status": "disabled"}}
        )
        
        response = await async_client.post(
            "/api/auth/token",
            json={
                "username": "testadmin",
                "password": "adminpassword123",
            }
        )
        assert response.status_code == 403
        assert "用户已被禁用" in response.json()["detail"]
        
        users_coll.update_one(
            {"username": "testadmin"},
            {"$set": {"status": "active"}}
        )

    @pytest.mark.asyncio
    async def test_logout(self, async_client: AsyncClient, auth_headers):
        """Test logout"""
        response = await async_client.post(
            "/api/auth/logout",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["message"] == "登出成功"

    @pytest.mark.asyncio
    async def test_logout_without_auth(self, async_client: AsyncClient):
        """Test logout without authentication"""
        response = await async_client.post("/api/auth/logout")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_change_password_success(self, async_client: AsyncClient, auth_headers, test_db, test_admin_data):
        """Test successful password change"""
        response = await async_client.post(
            "/api/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": test_admin_data["password"],
                "new_password": "newpassword123",
            }
        )
        assert response.status_code == 200
        assert "密码修改成功" in response.json()["message"]
        
        users_coll = test_db["users"]
        users_coll.update_one(
            {"username": test_admin_data["username"]},
            {"$set": {"password_hash": __import__("app.user.password", fromlist=["hash_password"]).hash_password(test_admin_data["password"])}}
        )

    @pytest.mark.asyncio
    async def test_change_password_wrong_old(self, async_client: AsyncClient, auth_headers):
        """Test password change with wrong old password"""
        response = await async_client.post(
            "/api/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": "wrongpassword",
                "new_password": "newpassword123",
            }
        )
        assert response.status_code == 400
        assert "原密码错误" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_change_password_too_short(self, async_client: AsyncClient, auth_headers, test_admin_data):
        """Test password change with too short new password"""
        response = await async_client.post(
            "/api/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": test_admin_data["password"],
                "new_password": "short",
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_current_user_info(self, async_client: AsyncClient, auth_headers):
        """Test getting current user info"""
        response = await async_client.get(
            "/api/auth/me",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "display_name" in data
        assert "permissions" in data

    @pytest.mark.asyncio
    async def test_get_current_user_info_without_auth(self, async_client: AsyncClient):
        """Test getting current user info without authentication"""
        response = await async_client.get("/api/auth/me")
        assert response.status_code == 401
