from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import logging

from ..storage import MongoStorage
from ..scheduler import AfterMarketJob
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def get_storage() -> MongoStorage:
    db_config = settings.database
    storage = MongoStorage(
        db_config.get("host", "localhost"),
        db_config.get("port", 27017),
        db_config.get("name", "after_market")
    )
    storage.connect()
    try:
        yield storage
    finally:
        storage.close()


@router.get("/after-market")
def get_after_market_list(
    limit: int = 50,
    storage: MongoStorage = Depends(get_storage)
):
    """获取盘后信息列表"""
    try:
        return storage.get_all(limit)
    except Exception as e:
        logger.error(f"Failed to get list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/after-market/{date}")
def get_after_market_by_date(
    date: str,
    storage: MongoStorage = Depends(get_storage)
):
    """根据日期获取盘后信息"""
    try:
        data = storage.get_by_date(date)
        if not data:
            raise HTTPException(status_code=404, detail="Not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get by date: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/after-market/{date}")
def delete_after_market(
    date: str,
    storage: MongoStorage = Depends(get_storage)
):
    """删除盘后信息"""
    try:
        count = storage.delete(date)
        if count == 0:
            raise HTTPException(status_code=404, detail="Not found")
        return {"deleted": count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/after-market/trigger")
def trigger_job(date: Optional[str] = None):
    """手动触发采集任务"""
    try:
        config = {
            "database": settings.database,
            "news_api": settings.news_api,
            "dingtalk": settings.dingtalk,
        }
        job = AfterMarketJob(config)
        result = job.run(date)
        return {"result": result, "success": True}
    except Exception as e:
        logger.error(f"Job failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
