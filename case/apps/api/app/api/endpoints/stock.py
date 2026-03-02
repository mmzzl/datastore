from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import logging

from ...storage import MongoStorage
from ...core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stock", tags=["股票数据"])


def get_storage() -> MongoStorage:
    storage = MongoStorage(
        settings.mongodb_host,
        settings.mongodb_port,
        settings.mongodb_database,
        settings.mongodb_username,
        settings.mongodb_password
    )
    storage.connect()
    try:
        yield storage
    finally:
        storage.close()


@router.get("/kline/{code}")
def get_stock_kline(
    code: str,
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=5000, description="返回数量"),
    storage: MongoStorage = Depends(get_storage)
):
    """获取股票K线数据"""
    try:
        results = storage.get_kline(code, start_date, end_date, limit)
        return {
            "code": code,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kline/all/{date}")
def get_all_stocks_kline(
    date: str,
    limit: int = Query(5000, ge=1, le=10000, description="返回数量"),
    storage: MongoStorage = Depends(get_storage)
):
    """获取指定日期所有股票的K线数据"""
    try:
        results = storage.get_all_kline_by_date(date, limit)
        return {
            "date": date,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        logger.error(f"获取全部K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kline/{code}/{date}")
def get_stock_kline_by_date(
    code: str,
    date: str,
    storage: MongoStorage = Depends(get_storage)
):
    """获取指定日期的股票K线数据"""
    try:
        result = storage.get_kline_by_date(code, date)
        if not result:
            raise HTTPException(status_code=404, detail="数据不存在")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
