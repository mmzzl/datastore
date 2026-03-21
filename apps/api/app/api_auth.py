import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.core.config import settings
import hashlib
from app.auth import create_token, verify_token

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginInput(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(user: LoginInput):
    # 简单示例：将固定密码校验逻辑作为演示；实际应接入用户数据库校验
    passwd = f"{user.password}sangfornetwork" 
    password = str(hashlib.sha1(passwd.encode("utf-8")).hexdigest())
    if (
        password != settings.auth_password
        or user.username != settings.auth_username
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的用户名或密码"
        )
    token = create_token(user.username)
    return {"token": token}
