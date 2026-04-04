import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends, Query

from app.core.auth import get_current_user, get_storage, require_permission, AuthenticatedUser
from app.core.config import settings
from app.core.permissions import ALL_PERMISSIONS
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserStatus,
)
from app.user.password import hash_password
from app.storage import MongoStorage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])


def _user_to_response(user_data: dict, role_name: str = None) -> UserResponse:
    return UserResponse(
        id=str(user_data["_id"]),
        username=user_data["username"],
        display_name=user_data.get("display_name", ""),
        role_id=user_data.get("role_id", ""),
        role_name=role_name,
        email=user_data.get("email"),
        phone=user_data.get("phone"),
        status=user_data.get("status", "active"),
        is_superuser=user_data.get("is_superuser", False),
        last_login=datetime.fromisoformat(user_data["last_login"]) if user_data.get("last_login") else None,
        login_count=user_data.get("login_count", 0),
        created_at=datetime.fromisoformat(user_data["created_at"]) if user_data.get("created_at") else datetime.now(),
        updated_at=datetime.fromisoformat(user_data["updated_at"]) if user_data.get("updated_at") else datetime.now(),
        created_by=user_data.get("created_by"),
    )


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[UserStatus] = None,
    role_id: Optional[str] = None,
    search: Optional[str] = None,
    current_user: AuthenticatedUser = Depends(require_permission("user:view")),
):
    """获取用户列表"""
    storage = get_storage()
    try:
        storage.connect()
        
        skip = (page - 1) * page_size
        
        all_users = storage.get_all_users(skip=0, limit=10000)
        
        filtered_users = all_users
        if status:
            filtered_users = [u for u in filtered_users if u.get("status") == status.value]
        if role_id:
            filtered_users = [u for u in filtered_users if u.get("role_id") == role_id]
        if search:
            search_lower = search.lower()
            filtered_users = [
                u for u in filtered_users
                if search_lower in u.get("username", "").lower()
                or search_lower in u.get("display_name", "").lower()
                or search_lower in (u.get("email", "") or "").lower()
            ]
        
        total = len(filtered_users)
        paginated_users = filtered_users[skip:skip + page_size]
        
        roles = {r["role_id"]: r["name"] for r in storage.get_all_roles()}
        
        items = [_user_to_response(u, roles.get(u.get("role_id"))) for u in paginated_users]
        
        return UserListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )
    finally:
        storage.close()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: AuthenticatedUser = Depends(require_permission("user:manage")),
):
    """创建用户"""
    storage = get_storage()
    try:
        storage.connect()
        
        existing = storage.get_user_by_username(user_data.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在",
            )
        
        role = storage.get_role_by_id(user_data.role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色不存在",
            )
        
        now = datetime.now()
        new_user = {
            "username": user_data.username,
            "password_hash": hash_password(user_data.password),
            "display_name": user_data.display_name,
            "role_id": user_data.role_id,
            "email": user_data.email,
            "phone": user_data.phone,
            "status": user_data.status.value,
            "is_superuser": False,
            "login_count": 0,
            "created_at": now,
            "updated_at": now,
            "created_by": current_user.user_id,
        }
        
        user_id = storage.save_user(new_user)
        logger.info(f"User {current_user.username} created user {user_data.username}")
        
        return _user_to_response({**new_user, "_id": user_id}, role["name"])
    finally:
        storage.close()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("user:view")),
):
    """获取用户详情"""
    storage = get_storage()
    try:
        storage.connect()
        
        user_data = storage.get_user_by_id(user_id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
        
        role = storage.get_role_by_id(user_data.get("role_id")) if user_data.get("role_id") else None
        role_name = role.get("name") if role else None
        
        return _user_to_response(user_data, role_name)
    finally:
        storage.close()


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: AuthenticatedUser = Depends(require_permission("user:edit")),
):
    """更新用户"""
    storage = get_storage()
    try:
        storage.connect()
        
        existing = storage.get_user_by_id(user_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
        
        if existing.get("is_superuser") and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改超级管理员",
            )
        
        update_data = {}
        if user_data.display_name is not None:
            update_data["display_name"] = user_data.display_name
        if user_data.role_id is not None:
            role = storage.get_role_by_id(user_data.role_id)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="角色不存在",
                )
            update_data["role_id"] = user_data.role_id
        if user_data.email is not None:
            update_data["email"] = user_data.email
        if user_data.phone is not None:
            update_data["phone"] = user_data.phone
        if user_data.status is not None:
            update_data["status"] = user_data.status.value
        
        if update_data:
            storage.update_user(user_id, update_data)
            logger.info(f"User {current_user.username} updated user {user_id}")
        
        updated_user = storage.get_user_by_id(user_id)
        role = storage.get_role_by_id(updated_user.get("role_id")) if updated_user.get("role_id") else None
        role_name = role.get("name") if role else None
        
        return _user_to_response(updated_user, role_name)
    finally:
        storage.close()


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("user:delete")),
):
    """删除用户"""
    storage = get_storage()
    try:
        storage.connect()
        
        existing = storage.get_user_by_id(user_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
        
        if existing.get("is_superuser"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不能删除超级管理员",
            )
        
        if existing.get("username") == current_user.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除自己",
            )
        
        storage.delete_user(user_id)
        logger.info(f"User {current_user.username} deleted user {existing['username']}")
    finally:
        storage.close()


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("user:manage")),
):
    """重置用户密码"""
    storage = get_storage()
    try:
        storage.connect()
        
        existing = storage.get_user_by_id(user_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
        
        if existing.get("is_superuser") and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权重置超级管理员密码",
            )
        
        default_password = settings.default_user_password
        new_password_hash = hash_password(default_password)
        storage.update_user(user_id, {"password_hash": new_password_hash})
        
        logger.info(f"User {current_user.username} reset password for user {existing['username']}")
        
        return {"message": "密码已重置为默认密码", "default_password": default_password}
    finally:
        storage.close()


@router.post("/{user_id}/unlock")
async def unlock_user(
    user_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("user:edit")),
):
    """解锁用户"""
    storage = get_storage()
    try:
        storage.connect()

        existing = storage.get_user_by_id(user_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )

        if existing.get("status") != "locked":
            return {"message": "用户未锁定，无需解锁"}

        storage.update_user(user_id, {"status": "active"})
        logger.info(f"User {current_user.username} unlocked user {existing['username']}")

        return {"message": "用户已解锁"}
    finally:
        storage.close()
