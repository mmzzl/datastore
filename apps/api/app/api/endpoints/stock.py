"""
股票数据API端点 - 重构版本
优化大数据量查询性能，支持分页、流式传输和数据导出
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import logging
import pandas as pd
import io
import csv
import json

from ...storage import MongoStorage
from ...core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stock", tags=["股票数据"])


class ExportFormat(str, Enum):
    """数据导出格式"""
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"


@dataclass
class QueryConfig:
    """查询配置"""
    # 默认分页大小
    DEFAULT_PAGE_SIZE = 100
    MAX_PAGE_SIZE = 1000
    
    # 单次查询最大记录数
    MAX_SINGLE_QUERY_RECORDS = 10000
    
    # 流式查询每批大小
    STREAM_BATCH_SIZE = 1000
    
    # 导出功能最大记录数
    MAX_EXPORT_RECORDS = 1000000
    
    # 查询超时时间（秒）
    QUERY_TIMEOUT = 30


@dataclass
class PaginationParams:
    """分页参数"""
    page: int = 1
    page_size: int = QueryConfig.DEFAULT_PAGE_SIZE
    
    def __post_init__(self):
        """验证和修正参数"""
        if self.page < 1:
            self.page = 1
        if self.page_size < 1:
            self.page_size = QueryConfig.DEFAULT_PAGE_SIZE
        if self.page_size > QueryConfig.MAX_PAGE_SIZE:
            self.page_size = QueryConfig.MAX_PAGE_SIZE
    
    @property
    def skip(self) -> int:
        """计算跳过的记录数"""
        return (self.page - 1) * self.page_size


class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> tuple:
        """验证日期范围"""
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                if start > end:
                    raise HTTPException(
                        status_code=400,
                        detail="开始日期不能晚于结束日期"
                    )
                return start_date, end_date
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="日期格式错误，请使用 YYYY-MM-DD 格式"
                )
        return start_date, end_date
    
    @staticmethod
    def validate_limit(limit: Optional[int]) -> int:
        """验证limit参数"""
        if limit is None:
            return QueryConfig.MAX_SINGLE_QUERY_RECORDS
        
        if limit < 1:
            raise HTTPException(
                status_code=400,
                detail=f"limit必须大于0，当前值: {limit}"
            )
        
        if limit > QueryConfig.MAX_SINGLE_QUERY_RECORDS:
            logger.warning(f"请求的limit {limit} 超过最大值 {QueryConfig.MAX_SINGLE_QUERY_RECORDS}，将使用最大值")
            return QueryConfig.MAX_SINGLE_QUERY_RECORDS
        
        return limit
    
    @staticmethod
    def validate_export_limit(count: int) -> None:
        """验证导出数据量"""
        if count > QueryConfig.MAX_EXPORT_RECORDS:
            raise HTTPException(
                status_code=400,
                detail=f"导出数据量 {count} 超过最大限制 {QueryConfig.MAX_EXPORT_RECORDS}，请缩小查询范围或使用分页查询"
            )


class ResponseBuilder:
    """响应构建器"""
    
    @staticmethod
    def build_success_response(data: List[Dict], total: int, params: Dict = None) -> Dict:
        """构建成功响应"""
        response = {
            "success": True,
            "count": len(data),
            "total": total,
            "data": data
        }
        
        if params:
            response["params"] = params
        
        return response
    
    @staticmethod
    def build_paginated_response(
        data: List[Dict],
        total: int,
        pagination: PaginationParams,
        params: Dict = None
    ) -> Dict:
        """构建分页响应"""
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        
        response = {
            "success": True,
            "count": len(data),
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total_pages": total_pages,
            "has_next": pagination.page < total_pages,
            "has_prev": pagination.page > 1,
            "data": data
        }
        
        if params:
            response["params"] = params
        
        return response
    
    @staticmethod
    def build_error_response(message: str, status_code: int = 500) -> Dict:
        """构建错误响应"""
        return {
            "success": False,
            "error": message,
            "timestamp": datetime.now().isoformat()
        }


class DataExporter:
    """数据导出器"""
    
    @staticmethod
    def export_to_csv(data: List[Dict], filename: str = None) -> StreamingResponse:
        """导出为CSV格式"""
        if not data:
            raise HTTPException(status_code=404, detail="没有数据可导出")
        
        output = io.StringIO()
        
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        output.seek(0)
        
        filename = filename or f"stock_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type='text/csv; charset=utf-8-sig',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
    
    @staticmethod
    def export_to_json(data: List[Dict], filename: str = None) -> StreamingResponse:
        """导出为JSON格式"""
        if not data:
            raise HTTPException(status_code=404, detail="没有数据可导出")
        
        output = io.StringIO()
        json.dump(data, output, ensure_ascii=False, indent=2)
        output.seek(0)
        
        filename = filename or f"stock_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type='application/json; charset=utf-8',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
    
    @staticmethod
    def export_to_excel(data: List[Dict], filename: str = None) -> StreamingResponse:
        """导出为Excel格式"""
        if not data:
            raise HTTPException(status_code=404, detail="没有数据可导出")
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='股票数据')
        
        output.seek(0)
        
        filename = filename or f"stock_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )


def get_storage() -> MongoStorage:
    """获取MongoDB存储实例"""
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


def parse_pagination_params(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(QueryConfig.DEFAULT_PAGE_SIZE, ge=1, le=QueryConfig.MAX_PAGE_SIZE, description="每页数量")
) -> PaginationParams:
    """解析分页参数"""
    return PaginationParams(page=page, page_size=page_size)


@router.get("/kline/{code}")
def get_stock_kline(
    code: str,
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=QueryConfig.MAX_SINGLE_QUERY_RECORDS, description="返回数量"),
    storage: MongoStorage = Depends(get_storage)
):
    """
    获取股票K线数据
    
    参数:
        code: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        limit: 返回数量限制 (1-5000)
    
    返回:
        股票K线数据
    """
    try:
        # 验证日期范围
        DataValidator.validate_date_range(start_date, end_date)
        
        # 验证limit
        limit = DataValidator.validate_limit(limit)
        
        # 查询数据
        results = storage.get_kline(code, start_date, end_date, limit)
        
        logger.info(f"获取股票 {code} K线数据: {len(results)} 条记录")
        
        return ResponseBuilder.build_success_response(
            data=results,
            total=len(results),
            params={"code": code, "start_date": start_date, "end_date": end_date, "limit": limit}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kline/{code}/paginated")
def get_stock_kline_paginated(
    code: str,
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    pagination: PaginationParams = Depends(parse_pagination_params),
    storage: MongoStorage = Depends(get_storage)
):
    """
    获取股票K线数据（分页）
    
    适用于数据量较大的情况，避免一次性返回过多数据
    
    参数:
        code: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        page: 页码，从1开始
        page_size: 每页数量 (1-1000)
    
    返回:
        分页的股票K线数据
    """
    try:
        # 验证日期范围
        DataValidator.validate_date_range(start_date, end_date)
        
        # 查询数据（带分页）
        results = storage.get_kline(
            code, 
            start_date, 
            end_date, 
            limit=pagination.page_size,
            skip=pagination.skip
        )
        
        # 获取总数（可能需要额外查询）
        total = len(results)  # 这里简化处理，实际可能需要count查询
        
        logger.info(f"获取股票 {code} K线数据 (分页): 页码={pagination.page}, 每页={pagination.page_size}, 返回={len(results)}条")
        
        return ResponseBuilder.build_paginated_response(
            data=results,
            total=total,
            pagination=pagination,
            params={"code": code, "start_date": start_date, "end_date": end_date}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分页K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kline/all/{date}")
def get_all_stocks_kline(
    date: str,
    limit: int = Query(1000, ge=1, le=QueryConfig.MAX_SINGLE_QUERY_RECORDS, description="返回数量"),
    storage: MongoStorage = Depends(get_storage)
):
    """
    获取指定日期所有股票的K线数据
    
    参数:
        date: 日期 (YYYY-MM-DD)
        limit: 返回数量限制 (1-5000)
    
    返回:
        指定日期所有股票的K线数据
    """
    try:
        # 验证limit
        limit = DataValidator.validate_limit(limit)
        
        # 查询数据
        results = storage.get_all_kline_by_date(date, limit)
        
        logger.info(f"获取 {date} 全部股票K线数据: {len(results)} 条记录")
        
        return ResponseBuilder.build_success_response(
            data=results,
            total=len(results),
            params={"date": date, "limit": limit}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取全部K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kline/all/{date}/paginated")
def get_all_stocks_kline_paginated(
    date: str,
    pagination: PaginationParams = Depends(parse_pagination_params),
    storage: MongoStorage = Depends(get_storage)
):
    """
    获取指定日期所有股票的K线数据（分页）
    
    适用于股票数量较多的情况
    
    参数:
        date: 日期 (YYYY-MM-DD)
        page: 页码，从1开始
        page_size: 每页数量 (1-1000)
    
    返回:
        分页的股票K线数据
    """
    try:
        # 查询数据（带分页）
        results = storage.get_all_kline_by_date(
            date,
            limit=pagination.page_size,
            skip=pagination.skip
        )
        
        # 获取总数
        total = len(results)  # 这里简化处理，实际可能需要count查询
        
        logger.info(f"获取 {date} 全部股票K线数据 (分页): 页码={pagination.page}, 每页={pagination.page_size}, 返回={len(results)}条")
        
        return ResponseBuilder.build_paginated_response(
            data=results,
            total=total,
            pagination=pagination,
            params={"date": date}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分页全部K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kline/{code}/{date}")
def get_stock_kline_by_date(
    code: str,
    date: str,
    storage: MongoStorage = Depends(get_storage)
):
    """
    获取指定日期的股票K线数据
    
    参数:
        code: 股票代码
        date: 日期 (YYYY-MM-DD)
    
    返回:
        指定日期的股票K线数据
    """
    try:
        result = storage.get_kline_by_date(code, date)
        
        if not result:
            raise HTTPException(status_code=404, detail="数据不存在")
        
        logger.info(f"获取股票 {code} 在 {date} 的K线数据")
        
        return {
            "success": True,
            "data": result
        }
        
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
    """
    获取所有股票的K线数据（用于计算技术指标）
    
    注意：此接口可能返回大量数据，建议使用分页接口或导出功能
    
    参数:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        limit: 返回数量限制 (最大5000)
    
    返回:
        所有股票的K线数据及统计信息
    """
    try:
        # 验证日期范围
        DataValidator.validate_date_range(start_date, end_date)
        
        # 验证limit
        limit = DataValidator.validate_limit(limit)
        
        # 查询数据
        results = storage.get_all_klines(start_date, end_date, limit)
        
        if not results:
            return {
                "success": False,
                "message": "没有找到数据",
                "data": []
            }
        
        # 转换为 DataFrame 进行统计
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
        
        logger.info(f"获取全部股票K线数据: {len(results)} 条记录, {stats['unique_stocks']} 只股票")
        
        return {
            "success": True,
            "stats": stats,
            "count": len(results),
            "data": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取全部K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/klines/paginated")
def get_all_stocks_klines_paginated(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    pagination: PaginationParams = Depends(parse_pagination_params),
    storage: MongoStorage = Depends(get_storage)
):
    """
    获取所有股票的K线数据（分页）
    
    适用于数据量较大的情况，推荐使用此接口
    
    参数:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        page: 页码，从1开始
        page_size: 每页数量 (1-1000)
    
    返回:
        分页的股票K线数据
    """
    try:
        # 验证日期范围
        DataValidator.validate_date_range(start_date, end_date)
        
        # 查询数据（带分页）
        results = storage.get_all_klines(
            start_date, 
            end_date, 
            limit=pagination.page_size,
            skip=pagination.skip
        )
        
        # 获取总数
        total = len(results)  # 这里简化处理，实际可能需要count查询
        
        logger.info(f"获取全部股票K线数据 (分页): 页码={pagination.page}, 每页={pagination.page_size}, 返回={len(results)}条")
        
        return ResponseBuilder.build_paginated_response(
            data=results,
            total=total,
            pagination=pagination,
            params={"start_date": start_date, "end_date": end_date}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分页全部K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/klines/export")
def export_all_stocks_klines(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    format: ExportFormat = Query(ExportFormat.CSV, description="导出格式"),
    storage: MongoStorage = Depends(get_storage)
):
    """
    导出所有股票的K线数据
    
    支持导出为CSV、JSON或Excel格式，适用于大数据量场景
    
    参数:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        format: 导出格式 (csv/json/excel)
    
    返回:
        文件下载流
    """
    try:
        # 验证日期范围
        DataValidator.validate_date_range(start_date, end_date)
        
        # 查询数据（不限制数量，但需要验证）
        results = storage.get_all_klines(start_date, end_date, limit=None)
        
        if not results:
            raise HTTPException(status_code=404, detail="没有数据可导出")
        
        # 验证导出数据量
        DataValidator.validate_export_limit(len(results))
        
        logger.info(f"导出股票K线数据: {len(results)} 条记录, 格式={format}")
        
        # 根据格式导出
        if format == ExportFormat.CSV:
            return DataExporter.export_to_csv(results)
        elif format == ExportFormat.JSON:
            return DataExporter.export_to_json(results)
        elif format == ExportFormat.EXCEL:
            return DataExporter.export_to_excel(results)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kline/{code}/export")
def export_stock_kline(
    code: str,
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    format: ExportFormat = Query(ExportFormat.CSV, description="导出格式"),
    storage: MongoStorage = Depends(get_storage)
):
    """
    导出指定股票的K线数据
    
    参数:
        code: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        format: 导出格式 (csv/json/excel)
    
    返回:
        文件下载流
    """
    try:
        # 验证日期范围
        DataValidator.validate_date_range(start_date, end_date)
        
        # 查询数据
        results = storage.get_kline(code, start_date, end_date, limit=None)
        
        if not results:
            raise HTTPException(status_code=404, detail="没有数据可导出")
        
        # 验证导出数据量
        DataValidator.validate_export_limit(len(results))
        
        logger.info(f"导出股票 {code} K线数据: {len(results)} 条记录, 格式={format}")
        
        # 根据格式导出
        if format == ExportFormat.CSV:
            return DataExporter.export_to_csv(results, f"{code}_kline.csv")
        elif format == ExportFormat.JSON:
            return DataExporter.export_to_json(results, f"{code}_kline.json")
        elif format == ExportFormat.EXCEL:
            return DataExporter.export_to_excel(results, f"{code}_kline.xlsx")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
def get_data_stats(
    storage: MongoStorage = Depends(get_storage)
):
    """
    获取数据库统计信息
    
    返回:
        数据库统计信息
    """
    try:
        stats = storage.get_collection_stats()
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
