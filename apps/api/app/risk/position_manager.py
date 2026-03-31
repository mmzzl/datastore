import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..core.config import settings
from ..storage.mongo_client import MongoStorage
from .risk_report import RiskReportGenerator

logger = logging.getLogger(__name__)


@dataclass
class PositionSizeValidation:
    valid: bool
    current_allocation: float
    new_allocation: float
    max_allowed: float
    warning: Optional[str] = None


@dataclass
class IndustryConcentrationValidation:
    valid: bool
    current_concentration: float
    new_concentration: float
    max_allowed: float
    warning: Optional[str] = None


@dataclass
class PositionSizingRecommendation:
    recommended_size: float
    max_allowed: float
    current_allocation: float
    available_capacity: float
    warnings: List[str] = field(default_factory=list)


@dataclass
class PositionRiskMetrics:
    code: str
    position_var: float
    position_risk_score: int
    industry_concentration_pct: float


class PositionManager:
    MAX_POSITION_SIZE_PCT = 0.10
    MAX_INDUSTRY_CONCENTRATION_PCT = 0.30

    def __init__(self, storage: Optional[MongoStorage] = None):
        self._storage = storage
        self._holdings_collection = None
        self._risk_generator = RiskReportGenerator(storage)

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

    def _get_holdings_collection(self):
        storage = self._get_storage()
        if self._holdings_collection is None:
            self._holdings_collection = storage.db.get_collection("holdings")
        return self._holdings_collection

    async def _get_portfolio_value(
        self,
        positions: List[Dict[str, Any]],
        price_fetcher: Callable[[str], float],
    ) -> float:
        total_value = 0.0
        for pos in positions:
            code = pos.get("code", "")
            quantity = pos.get("quantity", 0)
            if quantity > 0:
                price = price_fetcher(code)
                total_value += quantity * price
        return total_value

    async def _get_industry_for_code(self, code: str) -> str:
        storage = self._get_storage()
        try:
            stock_info_coll = storage.db.get_collection("stock_info")
            doc = await asyncio.to_thread(stock_info_coll.find_one, {"code": code})
            if doc:
                return doc.get("industry") or "未知"
        except Exception as e:
            logger.warning(f"Failed to get industry for {code}: {e}")
        return "未知"

    async def validate_position_size(
        self,
        user_id: str,
        code: str,
        quantity: float,
        price: float,
        price_fetcher: Callable[[str], float],
        is_add: bool = True,
    ) -> PositionSizeValidation:
        holdings = await self.get_holdings(user_id)
        portfolio_value = await self._get_portfolio_value(holdings, price_fetcher)
        new_position_value = quantity * price
        existing_position = next(
            (p for p in holdings if p.get("code") == code), None
        )
        existing_value = 0.0
        if existing_position:
            existing_qty = existing_position.get("quantity", 0)
            existing_price = price_fetcher(code)
            existing_value = existing_qty * existing_price
        if is_add:
            total_position_value = existing_value + new_position_value
        else:
            total_position_value = new_position_value
        if portfolio_value <= 0:
            current_allocation = 0.0
            new_allocation = 1.0 if new_position_value > 0 else 0.0
        else:
            current_allocation = existing_value / portfolio_value if existing_value > 0 else 0.0
            new_allocation = total_position_value / portfolio_value
        max_allowed_value = portfolio_value * self.MAX_POSITION_SIZE_PCT
        warning = None
        valid = new_allocation <= self.MAX_POSITION_SIZE_PCT
        if not valid:
            warning = (
                f"Position size {new_allocation:.1%} exceeds max allowed "
                f"{self.MAX_POSITION_SIZE_PCT:.0%} of portfolio"
            )
            logger.warning(
                f"Position size validation failed for {code}: "
                f"new_allocation={new_allocation:.1%}, max_allowed={self.MAX_POSITION_SIZE_PCT:.0%}"
            )
        return PositionSizeValidation(
            valid=valid,
            current_allocation=current_allocation,
            new_allocation=new_allocation,
            max_allowed=self.MAX_POSITION_SIZE_PCT,
            warning=warning,
        )

    async def validate_industry_concentration(
        self,
        user_id: str,
        code: str,
        quantity: float,
        price: float,
        price_fetcher: Callable[[str], float],
        is_add: bool = True,
    ) -> IndustryConcentrationValidation:
        holdings = await self.get_holdings(user_id)
        portfolio_value = await self._get_portfolio_value(holdings, price_fetcher)
        if portfolio_value <= 0:
            return IndustryConcentrationValidation(
                valid=True,
                current_concentration=0.0,
                new_concentration=0.0,
                max_allowed=self.MAX_INDUSTRY_CONCENTRATION_PCT,
            )
        target_industry = await self._get_industry_for_code(code)
        industry_value = 0.0
        for pos in holdings:
            pos_code = pos.get("code", "")
            pos_qty = pos.get("quantity", 0)
            if pos_qty <= 0:
                continue
            pos_industry = await self._get_industry_for_code(pos_code)
            if pos_industry == target_industry:
                pos_price = price_fetcher(pos_code)
                industry_value += pos_qty * pos_price
        current_concentration = industry_value / portfolio_value
        new_position_value = quantity * price
        if is_add:
            new_industry_value = industry_value + new_position_value
        else:
            existing_pos = next((p for p in holdings if p.get("code") == code), None)
            existing_qty = existing_pos.get("quantity", 0) if existing_pos else 0
            existing_price = price_fetcher(code)
            existing_value = existing_qty * existing_price
            new_industry_value = industry_value - existing_value + new_position_value
        new_concentration = new_industry_value / portfolio_value
        warning = None
        valid = new_concentration <= self.MAX_INDUSTRY_CONCENTRATION_PCT
        if not valid:
            warning = (
                f"Industry '{target_industry}' concentration {new_concentration:.1%} "
                f"exceeds max allowed {self.MAX_INDUSTRY_CONCENTRATION_PCT:.0%}"
            )
            logger.warning(
                f"Industry concentration validation failed for {code}: "
                f"industry={target_industry}, new_concentration={new_concentration:.1%}, "
                f"max_allowed={self.MAX_INDUSTRY_CONCENTRATION_PCT:.0%}"
            )
        return IndustryConcentrationValidation(
            valid=valid,
            current_concentration=current_concentration,
            new_concentration=new_concentration,
            max_allowed=self.MAX_INDUSTRY_CONCENTRATION_PCT,
            warning=warning,
        )

    async def recommend_position_size(
        self,
        user_id: str,
        code: str,
        target_allocation: float,
        price: float,
        price_fetcher: Callable[[str], float],
    ) -> PositionSizingRecommendation:
        warnings = []
        holdings = await self.get_holdings(user_id)
        portfolio_value = await self._get_portfolio_value(holdings, price_fetcher)
        if portfolio_value <= 0:
            return PositionSizingRecommendation(
                recommended_size=0,
                max_allowed=0,
                current_allocation=0,
                available_capacity=0,
                warnings=["Portfolio has no value"],
            )
        existing_position = next(
            (p for p in holdings if p.get("code") == code), None
        )
        existing_qty = existing_position.get("quantity", 0) if existing_position else 0
        existing_price = price_fetcher(code) if existing_qty > 0 else 0
        existing_value = existing_qty * existing_price
        current_allocation = existing_value / portfolio_value
        max_allowed_value = portfolio_value * self.MAX_POSITION_SIZE_PCT
        max_allowed_qty = max_allowed_value / price if price > 0 else 0
        target_industry = await self._get_industry_for_code(code)
        industry_value = 0.0
        for pos in holdings:
            pos_code = pos.get("code", "")
            if pos_code == code:
                continue
            pos_qty = pos.get("quantity", 0)
            if pos_qty <= 0:
                continue
            pos_industry = await self._get_industry_for_code(pos_code)
            if pos_industry == target_industry:
                pos_price = price_fetcher(pos_code)
                industry_value += pos_qty * pos_price
        current_industry_concentration = industry_value / portfolio_value
        max_industry_capacity = (
            self.MAX_INDUSTRY_CONCENTRATION_PCT - current_industry_concentration
        ) * portfolio_value
        max_position_capacity = max_allowed_value - existing_value
        available_capacity = min(max_position_capacity, max_industry_capacity)
        if available_capacity <= 0:
            warnings.append(
                f"No capacity available. Position limit or industry concentration "
                f"limit already reached."
            )
            recommended_size = 0
        else:
            target_value = portfolio_value * min(target_allocation, self.MAX_POSITION_SIZE_PCT)
            target_value = min(target_value, available_capacity)
            recommended_size = target_value / price if price > 0 else 0
            if target_allocation > self.MAX_POSITION_SIZE_PCT:
                warnings.append(
                    f"Target allocation {target_allocation:.1%} exceeds max "
                    f"{self.MAX_POSITION_SIZE_PCT:.0%}, capping at limit"
                )
        if current_industry_concentration + (recommended_size * price / portfolio_value) > self.MAX_INDUSTRY_CONCENTRATION_PCT:
            warnings.append(
                f"Recommended size may breach industry concentration limit "
                f"for '{target_industry}'"
            )
        return PositionSizingRecommendation(
            recommended_size=recommended_size,
            max_allowed=max_allowed_qty,
            current_allocation=current_allocation,
            available_capacity=available_capacity,
            warnings=warnings,
        )

    async def get_holdings(self, user_id: str) -> List[Dict[str, Any]]:
        collection = self._get_holdings_collection()
        try:
            doc = await asyncio.to_thread(
                collection.find_one, {"user_id": user_id}
            )
            if doc:
                return doc.get("positions", [])
            return []
        except Exception as e:
            logger.error(f"Failed to get holdings for user {user_id}: {e}")
            return []

    async def update_position_notes(
        self,
        user_id: str,
        code: str,
        notes: Optional[str] = None,
    ) -> bool:
        collection = self._get_holdings_collection()
        try:
            result = await asyncio.to_thread(
                collection.update_one,
                {"user_id": user_id, "positions.code": code},
                {"$set": {"positions.$.notes": notes, "updated_at": datetime.now()}},
            )
            if result.matched_count == 0:
                await asyncio.to_thread(
                    collection.update_one,
                    {"user_id": user_id},
                    {
                        "$push": {
                            "positions": {
                                "code": code,
                                "quantity": 0,
                                "average_cost": 0,
                                "notes": notes,
                                "tags": [],
                            }
                        },
                        "$set": {"updated_at": datetime.now()},
                    },
                    upsert=True,
                )
            logger.info(f"Updated notes for {code} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update notes for {code}: {e}")
            return False

    async def update_position_tags(
        self,
        user_id: str,
        code: str,
        tags: List[str],
    ) -> bool:
        collection = self._get_holdings_collection()
        try:
            result = await asyncio.to_thread(
                collection.update_one,
                {"user_id": user_id, "positions.code": code},
                {"$set": {"positions.$.tags": tags, "updated_at": datetime.now()}},
            )
            if result.matched_count == 0:
                await asyncio.to_thread(
                    collection.update_one,
                    {"user_id": user_id},
                    {
                        "$push": {
                            "positions": {
                                "code": code,
                                "quantity": 0,
                                "average_cost": 0,
                                "notes": None,
                                "tags": tags,
                            }
                        },
                        "$set": {"updated_at": datetime.now()},
                    },
                    upsert=True,
                )
            logger.info(f"Updated tags for {code} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update tags for {code}: {e}")
            return False

    async def get_position_tags(self, user_id: str, code: str) -> List[str]:
        holdings = await self.get_holdings(user_id)
        position = next((p for p in holdings if p.get("code") == code), None)
        if position:
            return position.get("tags", [])
        return []

    async def get_position_notes(self, user_id: str, code: str) -> Optional[str]:
        holdings = await self.get_holdings(user_id)
        position = next((p for p in holdings if p.get("code") == code), None)
        if position:
            return position.get("notes")
        return None

    async def calculate_position_risk_metrics(
        self,
        user_id: str,
        code: str,
        price_fetcher: Callable[[str], float],
    ) -> PositionRiskMetrics:
        holdings = await self.get_holdings(user_id)
        position = next((p for p in holdings if p.get("code") == code), None)
        if not position:
            return PositionRiskMetrics(
                code=code,
                position_var=0.0,
                position_risk_score=0,
                industry_concentration_pct=0.0,
            )
        quantity = position.get("quantity", 0)
        if quantity <= 0:
            return PositionRiskMetrics(
                code=code,
                position_var=0.0,
                position_risk_score=0,
                industry_concentration_pct=0.0,
            )
        position_var = await self._risk_generator._calculate_position_var(code)
        portfolio_value = await self._get_portfolio_value(holdings, price_fetcher)
        position_value = quantity * price_fetcher(code)
        industry = await self._get_industry_for_code(code)
        industry_value = 0.0
        for pos in holdings:
            pos_code = pos.get("code", "")
            pos_qty = pos.get("quantity", 0)
            if pos_qty <= 0:
                continue
            pos_industry = await self._get_industry_for_code(pos_code)
            if pos_industry == industry:
                pos_price = price_fetcher(pos_code)
                industry_value += pos_qty * pos_price
        industry_concentration_pct = (
            industry_value / portfolio_value if portfolio_value > 0 else 0.0
        )
        cost_price = position.get("average_cost", 0)
        current_price = price_fetcher(code)
        pnl_pct = (current_price - cost_price) / cost_price if cost_price > 0 else 0
        var_contribution = position_value * position_var / portfolio_value if portfolio_value > 0 else 0
        risk_score = self._risk_generator._calculate_position_risk_score(
            pnl_pct, position_var, var_contribution
        )
        return PositionRiskMetrics(
            code=code,
            position_var=position_var,
            position_risk_score=risk_score,
            industry_concentration_pct=industry_concentration_pct,
        )

    async def enhance_holdings_with_risk(
        self,
        user_id: str,
        price_fetcher: Callable[[str], float],
    ) -> List[Dict[str, Any]]:
        holdings = await self.get_holdings(user_id)
        enhanced_holdings = []
        for holding in holdings:
            code = holding.get("code", "")
            enhanced = dict(holding)
            try:
                metrics = await self.calculate_position_risk_metrics(
                    user_id, code, price_fetcher
                )
                enhanced["position_var"] = metrics.position_var
                enhanced["position_risk_score"] = metrics.position_risk_score
                enhanced["industry_concentration_pct"] = metrics.industry_concentration_pct
            except Exception as e:
                logger.warning(f"Failed to calculate risk metrics for {code}: {e}")
                enhanced["position_var"] = 0.0
                enhanced["position_risk_score"] = 0
                enhanced["industry_concentration_pct"] = 0.0
            enhanced_holdings.append(enhanced)
        return enhanced_holdings

    def close(self):
        if self._risk_generator:
            self._risk_generator.close()
        if self._storage:
            self._storage.close()
            logger.info("PositionManager storage connection closed")
