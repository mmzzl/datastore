"""Unit tests for StockPoolService."""

import pytest
import pandas as pd
import tempfile
import os
from unittest.mock import patch, MagicMock

from app.stock_selection.stock_pool import StockPoolService


class TestStockPoolService:
    """Tests for StockPoolService class."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory with test CSV files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create HS300 test data
            hs300_df = pd.DataFrame({
                'code': ['000001', '000002', '600000'],
                'name': ['平安银行', '万科A', '浦发银行']
            })
            hs300_df.to_csv(os.path.join(tmpdir, 'hs300_stocks.csv'), index=False)

            # Create ZZ500 test data
            zz500_df = pd.DataFrame({
                'code': ['000003', '000004', '600001'],
                'name': ['股票A', '股票B', '股票C']
            })
            zz500_df.to_csv(os.path.join(tmpdir, 'zz500_stocks.csv'), index=False)

            # Create industry test data
            industry_df = pd.DataFrame({
                'code': ['sh.000001', 'sh.000002', 'sh.600000'],
                'code_name': ['平安银行', '万科A', '浦发银行'],
                'industry': ['J66货币金融服务', 'K70房地产业', 'J66货币金融服务']
            })
            industry_df.to_csv(os.path.join(tmpdir, 'stock_industry.csv'), index=False)

            yield tmpdir

    def test_load_hs300_pool(self, temp_data_dir):
        """Test loading HS300 stock pool."""
        service = StockPoolService(data_dir=temp_data_dir)
        codes = service.get_codes('hs300')

        assert len(codes) == 3
        assert '000001' in codes
        assert '000002' in codes
        assert '600000' in codes

    def test_load_zz500_pool(self, temp_data_dir):
        """Test loading ZZ500 stock pool."""
        service = StockPoolService(data_dir=temp_data_dir)
        codes = service.get_codes('zz500')

        assert len(codes) == 3
        assert '000003' in codes

    def test_load_all_pool(self, temp_data_dir):
        """Test loading all market pool (combined HS300 + ZZ500)."""
        service = StockPoolService(data_dir=temp_data_dir)
        codes = service.get_codes('all')

        # Should have 6 unique stocks (combined)
        assert len(codes) == 6

    def test_cache_ttl(self, temp_data_dir):
        """Test that caching works with TTL."""
        service = StockPoolService(data_dir=temp_data_dir)

        # First call loads from file
        codes1 = service.get_codes('hs300')

        # Second call should use cache
        codes2 = service.get_codes('hs300')

        assert codes1 == codes2
        assert 'hs300' in service._pool_cache
        assert 'hs300' in service._pool_cache_time

    def test_clear_cache(self, temp_data_dir):
        """Test cache clearing."""
        service = StockPoolService(data_dir=temp_data_dir)

        # Load data
        service.get_codes('hs300')
        assert 'hs300' in service._pool_cache

        # Clear cache
        service.clear_cache()
        assert 'hs300' not in service._pool_cache

    def test_load_industry_map(self, temp_data_dir):
        """Test loading industry classification map."""
        service = StockPoolService(data_dir=temp_data_dir)
        industry_map = service.load_industry_map()

        assert len(industry_map) == 3
        # Check industry simplification
        assert industry_map.get('000001') == '银行'
        assert industry_map.get('000002') == '房地产'

    def test_get_industry(self, temp_data_dir):
        """Test getting industry for a specific code."""
        service = StockPoolService(data_dir=temp_data_dir)
        service.load_industry_map()

        industry = service.get_industry('000001')
        assert industry == '银行'

        # Test with prefix
        industry = service.get_industry('sh.000001')
        assert industry == '银行'

    def test_get_stock_name(self, temp_data_dir):
        """Test getting stock name."""
        service = StockPoolService(data_dir=temp_data_dir)
        service.load_name_map()

        name = service.get_stock_name('000001')
        assert name == '平安银行'

    def test_invalid_pool_type(self, temp_data_dir):
        """Test handling invalid pool type."""
        service = StockPoolService(data_dir=temp_data_dir)
        codes = service.get_codes('invalid_pool')
        assert codes == []

    def test_missing_csv_file(self, temp_data_dir):
        """Test handling missing CSV file."""
        service = StockPoolService(data_dir=temp_data_dir)

        # Remove the file
        os.remove(os.path.join(temp_data_dir, 'hs300_stocks.csv'))

        codes = service.get_codes('hs300')
        assert codes == []

    def test_simplify_industry(self, temp_data_dir):
        """Test industry name simplification."""
        service = StockPoolService(data_dir=temp_data_dir)

        # Test various industry codes
        assert service._simplify_industry('J66货币金融服务') == '银行'
        assert service._simplify_industry('C15酒、饮料和精制茶制造业') == '白酒'
        assert service._simplify_industry('C27医药制造业') == '医药'
