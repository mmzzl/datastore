from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging

from ...storage import get_async_storage
from ...scheduler import AfterMarketJob
from ...core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/after-market", tags=["盘后信息"])


@router.get("")
async def get_after_market_list(limit: int = 50):
    """获取盘后信息列表"""
    try:
        storage = await get_async_storage()
        return await storage.get_all(limit)
    except Exception as e:
        logger.error(f"Failed to get list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{date}")
async def get_after_market_by_date(date: str):
    """根据日期获取盘后信息"""
    try:
        storage = await get_async_storage()
        data = await storage.get_by_date(date)
        if not data:
            raise HTTPException(status_code=404, detail="Not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get by date: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{date}")
async def delete_after_market(date: str):
    """删除盘后信息"""
    try:
        storage = await get_async_storage()
        count = await storage.delete(date)
        if count == 0:
            raise HTTPException(status_code=404, detail="Not found")
        return {"deleted": count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger")
def trigger_job(date: Optional[str] = None):
    """手动触发采集任务"""
    try:
        config = {
            "database": {
                "host": settings.mongodb_host,
                "port": settings.mongodb_port,
                "name": settings.mongodb_database,
                "username": settings.mongodb_username,
                "password": settings.mongodb_password,
            },
            "data_source": {
                "provider": settings.data_source,
                "tushare_token": settings.tushare_token,
            },
            "news_api": {
                "base_url": settings.after_market_news_api_url,
                "username": settings.after_market_news_api_username,
                "password": settings.after_market_news_api_password,
            },
            "llm": {
                "provider": settings.llm_provider,
                "api_key": settings.llm_api_key,
                "model": settings.llm_model,
                "base_url": settings.llm_base_url,
            },
            "dingtalk": {
                "webhook_url": settings.after_market_dingtalk_webhook,
                "secret": settings.after_market_dingtalk_secret,
            },
        }
        job = AfterMarketJob(config)
        result = job.run(date)
        return {"result": result, "success": True}
    except Exception as e:
        logger.error(f"Job failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
