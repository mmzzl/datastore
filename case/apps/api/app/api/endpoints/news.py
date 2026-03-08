from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime, timedelta
from app.core.database import mongodb
from app.api.middleware.auth import get_current_user
from app.schemas.news import NewsResponse, NewsListResponse
import logging

router = APIRouter(prefix="/api/news", tags=["news"])
logger = logging.getLogger(__name__)

def get_date_range(period: str, date_str: Optional[str] = None):
    """获取日期范围"""
    if date_str:
        base_date = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        base_date = datetime.now()
    
    if period == "daily":
        start_date = base_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif period == "weekly":
        # 计算本周一
        start_date = base_date - timedelta(days=base_date.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)
    elif period == "monthly":
        # 计算本月第一天
        start_date = base_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # 计算下个月第一天
        if base_date.month == 12:
            end_date = start_date.replace(year=base_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=base_date.month + 1)
    else:
        raise ValueError(f"Invalid period: {period}")
    
    return start_date, end_date

def format_date_for_mongo(dt):
    """格式化日期为MongoDB查询格式"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

@router.get("/daily", response_model=NewsListResponse)
def get_daily_news(
    date: Optional[str] = Query(None, description="查询日期，格式：YYYY-MM-DD"),
    limit: int = Query(10, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="分页偏移量"),
    current_user = Depends(get_current_user)
):
    """查询当日新闻"""
    try:
        start_date, end_date = get_date_range("daily", date)
        collection = mongodb.get_collection()
        
        # 构建查询条件
        query = {
            "showTime": {
                "$gte": format_date_for_mongo(start_date),
                "$lt": format_date_for_mongo(end_date)
            }
        }
        
        # 查询总数
        total = collection.count_documents(query)
        
        # 查询数据
        news_list = list(collection.find(query).skip(offset).limit(limit).sort("showTime", -1))
        
        # 转换为响应模型
        items = []
        for news in news_list:
            news_dict = {
                "_id": str(news.get("_id")),
                "code": news.get("code"),
                "title": news.get("title"),
                "summary": news.get("summary"),
                "showTime": news.get("showTime"),
                "stockList": news.get("stockList", []),
                "image": news.get("image", []),
                "pinglun_Num": news.get("pinglun_Num", 0),
                "share": news.get("share", 0),
                "realSort": news.get("realSort"),
                "titleColor": news.get("titleColor", 0),
                "crawlTime": news.get("crawlTime")
            }
            items.append(NewsResponse(**news_dict))
        
        return NewsListResponse(total=total, items=items)
    except Exception as e:
        logger.error(f"查询当日新闻失败: {e}")
        raise

@router.get("/weekly", response_model=NewsListResponse)
def get_weekly_news(
    date: Optional[str] = Query(None, description="查询日期，格式：YYYY-MM-DD"),
    limit: int = Query(10, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="分页偏移量"),
    current_user = Depends(get_current_user)
):
    """查询本周新闻"""
    try:
        start_date, end_date = get_date_range("weekly", date)
        collection = mongodb.get_collection()
        
        # 构建查询条件
        query = {
            "showTime": {
                "$gte": format_date_for_mongo(start_date),
                "$lt": format_date_for_mongo(end_date)
            }
        }
        
        # 查询总数
        total = collection.count_documents(query)
        
        # 查询数据
        news_list = list(collection.find(query).skip(offset).limit(limit).sort("showTime", -1))
        
        # 转换为响应模型
        items = []
        for news in news_list:
            news_dict = {
                "_id": str(news.get("_id")),
                "code": news.get("code"),
                "title": news.get("title"),
                "summary": news.get("summary"),
                "showTime": news.get("showTime"),
                "stockList": news.get("stockList", []),
                "image": news.get("image", []),
                "pinglun_Num": news.get("pinglun_Num", 0),
                "share": news.get("share", 0),
                "realSort": news.get("realSort"),
                "titleColor": news.get("titleColor", 0),
                "crawlTime": news.get("crawlTime")
            }
            items.append(NewsResponse(**news_dict))
        
        return NewsListResponse(total=total, items=items)
    except Exception as e:
        logger.error(f"查询本周新闻失败: {e}")
        raise

@router.get("/monthly", response_model=NewsListResponse)
def get_monthly_news(
    date: Optional[str] = Query(None, description="查询日期，格式：YYYY-MM-DD"),
    limit: int = Query(10, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="分页偏移量"),
    current_user = Depends(get_current_user)
):
    """查询本月新闻"""
    try:
        start_date, end_date = get_date_range("monthly", date)
        collection = mongodb.get_collection()
        
        # 构建查询条件
        query = {
            "showTime": {
                "$gte": format_date_for_mongo(start_date),
                "$lt": format_date_for_mongo(end_date)
            }
        }
        
        # 查询总数
        total = collection.count_documents(query)
        
        # 查询数据
        news_list = list(collection.find(query).skip(offset).limit(limit).sort("showTime", -1))
        
        # 转换为响应模型
        items = []
        for news in news_list:
            news_dict = {
                "_id": str(news.get("_id")),
                "code": news.get("code"),
                "title": news.get("title"),
                "summary": news.get("summary"),
                "showTime": news.get("showTime"),
                "stockList": news.get("stockList", []),
                "image": news.get("image", []),
                "pinglun_Num": news.get("pinglun_Num", 0),
                "share": news.get("share", 0),
                "realSort": news.get("realSort"),
                "titleColor": news.get("titleColor", 0),
                "crawlTime": news.get("crawlTime")
            }
            items.append(NewsResponse(**news_dict))
        
        return NewsListResponse(total=total, items=items)
    except Exception as e:
        logger.error(f"查询本月新闻失败: {e}")
        raise
