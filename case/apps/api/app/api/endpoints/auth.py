from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.core.security import security
from datetime import timedelta
from app.core.config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])

class TokenRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/token", response_model=TokenResponse)
def login_for_access_token(request: TokenRequest):
    """获取访问令牌"""
    # 使用配置文件中的用户名和密码进行验证
    if request.username != settings.auth_username or request.password != settings.auth_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = security.create_access_token(
        data={"sub": request.username}, expires_delta=access_token_expires
    )
    
    return TokenResponse(access_token=access_token)
