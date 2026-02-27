from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class IndexData(BaseModel):
    code: str
    name: str
    close: float = 0
    change: float = 0
    pct_chg: float = 0
    volume: float = 0


class MarketOverview(BaseModel):
    date: str
    indices: List[IndexData] = []
    up_count: int = 0
    down_count: int = 0
    limit_up: int = 0
    limit_down: int = 0
    break_board: int = 0


class StockData(BaseModel):
    code: str
    name: str
    open: float = 0
    high: float = 0
    low: float = 0
    close: float = 0
    pct_chg: float = 0
    turnover: float = 0
    amplitude: float = 0
    volume: float = 0


class CapitalFlow(BaseModel):
    main: float = 0
    super_large: float = 0
    large: float = 0
    north_money: float = 0
    margin: float = 0


class SectorData(BaseModel):
    code: str
    name: str
    pct_chg: float = 0


class NewsItem(BaseModel):
    code: str = ""
    title: str = ""
    summary: str = ""
    show_time: str = ""
    stock_list: List[str] = []
    image: List[str] = []
    pinglun_num: int = 0
    share: int = 0
    sentiment: str = "中性"


class MarketRecommendation(BaseModel):
    trend: str = "震荡"
    position: str = "5成"
    risk: str = "无"


class SectorRecommendation(BaseModel):
    main: List[str] = []
    avoid: List[str] = []
    rotation: str = ""


class StockRecommendation(BaseModel):
    hold: List[Dict[str, str]] = []
    watch: List[Dict[str, str]] = []
    avoid: List[Dict[str, str]] = []


class Recommendation(BaseModel):
    market: MarketRecommendation = MarketRecommendation()
    sectors: SectorRecommendation = SectorRecommendation()
    stocks: StockRecommendation = StockRecommendation()


class AfterMarketData(BaseModel):
    date: str
    created_at: datetime = None
    market_overview: Optional[MarketOverview] = None
    stocks: List[StockData] = []
    capital_flow: Optional[CapitalFlow] = None
    sectors: List[SectorData] = []
    news: List[Dict[str, Any]] = []
    recommendations: Optional[Recommendation] = None

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat() if v else None
        }
    }
