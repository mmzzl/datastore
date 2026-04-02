import pytest
from datetime import datetime
from app.user import User, Role
from app.user.password import hash_password, verify_password


class TestUserModel:
    def test_user_creation(self):
        user = User(
            username="testuser",
            password_hash="hashed_password",
            display_name="Test User",
            role_id="admin",
        )
        assert user.username == "testuser"
        assert user.password_hash == "hashed_password"
        assert user.display_name == "Test User"
        assert user.role_id == "admin"
        assert user.status == "active"
        assert user.is_superuser is False
        assert user.login_count == 0

    def test_user_with_optional_fields(self):
        user = User(
            username="testuser",
            password_hash="hashed_password",
            display_name="Test User",
            role_id="admin",
            email="test@example.com",
            phone="1234567890",
            status="disabled",
            is_superuser=True,
            created_by="admin",
        )
        assert user.email == "test@example.com"
        assert user.phone == "1234567890"
        assert user.status == "disabled"
        assert user.is_superuser is True
        assert user.created_by == "admin"

    def test_user_to_dict(self):
        user = User(
            username="testuser",
            password_hash="hashed_password",
            display_name="Test User",
            role_id="admin",
            email="test@example.com",
        )
        data = user.to_dict()
        assert data["username"] == "testuser"
        assert data["password_hash"] == "hashed_password"
        assert data["display_name"] == "Test User"
        assert data["role_id"] == "admin"
        assert data["email"] == "test@example.com"
        assert data["status"] == "active"

    def test_user_from_dict(self):
        data = {
            "username": "testuser",
            "password_hash": "hashed_password",
            "display_name": "Test User",
            "role_id": "admin",
            "email": "test@example.com",
            "status": "active",
            "is_superuser": False,
            "login_count": 5,
        }
        user = User.from_dict(data)
        assert user.username == "testuser"
        assert user.password_hash == "hashed_password"
        assert user.display_name == "Test User"
        assert user.role_id == "admin"
        assert user.email == "test@example.com"
        assert user.login_count == 5


class TestRoleModel:
    def test_role_creation(self):
        role = Role(
            role_id="admin",
            name="Administrator",
            description="Full access role",
        )
        assert role.role_id == "admin"
        assert role.name == "Administrator"
        assert role.description == "Full access role"
        assert role.permissions == []
        assert role.is_system is False

    def test_role_with_permissions(self):
        role = Role(
            role_id="admin",
            name="Administrator",
            description="Full access role",
            permissions=["read", "write", "delete"],
            is_system=True,
        )
        assert role.permissions == ["read", "write", "delete"]
        assert role.is_system is True

    def test_role_to_dict(self):
        role = Role(
            role_id="admin",
            name="Administrator",
            description="Full access role",
            permissions=["read", "write"],
        )
        data = role.to_dict()
        assert data["role_id"] == "admin"
        assert data["name"] == "Administrator"
        assert data["description"] == "Full access role"
        assert data["permissions"] == ["read", "write"]

    def test_role_from_dict(self):
        data = {
            "role_id": "admin",
            "name": "Administrator",
            "description": "Full access role",
            "permissions": ["read", "write"],
            "is_system": True,
        }
        role = Role.from_dict(data)
        assert role.role_id == "admin"
        assert role.name == "Administrator"
        assert role.permissions == ["read", "write"]
        assert role.is_system is True


class TestPasswordHashing:
    def test_hash_password(self):
        password = "my_secret_password"
        hashed = hash_password(password)
        assert hashed != password
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        password = "my_secret_password"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        password = "my_secret_password"
        hashed = hash_password(password)
        assert verify_password("wrong_password", hashed) is False

    def test_different_passwords_have_different_hashes(self):
        password = "my_secret_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_same_password_verifies_with_different_hashes(self):
        password = "my_secret_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_empty_password(self):
        password = ""
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_long_password(self):
        password = "a" * 100
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_special_characters_password(self):
        password = "p@ssw0rd!#$%^&*()"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
