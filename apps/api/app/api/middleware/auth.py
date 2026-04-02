from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import security
from app.core.config import settings
from typing import Optional

class CustomHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未提供认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )

        parts = auth_header.split()
        if len(parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="认证凭据格式错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        scheme, token = parts
        if scheme.lower() not in ["bearer", "beare"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="认证方案错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

security_scheme = CustomHTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    """获取当前用户"""
    token = credentials.credentials
    payload = security.verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
    """获取当前用户（可选）"""
    if credentials is None:
        return None
    
    token = credentials.credentials
    payload = security.verify_token(token)
    
    if payload is None:
        return None
    
    return payload
