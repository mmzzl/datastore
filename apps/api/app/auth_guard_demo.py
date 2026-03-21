import logging
from fastapi import APIRouter, Depends

from case.apps.api.app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/guard_demo")
def guard_demo(current_user: str = Depends(get_current_user)):
    return {"user": current_user, "ok": True}
