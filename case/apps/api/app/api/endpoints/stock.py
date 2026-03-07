from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import logging
import pandas as pd

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


@router.get("/klines")
def get_all_stocks_klines(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: Optional[int] = Query(None, ge=1, description="返回数量限制"),
    storage: MongoStorage = Depends(get_storage)
):
    """获取所有股票的K线数据（用于计算技术指标）"""
    try:
        results = storage.get_all_klines(start_date, end_date, limit)
        
        # 转换为 DataFrame
        if results:
            df = pd.DataFrame(results)
            
            # 转换日期格式
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            
            # 转换数值类型
            numeric_columns = ['open', 'close', 'high', 'low', 'volume', 'amount', 'pct_chg', 'amplitude', 'turnover']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 统计信息
            stats = {
                "total_records": len(df),
                "unique_stocks": df['code'].nunique() if 'code' in df.columns else 0,
                "date_range": {
                    "start": df['date'].min().strftime('%Y-%m-%d') if 'date' in df.columns and not df.empty else None,
                    "end": df['date'].max().strftime('%Y-%m-%d') if 'date' in df.columns and not df.empty else None
                },
                "columns": list(df.columns)
            }
            
            return {
                "success": True,
                "stats": stats,
                "data": df.to_dict('records')
            }
        else:
            return {
                "success": False,
                "message": "没有找到数据",
                "data": []
            }
    except Exception as e:
        logger.error(f"获取全部K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
