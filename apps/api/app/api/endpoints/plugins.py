"""Plugin Management API Endpoints

Provides REST endpoints for uploading, managing, and activating strategy plugins.
"""

import io
import json
import logging
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from app.backtest.plugin.validator import (
    PluginValidator,
    validate_zip_structure,
    validate_manifest_schema,
    validate_code_ast,
    validate_strategy_class,
    check_version_rules,
)
from app.backtest.plugin.loader import PluginLoader
from app.backtest.plugin.registry import PluginRegistry
from app.core.auth import AuthenticatedUser, get_storage, require_permission
from app.core.config import settings
from app.storage import MongoStorage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/plugins", tags=["plugins"])

PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backtest", "strategies", "plugins")
PLUGINS_DIR = os.path.normpath(PLUGINS_DIR)


class PluginParameterSchema(BaseModel):
    type: str
    default: Any
    label: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    options: Optional[List[str]] = None


class PluginManifestSchema(BaseModel):
    name: str
    version: str
    display_name: str
    description: str
    author: str
    strategy_class: str
    min_data_points: int = 1
    tags: List[str] = []
    parameters: Dict[str, PluginParameterSchema] = {}


class PluginResponse(BaseModel):
    id: str
    name: str
    version: str
    display_name: str
    description: str
    author: str
    strategy_class: str
    path: str
    status: str
    min_data_points: int = 1
    tags: List[str] = []
    parameters: Dict[str, Any] = {}
    created_at: str
    updated_at: str


class PluginListResponse(BaseModel):
    items: List[PluginResponse]
    total: int
    page: int
    page_size: int


class PluginUploadResponse(BaseModel):
    id: str
    message: str
    plugin: PluginResponse


def _get_plugin_dir(name: str, version: str = None) -> str:
    """Get plugin directory path."""
    if version:
        return os.path.join(PLUGINS_DIR, f"{name}_{version}")
    return os.path.join(PLUGINS_DIR, name)


def _ensure_plugins_dir() -> None:
    """Ensure plugins directory exists."""
    if not os.path.exists(PLUGINS_DIR):
        os.makedirs(PLUGINS_DIR)
        init_file = os.path.join(PLUGINS_DIR, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write('"""Strategy plugins directory."""\n')


def _extract_and_validate_zip(
    file_content: bytes,
    filename: str,
) -> Dict[str, Any]:
    """Extract and validate uploaded ZIP file.

    Returns:
        Dict with 'valid', 'errors', 'manifest', 'strategy_code', 'extract_dir'

    Raises:
        HTTPException: If validation fails
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "manifest": None,
        "strategy_code": None,
        "extract_dir": None,
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, filename)
        with open(zip_path, "wb") as f:
            f.write(file_content)

        zip_result = validate_zip_structure(zip_path)
        result["errors"].extend(zip_result.errors)
        result["warnings"].extend(zip_result.warnings)

        if not zip_result.valid:
            result["valid"] = False
            return result

        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        manifest_path = None
        strategy_path = None

        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file == "manifest.json":
                    manifest_path = os.path.join(root, file)
                elif file == "strategy.py":
                    strategy_path = os.path.join(root, file)

        if not manifest_path:
            result["errors"].append("manifest.json not found in ZIP")
            result["valid"] = False
            return result

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        manifest_result = validate_manifest_schema(manifest)
        result["errors"].extend(manifest_result.errors)
        result["warnings"].extend(manifest_result.warnings)

        if not manifest_result.valid:
            result["valid"] = False
            return result

        result["manifest"] = manifest

        if strategy_path:
            with open(strategy_path, "r", encoding="utf-8") as f:
                strategy_code = f.read()

            code_result = validate_code_ast(strategy_code)
            result["errors"].extend(code_result.errors)
            result["warnings"].extend(code_result.warnings)

            if not code_result.valid:
                result["valid"] = False
                return result

            strategy_class = manifest.get("strategy_class", "")
            if strategy_class:
                strategy_result = validate_strategy_class(strategy_code, strategy_class)
                result["errors"].extend(strategy_result.errors)
                result["warnings"].extend(strategy_result.warnings)

                if not strategy_result.valid:
                    result["valid"] = False
                    return result

            result["strategy_code"] = strategy_code

        result["extract_dir"] = extract_dir

    return result


def get_registry(storage: MongoStorage) -> PluginRegistry:
    """Get PluginRegistry instance."""
    return PluginRegistry(storage)


@router.post("/upload", response_model=PluginUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_plugin(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(require_permission("plugin:manage")),
):
    """Upload a strategy plugin.

    Uploads a ZIP file containing strategy implementation.

    ZIP structure:
    - manifest.json (required): Plugin metadata
    - strategy.py (required): Strategy implementation
    - __init__.py (optional): Module initialization
    - utils.py (optional): Additional utilities

    Requires permission: plugin:manage
    """
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a ZIP archive",
        )

    file_content = await file.read()

    validation_result = _extract_and_validate_zip(file_content, file.filename)

    if not validation_result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Plugin validation failed",
                "errors": validation_result["errors"],
                "warnings": validation_result["warnings"],
            },
        )

    manifest = validation_result["manifest"]
    name = manifest.get("name")
    version = manifest.get("version")

    storage = get_storage()
    registry = get_registry(storage)

    existing = registry.get_by_name(name)
    if existing:
        existing_versions = registry.get_existing_versions(existing["_id"])
        version_valid, version_msg = check_version_rules(version, existing_versions)
        if not version_valid:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=version_msg,
            )

    _ensure_plugins_dir()

    plugin_dir = _get_plugin_dir(name, version)

    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, file.filename)
        with open(zip_path, "wb") as f:
            f.write(file_content)

        if os.path.exists(plugin_dir):
            shutil.rmtree(plugin_dir)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(plugin_dir)

    plugin_id = registry.register(
        name=name,
        version=version,
        path=plugin_dir,
        manifest=manifest,
    )

    logger.info(
        f"User {current_user.username} uploaded plugin {name} v{version}"
    )

    plugin = registry.get(plugin_id)

    return PluginUploadResponse(
        id=plugin_id,
        message="Plugin uploaded successfully",
        plugin=PluginResponse(
            id=plugin["_id"],
            name=plugin["name"],
            version=plugin["version"],
            display_name=plugin["manifest"].get("display_name", ""),
            description=plugin["manifest"].get("description", ""),
            author=plugin["manifest"].get("author", ""),
            strategy_class=plugin["manifest"].get("strategy_class", ""),
            path=plugin["path"],
            status=plugin["status"],
            min_data_points=plugin["manifest"].get("min_data_points", 1),
            tags=plugin["manifest"].get("tags", []),
            parameters=plugin["manifest"].get("parameters", {}),
            created_at=plugin["created_at"].isoformat()
            if isinstance(plugin.get("created_at"), datetime)
            else plugin.get("created_at", ""),
            updated_at=plugin["updated_at"].isoformat()
            if isinstance(plugin.get("updated_at"), datetime)
            else plugin.get("updated_at", ""),
        ),
    )


@router.get("", response_model=PluginListResponse)
async def list_plugins(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, regex="^(active|inactive)$"),
    current_user: AuthenticatedUser = Depends(require_permission("plugin:view")),
):
    """List all plugins with pagination.

    Requires permission: plugin:view
    """
    storage = get_storage()
    registry = get_registry(storage)

    skip = (page - 1) * page_size
    plugins = registry.list(status=status, skip=skip, limit=page_size)
    total = registry.count(status=status)

    items = []
    for plugin in plugins:
        manifest = plugin.get("manifest", {})
        items.append(
            PluginResponse(
                id=plugin["_id"],
                name=plugin["name"],
                version=plugin["version"],
                display_name=manifest.get("display_name", ""),
                description=manifest.get("description", ""),
                author=manifest.get("author", ""),
                strategy_class=manifest.get("strategy_class", ""),
                path=plugin["path"],
                status=plugin["status"],
                min_data_points=manifest.get("min_data_points", 1),
                tags=manifest.get("tags", []),
                parameters=manifest.get("parameters", {}),
                created_at=plugin["created_at"].isoformat()
                if isinstance(plugin.get("created_at"), datetime)
                else plugin.get("created_at", ""),
                updated_at=plugin["updated_at"].isoformat()
                if isinstance(plugin.get("updated_at"), datetime)
                else plugin.get("updated_at", ""),
            )
        )

    return PluginListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{plugin_id}", response_model=PluginResponse)
async def get_plugin(
    plugin_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("plugin:view")),
):
    """Get a plugin by ID.

    Requires permission: plugin:view
    """
    storage = get_storage()
    registry = get_registry(storage)

    plugin = registry.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plugin not found",
        )

    manifest = plugin.get("manifest", {})

    return PluginResponse(
        id=plugin["_id"],
        name=plugin["name"],
        version=plugin["version"],
        display_name=manifest.get("display_name", ""),
        description=manifest.get("description", ""),
        author=manifest.get("author", ""),
        strategy_class=manifest.get("strategy_class", ""),
        path=plugin["path"],
        status=plugin["status"],
        min_data_points=manifest.get("min_data_points", 1),
        tags=manifest.get("tags", []),
        parameters=manifest.get("parameters", {}),
        created_at=plugin["created_at"].isoformat()
        if isinstance(plugin.get("created_at"), datetime)
        else plugin.get("created_at", ""),
        updated_at=plugin["updated_at"].isoformat()
        if isinstance(plugin.get("updated_at"), datetime)
        else plugin.get("updated_at", ""),
    )


@router.delete("/{plugin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plugin(
    plugin_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("plugin:manage")),
):
    """Delete a plugin.

    Removes plugin from registry and deletes plugin files.

    Requires permission: plugin:manage
    """
    storage = get_storage()
    registry = get_registry(storage)

    plugin = registry.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plugin not found",
        )

    plugin_path = plugin.get("path", "")
    if plugin_path and os.path.exists(plugin_path):
        shutil.rmtree(plugin_path)
        logger.info(f"Deleted plugin files: {plugin_path}")

    registry.unregister(plugin_id)

    logger.info(f"User {current_user.username} deleted plugin {plugin_id}")


@router.post("/{plugin_id}/activate", response_model=PluginResponse)
async def activate_plugin(
    plugin_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("plugin:manage")),
):
    """Activate a plugin.

    Only one version of a plugin can be active at a time.

    Requires permission: plugin:manage
    """
    storage = get_storage()
    registry = get_registry(storage)

    plugin = registry.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plugin not found",
        )

    registry.activate(plugin_id)

    plugin = registry.get(plugin_id)
    manifest = plugin.get("manifest", {})

    logger.info(f"User {current_user.username} activated plugin {plugin_id}")

    return PluginResponse(
        id=plugin["_id"],
        name=plugin["name"],
        version=plugin["version"],
        display_name=manifest.get("display_name", ""),
        description=manifest.get("description", ""),
        author=manifest.get("author", ""),
        strategy_class=manifest.get("strategy_class", ""),
        path=plugin["path"],
        status=plugin["status"],
        min_data_points=manifest.get("min_data_points", 1),
        tags=manifest.get("tags", []),
        parameters=manifest.get("parameters", {}),
        created_at=plugin["created_at"].isoformat()
        if isinstance(plugin.get("created_at"), datetime)
        else plugin.get("created_at", ""),
        updated_at=plugin["updated_at"].isoformat()
        if isinstance(plugin.get("updated_at"), datetime)
        else plugin.get("updated_at", ""),
    )


@router.post("/{plugin_id}/deactivate", response_model=PluginResponse)
async def deactivate_plugin(
    plugin_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("plugin:manage")),
):
    """Deactivate a plugin.

    Requires permission: plugin:manage
    """
    storage = get_storage()
    registry = get_registry(storage)

    plugin = registry.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plugin not found",
        )

    registry.deactivate(plugin_id)

    plugin = registry.get(plugin_id)
    manifest = plugin.get("manifest", {})

    logger.info(f"User {current_user.username} deactivated plugin {plugin_id}")

    return PluginResponse(
        id=plugin["_id"],
        name=plugin["name"],
        version=plugin["version"],
        display_name=manifest.get("display_name", ""),
        description=manifest.get("description", ""),
        author=manifest.get("author", ""),
        strategy_class=manifest.get("strategy_class", ""),
        path=plugin["path"],
        status=plugin["status"],
        min_data_points=manifest.get("min_data_points", 1),
        tags=manifest.get("tags", []),
        parameters=manifest.get("parameters", {}),
        created_at=plugin["created_at"].isoformat()
        if isinstance(plugin.get("created_at"), datetime)
        else plugin.get("created_at", ""),
        updated_at=plugin["updated_at"].isoformat()
        if isinstance(plugin.get("updated_at"), datetime)
        else plugin.get("updated_at", ""),
    )


@router.get("/{plugin_id}/versions")
async def get_plugin_versions(
    plugin_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("plugin:view")),
):
    """Get all versions of a plugin.

    Requires permission: plugin:view
    """
    storage = get_storage()
    registry = get_registry(storage)

    plugin = registry.get(plugin_id)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plugin not found",
        )

    versions = registry.get_versions(plugin_id)

    return {
        "plugin_id": plugin_id,
        "versions": versions,
    }
