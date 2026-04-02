import bcrypt
import logging

logger = logging.getLogger(__name__)

BCRYPT_MAX_PASSWORD_LENGTH = 72


class PasswordError(ValueError):
    """Exception raised for password validation errors."""
    pass


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password to hash.

    Returns:
        The hashed password string.

    Raises:
        PasswordError: If password is None or empty.
    """
    if password is None:
        raise PasswordError("Password cannot be None")
    if not password:
        raise PasswordError("Password cannot be empty")
    password_bytes = password.encode()[:BCRYPT_MAX_PASSWORD_LENGTH]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against a bcrypt hash.

    Args:
        password: The plain text password to verify.
        password_hash: The bcrypt hash to compare against.

    Returns:
        True if the password matches the hash, False otherwise.

    Raises:
        PasswordError: If password or password_hash is None or empty.
    """
    if password is None:
        raise PasswordError("Password cannot be None")
    if not password:
        raise PasswordError("Password cannot be empty")
    if password_hash is None:
        raise PasswordError("Password hash cannot be None")
    if not password_hash:
        raise PasswordError("Password hash cannot be empty")
    password_bytes = password.encode()[:BCRYPT_MAX_PASSWORD_LENGTH]
    return bcrypt.checkpw(password_bytes, password_hash.encode())
