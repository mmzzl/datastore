import time
import hmac
import hashlib
import base64
from typing import Optional

SECRET_KEY = "dev-secret-please-change-when-prod"


def create_token(username: str, expire_seconds: int = 3600) -> str:
    ts = int(time.time()) + expire_seconds
    msg = f"{username}:{ts}"
    sig = hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(f"{username}:{ts}:{sig}".encode()).decode()
    return token


def verify_token(token: str) -> Optional[str]:
    try:
        payload = base64.urlsafe_b64decode(token.encode()).decode()
        user_id, ts, sig = payload.split(":", 2)
        if int(ts) < int(time.time()):
            return None
        expected = hmac.new(
            SECRET_KEY.encode(), f"{user_id}:{ts}".encode(), hashlib.sha256
        ).hexdigest()
        if sig != expected:
            return None
        return user_id
    except Exception:
        return None


from fastapi import Header, HTTPException, status
from app.core.security import security


def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供认证信息"
        )
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证头"
        )
    token = authorization.split(" ", 1)[1]
    # Try custom token first
    user = verify_token(token)
    if user:
        return user
    # Try JWT token
    payload = security.verify_token(token)
    if payload:
        sub = payload.get("sub")
        if sub:
            return sub
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效令牌")
