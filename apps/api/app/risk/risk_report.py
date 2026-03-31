import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from ..core.config import settings
from ..storage.mongo_client import MongoStorage

logger = logging.getLogger(__name__)


@dataclass
class PositionRisk:
    code: str
    name: Optional[str]
    quantity: float
    cost_price: float
    current_price: float
    pnl_pct: float
    var_95: float
    risk_score: int
    industry: Optional[str] = None


@dataclass
class IndustryConcentration:
    industry: str
    allocation_pct: float
    position_count: int
    value: float


@dataclass
class PortfolioRisk:
    total_value: float
    total_cost: float
    portfolio_var_95: float
    industry_concentrations: List[IndustryConcentration] = field(default_factory=list)
    var_warning: bool = False
    concentration_warning: bool = False


@dataclass
class RiskReport:
    report_id: str
    user_id: str
    date: str
    risk_score: int
    risk_level: str
    holdings_risk: List[PositionRisk]
    portfolio_risk: PortfolioRisk
    recommendations: List[str]
    created_at: datetime


class RiskReportGenerator:
    VAR_THRESHOLD = 0.05
    PNL_WARNING_THRESHOLD = -0.08
    INDUSTRY_CONCENTRATION_THRESHOLD = 0.50
    LOOKBACK_DAYS = 252

    def __init__(self, storage: Optional[MongoStorage] = None):
        self._storage = storage
        self._risk_collection = None

    def _get_storage(self) -> MongoStorage:
        if self._storage is None:
            self._storage = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_database,
                username=settings.mongodb_username,
                password=settings.mongodb_password,
            )
            self._storage.connect()
        return self._storage

    def _get_risk_collection(self):
        storage = self._get_storage()
        if self._risk_collection is None:
            self._risk_collection = storage.db.get_collection("risk_reports")
        return self._risk_collection

    def _get_kline_data(
        self, code: str, days: int = 252
    ) -> List[Dict[str, Any]]:
        storage = self._get_storage()
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y-%m-%d")
        return storage.get_kline(code, start_date=start_date, end_date=end_date, limit=days + 30)

    def _calculate_var_95(self, returns: List[float]) -> float:
        if not returns or len(returns) < 10:
            return 0.0
        sorted_returns = sorted(returns)
        var_index = int(len(sorted_returns) * 0.05)
        var_index = max(0, var_index)
        return abs(sorted_returns[var_index])

    def _calculate_returns(self, kline_data: List[Dict[str, Any]]) -> List[float]:
        if not kline_data or len(kline_data) < 2:
            return []
        returns = []
        sorted_data = sorted(kline_data, key=lambda x: x.get("date", ""))
        for i in range(1, len(sorted_data)):
            prev_close = sorted_data[i - 1].get("close", 0)
            curr_close = sorted_data[i].get("close", 0)
            if prev_close > 0:
                returns.append((curr_close - prev_close) / prev_close)
        return returns

    async def _calculate_position_var(self, code: str) -> float:
        kline_data = await asyncio.to_thread(self._get_kline_data, code, self.LOOKBACK_DAYS)
        returns = self._calculate_returns(kline_data)
        return self._calculate_var_95(returns)

    def _calculate_position_risk_score(
        self, pnl_pct: float, var_95: float, var_contribution: float
    ) -> int:
        score = 0
        if pnl_pct < self.PNL_WARNING_THRESHOLD:
            score += 40
        elif pnl_pct < 0:
            score += int(abs(pnl_pct) * 250)
        if var_95 > self.VAR_THRESHOLD:
            score += 30
        elif var_95 > 0.03:
            score += int(var_95 * 500)
        if var_contribution > 0.2:
            score += 20
        return min(100, max(0, score))

    async def _get_industry(self, code: str) -> Optional[str]:
        storage = self._get_storage()
        try:
            stock_info_coll = storage.db.get_collection("stock_info")
            doc = await asyncio.to_thread(stock_info_coll.find_one, {"code": code})
            if doc:
                return doc.get("industry")
        except Exception as e:
            logger.warning(f"Failed to get industry for {code}: {e}")
        return None

    async def _calculate_industry_concentrations(
        self, positions: List[Dict[str, Any]], price_fetcher: Callable[[str], float]
    ) -> List[IndustryConcentration]:
        industry_values: Dict[str, float] = {}
        total_value = 0.0
        for pos in positions:
            code = pos.get("code", "")
            quantity = pos.get("quantity", 0)
            price = price_fetcher(code) if quantity > 0 else 0
            value = quantity * price
            if value <= 0:
                continue
            total_value += value
            industry = await self._get_industry(code) or "未知"
            industry_values[industry] = industry_values.get(industry, 0) + value
        if total_value <= 0:
            return []
        concentrations = []
        for industry, value in industry_values.items():
            pct = value / total_value
            position_count = 0
            for p in positions:
                if p.get("quantity", 0) > 0:
                    p_industry = await self._get_industry(p.get("code", "")) or "未知"
                    if p_industry == industry:
                        position_count += 1
            concentrations.append(
                IndustryConcentration(
                    industry=industry,
                    allocation_pct=pct,
                    position_count=position_count,
                    value=value,
                )
            )
        return sorted(concentrations, key=lambda x: x.allocation_pct, reverse=True)

    async def _calculate_portfolio_var(
        self, positions: List[Dict[str, Any]], price_fetcher: Callable[[str], float]
    ) -> float:
        total_var = 0.0
        total_value = 0.0
        for pos in positions:
            code = pos.get("code", "")
            quantity = pos.get("quantity", 0)
            if quantity <= 0:
                continue
            price = price_fetcher(code)
            value = quantity * price
            var = await self._calculate_position_var(code)
            total_var += value * var
            total_value += value
        if total_value <= 0:
            return 0.0
        return total_var / total_value

    def _calculate_risk_score(
        self,
        portfolio_var: float,
        concentrations: List[IndustryConcentration],
        positions_risk: List[PositionRisk],
    ) -> int:
        score = 0
        var_score = min(30, int(portfolio_var * 500))
        score += var_score
        max_concentration = max(
            (c.allocation_pct for c in concentrations), default=0
        )
        concentration_score = min(30, int(max_concentration * 50))
        score += concentration_score
        loss_count = sum(1 for p in positions_risk if p.pnl_pct < 0)
        total_count = len(positions_risk)
        if total_count > 0:
            loss_ratio = loss_count / total_count
            loss_score = min(40, int(loss_ratio * 80))
            score += loss_score
        return min(100, score)

    def _get_risk_level(self, score: int) -> str:
        if score < 30:
            return "low"
        elif score < 60:
            return "medium"
        else:
            return "high"

    def _generate_recommendations(
        self,
        portfolio_risk: PortfolioRisk,
        positions_risk: List[PositionRisk],
        risk_level: str,
    ) -> List[str]:
        recommendations = []
        if portfolio_risk.var_warning:
            recommendations.append(
                f"【高风险】组合VaR超过5%阈值({portfolio_risk.portfolio_var_95:.2%})，建议降低仓位或分散持仓"
            )
        for conc in portfolio_risk.industry_concentrations:
            if conc.allocation_pct > self.INDUSTRY_CONCENTRATION_THRESHOLD:
                recommendations.append(
                    f"【高风险】{conc.industry}行业集中度过高({conc.allocation_pct:.1%})，建议分散配置"
                )
        for pos in positions_risk:
            if pos.pnl_pct < self.PNL_WARNING_THRESHOLD:
                recommendations.append(
                    f"【警告】{pos.name or pos.code}亏损{abs(pos.pnl_pct):.1%}，建议止损或减仓"
                )
            elif pos.pnl_pct < -0.05:
                recommendations.append(
                    f"【注意】{pos.name or pos.code}亏损{abs(pos.pnl_pct):.1%}，请关注风险"
                )
        if risk_level == "high":
            recommendations.append("组合整体风险偏高，建议审视持仓结构，控制回撤")
        elif risk_level == "medium":
            recommendations.append("组合风险处于中等水平，建议适度优化持仓结构")
        elif not recommendations:
            recommendations.append("组合风险处于低位，当前配置较为合理")
        return recommendations

    async def generate_report(
        self,
        user_id: str,
        holdings: List[Dict[str, Any]],
        price_fetcher: Callable[[str], float],
    ) -> RiskReport:
        positions_risk: List[PositionRisk] = []
        for holding in holdings:
            code = holding.get("code", "")
            name = holding.get("name")
            quantity = holding.get("quantity", 0)
            cost_price = holding.get("average_cost", 0)
            if quantity <= 0:
                continue
            current_price = price_fetcher(code)
            pnl_pct = (
                (current_price - cost_price) / cost_price if cost_price > 0 else 0
            )
            var_95 = await self._calculate_position_var(code)
            position_value = quantity * current_price
            total_value = sum(
                h.get("quantity", 0) * price_fetcher(h.get("code", ""))
                for h in holdings
                if h.get("quantity", 0) > 0
            )
            var_contribution = (
                position_value * var_95 / total_value if total_value > 0 else 0
            )
            risk_score = self._calculate_position_risk_score(
                pnl_pct, var_95, var_contribution
            )
            industry = await self._get_industry(code)
            positions_risk.append(
                PositionRisk(
                    code=code,
                    name=name,
                    quantity=quantity,
                    cost_price=cost_price,
                    current_price=current_price,
                    pnl_pct=pnl_pct,
                    var_95=var_95,
                    risk_score=risk_score,
                    industry=industry,
                )
            )
        concentrations = await self._calculate_industry_concentrations(holdings, price_fetcher)
        portfolio_var = await self._calculate_portfolio_var(holdings, price_fetcher)
        total_value = sum(p.quantity * p.current_price for p in positions_risk)
        total_cost = sum(p.quantity * p.cost_price for p in positions_risk)
        var_warning = portfolio_var > self.VAR_THRESHOLD
        concentration_warning = any(
            c.allocation_pct > self.INDUSTRY_CONCENTRATION_THRESHOLD
            for c in concentrations
        )
        portfolio_risk = PortfolioRisk(
            total_value=total_value,
            total_cost=total_cost,
            portfolio_var_95=portfolio_var,
            industry_concentrations=concentrations,
            var_warning=var_warning,
            concentration_warning=concentration_warning,
        )
        risk_score = self._calculate_risk_score(
            portfolio_var, concentrations, positions_risk
        )
        risk_level = self._get_risk_level(risk_score)
        recommendations = self._generate_recommendations(
            portfolio_risk, positions_risk, risk_level
        )
        report = RiskReport(
            report_id=str(uuid.uuid4()),
            user_id=user_id,
            date=datetime.now().strftime("%Y-%m-%d"),
            risk_score=risk_score,
            risk_level=risk_level,
            holdings_risk=positions_risk,
            portfolio_risk=portfolio_risk,
            recommendations=recommendations,
            created_at=datetime.now(),
        )
        return report

    async def save_report(self, report: RiskReport) -> Optional[str]:
        try:
            collection = self._get_risk_collection()
            doc = {
                "report_id": report.report_id,
                "user_id": report.user_id,
                "date": report.date,
                "risk_score": report.risk_score,
                "risk_level": report.risk_level,
                "holdings_risk": [
                    {
                        "code": p.code,
                        "name": p.name,
                        "quantity": p.quantity,
                        "cost_price": p.cost_price,
                        "current_price": p.current_price,
                        "pnl_pct": p.pnl_pct,
                        "var_95": p.var_95,
                        "risk_score": p.risk_score,
                        "industry": p.industry,
                    }
                    for p in report.holdings_risk
                ],
                "portfolio_risk": {
                    "total_value": report.portfolio_risk.total_value,
                    "total_cost": report.portfolio_risk.total_cost,
                    "portfolio_var_95": report.portfolio_risk.portfolio_var_95,
                    "industry_concentrations": [
                        {
                            "industry": c.industry,
                            "allocation_pct": c.allocation_pct,
                            "position_count": c.position_count,
                            "value": c.value,
                        }
                        for c in report.portfolio_risk.industry_concentrations
                    ],
                    "var_warning": report.portfolio_risk.var_warning,
                    "concentration_warning": report.portfolio_risk.concentration_warning,
                },
                "recommendations": report.recommendations,
                "created_at": report.created_at,
            }
            result = await asyncio.to_thread(collection.insert_one, doc)
            logger.info(f"Saved risk report {report.report_id} for user {report.user_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to save risk report: {e}")
            return None

    async def get_latest_report(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            collection = self._get_risk_collection()
            doc = await asyncio.to_thread(
                collection.find_one,
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )
            if doc:
                doc["_id"] = str(doc.get("_id"))
                if doc.get("created_at"):
                    doc["created_at"] = doc["created_at"].isoformat()
                return doc
        except Exception as e:
            logger.error(f"Failed to get latest risk report: {e}")
        return None

    async def get_reports_by_date(
        self, user_id: str, date: str
    ) -> List[Dict[str, Any]]:
        try:
            collection = self._get_risk_collection()
            cursor = await asyncio.to_thread(
                lambda: list(collection.find({"user_id": user_id, "date": date}).sort("created_at", -1))
            )
            results = []
            for doc in cursor:
                doc["_id"] = str(doc.get("_id"))
                if doc.get("created_at"):
                    doc["created_at"] = doc["created_at"].isoformat()
                results.append(doc)
            return results
        except Exception as e:
            logger.error(f"Failed to get risk reports by date: {e}")
            return []

    def close(self):
        if self._storage:
            self._storage.close()
            logger.info("RiskReportGenerator storage connection closed")
