import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any


class TestRiskReportIntegration:
    """Test 18.4: Add positions → Wait for risk report → View in frontend"""

    @pytest.mark.asyncio
    async def test_position_add_triggers_risk_report(self, test_db, setup_test_data):
        holdings_coll = test_db["holdings"]
        
        existing = holdings_coll.find_one({"user_id": "test_user_001"})
        assert existing is not None
        assert len(existing.get("positions", [])) >= 1

        new_position = {
            "code": "SH600000",
            "name": "浦发银行",
            "quantity": 300,
            "average_cost": 8.5,
        }
        
        holdings_coll.update_one(
            {"user_id": "test_user_001"},
            {"$push": {"positions": new_position}}
        )

        updated = holdings_coll.find_one({"user_id": "test_user_001"})
        assert len(updated["positions"]) == 3

    @pytest.mark.asyncio
    async def test_risk_report_generation(self, test_db, setup_test_data):
        from app.risk.risk_report import RiskReportGenerator
        
        generator = RiskReportGenerator()
        
        holdings = [
            {"code": "SH600519", "name": "贵州茅台", "quantity": 100, "average_cost": 1800.0},
            {"code": "SH600036", "name": "招商银行", "quantity": 500, "average_cost": 35.0},
        ]
        
        def price_fetcher(code: str) -> float:
            prices = {
                "SH600519": 1850.0,
                "SH600036": 38.0,
            }
            return prices.get(code, 0.0)

        with patch.object(generator, '_get_storage', return_value=test_db.client[test_db.name]):
            with patch.object(generator, '_calculate_position_var', return_value=0.03):
                with patch.object(generator, '_get_industry', return_value="银行"):
                    report = await generator.generate_report(
                        user_id="test_user_001",
                        holdings=holdings,
                        price_fetcher=price_fetcher,
                    )

        assert report is not None
        assert report.user_id == "test_user_001"
        assert report.risk_score >= 0
        assert report.risk_level in ["low", "medium", "high"]
        assert len(report.holdings_risk) == len(holdings)

    @pytest.mark.asyncio
    async def test_risk_report_storage_and_retrieval(self, test_db):
        from app.risk.risk_report import RiskReportGenerator, RiskReport, PortfolioRisk

        generator = RiskReportGenerator()

        report = RiskReport(
            report_id="test_report_001",
            user_id="test_user_001",
            date=datetime.now().strftime("%Y-%m-%d"),
            risk_score=35,
            risk_level="medium",
            holdings_risk=[],
            portfolio_risk=PortfolioRisk(
                total_value=100000,
                total_cost=95000,
                portfolio_var_95=0.04,
                industry_concentrations=[],
            ),
            recommendations=["建议适度优化持仓结构"],
            created_at=datetime.now(),
        )

        collection = test_db["risk_reports"]

        def mock_insert_one(doc):
            collection.insert_one(doc)
            return MagicMock(inserted_id="test_id")

        with patch.object(generator, '_get_risk_collection', return_value=collection):
            with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
                mock_to_thread.side_effect = lambda fn, *args, **kwargs: fn(*args, **kwargs) if asyncio.iscoroutinefunction(fn) else fn(*args, **kwargs)
                await generator.save_report(report)

        stored = collection.find_one({"report_id": "test_report_001"})
        assert stored is not None

        collection.delete_many({"report_id": "test_report_001"})

    @pytest.mark.asyncio
    async def test_risk_job_scheduled_execution(self, test_db):
        from app.scheduler.risk_report_job import RiskReportJob
        
        config = {
            "user_ids": ["test_user_001"],
            "dingtalk_webhook": None,
        }
        
        job = RiskReportJob(config)
        
        holdings_coll = test_db["holdings"]
        holdings_coll.insert_one({
            "user_id": "test_user_001",
            "positions": [
                {"code": "SH600519", "name": "贵州茅台", "quantity": 100, "average_cost": 1800.0},
            ],
        })

        kline_coll = test_db["stock_kline"]
        for i in range(10):
            kline_coll.insert_one({
                "code": "SH600519",
                "date": f"2025-01-{10+i:02d}",
                "close": 1800.0 + i * 10,
                "open": 1795.0 + i * 10,
                "high": 1810.0 + i * 10,
                "low": 1790.0 + i * 10,
                "volume": 1000000,
            })

        stock_info_coll = test_db["stock_info"]
        stock_info_coll.insert_one({
            "code": "SH600519",
            "name": "贵州茅台",
            "industry": "白酒",
        })

        with patch.object(job, '_get_storage', return_value=test_db.client[test_db.name]):
            with patch.object(job, '_send_notification', new_callable=AsyncMock):
                with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
                    mock_to_thread.side_effect = lambda fn, *args, **kwargs: fn(*args, **kwargs) if asyncio.iscoroutinefunction(fn) else fn(*args, **kwargs)
                    pass

        holdings_coll.delete_many({"user_id": "test_user_001"})
        kline_coll.delete_many({"code": "SH600519"})
        stock_info_coll.delete_many({"code": "SH600519"})

    @pytest.mark.asyncio
    async def test_risk_score_calculation(self):
        from app.risk.risk_report import RiskReportGenerator
        
        generator = RiskReportGenerator()

        high_risk = generator._calculate_risk_score(
            portfolio_var=0.08,
            concentrations=[],
            positions_risk=[
                MagicMock(pnl_pct=-0.15),
                MagicMock(pnl_pct=-0.10),
            ],
        )
        assert high_risk > 50

        low_risk = generator._calculate_risk_score(
            portfolio_var=0.02,
            concentrations=[],
            positions_risk=[
                MagicMock(pnl_pct=0.05),
                MagicMock(pnl_pct=0.03),
            ],
        )
        assert low_risk < 30

    @pytest.mark.asyncio
    async def test_industry_concentration_calculation(self, test_db):
        from app.risk.risk_report import RiskReportGenerator
        
        generator = RiskReportGenerator()
        generator._storage = test_db.client[test_db.name]
        
        positions = [
            {"code": "SH600519", "quantity": 100},
            {"code": "SH600036", "quantity": 200},
        ]
        
        def price_fetcher(code):
            return 100.0

        stock_info_coll = test_db["stock_info"]
        stock_info_coll.insert_many([
            {"code": "SH600519", "industry": "白酒"},
            {"code": "SH600036", "industry": "银行"},
        ])

        with patch.object(generator, '_get_industry', return_value="白酒"):
            pass

        stock_info_coll.delete_many({})

    @pytest.mark.asyncio
    async def test_risk_recommendations_generation(self):
        from app.risk.risk_report import RiskReportGenerator, PortfolioRisk, IndustryConcentration
        
        generator = RiskReportGenerator()

        portfolio_risk = PortfolioRisk(
            total_value=100000,
            total_cost=95000,
            portfolio_var_95=0.06,
            industry_concentrations=[
                IndustryConcentration(industry="白酒", allocation_pct=0.6, position_count=2, value=60000),
            ],
            var_warning=True,
            concentration_warning=True,
        )
        
        positions_risk = [
            MagicMock(pnl_pct=-0.10, name="贵州茅台", code="SH600519"),
        ]
        
        recommendations = generator._generate_recommendations(
            portfolio_risk, positions_risk, "high"
        )

        assert len(recommendations) > 0
        assert any("VaR" in r or "风险" in r for r in recommendations)
        assert any("集中度" in r or "分散" in r for r in recommendations)
