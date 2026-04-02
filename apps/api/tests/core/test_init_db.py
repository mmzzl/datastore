import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

from app.core.init_db import (
    create_default_roles,
    create_default_admin,
    init_database,
)
from app.core.permissions import DEFAULT_ROLES


class TestCreateDefaultRoles:
    @pytest.mark.asyncio
    async def test_creates_missing_roles(self):
        mock_storage = MagicMock()
        mock_storage.get_role_by_id.return_value = None
        mock_storage.save_role.return_value = "role_id"

        result = await create_default_roles(mock_storage)

        assert result == len(DEFAULT_ROLES)
        assert mock_storage.save_role.call_count == len(DEFAULT_ROLES)

    @pytest.mark.asyncio
    async def test_skips_existing_roles(self):
        mock_storage = MagicMock()
        mock_storage.get_role_by_id.return_value = {"role_id": "existing"}
        mock_storage.save_role.return_value = "role_id"

        result = await create_default_roles(mock_storage)

        assert result == 0
        mock_storage.save_role.assert_not_called()

    @pytest.mark.asyncio
    async def test_mixed_existing_and_new(self):
        mock_storage = MagicMock()
        call_count = 0

        def get_role_side_effect(role_id):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return None
            return {"role_id": role_id}

        mock_storage.get_role_by_id.side_effect = get_role_side_effect
        mock_storage.save_role.return_value = "role_id"

        result = await create_default_roles(mock_storage)

        assert result == 2


class TestCreateDefaultAdmin:
    @pytest.mark.asyncio
    async def test_creates_admin_when_none_exists(self):
        mock_storage = MagicMock()
        mock_storage.get_user_by_username.return_value = None
        mock_storage.save_user.return_value = "admin_user_id"

        with patch("app.core.init_db.settings") as mock_settings:
            mock_settings.default_admin_username = "admin"
            mock_settings.default_admin_password = "admin"
            result = await create_default_admin(mock_storage)

        assert result == "admin_user_id"
        mock_storage.save_user.assert_called_once()
        saved_user = mock_storage.save_user.call_args[0][0]
        assert saved_user["username"] == "admin"
        assert saved_user["is_superuser"] is True
        assert saved_user["role_id"] == "role_superuser"
        assert saved_user["status"] == "active"

    @pytest.mark.asyncio
    async def test_skips_when_admin_exists(self):
        mock_storage = MagicMock()
        mock_storage.get_user_by_username.return_value = {
            "username": "admin",
            "is_superuser": True,
        }

        with patch("app.core.init_db.settings") as mock_settings:
            mock_settings.default_admin_username = "admin"
            mock_settings.default_admin_password = "admin"
            result = await create_default_admin(mock_storage)

        assert result is None
        mock_storage.save_user.assert_not_called()


class TestInitDatabase:
    @pytest.mark.asyncio
    async def test_skips_when_users_exist(self):
        mock_storage = MagicMock()
        mock_storage.get_all_users.return_value = [{"username": "existing_user"}]
        mock_storage.connect = MagicMock()
        mock_storage.close = MagicMock()

        with patch("app.core.init_db.MongoStorage", return_value=mock_storage):
            with patch("app.core.init_db.settings") as mock_settings:
                mock_settings.mongodb_host = "localhost"
                mock_settings.mongodb_port = 27017
                mock_settings.mongodb_database = "test_db"
                mock_settings.mongodb_username = "admin"
                mock_settings.mongodb_password = "password"
                result = await init_database()

        assert result is False
        mock_storage.connect.assert_called_once()
        mock_storage.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_initializes_when_no_users(self):
        mock_storage = MagicMock()
        mock_storage.get_all_users.return_value = []
        mock_storage.get_user_by_username.return_value = None
        mock_storage.get_role_by_id.return_value = None
        mock_storage.save_user.return_value = "admin_id"
        mock_storage.save_role.return_value = "role_id"
        mock_storage.connect = MagicMock()
        mock_storage.close = MagicMock()

        with patch("app.core.init_db.MongoStorage", return_value=mock_storage):
            with patch("app.core.init_db.settings") as mock_settings:
                mock_settings.mongodb_host = "localhost"
                mock_settings.mongodb_port = 27017
                mock_settings.mongodb_database = "test_db"
                mock_settings.mongodb_username = "admin"
                mock_settings.mongodb_password = "password"
                mock_settings.default_admin_username = "admin"
                mock_settings.default_admin_password = "admin"
                result = await init_database()

        assert result is True
        mock_storage.save_role.assert_called()
        mock_storage.save_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_connection_error(self):
        mock_storage = MagicMock()
        mock_storage.connect.side_effect = Exception("Connection failed")

        with patch("app.core.init_db.MongoStorage", return_value=mock_storage):
            with patch("app.core.init_db.settings") as mock_settings:
                mock_settings.mongodb_host = "localhost"
                mock_settings.mongodb_port = 27017
                mock_settings.mongodb_database = "test_db"
                mock_settings.mongodb_username = "admin"
                mock_settings.mongodb_password = "password"
                with pytest.raises(Exception) as exc_info:
                    await init_database()

        assert "Connection failed" in str(exc_info.value)
