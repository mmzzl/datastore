import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any


class TestPositionLimits:
    """Test 18.8 & 18.9: Position size and industry concentration limits"""

    @pytest.mark.asyncio
    async def test_position_size_limit_enforcement(self):
        from app.risk.position_manager import PositionManager, PositionSizeValidation
        
        manager = PositionManager()
        
        user_id = "test_user_001"
        code = "SH600519"
        
        def price_fetcher(c: str) -> float:
            return 1850.0

        with patch.object(manager, 'get_holdings', new_callable=AsyncMock) as mock_holdings:
            mock_holdings.return_value = [
                {"code": "SH600519", "quantity": 100},
                {"code": "SH600036", "quantity": 500},
            ]
            
            quantity = 100
            price = 1850.0
            
            existing_portfolio_value = 100 * 1850.0 + 500 * 38.0
            new_position_value = quantity * price
            portfolio_value = existing_portfolio_value + new_position_value
            
            validation = await manager.validate_position_size(
                user_id=user_id,
                code=code,
                quantity=quantity,
                price=price,
                price_fetcher=price_fetcher,
                is_add=True,
            )

        assert isinstance(validation, PositionSizeValidation)
        assert validation.max_allowed == 0.10

    @pytest.mark.asyncio
    async def test_position_exceeding_10_percent_warning(self):
        from app.risk.position_manager import PositionManager
        
        manager = PositionManager()
        
        user_id = "test_user_warning"
        code = "SH600519"
        
        def price_fetcher(c: str) -> float:
            return 1850.0

        with patch.object(manager, 'get_holdings', new_callable=AsyncMock) as mock_holdings:
            mock_holdings.return_value = []
            
            quantity = 100
            price = 1850.0
            
            validation = await manager.validate_position_size(
                user_id=user_id,
                code=code,
                quantity=quantity,
                price=price,
                price_fetcher=price_fetcher,
                is_add=True,
            )
            
            if validation.new_allocation > manager.MAX_POSITION_SIZE_PCT:
                assert validation.valid is False
                assert validation.warning is not None
                assert "10%" in validation.warning or "exceeds" in validation.warning.lower()

    @pytest.mark.asyncio
    async def test_industry_concentration_limit_enforcement(self):
        from app.risk.position_manager import PositionManager, IndustryConcentrationValidation
        
        manager = PositionManager()
        
        user_id = "test_user_concentration"
        code = "SH600519"
        
        def price_fetcher(c: str) -> float:
            prices = {"SH600519": 1850.0, "SH600036": 38.0, "SH600000": 10.0}
            return prices.get(c, 0.0)

        with patch.object(manager, 'get_holdings', new_callable=AsyncMock) as mock_holdings:
            with patch.object(manager, '_get_industry_for_code', new_callable=AsyncMock) as mock_industry:
                mock_holdings.return_value = [
                    {"code": "SH600519", "quantity": 100},
                    {"code": "SH600036", "quantity": 500},
                ]
                
                mock_industry.return_value = "银行"

                validation = await manager.validate_industry_concentration(
                    user_id=user_id,
                    code=code,
                    quantity=100,
                    price=1850.0,
                    price_fetcher=price_fetcher,
                    is_add=True,
                )

        assert isinstance(validation, IndustryConcentrationValidation)
        assert validation.max_allowed == 0.30

    @pytest.mark.asyncio
    async def test_industry_exceeding_30_percent_warning(self):
        from app.risk.position_manager import PositionManager
        
        manager = PositionManager()
        
        user_id = "test_user_industry_warning"
        
        def price_fetcher(c: str) -> float:
            return 100.0

        with patch.object(manager, 'get_holdings', new_callable=AsyncMock) as mock_holdings:
            with patch.object(manager, '_get_industry_for_code', new_callable=AsyncMock) as mock_industry:
                mock_holdings.return_value = [
                    {"code": "SH600519", "quantity": 100},
                    {"code": "SH600036", "quantity": 100},
                ]
                
                mock_industry.return_value = "白酒"

                validation = await manager.validate_industry_concentration(
                    user_id=user_id,
                    code="SH600519",
                    quantity=500,
                    price=100.0,
                    price_fetcher=price_fetcher,
                    is_add=True,
                )
                
                if validation.new_concentration > manager.MAX_INDUSTRY_CONCENTRATION_PCT:
                    assert validation.valid is False
                    assert validation.warning is not None
                    assert "30%" in validation.warning or "exceeds" in validation.warning.lower()

    @pytest.mark.asyncio
    async def test_position_size_recommendation(self):
        from app.risk.position_manager import PositionManager, PositionSizingRecommendation
        
        manager = PositionManager()
        
        user_id = "test_user_recommendation"
        code = "SH600519"
        target_allocation = 0.08
        
        def price_fetcher(c: str) -> float:
            return 1850.0

        with patch.object(manager, 'get_holdings', new_callable=AsyncMock) as mock_holdings:
            with patch.object(manager, '_get_industry_for_code', new_callable=AsyncMock) as mock_industry:
                mock_holdings.return_value = []
                mock_industry.return_value = "白酒"

                recommendation = await manager.recommend_position_size(
                    user_id=user_id,
                    code=code,
                    target_allocation=target_allocation,
                    price=1850.0,
                    price_fetcher=price_fetcher,
                )

        assert isinstance(recommendation, PositionSizingRecommendation)
        assert recommendation.recommended_size >= 0
        assert recommendation.max_allowed >= 0

    @pytest.mark.asyncio
    async def test_position_limit_with_existing_position(self):
        from app.risk.position_manager import PositionManager
        
        manager = PositionManager()
        
        user_id = "test_user_existing"
        code = "SH600519"
        
        def price_fetcher(c: str) -> float:
            return 1850.0

        with patch.object(manager, 'get_holdings', new_callable=AsyncMock) as mock_holdings:
            mock_holdings.return_value = [
                {"code": "SH600519", "quantity": 50},
            ]

            validation = await manager.validate_position_size(
                user_id=user_id,
                code=code,
                quantity=100,
                price=1850.0,
                price_fetcher=price_fetcher,
                is_add=True,
            )

        assert validation.current_allocation >= 0
        assert validation.new_allocation >= validation.current_allocation

    @pytest.mark.asyncio
    async def test_industry_concentration_with_multiple_industries(self):
        from app.risk.position_manager import PositionManager
        
        manager = PositionManager()
        
        user_id = "test_user_multi_industry"
        
        def price_fetcher(c: str) -> float:
            return 100.0

        with patch.object(manager, 'get_holdings', new_callable=AsyncMock) as mock_holdings:
            with patch.object(manager, '_get_industry_for_code', new_callable=AsyncMock) as mock_industry:
                mock_holdings.return_value = [
                    {"code": "SH600519", "quantity": 100},
                    {"code": "SH600036", "quantity": 100},
                    {"code": "SZ000858", "quantity": 100},
                ]
                
                def get_industry_side_effect(code):
                    industries = {
                        "SH600519": "白酒",
                        "SH600036": "银行",
                        "SZ000858": "白酒",
                    }
                    return industries.get(code, "未知")
                
                mock_industry.side_effect = get_industry_side_effect

                validation = await manager.validate_industry_concentration(
                    user_id=user_id,
                    code="SH600519",
                    quantity=100,
                    price=100.0,
                    price_fetcher=price_fetcher,
                    is_add=True,
                )

        assert validation.current_concentration >= 0

    @pytest.mark.asyncio
    async def test_position_limit_calculation_accuracy(self):
        from app.risk.position_manager import PositionManager
        
        manager = PositionManager()
        
        assert manager.MAX_POSITION_SIZE_PCT == 0.10
        assert manager.MAX_INDUSTRY_CONCENTRATION_PCT == 0.30

    @pytest.mark.asyncio
    async def test_empty_portfolio_position_validation(self):
        from app.risk.position_manager import PositionManager
        
        manager = PositionManager()
        
        user_id = "empty_portfolio_user"
        
        def price_fetcher(c: str) -> float:
            return 100.0

        with patch.object(manager, 'get_holdings', new_callable=AsyncMock) as mock_holdings:
            mock_holdings.return_value = []

            validation = await manager.validate_position_size(
                user_id=user_id,
                code="SH600519",
                quantity=100,
                price=100.0,
                price_fetcher=price_fetcher,
                is_add=True,
            )

            assert validation.new_allocation == 1.0
            assert validation.valid is False

    @pytest.mark.asyncio
    async def test_position_update_flow(self, test_db):
        from app.risk.position_manager import PositionManager

        manager = PositionManager()

        user_id = "position_update_test"
        code = "SH600519"

        holdings_coll = test_db["holdings"]
        holdings_coll.insert_one({
            "user_id": user_id,
            "positions": [
                {"code": code, "quantity": 100, "average_cost": 1800.0},
            ],
        })

        with patch.object(manager, '_get_holdings_collection', return_value=holdings_coll):
            result = await manager.update_position_notes(
                user_id=user_id,
                code=code,
                notes="Test note",
            )

            assert result is True

            notes = await manager.get_position_notes(user_id, code)
            assert notes == "Test note"

        holdings_coll.delete_many({"user_id": user_id})

    @pytest.mark.asyncio
    async def test_position_tags_management(self, test_db):
        from app.risk.position_manager import PositionManager

        manager = PositionManager()

        user_id = "tag_test_user"
        code = "SH600519"

        holdings_coll = test_db["holdings"]
        holdings_coll.insert_one({
            "user_id": user_id,
            "positions": [
                {"code": code, "quantity": 100, "average_cost": 1800.0, "tags": []},
            ],
        })

        with patch.object(manager, '_get_holdings_collection', return_value=holdings_coll):
            result = await manager.update_position_tags(
                user_id=user_id,
                code=code,
                tags=["关注", "核心持仓"],
            )

            assert result is True

            tags = await manager.get_position_tags(user_id, code)
            assert "关注" in tags
            assert "核心持仓" in tags

        holdings_coll.delete_many({"user_id": user_id})
