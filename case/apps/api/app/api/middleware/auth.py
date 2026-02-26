from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import security

# 自定义HTTPBearer，处理常见的格式错误
class CustomHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request):
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未提供认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 处理常见的格式错误（使用split()会自动处理多个空格）
        parts = auth_header.split()
        if len(parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="认证凭据格式错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        scheme, token = parts
        # 处理大小写和拼写错误
        if scheme.lower() not in ["bearer", "beare"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="认证方案错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 返回标准化的凭据
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
