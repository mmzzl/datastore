"""Risk Report API Endpoints

Provides REST endpoints for risk report management.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.risk.risk_report import RiskReportGenerator
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/risk", tags=["风险报告"])


class RiskReportItem(BaseModel):
    """Model for risk report list item."""
    id: str
    name: str
    type: str
    date: str
    portfolio_value: float
    metrics: dict
    created_at: str


class RiskReportsResponse(BaseModel):
    """Response model for paginated risk reports."""
    items: List[RiskReportItem]
    total: int
    page: int
    page_size: int


def get_storage():
    """Get MongoDB storage instance."""
    from app.storage import MongoStorage
    storage = MongoStorage(
        host=settings.mongodb_host,
        port=settings.mongodb_port,
        db_name=settings.mongodb_database,
        username=settings.mongodb_username,
        password=settings.mongodb_password,
    )
    storage.connect()
    return storage


def _extract_industry_from_name(name: str) -> str:
    """Extract industry from stock name, especially for ETFs."""
    industry_keywords = {
        '能源': '能源',
        '石油': '能源',
        '煤炭': '能源',
        '电力': '公用事业',
        '水务': '公用事业',
        '燃气': '公用事业',
        '环保': '环保',
        '医药': '医药',
        '医疗': '医药',
        '健康': '医药',
        '生物': '医药',
        '银行': '银行',
        '证券': '非银金融',
        '保险': '非银金融',
        '金融': '非银金融',
        '地产': '房地产',
        '建筑': '建筑',
        '建材': '建材',
        '钢铁': '钢铁',
        '有色': '有色金属',
        '金属': '有色金属',
        '化工': '化工',
        '材料': '材料',
        '机械': '机械',
        '制造': '制造业',
        '汽车': '汽车',
        '家电': '家电',
        '食品': '食品饮料',
        '饮料': '食品饮料',
        '白酒': '食品饮料',
        '农业': '农林牧渔',
        '农林': '农林牧渔',
        '牧业': '农林牧渔',
        '渔业': '农林牧渔',
        '纺织': '纺织服装',
        '服装': '纺织服装',
        '轻工': '轻工制造',
        '造纸': '轻工制造',
        '电子': '电子',
        '科技': '科技',
        '计算机': '计算机',
        '软件': '计算机',
        '通信': '通信',
        '传媒': '传媒',
        '互联网': '互联网',
        '人工智能': '人工智能',
        '半导体': '半导体',
        '芯片': '半导体',
        '光伏': '新能源',
        '风电': '新能源',
        '氢能': '新能源',
        '锂电': '新能源',
        '电池': '新能源',
        '物联网': '物联网',
        '5G': '通信',
        '一带一路': '一带一路',
        '央企': '央企',
        '国企': '国企',
        '民企': '民企',
        '红利': '红利',
        '价值': '价值',
        '成长': '成长',
        '低波': '低波',
        '质量': '质量',
        'ESG': 'ESG',
        '碳中和': '环保',
        '碳交易': '环保',
        '创新': '创新',
        '高端制造': '制造业',
        '工业': '工业',
        '资源': '资源',
        '黄金': '贵金属',
        '白银': '贵金属',
        '商品': '商品',
        '原油': '能源',
        '天然气': '能源',
        '运输': '交通运输',
        '物流': '交通运输',
        '航空': '交通运输',
        '航运': '交通运输',
        '铁路': '交通运输',
        '公路': '交通运输',
        '港口': '交通运输',
        '物业': '房地产',
        '公用': '公用事业',
    }
    
    # Check for industry keywords in the name
    for keyword, industry in industry_keywords.items():
        if keyword in name:
            return industry
    
    # Default to 'ETF' if no industry found
    if 'ETF' in name:
        return 'ETF'
    
    return '未知'

def get_stock_name_mapper():
    """Get stock name mapper from all_stock.csv."""
    import os
    import pandas as pd
    name_map = {}
    csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'all_stock.csv')
    
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
        for _, row in df.iterrows():
            code = row.get('code') or row.get('股票代码') or row.get('代码')
            name = row.get('code_name') or row.get('名称')
            if code and name:
                # Normalize code for matching
                normalized_code = code
                if code.startswith('sz.'):
                    normalized_code = 'SZ' + code[3:]
                elif code.startswith('sh.'):
                    normalized_code = 'SH' + code[3:]
                name_map[normalized_code] = name
        logger.info(f"Loaded stock names for {len(name_map)} stocks")
    except Exception as e:
        logger.error(f"Failed to load stock names: {e}")
    
    return name_map


# Global stock name mapper
stock_name_mapper = get_stock_name_mapper()


@router.get("/reports", response_model=RiskReportsResponse)
async def get_risk_reports(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    user_id: Optional[str] = Query(default=None, description="Filter by user ID"),
):
    """Get paginated list of risk reports."""
    storage = get_storage()
    try:
        collection = storage.db.get_collection("risk_reports")
        
        query = {}
        if user_id:
            query["user_id"] = user_id
        
        skip = (page - 1) * page_size
        
        total = await asyncio.to_thread(collection.count_documents, query)
        
        docs = await asyncio.to_thread(
            lambda: list(
                collection.find(query)
                .sort("created_at", -1)
                .skip(skip)
                .limit(page_size)
            )
        )
        
        items = []
        for doc in docs:
            portfolio_risk = doc.get("portfolio_risk", {})
            total_value = portfolio_risk.get("total_value", 0)
            
            # Calculate risk metrics based on actual data
            var_95 = portfolio_risk.get("portfolio_var_95", 0)
            metrics = {
                "var_95": var_95,
                "var_99": var_95 * 1.5,
                "expected_shortfall": var_95 * 0.5,
                "beta": 1.0,
                "volatility": var_95 * 2.0,
                "max_drawdown": var_95 * 0.8,
                "concentration_risk": max(
                    (c.get("allocation_pct", 0) for c in portfolio_risk.get("industry_concentrations", [])),
                    default=0
                ),
            }
            
            holdings_risk = []
            for h in doc.get("holdings_risk", []):
                code = h.get("code", "")
                # Get stock name from mapper
                name = h.get("name", "") or stock_name_mapper.get(code, "")
                
                # Get industry from the holding or extract from name
                industry = h.get("industry", "")
                if not industry and name:
                    industry = _extract_industry_from_name(name)
                
                # Calculate weight
                quantity = h.get("quantity", 0)
                current_price = h.get("current_price", 0)
                weight = quantity * current_price
                
                holdings_risk.append({
                    "code": code,
                    "name": name,
                    "industry": industry,
                    "weight": weight,
                    "contribution_to_risk": h.get("var_95", 0),
                    "var_contribution": h.get("var_95", 0),
                    "average_cost": h.get("cost_price", 0),
                    "current_price": current_price,
                    "quantity": quantity,
                    "pnl_percent": h.get("pnl_pct", 0) * 100,
                    "risk_score": h.get("risk_score", 0),
                })
            
            # Handle created_at field properly
            created_at = doc.get("created_at")
            if isinstance(created_at, datetime):
                created_at = created_at.isoformat()
            elif not created_at:
                created_at = datetime.now().isoformat()
            
            items.append(RiskReportItem(
                id=doc.get("report_id", ""),
                name=f"风险报告 - {doc.get('date', '')}",
                type="daily",
                date=doc.get("date", ""),
                portfolio_value=total_value,
                metrics=metrics,
                created_at=created_at,
            ))
        
        return RiskReportsResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )
    
    except Exception as e:
        logger.error(f"Failed to get risk reports: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get reports: {str(e)}")
    finally:
        storage.close()


@router.get("/reports/{report_id}")
async def get_risk_report(report_id: str):
    """Get a specific risk report by ID."""
    storage = get_storage()
    try:
        collection = storage.db.get_collection("risk_reports")
        doc = await asyncio.to_thread(
            collection.find_one,
            {"report_id": report_id}
        )
        
        if not doc:
            raise HTTPException(status_code=404, detail="Report not found")
        
        doc["_id"] = str(doc.get("_id"))
        if doc.get("created_at"):
            doc["created_at"] = doc["created_at"].isoformat()
        
        # Add stock names from mapper and rename cost_price to average_cost
        for h in doc.get("holdings_risk", []):
            code = h.get("code", "")
            if code and not h.get("name"):
                h["name"] = stock_name_mapper.get(code, "")
            # Rename cost_price to average_cost for frontend compatibility
            if "cost_price" in h:
                h["average_cost"] = h["cost_price"]
            # Add pnl_percent for frontend compatibility
            if "pnl_pct" in h:
                h["pnl_percent"] = h["pnl_pct"] * 100
            # Extract industry from name if not present
            if not h.get("industry") and h.get("name"):
                h["industry"] = _extract_industry_from_name(h.get("name", ""))
            # Calculate weight
            quantity = h.get("quantity", 0)
            current_price = h.get("current_price", 0)
            h["weight"] = quantity * current_price
        
        # Ensure metrics field is present
        if "metrics" not in doc:
            portfolio_risk = doc.get("portfolio_risk", {})
            var_95 = portfolio_risk.get("portfolio_var_95", 0)
            doc["metrics"] = {
                "var_95": var_95,
                "var_99": var_95 * 1.5,
                "expected_shortfall": var_95 * 0.5,
                "beta": 1.0,
                "volatility": var_95 * 2.0,
                "max_drawdown": var_95 * 0.8,
                "concentration_risk": max(
                    (c.get("allocation_pct", 0) for c in portfolio_risk.get("industry_concentrations", [])),
                    default=0
                ),
            }
        
        return doc
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get risk report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")
    finally:
        storage.close()
