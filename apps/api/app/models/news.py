from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class NewsModel(BaseModel):
    """新闻数据模型"""
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
        arbitrary_types_allowed = True
