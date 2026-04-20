import logging
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.security import security
from app.user.models import User
from app.user.password import verify_password
from app.storage import MongoStorage
from app.role.models import Role
from app.auth import verify_token as verify_custom_token

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    def __init__(
        self,
        username: str,
        user_id: str,
        display_name: str,
        role_id: str,
        permissions: List[str],
        is_superuser: bool = False,
    ):
        self.username = username
        self.user_id = user_id
        self.display_name = display_name
        self.role_id = role_id
        self.permissions = permissions
        self.is_superuser = is_superuser

    def has_permission(self, permission: str) -> bool:
        if self.is_superuser:
            return True
        if "*" in self.permissions:
            return True
        resource = permission.split(":")[0] if ":" in permission else permission
        if f"{resource}:*" in self.permissions:
            return True
        return permission in self.permissions


def get_storage() -> MongoStorage:
    storage = MongoStorage(
        host=settings.mongodb_host,
        port=settings.mongodb_port,
        db_name=settings.mongodb_database,
        username=settings.mongodb_username,
        password=settings.mongodb_password,
    )
    storage.connect()
    return storage


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> AuthenticatedUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Try custom token first
    custom_user = verify_custom_token(token)
    if custom_user:
        username = custom_user
    else:
        # Try JWT token
        payload = security.verify_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌载荷",
                headers={"WWW-Authenticate": "Bearer"},
            )

    storage = get_storage()
    try:
        storage.connect()
        user_data = storage.get_user_by_username(username)
        if user_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user_data.get("status") != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已被禁用",
            )

        role_id = user_data.get("role_id")
        role_data = storage.get_role_by_id(role_id) if role_id else None
        permissions = role_data.get("permissions", []) if role_data else []
        is_superuser = user_data.get("is_superuser", False)

        return AuthenticatedUser(
            username=user_data.get("username"),
            user_id=str(user_data.get("_id")),
            display_name=user_data.get("display_name", ""),
            role_id=role_id,
            permissions=permissions,
            is_superuser=is_superuser,
        )
    finally:
        storage.close()


def require_permission(permission: str):
    async def permission_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        if current_user.is_superuser:
            return current_user
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {permission}",
            )
        return current_user

    return permission_checker


def require_permissions(permissions: List[str]):
    async def permission_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        if current_user.is_superuser:
            return current_user
        for permission in permissions:
            if not current_user.has_permission(permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少权限: {permission}",
                )
        return current_user

    return permission_checker
