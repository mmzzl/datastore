import logging
import hashlib
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, HTTPException, status, Depends

from app.core.config import settings
from app.core.security import security
from app.core.auth import get_current_user, AuthenticatedUser
from app.storage import get_async_storage
from app.schemas.user import (
    TokenRequest,
    TokenResponse,
    ChangePasswordRequest,
    RegisterRequest,
)
from app.user.password import hash_password, verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


async def _create_default_admin(storage) -> str:
    """异步创建默认超级管理员"""
    from app.core.permissions import DEFAULT_ROLES

    # 确保超级管理员角色存在
    superuser_role = None
    for role in DEFAULT_ROLES:
        if role["role_id"] == "role_superuser":
            superuser_role = role
            break

    if superuser_role:
        existing_role = await storage.get_role_by_id("role_superuser")
        if not existing_role:
            superuser_role["created_at"] = datetime.now()
            superuser_role["updated_at"] = datetime.now()
            await storage.save_role(superuser_role)
            logger.info("Created superuser role")

    # 创建超级管理员用户
    admin_user = {
        "username": settings.admin_username,
        "password_hash": hash_password(settings.admin_password),
        "display_name": "超级管理员",
        "role_id": "role_superuser",
        "is_superuser": True,
        "status": "active",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "login_count": 0,
    }

    user_id = await storage.save_user(admin_user)
    logger.info(f"Created default admin user: {settings.admin_username}")
    return user_id


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(request: TokenRequest):
    """获取访问令牌

    支持两种登录方式：
    1. 超级管理员：使用配置文件中的 default_admin_username 和 default_admin_password
    2. 普通用户：使用数据库中的用户信息
    """
    storage = await get_async_storage()
    # 优先检查配置文件中的超级管理员
    if request.username == settings.auth_username:
        passwd = f"{request.password}sangfornetwork"
        password = str(hashlib.sha1(passwd.encode("utf-8")).hexdigest())
        if password != settings.auth_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的用户名或密码"
            )

        # 超级管理员登录
        user_data = await storage.get_user_by_username(request.username)

        if user_data is None:
            # 数据库中不存在，自动创建
            user_id = await _create_default_admin(storage)
            user_data = await storage.get_user_by_username(request.username)
        else:
            # 更新登录时间
            await storage.update_user_login(str(user_data["_id"]))

        role_id = user_data.get("role_id", "role_superuser")
        role_data = await storage.get_role_by_id(role_id) if role_id else None
        permissions: List[str] = role_data.get("permissions", []) if role_data else []
        role_name = role_data.get("name", "") if role_data else ""

        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        access_token = security.create_access_token(
            data={
                "sub": request.username,
                "user_id": str(user_data["_id"]),
                "role_id": role_id,
                "is_superuser": True,
                "permissions": permissions,
            },
            expires_delta=access_token_expires,
        )

        logger.info(f"Superuser {request.username} logged in via config credentials")

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
            is_superuser=True,
        )

    # 普通用户登录
    user_data = await storage.get_user_by_username(request.username)

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
    role_data = await storage.get_role_by_id(role_id) if role_id else None
    permissions: List[str] = role_data.get("permissions", []) if role_data else []
    role_name = role_data.get("name", "") if role_data else ""
    is_superuser = user_data.get("is_superuser", False)

    await storage.update_user_login(str(user_data["_id"]))

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


@router.post("/logout")
async def logout(current_user: AuthenticatedUser = Depends(get_current_user)):
    """登出"""
    logger.info(f"User {current_user.username} logged out")
    return {"message": "登出成功"}


@router.post("/register")
async def register(request: RegisterRequest):
    """用户注册

    注册的普通用户默认使用 'user' 角色，需要管理员激活后才能登录
    """
    storage = await get_async_storage()

    # 检查用户名是否已存在
    existing = await storage.get_user_by_username(request.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    # 检查是否与超级管理员用户名冲突
    if request.username == settings.default_admin_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户名不可使用",
        )

    # 获取默认用户角色
    default_role = await storage.get_role_by_id("role_user")
    if not default_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="系统未初始化，请联系管理员",
        )

    now = datetime.now()
    new_user = {
        "username": request.username,
        "password_hash": hash_password(request.password),
        "display_name": request.display_name,
        "role_id": "role_user",
        "email": request.email,
        "phone": request.phone,
        "is_superuser": False,
        "status": "inactive",  # 新用户需要管理员激活
        "login_count": 0,
        "created_at": now,
        "updated_at": now,
    }

    user_id = await storage.save_user(new_user)
    logger.info(f"New user registered: {request.username}")

    return {
        "message": "注册成功，请等待管理员激活账号",
        "user_id": user_id,
        "username": request.username,
    }


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """修改密码"""
    storage = await get_async_storage()
    user_data = await storage.get_user_by_username(current_user.username)

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
    await storage.update_user(str(user_data["_id"]), {"password_hash": new_password_hash})

    logger.info(f"User {current_user.username} changed password")
    return {"message": "密码修改成功"}


@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: AuthenticatedUser = Depends(get_current_user)):
    """获取当前用户信息"""
    storage = await get_async_storage()
    user_data = await storage.get_user_by_username(current_user.username)

    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    role_data = await storage.get_role_by_id(current_user.role_id) if current_user.role_id else None
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
