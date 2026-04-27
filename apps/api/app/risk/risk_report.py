import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import numpy as np

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
    var_99: float = 0.0
    expected_shortfall: float = 0.0
    volatility: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    beta: float = 0.0
    liquidity_days: float = 0.0
    marginal_var: float = 0.0


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
    var_99: float = 0.0
    expected_shortfall: float = 0.0
    volatility: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    beta: float = 0.0
    concentration_score: float = 0.0
    liquidity_risk: Dict[str, Any] = field(default_factory=dict)
    style_exposure: Dict[str, float] = field(default_factory=dict)
    correlation_matrix: Optional[List[List[float]]] = None
    correlation_labels: Optional[List[str]] = None
    high_correlation_pairs: Optional[List[Dict[str, Any]]] = None


@dataclass
class StressScenario:
    name: str
    description: str
    market_shock: float
    estimated_loss: float
    estimated_loss_pct: float


@dataclass
class StressTestResult:
    scenarios: List[StressScenario] = field(default_factory=list)
    industry_shock: List[StressScenario] = field(default_factory=list)
    liquidity_crisis: Optional[StressScenario] = None


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
    stress_test: Optional[StressTestResult] = None


class RiskReportGenerator:
    VAR_THRESHOLD = 0.05
    PNL_WARNING_THRESHOLD = -0.08
    INDUSTRY_CONCENTRATION_THRESHOLD = 0.50
    LOOKBACK_DAYS = 252

    def __init__(self, storage: Optional[MongoStorage] = None):
        self._storage = storage
        self._risk_collection = None
        self._industry_cache: Dict[str, Optional[str]] = {}

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

    def _normalize_code(self, code: str) -> str:
        if code.startswith("SH") or code.startswith("SZ"):
            return code[2:]
        return code

    def _get_kline_data(
        self, code: str, days: int = 252
    ) -> List[Dict[str, Any]]:
        storage = self._get_storage()
        normalized = self._normalize_code(code)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y-%m-%d")
        return storage.get_kline(normalized, start_date=start_date, end_date=end_date, limit=days + 30)

    def _calculate_var_95(self, returns: List[float]) -> float:
        if not returns or len(returns) < 10:
            return 0.0
        arr = np.array(returns)
        return float(abs(np.percentile(arr, 5)))

    def _calculate_var_99(self, returns: List[float]) -> float:
        if not returns or len(returns) < 10:
            return 0.0
        arr = np.array(returns)
        return float(abs(np.percentile(arr, 1)))

    def _calculate_expected_shortfall(self, returns: List[float]) -> float:
        if not returns or len(returns) < 10:
            return 0.0
        arr = np.array(returns)
        threshold = np.percentile(arr, 5)
        tail = arr[arr <= threshold]
        if len(tail) == 0:
            return self._calculate_var_95(returns)
        return abs(float(np.mean(tail)))

    def _calculate_volatility(self, returns: List[float]) -> float:
        if not returns or len(returns) < 10:
            return 0.0
        return float(np.std(returns, ddof=1) * np.sqrt(252))

    def _calculate_max_drawdown(self, kline_data: List[Dict[str, Any]]) -> float:
        if not kline_data or len(kline_data) < 2:
            return 0.0
        sorted_data = sorted(kline_data, key=lambda x: x.get("date", ""))
        closes = np.array([d.get("close", 0) for d in sorted_data], dtype=float)
        if len(closes) < 2 or np.any(closes <= 0):
            return 0.0
        cummax = np.maximum.accumulate(closes)
        drawdowns = (cummax - closes) / cummax
        return float(np.max(drawdowns))

    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        if not returns or len(returns) < 10:
            return 0.0
        arr = np.array(returns)
        annualized_return = float(np.mean(arr) * 252)
        annualized_vol = float(np.std(arr, ddof=1) * np.sqrt(252))
        if annualized_vol <= 0:
            return 0.0
        return (annualized_return - 0.03) / annualized_vol

    async def _calculate_beta(self, code: str) -> float:
        kline_data = await asyncio.to_thread(
            self._get_kline_data, self._normalize_code(code), self.LOOKBACK_DAYS
        )
        returns = self._calculate_returns(kline_data)
        if not returns or len(returns) < 30:
            return 0.0
        market_kline = await asyncio.to_thread(
            self._get_kline_data, "sh.000300", self.LOOKBACK_DAYS
        )
        market_returns = self._calculate_returns(market_kline)
        if not market_returns or len(market_returns) < 30:
            return 0.0
        min_len = min(len(returns), len(market_returns))
        stock_arr = np.array(returns[:min_len])
        market_arr = np.array(market_returns[:min_len])
        cov_matrix = np.cov(stock_arr, market_arr)
        market_var = np.var(market_arr, ddof=1)
        if market_var <= 0:
            return 0.0
        return float(cov_matrix[0][1] / market_var)

    def _calculate_liquidity_days(self, kline_data: List[Dict[str, Any]], position_value: float) -> float:
        if not kline_data or position_value <= 0:
            return 0.0
        sorted_data = sorted(kline_data, key=lambda x: x.get("date", ""))
        recent = sorted_data[-20:] if len(sorted_data) >= 20 else sorted_data
        volumes = [d.get("volume", 0) for d in recent]
        closes = [d.get("close", 0) for d in recent]
        daily_values = [v * c for v, c in zip(volumes, closes) if v > 0 and c > 0]
        if not daily_values:
            return 0.0
        avg_daily_value = float(np.mean(daily_values))
        if avg_daily_value <= 0:
            return 0.0
        return position_value / (avg_daily_value * 0.1)

    def _calculate_concentration_score(self, positions_risk: List[PositionRisk]) -> float:
        total_value = sum(p.quantity * p.current_price for p in positions_risk)
        if total_value <= 0:
            return 0.0
        weights = [(p.quantity * p.current_price) / total_value for p in positions_risk]
        return sum(w * w for w in weights) * 100

    async def _calculate_correlation_matrix(
        self, positions: List[Dict[str, Any]]
    ) -> tuple:
        codes = [p.get("code", "") for p in positions if p.get("quantity", 0) > 0]
        if len(codes) < 2:
            return None, None, []
        returns_dict = {}
        for code in codes:
            kline_data = await asyncio.to_thread(
                self._get_kline_data, self._normalize_code(code), self.LOOKBACK_DAYS
            )
            returns = self._calculate_returns(kline_data)
            if len(returns) >= 30:
                returns_dict[code] = returns
        if len(returns_dict) < 2:
            return None, None, []
        min_len = min(len(r) for r in returns_dict.values())
        aligned = {code: r[-min_len:] for code, r in returns_dict.items()}
        codes_ordered = list(aligned.keys())
        matrix = np.corrcoef([aligned[c] for c in codes_ordered])
        high_pairs = []
        for i in range(len(codes_ordered)):
            for j in range(i + 1, len(codes_ordered)):
                corr = float(matrix[i][j])
                if abs(corr) > 0.7:
                    high_pairs.append({
                        "code_1": codes_ordered[i],
                        "code_2": codes_ordered[j],
                        "correlation": round(corr, 3),
                    })
        return matrix.tolist(), codes_ordered, high_pairs

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
        kline_data = await asyncio.to_thread(
            self._get_kline_data, self._normalize_code(code), self.LOOKBACK_DAYS
        )
        returns = self._calculate_returns(kline_data)
        return self._calculate_var_95(returns)

    async def _calculate_position_var_99(self, code: str) -> float:
        kline_data = await asyncio.to_thread(
            self._get_kline_data, self._normalize_code(code), self.LOOKBACK_DAYS
        )
        returns = self._calculate_returns(kline_data)
        return self._calculate_var_99(returns)

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
        normalized = self._normalize_code(code)
        if normalized in self._industry_cache:
            return self._industry_cache[normalized]
        storage = self._get_storage()
        try:
            stock_info_coll = storage.db.get_collection("stock_info")
            doc = await asyncio.to_thread(stock_info_coll.find_one, {"code": normalized})
            industry = doc.get("industry") if doc else None
        except Exception as e:
            logger.warning(f"Failed to get industry for {code}: {e}")
            industry = None
        self._industry_cache[normalized] = industry
        return industry

    async def _calculate_industry_concentrations(
        self, positions: List[Dict[str, Any]], price_fetcher: Callable[[str], float]
    ) -> List[IndustryConcentration]:
        industry_values: Dict[str, float] = {}
        industry_counts: Dict[str, int] = {}
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
            industry_counts[industry] = industry_counts.get(industry, 0) + 1
        if total_value <= 0:
            return []
        concentrations = []
        for industry, value in industry_values.items():
            pct = value / total_value
            concentrations.append(
                IndustryConcentration(
                    industry=industry,
                    allocation_pct=pct,
                    position_count=industry_counts.get(industry, 0),
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

    async def _calculate_portfolio_var_99(
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
            var = await self._calculate_position_var_99(code)
            total_var += value * var
            total_value += value
        if total_value <= 0:
            return 0.0
        return total_var / total_value

    def _calculate_portfolio_returns(self, positions_risk: List[PositionRisk]) -> List[float]:
        if not positions_risk:
            return []
        total_value = sum(p.quantity * p.current_price for p in positions_risk if p.current_price > 0)
        if total_value <= 0:
            return []
        weights = {}
        returns_cache = {}
        for p in positions_risk:
            if p.current_price <= 0:
                continue
            weights[p.code] = (p.quantity * p.current_price) / total_value
            kline_data = self._get_kline_data(self._normalize_code(p.code), self.LOOKBACK_DAYS)
            returns_cache[p.code] = self._calculate_returns(kline_data)
        valid_returns = {k: v for k, v in returns_cache.items() if len(v) >= 2 and k in weights}
        if not valid_returns:
            return []
        min_len = min(len(v) for v in valid_returns.values())
        portfolio_returns = [0.0] * min_len
        for code, rets in valid_returns.items():
            offset = len(rets) - min_len
            for j in range(min_len):
                portfolio_returns[j] += weights[code] * rets[offset + j]
        return portfolio_returns

    def _calculate_portfolio_max_drawdown(self, positions_risk: List[PositionRisk]) -> float:
        returns = self._calculate_portfolio_returns(positions_risk)
        if not returns:
            return 0.0
        cum_returns = np.cumprod(np.array(returns) + 1)
        cummax = np.maximum.accumulate(cum_returns)
        drawdowns = (cummax - cum_returns) / cummax
        return float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

    def _calculate_weighted_beta(self, positions_risk: List[PositionRisk]) -> float:
        weighted = sum(
            (p.quantity * p.current_price) * p.beta
            for p in positions_risk if p.beta > 0 and p.current_price > 0
        )
        total_value = sum(
            p.quantity * p.current_price
            for p in positions_risk if p.beta > 0 and p.current_price > 0
        )
        if total_value <= 0:
            return 0.0
        return weighted / total_value

    def _calculate_portfolio_liquidity_risk(self, positions_risk: List[PositionRisk]) -> Dict[str, Any]:
        if not positions_risk:
            return {}
        max_days = max((p.liquidity_days for p in positions_risk), default=0)
        high_liquidity = [p.code for p in positions_risk if p.liquidity_days > 5]
        return {
            "max_liquidity_days": round(max_days, 1),
            "high_liquidity_positions": high_liquidity,
        }

    def _calculate_stress_test(
        self, positions_risk: List[PositionRisk], concentrations: List[IndustryConcentration]
    ) -> StressTestResult:
        total_value = sum(p.quantity * p.current_price for p in positions_risk)
        if total_value <= 0:
            return StressTestResult()

        market_scenarios = []
        for shock_pct, name in [(-0.10, "市场下跌10%"), (-0.20, "市场下跌20%"), (-0.30, "市场下跌30%")]:
            estimated_loss = sum(
                p.quantity * p.current_price * p.beta * abs(shock_pct)
                for p in positions_risk if p.beta > 0
            )
            if estimated_loss == 0:
                estimated_loss = total_value * abs(shock_pct)
            market_scenarios.append(StressScenario(
                name=name,
                description=f"假设沪深300{shock_pct:.0%}，按Beta估算组合损失",
                market_shock=shock_pct,
                estimated_loss=estimated_loss,
                estimated_loss_pct=estimated_loss / total_value,
            ))

        industry_scenarios = []
        top_industries = sorted(concentrations, key=lambda c: c.allocation_pct, reverse=True)[:3]
        for conc in top_industries:
            if conc.allocation_pct < 0.15:
                continue
            industry_loss = sum(
                p.quantity * p.current_price * 0.20
                for p in positions_risk
                if (p.industry or "未知") == conc.industry
            )
            other_loss = sum(
                p.quantity * p.current_price * 0.05
                for p in positions_risk
                if (p.industry or "未知") != conc.industry
            )
            total_loss = industry_loss + other_loss
            industry_scenarios.append(StressScenario(
                name=f"{conc.industry}行业冲击",
                description=f"假设{conc.industry}行业下跌20%，其他行业下跌5%",
                market_shock=-0.20,
                estimated_loss=total_loss,
                estimated_loss_pct=total_loss / total_value,
            ))

        liquidity_crisis = None
        high_liquidity = [p for p in positions_risk if p.liquidity_days > 5]
        if high_liquidity:
            slippage_loss = sum(p.quantity * p.current_price * 0.05 for p in high_liquidity)
            liquidity_crisis = StressScenario(
                name="流动性危机",
                description=f"{len(high_liquidity)}只持仓流动性不足(>5天)，假设5%滑点损失",
                market_shock=-0.05,
                estimated_loss=slippage_loss,
                estimated_loss_pct=slippage_loss / total_value,
            )

        return StressTestResult(
            scenarios=market_scenarios,
            industry_shock=industry_scenarios,
            liquidity_crisis=liquidity_crisis,
        )

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
        if hasattr(portfolio_risk, 'high_correlation_pairs') and portfolio_risk.high_correlation_pairs:
            for pair in portfolio_risk.high_correlation_pairs[:3]:
                recommendations.append(
                    f"【注意】{pair['code_1']}与{pair['code_2']}相关性较高({pair['correlation']:.2f})，分散化效果有限"
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
            var_99 = await self._calculate_position_var_99(code)
            kline_data = await asyncio.to_thread(
                self._get_kline_data, self._normalize_code(code), self.LOOKBACK_DAYS
            )
            returns = self._calculate_returns(kline_data)
            expected_shortfall = self._calculate_expected_shortfall(returns)
            volatility = self._calculate_volatility(returns)
            max_drawdown = self._calculate_max_drawdown(kline_data)
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            beta = await self._calculate_beta(code)
            position_value = quantity * current_price
            liquidity_days = self._calculate_liquidity_days(kline_data, position_value)
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
                    var_99=var_99,
                    expected_shortfall=expected_shortfall,
                    volatility=volatility,
                    max_drawdown=max_drawdown,
                    sharpe_ratio=sharpe_ratio,
                    beta=beta,
                    liquidity_days=liquidity_days,
                    marginal_var=0.0,
                )
            )

        concentrations = await self._calculate_industry_concentrations(holdings, price_fetcher)
        portfolio_var = await self._calculate_portfolio_var(holdings, price_fetcher)
        portfolio_var_99 = await self._calculate_portfolio_var_99(holdings, price_fetcher)
        total_value = sum(p.quantity * p.current_price for p in positions_risk)
        total_cost = sum(p.quantity * p.cost_price for p in positions_risk)
        var_warning = portfolio_var > self.VAR_THRESHOLD
        concentration_warning = any(
            c.allocation_pct > self.INDUSTRY_CONCENTRATION_THRESHOLD
            for c in concentrations
        )
        concentration_score = self._calculate_concentration_score(positions_risk)
        corr_matrix, corr_labels, high_corr_pairs = await self._calculate_correlation_matrix(holdings)
        portfolio_returns = self._calculate_portfolio_returns(positions_risk)
        portfolio_es = self._calculate_expected_shortfall(portfolio_returns)
        portfolio_vol = self._calculate_volatility(portfolio_returns)
        portfolio_mdd = self._calculate_portfolio_max_drawdown(positions_risk)
        portfolio_sharpe = self._calculate_sharpe_ratio(portfolio_returns)
        portfolio_beta = self._calculate_weighted_beta(positions_risk)
        liquidity_risk = self._calculate_portfolio_liquidity_risk(positions_risk)

        portfolio_risk = PortfolioRisk(
            total_value=total_value,
            total_cost=total_cost,
            portfolio_var_95=portfolio_var,
            industry_concentrations=concentrations,
            var_warning=var_warning,
            concentration_warning=concentration_warning,
            var_99=portfolio_var_99,
            expected_shortfall=portfolio_es,
            volatility=portfolio_vol,
            max_drawdown=portfolio_mdd,
            sharpe_ratio=portfolio_sharpe,
            beta=portfolio_beta,
            concentration_score=concentration_score,
            liquidity_risk=liquidity_risk,
            style_exposure={},
            correlation_matrix=corr_matrix,
            correlation_labels=corr_labels,
            high_correlation_pairs=high_corr_pairs,
        )

        stress_test = self._calculate_stress_test(positions_risk, concentrations)

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
            stress_test=stress_test,
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
                        "var_99": p.var_99,
                        "expected_shortfall": p.expected_shortfall,
                        "volatility": p.volatility,
                        "max_drawdown": p.max_drawdown,
                        "sharpe_ratio": p.sharpe_ratio,
                        "beta": p.beta,
                        "liquidity_days": p.liquidity_days,
                        "marginal_var": p.marginal_var,
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
                    "var_99": report.portfolio_risk.var_99,
                    "expected_shortfall": report.portfolio_risk.expected_shortfall,
                    "volatility": report.portfolio_risk.volatility,
                    "max_drawdown": report.portfolio_risk.max_drawdown,
                    "sharpe_ratio": report.portfolio_risk.sharpe_ratio,
                    "beta": report.portfolio_risk.beta,
                    "concentration_score": report.portfolio_risk.concentration_score,
                    "liquidity_risk": report.portfolio_risk.liquidity_risk,
                    "style_exposure": report.portfolio_risk.style_exposure,
                    "correlation_matrix": report.portfolio_risk.correlation_matrix,
                    "correlation_labels": report.portfolio_risk.correlation_labels,
                    "high_correlation_pairs": report.portfolio_risk.high_correlation_pairs,
                },
                "recommendations": report.recommendations,
                "stress_test": {
                    "scenarios": [
                        {
                            "name": s.name,
                            "description": s.description,
                            "market_shock": s.market_shock,
                            "estimated_loss": s.estimated_loss,
                            "estimated_loss_pct": s.estimated_loss_pct,
                        }
                        for s in report.stress_test.scenarios
                    ] if report.stress_test else [],
                    "industry_shock": [
                        {
                            "name": s.name,
                            "description": s.description,
                            "market_shock": s.market_shock,
                            "estimated_loss": s.estimated_loss,
                            "estimated_loss_pct": s.estimated_loss_pct,
                        }
                        for s in report.stress_test.industry_shock
                    ] if report.stress_test else [],
                    "liquidity_crisis": {
                        "name": report.stress_test.liquidity_crisis.name,
                        "description": report.stress_test.liquidity_crisis.description,
                        "market_shock": report.stress_test.liquidity_crisis.market_shock,
                        "estimated_loss": report.stress_test.liquidity_crisis.estimated_loss,
                        "estimated_loss_pct": report.stress_test.liquidity_crisis.estimated_loss_pct,
                    } if report.stress_test and report.stress_test.liquidity_crisis else None,
                } if report.stress_test else None,
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

    async def get_trend_data(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        try:
            collection = self._get_risk_collection()
            from_date = (datetime.now() - timedelta(days=days + 5)).strftime("%Y-%m-%d")
            cursor = await asyncio.to_thread(
                lambda: list(
                    collection.find({"user_id": user_id, "date": {"$gte": from_date}})
                    .sort("date", 1)
                )
            )
            result = {
                "dates": [],
                "risk_score": [],
                "var_95": [],
                "var_99": [],
                "max_drawdown": [],
                "sharpe_ratio": [],
                "concentration_score": [],
            }
            for doc in cursor:
                result["dates"].append(doc.get("date", ""))
                result["risk_score"].append(doc.get("risk_score", 0))
                pr = doc.get("portfolio_risk", {})
                result["var_95"].append(pr.get("portfolio_var_95", 0))
                result["var_99"].append(pr.get("var_99", 0))
                result["max_drawdown"].append(pr.get("max_drawdown", 0))
                result["sharpe_ratio"].append(pr.get("sharpe_ratio", 0))
                result["concentration_score"].append(pr.get("concentration_score", 0))
            return result
        except Exception as e:
            logger.error(f"Failed to get trend data: {e}")
            return {"dates": [], "risk_score": [], "var_95": [], "var_99": [], "max_drawdown": [], "sharpe_ratio": [], "concentration_score": []}

    def close(self):
        if self._storage:
            self._storage.close()
        logger.info("RiskReportGenerator storage connection closed")
