import logging
from datetime import timedelta
from typing import List

from fastapi import APIRouter, HTTPException, status, Depends

from app.core.config import settings
from app.core.security import security
from app.core.auth import get_current_user, get_storage, AuthenticatedUser
from app.schemas.user import (
    TokenRequest,
    TokenResponse,
    ChangePasswordRequest,
)
from app.user.password import hash_password, verify_password
from app.storage import MongoStorage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(request: TokenRequest):
    """获取访问令牌"""
    storage = get_storage()
    try:
        storage.connect()
        user_data = storage.get_user_by_username(request.username)
        
        if user_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if user_data.get("status") != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已被禁用",
            )
        
        if not verify_password(request.password, user_data["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        role_id = user_data.get("role_id")
        role_data = storage.get_role_by_id(role_id) if role_id else None
        permissions: List[str] = role_data.get("permissions", []) if role_data else []
        role_name = role_data.get("name", "") if role_data else ""
        is_superuser = user_data.get("is_superuser", False)
        
        storage.update_user_login(str(user_data["_id"]))
        
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        access_token = security.create_access_token(
            data={
                "sub": request.username,
                "user_id": str(user_data["_id"]),
                "role_id": role_id,
                "is_superuser": is_superuser,
                "permissions": permissions,
            },
            expires_delta=access_token_expires,
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user_id=str(user_data["_id"]),
            username=user_data["username"],
            display_name=user_data.get("display_name", ""),
            role_id=role_id or "",
            role_name=role_name,
            permissions=permissions,
            is_superuser=is_superuser,
        )
    finally:
        storage.close()


@router.post("/logout")
async def logout(current_user: AuthenticatedUser = Depends(get_current_user)):
    """登出"""
    logger.info(f"User {current_user.username} logged out")
    return {"message": "登出成功"}


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """修改密码"""
    storage = get_storage()
    try:
        storage.connect()
        user_data = storage.get_user_by_username(current_user.username)
        
        if user_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
        
        if not verify_password(request.old_password, user_data["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="原密码错误",
            )
        
        new_password_hash = hash_password(request.new_password)
        storage.update_user(str(user_data["_id"]), {"password_hash": new_password_hash})
        
        logger.info(f"User {current_user.username} changed password")
        return {"message": "密码修改成功"}
    finally:
        storage.close()


@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: AuthenticatedUser = Depends(get_current_user)):
    """获取当前用户信息"""
    storage = get_storage()
    try:
        storage.connect()
        user_data = storage.get_user_by_username(current_user.username)
        
        if user_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
        
        role_data = storage.get_role_by_id(current_user.role_id) if current_user.role_id else None
        role_name = role_data.get("name", "") if role_data else ""
        
        return {
            "id": current_user.user_id,
            "username": current_user.username,
            "display_name": current_user.display_name,
            "role_id": current_user.role_id,
            "role_name": role_name,
            "permissions": current_user.permissions,
            "is_superuser": current_user.is_superuser,
        }
    finally:
        storage.close()
