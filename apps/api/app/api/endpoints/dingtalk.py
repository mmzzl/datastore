import asyncio
from bson import ObjectId
from cryptography.fernet import InvalidToken
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging

from app.core.config import settings
from app.core.security import security
from app.core.encryption import encrypt_value, decrypt_value, mask_value
from app.storage import MongoStorage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dingtalk/configs", tags=["dingtalk"])


storage = MongoStorage(
    host=settings.mongodb_host,
    port=settings.mongodb_port,
    db_name=settings.mongodb_database,
    username=settings.mongodb_username,
    password=settings.mongodb_password,
)


class DingTalkConfigCreate(BaseModel):
    user_id: str
    name: str
    webhook: str
    secret: Optional[str] = ""


class DingTalkConfigUpdate(BaseModel):
    name: Optional[str] = None
    webhook: Optional[str] = None
    secret: Optional[str] = None


class DingTalkConfigResponse(BaseModel):
    id: str
    user_id: str
    name: str
    webhook_masked: str
    secret_masked: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DingTalkConfigListResponse(BaseModel):
    items: List[DingTalkConfigResponse]
    total: int


class TestNotificationRequest(BaseModel):
    message: str = "Test notification from trading system"


def get_collection():
    if storage.db is None:
        storage.connect()
    return storage.db["dingtalk_configs"]


@router.post("/on_save", response_model=DingTalkConfigResponse)
async def create_config(config: DingTalkConfigCreate):
    collection = get_collection()

    existing = await asyncio.to_thread(
        collection.find_one, {"user_id": config.user_id, "name": config.name}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Config with this name already exists for user")

    now = datetime.now()
    doc = {
        "user_id": config.user_id,
        "name": config.name,
        "webhook": encrypt_value(config.webhook),
        "secret": encrypt_value(config.secret) if config.secret else "",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    result = await asyncio.to_thread(collection.insert_one, doc)
    doc["_id"] = result.inserted_id

    return DingTalkConfigResponse(
        id=str(doc["_id"]),
        user_id=doc["user_id"],
        name=doc["name"],
        webhook_masked=mask_value(config.webhook),
        secret_masked=mask_value(config.secret or ""),
        is_active=doc["is_active"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


def _decrypt_and_build_response(doc: dict) -> DingTalkConfigResponse:
    try:
        webhook = decrypt_value(doc["webhook"])
        secret = decrypt_value(doc["secret"]) if doc.get("secret") else ""
    except (InvalidToken, ValueError, KeyError):
        # Handle case where data is not encrypted or corrupted
        webhook = doc.get("webhook", "")
        secret = doc.get("secret", "")
        logger.warning("Using unencrypted or corrupted data for config %s", doc.get("_id"))

    return DingTalkConfigResponse(
        id=str(doc["_id"]),
        user_id=doc["user_id"],
        name=doc["name"],
        webhook_masked=mask_value(webhook),
        secret_masked=mask_value(secret),
        is_active=doc.get("is_active", True),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


@router.get("/{user_id}", response_model=DingTalkConfigListResponse)
async def list_configs(user_id: str):
    collection = get_collection()

    configs = []
    cursor = await asyncio.to_thread(
        lambda: list(collection.find({"user_id": user_id, "is_active": True}))
    )
    for doc in cursor:
        configs.append(_decrypt_and_build_response(doc))

    return DingTalkConfigListResponse(
        items=configs,
        total=len(configs)
    )


@router.post("/test/{config_id}")
async def test_notification(config_id: str, request: TestNotificationRequest):
    from app.notify.dingtalk import DingTalkNotifier

    collection = get_collection()

    doc = await asyncio.to_thread(collection.find_one, {"_id": ObjectId(config_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Config not found")

    try:
        webhook = decrypt_value(doc["webhook"])
        secret = decrypt_value(doc["secret"]) if doc.get("secret") else ""
    except (InvalidToken, ValueError, KeyError):
        # Handle case where data is not encrypted or corrupted
        webhook = doc.get("webhook", "")
        secret = doc.get("secret", "")
        logger.warning("Using unencrypted or corrupted data for config %s", config_id)

    notifier = DingTalkNotifier(webhook_url=webhook, secret=secret)

    success = await asyncio.to_thread(
        notifier.send, markdown=f"### Test Notification\n\n{request.message}"
    )

    if success:
        return {"status": "success", "message": "Notification sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send notification")


@router.get("/detail/{config_id}", response_model=DingTalkConfigResponse)
async def get_config(config_id: str):
    collection = get_collection()

    doc = await asyncio.to_thread(collection.find_one, {"_id": ObjectId(config_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Config not found")

    return _decrypt_and_build_response(doc)


@router.put("/{config_id}", response_model=DingTalkConfigResponse)
async def update_config(config_id: str, config: DingTalkConfigUpdate):
    collection = get_collection()

    doc = await asyncio.to_thread(collection.find_one, {"_id": ObjectId(config_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Config not found")

    update_data = {"updated_at": datetime.now()}
    if config.name is not None:
        update_data["name"] = config.name
    if config.webhook is not None:
        try:
            update_data["webhook"] = encrypt_value(config.webhook)
        except Exception as e:
            logger.warning("Failed to encrypt webhook: %s, storing as plain text", e)
            update_data["webhook"] = config.webhook
    if config.secret is not None:
        try:
            update_data["secret"] = encrypt_value(config.secret) if config.secret else ""
        except Exception as e:
            logger.warning("Failed to encrypt secret: %s, storing as plain text", e)
            update_data["secret"] = config.secret if config.secret else ""

    await asyncio.to_thread(
        collection.update_one, {"_id": ObjectId(config_id)}, {"$set": update_data}
    )

    updated_doc = await asyncio.to_thread(collection.find_one, {"_id": ObjectId(config_id)})

    return _decrypt_and_build_response(updated_doc)


@router.delete("/{config_id}")
async def delete_config(config_id: str):
    collection = get_collection()

    result = await asyncio.to_thread(collection.delete_one, {"_id": ObjectId(config_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Config not found")

    return {"status": "deleted", "id": config_id}



