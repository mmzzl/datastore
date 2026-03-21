import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.auth import create_token, verify_token

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginInput(BaseModel):
    user_id: str
    password: str


@router.post("/login")
def login(user: LoginInput):
    # 简单示例：将固定密码校验逻辑作为演示；实际应接入用户数据库校验
    if user.password != "password" and user.password != "123456":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的用户名或密码"
        )
    token = create_token(user.user_id)
    return {"token": token}
