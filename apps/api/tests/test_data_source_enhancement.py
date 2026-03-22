import pytest
from app.data_source.manager import DataSourceManager
from app.data_source.models import MarketBreadth, CorrelatedAssets, StockKLine


class TestDataSourceEnhancement:
    """数据源增强测试"""

    def test_manager_has_new_methods(self):
        dm = DataSourceManager()
        assert hasattr(dm, "get_market_breadth")
        assert hasattr(dm, "get_correlated_assets")
        assert hasattr(dm, "get_minute_kline")

    def test_market_breadth_fallback_on_error(self):
        dm = DataSourceManager()
        result = dm.get_market_breadth(provider="nonexistent")
        assert result is None

    def test_correlated_assets_fallback_on_error(self):
        dm = DataSourceManager()
        result = dm.get_correlated_assets(provider="nonexistent")
        assert result is None or isinstance(result, CorrelatedAssets)

    def test_minute_kline_fallback_on_error(self):
        dm = DataSourceManager()
        result = dm.get_minute_kline("INVALID_CODE", frequency="5")
        assert result == []
