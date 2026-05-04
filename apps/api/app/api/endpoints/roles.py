import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status, Depends, Query

from app.core.auth import (
    get_current_user,
    require_permission,
    AuthenticatedUser,
)
from app.core.permissions import ALL_PERMISSIONS
from app.schemas.user import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleListResponse,
    PermissionResponse,
)
from app.storage import get_async_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/roles", tags=["roles"])


def _parse_datetime(value: Any) -> datetime:
    if value is None:
        return datetime.now()
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return datetime.now()


def _role_to_response(role_data: dict) -> RoleResponse:
    return RoleResponse(
        id=str(role_data["_id"]),
        role_id=role_data["role_id"],
        name=role_data["name"],
        description=role_data["description"],
        permissions=role_data.get("permissions", []),
        is_system=role_data.get("is_system", False),
        created_at=_parse_datetime(role_data.get("created_at")),
        updated_at=_parse_datetime(role_data.get("updated_at")),
    )


@router.get("", response_model=RoleListResponse)
async def list_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(require_permission("role:view")),
):
    """获取角色列表"""
    storage = await get_async_storage()

    roles = await storage.get_all_roles()
    skip = (page - 1) * page_size
    total = len(roles)
    paginated_roles = roles[skip : skip + page_size]
    items = [_role_to_response(r) for r in paginated_roles]

    return RoleListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/permissions", response_model=PermissionResponse)
async def list_permissions(
    current_user: AuthenticatedUser = Depends(require_permission("role:view")),
):
    """获取所有可用权限"""
    return PermissionResponse(permissions=ALL_PERMISSIONS)


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: AuthenticatedUser = Depends(require_permission("role:manage")),
):
    """创建角色"""
    storage = await get_async_storage()

    existing = await storage.get_role_by_id(role_data.role_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色ID已存在",
        )

    for perm in role_data.permissions:
        if perm != "*" and not any(
            perm == p or perm.startswith(p.split(":")[0] + ":*")
            for p in ALL_PERMISSIONS
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的权限: {perm}",
            )

    now = datetime.now()
    new_role = {
        "role_id": role_data.role_id,
        "name": role_data.name,
        "description": role_data.description,
        "permissions": role_data.permissions,
        "is_system": False,
        "created_at": now,
        "updated_at": now,
    }

    role_id = await storage.save_role(new_role)
    logger.info(f"User {current_user.username} created role {role_data.role_id}")

    return _role_to_response({**new_role, "_id": role_id})


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("role:view")),
):
    """获取角色详情"""
    storage = await get_async_storage()

    role_data = await storage.get_role_by_id(role_id)
    if not role_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在",
        )

    return _role_to_response(role_data)


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    current_user: AuthenticatedUser = Depends(require_permission("role:edit")),
):
    """更新角色"""
    storage = await get_async_storage()

    existing = await storage.get_role_by_id(role_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在",
        )

    if existing.get("is_system"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="系统内置角色不能修改",
        )

    update_data = {}
    if role_data.name is not None:
        update_data["name"] = role_data.name
    if role_data.description is not None:
        update_data["description"] = role_data.description
    if role_data.permissions is not None:
        update_data["permissions"] = role_data.permissions

    if update_data:
        await storage.update_role(role_id, update_data)
        logger.info(f"User {current_user.username} updated role {role_id}")

    updated_role = await storage.get_role_by_id(role_id)
    return _role_to_response(updated_role)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("role:delete")),
):
    """删除角色"""
    storage = await get_async_storage()

    existing = await storage.get_role_by_id(role_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在",
        )

    if existing.get("is_system"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="系统内置角色不能删除",
        )

    all_users = await storage.get_all_users(limit=10000)
    users_with_role = [u for u in all_users if u.get("role_id") == role_id]
    if users_with_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"角色正在被 {len(users_with_role)} 个用户使用，无法删除",
        )

    await storage.delete_role(role_id)
    logger.info(f"User {current_user.username} deleted role {role_id}")
