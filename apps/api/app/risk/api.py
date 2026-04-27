"""Risk Report API Endpoints

Provides REST endpoints for risk report management.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.risk.industry_utils import extract_industry_from_name
from app.risk.risk_report import RiskReportGenerator
from app.core.config import settings
from app.core.auth import AuthenticatedUser, require_permission

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
    stress_test: Optional[dict] = None
    high_correlation_pairs: Optional[list] = None


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
    current_user: AuthenticatedUser = Depends(require_permission("risk:view")),
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
            
            metrics = {
                "var_95": portfolio_risk.get("portfolio_var_95", 0),
                "var_99": portfolio_risk.get("var_99", 0),
                "expected_shortfall": portfolio_risk.get("expected_shortfall", 0),
                "beta": portfolio_risk.get("beta", 0),
                "volatility": portfolio_risk.get("volatility", 0),
                "max_drawdown": portfolio_risk.get("max_drawdown", 0),
                "sharpe_ratio": portfolio_risk.get("sharpe_ratio", 0),
                "concentration_score": portfolio_risk.get("concentration_score", 0),
                "concentration_risk": max(
                    (c.get("allocation_pct", 0) for c in portfolio_risk.get("industry_concentrations", [])),
                    default=0
                ),
            }

            holdings_risk = []
            for h in doc.get("holdings_risk", []):
                code = h.get("code", "")
                name = h.get("name", "") or stock_name_mapper.get(code, "")

                industry = h.get("industry", "")
                if not industry and name:
                    industry = extract_industry_from_name(name)

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
                    "var_95": h.get("var_95", 0),
                    "var_99": h.get("var_99", 0),
                    "expected_shortfall": h.get("expected_shortfall", 0),
                    "volatility": h.get("volatility", 0),
                    "max_drawdown": h.get("max_drawdown", 0),
                    "sharpe_ratio": h.get("sharpe_ratio", 0),
                    "beta": h.get("beta", 0),
                    "liquidity_days": h.get("liquidity_days", 0),
                })

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
                stress_test=doc.get("stress_test"),
                high_correlation_pairs=portfolio_risk.get("high_correlation_pairs"),
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
async def get_risk_report(
    report_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("risk:view")),
):
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
                h["industry"] = extract_industry_from_name(h.get("name", ""))
            # Calculate weight
            quantity = h.get("quantity", 0)
            current_price = h.get("current_price", 0)
            h["weight"] = quantity * current_price

        # Ensure metrics field is present
        if "metrics" not in doc:
            portfolio_risk = doc.get("portfolio_risk", {})
            doc["metrics"] = {
                "var_95": portfolio_risk.get("portfolio_var_95", 0),
                "var_99": portfolio_risk.get("var_99", 0),
                "expected_shortfall": portfolio_risk.get("expected_shortfall", 0),
                "beta": portfolio_risk.get("beta", 0),
                "volatility": portfolio_risk.get("volatility", 0),
                "max_drawdown": portfolio_risk.get("max_drawdown", 0),
                "sharpe_ratio": portfolio_risk.get("sharpe_ratio", 0),
                "concentration_score": portfolio_risk.get("concentration_score", 0),
                "concentration_risk": max(
                    (c.get("allocation_pct", 0) for c in portfolio_risk.get("industry_concentrations", [])),
                    default=0
                ),
            }

        # Pass through stress_test data
        if "stress_test" not in doc:
            doc["stress_test"] = None

        # Pass through correlation data
        pr = doc.get("portfolio_risk", {})
        if "correlation_matrix" not in doc:
            doc["correlation_matrix"] = pr.get("correlation_matrix")
        if "correlation_labels" not in doc:
            doc["correlation_labels"] = pr.get("correlation_labels")
        if "high_correlation_pairs" not in doc:
            doc["high_correlation_pairs"] = pr.get("high_correlation_pairs")

        return doc

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get risk report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")
    finally:
        storage.close()


@router.get("/reports/trend/{user_id}")
async def get_risk_trend(
    user_id: str,
    days: int = Query(default=30, ge=7, le=365, description="Number of days"),
    current_user: AuthenticatedUser = Depends(require_permission("risk:view")),
):
    """Get risk trend data for a user."""
    generator = RiskReportGenerator()
    try:
        trend_data = await generator.get_trend_data(user_id, days)
        return trend_data
    except Exception as e:
        logger.error(f"Failed to get risk trend for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trend data: {str(e)}")
    finally:
        generator.close()
