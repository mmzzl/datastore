import base64
import hashlib
import logging
from cryptography.fernet import Fernet
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_encryption_key() -> bytes:
    key = hashlib.sha256(settings.jwt_secret_key.encode()).digest()
    return base64.urlsafe_b64encode(key)


def encrypt_value(value: str) -> str:
    if not value:
        return value
    f = Fernet(get_encryption_key())
    return f.encrypt(value.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    if not encrypted:
        return encrypted
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted.encode()).decode()


def mask_value(value: str, show_last: int = 8) -> str:
    if not value:
        return ""
    if len(value) <= show_last:
        return "*" * len(value)
    return "*" * (len(value) - show_last) + value[-show_last:]
