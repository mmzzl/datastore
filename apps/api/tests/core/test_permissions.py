import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, status

from app.core.auth import (
    AuthenticatedUser,
    require_permission,
    require_permissions,
    get_current_user,
)
from app.core.permissions import (
    ALL_PERMISSIONS,
    DEFAULT_ROLES,
    RESOURCE_USER,
    RESOURCE_ROLE,
    ACTION_VIEW,
    ACTION_EDIT,
)


class TestAuthenticatedUser:
    def test_has_permission_exact_match(self):
        user = AuthenticatedUser(
            username="test",
            user_id="1",
            display_name="Test",
            role_id="role_test",
            permissions=["user:view", "role:edit"],
        )
        assert user.has_permission("user:view") is True
        assert user.has_permission("role:edit") is True
        assert user.has_permission("user:delete") is False

    def test_has_permission_wildcard_all(self):
        user = AuthenticatedUser(
            username="test",
            user_id="1",
            display_name="Test",
            role_id="role_test",
            permissions=["*"],
        )
        assert user.has_permission("user:view") is True
        assert user.has_permission("role:delete") is True
        assert user.has_permission("system:manage") is True

    def test_has_permission_wildcard_resource(self):
        user = AuthenticatedUser(
            username="test",
            user_id="1",
            display_name="Test",
            role_id="role_test",
            permissions=["user:*"],
        )
        assert user.has_permission("user:view") is True
        assert user.has_permission("user:edit") is True
        assert user.has_permission("user:delete") is True
        assert user.has_permission("role:view") is False

    def test_has_permission_superuser(self):
        user = AuthenticatedUser(
            username="test",
            user_id="1",
            display_name="Test",
            role_id="role_test",
            permissions=[],
            is_superuser=True,
        )
        assert user.has_permission("user:view") is True
        assert user.has_permission("any:permission") is True


class TestRequirePermission:
    @pytest.mark.asyncio
    async def test_superuser_passes(self):
        user = AuthenticatedUser(
            username="admin",
            user_id="1",
            display_name="Admin",
            role_id="role_superuser",
            permissions=[],
            is_superuser=True,
        )
        checker = require_permission("system:manage")
        result = await checker(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_has_exact_permission(self):
        user = AuthenticatedUser(
            username="test",
            user_id="1",
            display_name="Test",
            role_id="role_test",
            permissions=["user:view", "user:edit"],
        )
        checker = require_permission("user:view")
        result = await checker(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_missing_permission_raises_403(self):
        user = AuthenticatedUser(
            username="test",
            user_id="1",
            display_name="Test",
            role_id="role_test",
            permissions=["user:view"],
        )
        checker = require_permission("user:delete")
        with pytest.raises(HTTPException) as exc_info:
            await checker(user)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "缺少权限" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_wildcard_permission_passes(self):
        user = AuthenticatedUser(
            username="test",
            user_id="1",
            display_name="Test",
            role_id="role_test",
            permissions=["user:*"],
        )
        checker = require_permission("user:delete")
        result = await checker(user)
        assert result == user


class TestRequirePermissions:
    @pytest.mark.asyncio
    async def test_all_permissions_present(self):
        user = AuthenticatedUser(
            username="test",
            user_id="1",
            display_name="Test",
            role_id="role_test",
            permissions=["user:view", "user:edit", "role:view"],
        )
        checker = require_permissions(["user:view", "user:edit"])
        result = await checker(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_one_permission_missing(self):
        user = AuthenticatedUser(
            username="test",
            user_id="1",
            display_name="Test",
            role_id="role_test",
            permissions=["user:view"],
        )
        checker = require_permissions(["user:view", "user:edit"])
        with pytest.raises(HTTPException) as exc_info:
            await checker(user)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "缺少权限" in exc_info.value.detail


class TestPermissionConstants:
    def test_all_permissions_list_not_empty(self):
        assert len(ALL_PERMISSIONS) > 0

    def test_all_permissions_format(self):
        for perm in ALL_PERMISSIONS:
            assert ":" in perm, f"Permission {perm} should contain ':'"
            parts = perm.split(":")
            assert len(parts) == 2, f"Permission {perm} should have format 'resource:action'"

    def test_default_roles_structure(self):
        assert len(DEFAULT_ROLES) == 4
        role_ids = [r["role_id"] for r in DEFAULT_ROLES]
        assert "role_superuser" in role_ids
        assert "role_admin" in role_ids
        assert "role_trader" in role_ids
        assert "role_viewer" in role_ids

    def test_superuser_has_wildcard(self):
        superuser_role = next(r for r in DEFAULT_ROLES if r["role_id"] == "role_superuser")
        assert "*" in superuser_role["permissions"]

    def test_all_default_roles_are_system(self):
        for role in DEFAULT_ROLES:
            assert role["is_system"] is True
