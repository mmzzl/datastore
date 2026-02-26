from typing import List, Optional
from pydantic import BaseModel

class NewsResponse(BaseModel):
    """新闻响应模型"""
    _id: Optional[str] = None
    code: str
    title: str
    summary: str
    showTime: str
    stockList: List[str]
    image: List[str]
    pinglun_Num: int
    share: int
    realSort: str
    titleColor: int
    crawlTime: str
    
    class Config:
        from_attributes = True

class NewsListResponse(BaseModel):
    """新闻列表响应模型"""
    total: int
    items: List[NewsResponse]

class NewsQuery(BaseModel):
    """新闻查询参数"""
    date: Optional[str] = None
    limit: int = 10
    offset: int = 0
