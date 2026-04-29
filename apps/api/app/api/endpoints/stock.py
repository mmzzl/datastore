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
from ...storage.mongo_client import get_storage
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
    def validate_date_range(
        start_date: Optional[str], end_date: Optional[str]
    ) -> tuple:
        """验证日期范围"""
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")
                if start > end:
                    raise HTTPException(
                        status_code=400, detail="开始日期不能晚于结束日期"
                    )
                return start_date, end_date
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD 格式"
                )
        return start_date, end_date

    @staticmethod
    def validate_limit(limit: Optional[int]) -> int:
        """验证limit参数"""
        if limit is None:
            return QueryConfig.MAX_SINGLE_QUERY_RECORDS

        if limit < 1:
            raise HTTPException(
                status_code=400, detail=f"limit必须大于0，当前值: {limit}"
            )

        if limit > QueryConfig.MAX_SINGLE_QUERY_RECORDS:
            logger.warning(
                f"请求的limit {limit} 超过最大值 {QueryConfig.MAX_SINGLE_QUERY_RECORDS}，将使用最大值"
            )
            return QueryConfig.MAX_SINGLE_QUERY_RECORDS

        return limit

    @staticmethod
    def validate_export_limit(count: int) -> None:
        """验证导出数据量"""
        if count > QueryConfig.MAX_EXPORT_RECORDS:
            raise HTTPException(
                status_code=400,
                detail=f"导出数据量 {count} 超过最大限制 {QueryConfig.MAX_EXPORT_RECORDS}，请缩小查询范围或使用分页查询",
            )


class ResponseBuilder:
    """响应构建器"""

    @staticmethod
    def build_success_response(
        data: List[Dict], total: int, params: Dict = None
    ) -> Dict:
        """构建成功响应"""
        response = {"success": True, "count": len(data), "total": total, "data": data}

        if params:
            response["params"] = params

        return response

    @staticmethod
    def build_paginated_response(
        data: List[Dict], total: int, pagination: PaginationParams, params: Dict = None
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
            "data": data,
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
            "timestamp": datetime.now().isoformat(),
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

        filename = (
            filename or f"stock_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8-sig")),
            media_type="text/csv; charset=utf-8-sig",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @staticmethod
    def export_to_json(data: List[Dict], filename: str = None) -> StreamingResponse:
        """导出为JSON格式"""
        if not data:
            raise HTTPException(status_code=404, detail="没有数据可导出")

        output = io.StringIO()
        json.dump(data, output, ensure_ascii=False, indent=2)
        output.seek(0)

        filename = (
            filename or f"stock_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @staticmethod
    def export_to_excel(data: List[Dict], filename: str = None) -> StreamingResponse:
        """导出为Excel格式"""
        if not data:
            raise HTTPException(status_code=404, detail="没有数据可导出")

        df = pd.DataFrame(data)
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="股票数据")

        output.seek(0)

        filename = (
            filename or f"stock_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )


def parse_pagination_params(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(
        QueryConfig.DEFAULT_PAGE_SIZE,
        ge=1,
        le=QueryConfig.MAX_PAGE_SIZE,
        description="每页数量",
    ),
) -> PaginationParams:
    """解析分页参数"""
    return PaginationParams(page=page, page_size=page_size)


@router.get("/kline/{code}")
def get_stock_kline(
    code: str,
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(
        100, ge=1, le=QueryConfig.MAX_SINGLE_QUERY_RECORDS, description="返回数量"
    ),
    storage: MongoStorage = Depends(get_storage),
):
    """
    获取股票K线数据

    参数:
    code: 股票代码 (支持带前缀如 SH600000 或纯代码 600000)
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

        # 处理代码，去掉前缀
        pure_code = code.split("SZ")[-1].split("SH")[-1].split("sz")[-1].split("sh")[-1]

        # 查询数据
        results = storage.get_kline(pure_code, start_date, end_date, limit)

        logger.info(f"获取股票 {code} K线数据: {len(results)} 条记录")

        return ResponseBuilder.build_success_response(
            data=results,
            total=len(results),
            params={
                "code": code,
                "pure_code": pure_code,
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit,
            },
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
    storage: MongoStorage = Depends(get_storage),
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
            code, start_date, end_date, limit=pagination.page_size, skip=pagination.skip
        )

        # 获取总数（可能需要额外查询）
        total = len(results)  # 这里简化处理，实际可能需要count查询

        logger.info(
            f"获取股票 {code} K线数据 (分页): 页码={pagination.page}, 每页={pagination.page_size}, 返回={len(results)}条"
        )

        return ResponseBuilder.build_paginated_response(
            data=results,
            total=total,
            pagination=pagination,
            params={"code": code, "start_date": start_date, "end_date": end_date},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分页K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kline/all/{date}")
def get_all_stocks_kline(
    date: str,
    limit: int = Query(
        1000, ge=1, le=QueryConfig.MAX_SINGLE_QUERY_RECORDS, description="返回数量"
    ),
    storage: MongoStorage = Depends(get_storage),
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
            data=results, total=len(results), params={"date": date, "limit": limit}
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
    storage: MongoStorage = Depends(get_storage),
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
            date, limit=pagination.page_size, skip=pagination.skip
        )

        # 获取总数
        total = len(results)  # 这里简化处理，实际可能需要count查询

        logger.info(
            f"获取 {date} 全部股票K线数据 (分页): 页码={pagination.page}, 每页={pagination.page_size}, 返回={len(results)}条"
        )

        return ResponseBuilder.build_paginated_response(
            data=results, total=total, pagination=pagination, params={"date": date}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分页全部K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kline/{code}/{date}")
def get_stock_kline_by_date(
    code: str, date: str, storage: MongoStorage = Depends(get_storage)
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

        return {"success": True, "data": result}

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
    storage: MongoStorage = Depends(get_storage),
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
            return {"success": False, "message": "没有找到数据", "data": []}

        # 转换为 DataFrame 进行统计
        df = pd.DataFrame(results)

        # 转换日期格式
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])

        # 转换数值类型
        numeric_columns = [
            "open",
            "close",
            "high",
            "low",
            "volume",
            "amount",
            "pct_chg",
            "amplitude",
            "turnover",
        ]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # 统计信息
        stats = {
            "total_records": len(df),
            "unique_stocks": df["code"].nunique() if "code" in df.columns else 0,
            "date_range": {
                "start": df["date"].min().strftime("%Y-%m-%d")
                if "date" in df.columns and not df.empty
                else None,
                "end": df["date"].max().strftime("%Y-%m-%d")
                if "date" in df.columns and not df.empty
                else None,
            },
            "columns": list(df.columns),
        }

        logger.info(
            f"获取全部股票K线数据: {len(results)} 条记录, {stats['unique_stocks']} 只股票"
        )

        return {"success": True, "stats": stats, "count": len(results), "data": results}

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
    storage: MongoStorage = Depends(get_storage),
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
            start_date, end_date, limit=pagination.page_size, skip=pagination.skip
        )

        # 获取总数
        total = len(results)  # 这里简化处理，实际可能需要count查询

        logger.info(
            f"获取全部股票K线数据 (分页): 页码={pagination.page}, 每页={pagination.page_size}, 返回={len(results)}条"
        )

        return ResponseBuilder.build_paginated_response(
            data=results,
            total=total,
            pagination=pagination,
            params={"start_date": start_date, "end_date": end_date},
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
    storage: MongoStorage = Depends(get_storage),
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
    storage: MongoStorage = Depends(get_storage),
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
def get_data_stats(storage: MongoStorage = Depends(get_storage)):
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
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


_stock_df_cache: Optional[pd.DataFrame] = None
_stock_df_cache_time: Optional[float] = None
STOCK_LIST_CACHE_TTL = 3600


def _load_stock_list() -> pd.DataFrame:
    global _stock_df_cache, _stock_df_cache_time
    import os

    now = datetime.now().timestamp()
    if _stock_df_cache is not None and _stock_df_cache_time is not None:
        if now - _stock_df_cache_time < STOCK_LIST_CACHE_TTL:
            return _stock_df_cache

    csv_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "data", "all_stock.csv"
    )
    csv_path = os.path.normpath(csv_path)

    if not os.path.exists(csv_path):
        logger.warning(f"Stock list file not found: {csv_path}")
        return pd.DataFrame(
            columns=["code", "pure_code", "name", "market", "type", "status"]
        )

    try:
        df = pd.read_csv(csv_path)

        df["code_raw"] = df["code"].astype(str).str.strip()
        df["name"] = df["code_name"].astype(str).str.strip()
        df["status"] = df["tradeStatus"].fillna(1)

        df["pure_code"] = df["code_raw"].apply(
            lambda x: x.split(".")[-1] if "." in x else x
        )
        df["market"] = df["code_raw"].apply(
            lambda x: x.split(".")[0].upper() if "." in x else ""
        )
        df["code"] = df.apply(
            lambda row: f"{row['market']}{row['pure_code']}"
            if row["market"]
            else row["pure_code"],
            axis=1,
        )

        def get_type(row):
            pure = row["pure_code"]
            index_prefixes = [
                "000001",
                "000002",
                "000003",
                "000004",
                "000005",
                "000006",
                "000007",
                "000008",
                "000009",
                "000010",
                "000011",
                "000012",
                "000013",
                "000015",
                "000016",
                "000300",
                "000852",
                "000905",
                "399001",
                "399006",
            ]
            if any(pure.startswith(p) for p in index_prefixes):
                return "index"
            elif pure.startswith(("5", "15")) and len(pure) == 6:
                return "etf"
            else:
                return "stock"

        df["type"] = df.apply(get_type, axis=1)

        df = df[["code", "pure_code", "name", "market", "type", "status"]]

        _stock_df_cache = df
        _stock_df_cache_time = now

        logger.info(f"Loaded stock list: {len(df)} items")

        return df

    except Exception as e:
        logger.error(f"Failed to load stock list: {e}")
        return pd.DataFrame(
            columns=["code", "pure_code", "name", "market", "type", "status"]
        )


@router.get("/list")
def get_stock_list(
    keyword: Optional[str] = Query(None, description="搜索关键词(代码或名称)"),
    market: Optional[str] = Query(None, description="市场筛选: sh/sz"),
    type: Optional[str] = Query(None, description="类型筛选: stock/index/etf"),
    limit: int = Query(50, ge=1, le=500, description="返回数量限制"),
):
    """
    查询股票/指数/ETF列表

    支持关键词搜索、市场筛选和类型筛选
    """
    try:
        df = _load_stock_list()

        if type and type in ["stock", "index", "etf"]:
            df = df[df["type"] == type]

        if market:
            df = df[df["market"] == market.upper()]

        if keyword:
            keyword_lower = keyword.lower()
            mask = (
                df["code"].str.lower().str.contains(keyword_lower, na=False)
                | df["pure_code"].str.lower().str.contains(keyword_lower, na=False)
                | df["name"].str.lower().str.contains(keyword_lower, na=False)
            )
            df = df[mask]

        total = len(df)
        df = df.head(limit)

        return {
            "success": True,
            "total": total,
            "count": len(df),
            "keyword": keyword,
            "market": market,
            "type": type,
            "data": df.to_dict(orient="records"),
        }

    except Exception as e:
        logger.error(f"查询股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
def search_stock(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
):
    """
    快速搜索股票/指数/ETF

    简化的搜索接口，用于自动补全等场景
    """
    try:
        df = _load_stock_list()

        q_lower = q.lower()

        code_mask = df["pure_code"].str.lower().str.startswith(q_lower)
        code_matches = df[code_mask].copy()

        name_mask = df["name"].str.lower().str.contains(q_lower, na=False)
        name_matches = df[name_mask & ~code_mask].copy()

        results = pd.concat([code_matches, name_matches]).head(limit)

        return {
            "success": True,
            "query": q,
            "count": len(results),
            "data": results.to_dict(orient="records"),
        }

    except Exception as e:
        logger.error(f"搜索股票失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))





_realtime_price_cache: Dict[str, Dict[str, Any]] = {}
_price_cache_time: Optional[float] = None
PRICE_CACHE_TTL = 300


def _get_prev_close_from_db(code: str) -> Optional[float]:
    """从MongoDB获取昨日收盘价"""
    try:
        storage = get_storage()

        pure_code = code.split("SZ")[-1].split("SH")[-1].split("sz")[-1].split("sh")[-1]

        coll = storage.kline_collection
        if coll is None:
            return None

        doc = coll.find_one({"code": {"$regex": pure_code + "$"}}, sort=[("date", -1)])

        if doc and "close" in doc:
            return float(doc["close"])
        return None
    except Exception as e:
        logger.warning(f"从数据库获取收盘价失败: {code}, error: {e}")
        return None


def _fetch_realtime_prices(codes: List[str]) -> Dict[str, Dict[str, Any]]:
    """从腾讯/新浪/通达信获取实时股票价格"""
    import requests

    global _realtime_price_cache, _price_cache_time

    now = datetime.now().timestamp()
    if _price_cache_time is not None and now - _price_cache_time < PRICE_CACHE_TTL:
        return _realtime_price_cache

    if not codes:
        return {}

    result = {}

    # Build code mapping
    code_map = {}
    for code in codes:
        pure_code = code.split("SZ")[-1].split("SH")[-1].split("sz")[-1].split("sh")[-1]
        if code.upper().startswith("SH") or pure_code.startswith("6"):
            tencent_code = f"sh{pure_code}"
        elif code.upper().startswith("SZ") or pure_code.startswith(("0", "3")):
            tencent_code = f"sz{pure_code}"
        else:
            tencent_code = f"sh{pure_code}"
        code_map[tencent_code] = code

        # Try Tencent API first (supports batch query)
        # Use full format (no s_ prefix) to get complete fields
        tencent_codes = list(code_map.keys())
        tencent_url = f"http://qt.gtimg.cn/q={','.join(tencent_codes)}"
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(tencent_url, headers=headers, timeout=10)
            resp.encoding = "gbk"

            if resp.status_code == 200:
                for line in resp.text.strip().split("\n"):
                    if "=" not in line:
                        continue
                    try:
                        var_part, data_part = line.split('="')
                        tencent_code = var_part.replace("v_", "").replace('"', "")
                        data = data_part.rstrip('";').split("~")
                        if len(data) < 35:
                            continue

                        original_code = code_map.get(tencent_code, tencent_code)
                        name = data[1]
                        price = float(data[3]) if data[3] else 0.0
                        prev_close = float(data[4]) if data[4] else 0.0
                        open_price = float(data[5]) if data[5] else 0.0
                        volume = int(float(data[6])) if data[6] else 0
                        high = float(data[33]) if len(data) > 33 and data[33] else 0.0
                        low = float(data[34]) if len(data) > 34 and data[34] else 0.0
                        amount = float(data[37]) * 10000 if len(data) > 37 and data[37] else 0.0
                        change_pct = float(data[32]) if len(data) > 32 and data[32] else (round((price - prev_close) / prev_close * 100, 2) if prev_close > 0 else 0.0)
                        change = round(price - prev_close, 2) if prev_close > 0 else 0.0

                        if price > 0:
                            result[original_code] = {
                                "code": original_code,
                                "name": name,
                                "price": price,
                                "open": open_price,
                                "high": high,
                                "low": low,
                                "prev_close": prev_close,
                                "volume": volume,
                                "amount": amount,
                                "change": round(change, 2),
                                "change_pct": round(change_pct, 2),
                                "time": datetime.now().isoformat(),
                                "source": "tencent",
                            }
                    except (ValueError, IndexError) as e:
                        logger.warning(f"解析腾讯数据失败: {line}, error: {e}")
        except Exception as e:
            logger.warning(f"腾讯API请求失败: {e}")

    # Try Sina API for missing codes
    missing_codes = [c for c in codes if c not in result]
    if missing_codes:
        sina_codes = []
        sina_code_map = {}
        for code in missing_codes:
            pure_code = code.split("SZ")[-1].split("SH")[-1].split("sz")[-1].split("sh")[-1]
            if pure_code.startswith("6"):
                sina_code = f"sh{pure_code}"
            elif pure_code.startswith(("0", "3")):
                sina_code = f"sz{pure_code}"
            else:
                sina_code = f"sh{pure_code}"
            sina_codes.append(sina_code)
            sina_code_map[sina_code] = code

        sina_url = f"https://hq.sinajs.cn/list={','.join(sina_codes)}"
        try:
            headers = {
                "Referer": "https://finance.sina.com.cn/",
                "User-Agent": "Mozilla/5.0",
            }
            resp = requests.get(sina_url, headers=headers, timeout=10)
            resp.encoding = "gbk"

            if resp.status_code == 200:
                for line in resp.text.strip().split("\n"):
                    if "=" not in line or '""' in line:
                        continue
                    try:
                        var_part, data_part = line.split('="')
                        sina_code = var_part.split("_")[-1].replace('"', "")
                        data = data_part.rstrip('";').split(",")
                        if len(data) < 32:
                            continue

                        original_code = sina_code_map.get(sina_code, sina_code)
                        price = float(data[3]) if data[3] else 0.0
                        prev_close = float(data[2]) if data[2] else 0.0

                        if price > 0:
                            change = price - prev_close if prev_close > 0 else 0
                            change_pct = (change / prev_close * 100) if prev_close > 0 else 0
                            result[original_code] = {
                                "code": original_code,
                                "name": data[0],
                                "price": price,
                                "open": float(data[1]) if data[1] else 0.0,
                                "high": float(data[4]) if data[4] else 0.0,
                                "low": float(data[5]) if data[5] else 0.0,
                                "prev_close": prev_close,
                                "volume": int(data[8]) if data[8] else 0,
                                "amount": float(data[9]) if data[9] else 0.0,
                                "change": round(change, 2),
                                "change_pct": round(change_pct, 2),
                                "time": datetime.now().isoformat(),
                                "source": "sina",
                            }
                    except (ValueError, IndexError) as e:
                        logger.warning(f"解析新浪数据失败: {line}, error: {e}")
        except Exception as e:
            logger.warning(f"新浪API请求失败: {e}")

    # Try TDX adapter for remaining missing codes
    missing_codes = [c for c in codes if c not in result]
    if missing_codes:
        try:
            from app.data_source.adapters.tdx_adapter import TDXAdapter
            tdx = TDXAdapter()
            for code in missing_codes:
                try:
                    rt_data = tdx.get_realtime_data(code)
                    if rt_data and rt_data.get("price", 0) > 0:
                        result[code] = {
                            "code": code,
                            "name": rt_data.get("name", ""),
                            "price": rt_data["price"],
                            "open": rt_data.get("open", 0),
                            "high": rt_data.get("high", 0),
                            "low": rt_data.get("low", 0),
                            "prev_close": rt_data.get("last_close", rt_data["price"]),
                            "volume": rt_data.get("volume", 0),
                            "amount": rt_data.get("amount", 0),
                            "change": rt_data.get("change", 0),
                            "change_pct": rt_data.get("change_pct", 0),
                            "time": datetime.now().isoformat(),
                            "source": "tdx",
                        }
                except Exception as ex:
                    logger.warning(f"TDX获取 {code} 失败: {ex}")
        except Exception as e:
            logger.warning(f"TDX adapter初始化失败: {e}")

    # Final fallback: MongoDB
    for code in codes:
        if code not in result:
            db_close = _get_prev_close_from_db(code)
            if db_close:
                result[code] = {
                    "code": code,
                    "name": "",
                    "price": db_close,
                    "open": db_close,
                    "high": db_close,
                    "low": db_close,
                    "prev_close": db_close,
                    "volume": 0,
                    "amount": 0,
                    "change": 0,
                    "change_pct": 0,
                    "time": datetime.now().isoformat(),
                    "source": "mongodb",
                }

    _realtime_price_cache = result
    _price_cache_time = now
    return result

    code_map = {}
    sina_codes = []
    for code in codes:
        pure_code = code.split("SZ")[-1].split("SH")[-1].split("sz")[-1].split("sh")[-1]
        if code.upper().startswith("SH") or pure_code.startswith("6"):
            sina_code = f"sh{pure_code}"
        elif code.upper().startswith("SZ") or pure_code.startswith(("0", "3")):
            sina_code = f"sz{pure_code}"
        else:
            sina_code = f"sh{pure_code}"
        sina_codes.append(sina_code)
        code_map[sina_code] = code

    url = f"https://hq.sinajs.cn/list={','.join(sina_codes)}"

    try:
        headers = {
            "Referer": "https://finance.sina.com.cn/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "gbk"

        result = {}
        for line in resp.text.strip().split("\n"):
            if "=" not in line or '""' in line:
                continue
            try:
                var_part, data_part = line.split('="')
                sina_code = var_part.split("_")[-1].replace('"', "")
                data = data_part.rstrip('";').split(",")
                if len(data) < 32:
                    continue

                original_code = code_map.get(sina_code, sina_code)
                price = float(data[3]) if data[3] else 0.0
                prev_close = float(data[2]) if data[2] else 0.0
                open_price = float(data[1]) if data[1] else 0.0
                high = float(data[4]) if data[4] else 0.0
                low = float(data[5]) if data[5] else 0.0
                volume = int(data[8]) if data[8] else 0
                amount = float(data[9]) if data[9] else 0.0

                change = price - prev_close if prev_close > 0 else 0
                change_pct = (change / prev_close * 100) if prev_close > 0 else 0

                result[original_code] = {
                    "code": original_code,
                    "name": data[0],
                    "price": price,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "prev_close": prev_close,
                    "volume": volume,
                    "amount": amount,
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "time": datetime.now().isoformat(),
                }
            except (ValueError, IndexError) as e:
                logger.warning(f"解析股票数据失败: {line}, error: {e}")
                continue

        _realtime_price_cache = result
        _price_cache_time = now
        return result

    except Exception as e:
        logger.error(f"获取实时价格失败: {e}")
        return _realtime_price_cache


@router.get("/realtime")
def get_realtime_prices(
    codes: str = Query(..., description="股票代码列表，逗号分隔"),
):
    """
    获取股票实时价格

    从新浪财经获取实时行情数据

    参数:
    codes: 股票代码列表，逗号分隔，如 600000,000001

    返回:
    实时行情数据
    """
    try:
        code_list = [c.strip() for c in codes.split(",") if c.strip()]
        if not code_list:
            return {"success": True, "data": {}}

        prices = _fetch_realtime_prices(code_list)

        return {
            "success": True,
            "count": len(prices),
            "data": prices,
            "cached": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"获取实时价格失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/realtime/{code}")
def get_realtime_price(code: str):
    """
    获取单只股票实时价格

    参数:
    code: 股票代码

    返回:
    实时行情数据
    """
    try:
        prices = _fetch_realtime_prices([code])

        if code not in prices:
            raise HTTPException(status_code=404, detail=f"未找到股票 {code} 的行情数据")

        return {"success": True, "data": prices[code]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实时价格失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
