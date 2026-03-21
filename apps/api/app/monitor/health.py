import logging
from fastapi import APIRouter, Depends

from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health(current_user: str = Depends(get_current_user)):
    return {"status": "ok", "user": current_user}
