import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.data_source import DataSourceManager
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()
_data_manager = DataSourceManager()


class SettingsInput(BaseModel):
    watchlist: Optional[List[str]] = None
    interval_sec: Optional[int] = None
    days: Optional[int] = None
    cache_ttl: Optional[int] = None


@router.get("/settings/{user_id}")
def get_settings(user_id: str, current_user: str = Depends(get_current_user)):
    if current_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此设置"
        )
    return _data_manager.get_settings(user_id)


@router.post("/settings/{user_id}")
def set_settings(
    user_id: str, settings: SettingsInput, current_user: str = Depends(get_current_user)
):
    if current_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此设置"
        )
    _data_manager.set_settings(user_id, settings.dict(exclude_none=True))
    return {"ok": True}
