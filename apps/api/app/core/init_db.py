import logging
from datetime import datetime
from typing import Optional

from app.core.config import settings
from app.core.permissions import DEFAULT_ROLES
from app.storage import MongoStorage
from app.user.password import hash_password

logger = logging.getLogger(__name__)


async def create_default_roles(storage: MongoStorage) -> int:
    created_count = 0
    for role_data in DEFAULT_ROLES:
        existing = storage.get_role_by_id(role_data["role_id"])
        if existing is None:
            role_data["created_at"] = datetime.now()
            role_data["updated_at"] = datetime.now()
            storage.save_role(role_data)
            created_count += 1
            logger.info(f"Created default role: {role_data['role_id']}")
        else:
            logger.debug(f"Role already exists: {role_data['role_id']}")
    return created_count


async def create_default_admin(storage: MongoStorage) -> Optional[str]:
    admin_username = settings.default_admin_username
    existing = storage.get_user_by_username(admin_username)
    if existing is not None:
        logger.info(f"Default admin user already exists: {admin_username}")
        return None

    admin_user = {
        "username": admin_username,
        "password_hash": hash_password(settings.default_admin_password),
        "display_name": "系统管理员",
        "role_id": "role_superuser",
        "is_superuser": True,
        "status": "active",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "login_count": 0,
    }

    user_id = storage.save_user(admin_user)
    logger.info(f"Created default admin user: {admin_username}")
    return user_id


async def init_database() -> bool:
    storage = MongoStorage(
        host=settings.mongodb_host,
        port=settings.mongodb_port,
        db_name=settings.mongodb_database,
        username=settings.mongodb_username,
        password=settings.mongodb_password,
    )

    try:
        storage.connect()
        user_count = len(storage.get_all_users(limit=1))
        if user_count > 0:
            logger.info("Users already exist, skipping initialization")
            return False

        logger.info("Initializing database with default roles and admin user...")
        roles_created = await create_default_roles(storage)
        logger.info(f"Created {roles_created} default roles")

        admin_created = await create_default_admin(storage)
        if admin_created:
            logger.info(f"Default admin user created with ID: {admin_created}")
        else:
            logger.info("Default admin user already exists or was not created")

        logger.info("Database initialization completed")
        return True

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        storage.close()
