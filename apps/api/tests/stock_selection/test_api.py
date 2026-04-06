"""Integration tests for Stock Selection API endpoints."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from fastapi.testclient import TestClient

from app.schemas.stock_selection import (
    StockPoolType,
    SelectionStatus,
    StockSelectionTask,
    SelectionStockResult,
    StockIndicator,
    MarketTrendData,
)


class TestStockSelectionAPI:
    """Tests for Stock Selection API endpoints."""

    @pytest.fixture
    def mock_engine(self):
        """Create mock selection engine."""
        engine = MagicMock()

        # Mock get_task
        sample_task = StockSelectionTask(
            id='test-task-id',
            strategy_type='ma_cross',
            strategy_params={'fast_period': 5, 'slow_period': 20},
            stock_pool=StockPoolType.HS300,
            status=SelectionStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            results=[
                SelectionStockResult(
                    code='600519',
                    name='贵州茅台',
                    score=85.0,
                    signal_type='buy',
                    signal_strength='强',
                    confidence=0.85,
                    indicators=StockIndicator(ma5=1856.2, rsi=58.2),
                    industry='白酒'
                )
            ],
            market_trend=MarketTrendData(
                total_stocks=300,
                macd_golden_cross_count=156,
                macd_golden_cross_ratio=52.0,
                trend_direction='震荡',
                trend_strength='中'
            ),
            total_stocks=300,
            selected_count=1
        )
        engine.get_task.return_value = sample_task

        # Mock get_history
        engine.get_history.return_value = {
            'items': [
                {
                    'id': 'test-task-id',
                    'task_id': 'test-task-id',
                    'strategy_type': 'ma_cross',
                    'stock_pool': 'hs300',
                    'created_at': '2024-01-01T10:00:00',
                    'selected_count': 1,
                    'status': 'completed'
                }
            ],
            'total': 1,
            'page': 1,
            'page_size': 20
        }

        return engine

    @pytest.fixture
    def mock_pool_service(self):
        """Create mock stock pool service."""
        service = MagicMock()
        service.get_codes.side_effect = lambda pool: {
            'hs300': ['600519', '000858'],
            'zz500': ['000001', '000002'],
            'all': ['600519', '000858', '000001', '000002']
        }.get(pool, [])
        return service

    def test_get_stock_pools(self, client, mock_auth):
        """Test GET /api/stock-selection/pools endpoint."""
        response = client.get('/stock-selection/pools')

        assert response.status_code == 200
        data = response.json()
        assert 'pools' in data
        assert len(data['pools']) == 3

        # Check pool structure
        pool = data['pools'][0]
        assert 'id' in pool
        assert 'name' in pool
        assert 'count' in pool
        assert 'description' in pool

    def test_get_history(self, client, mock_auth, mock_engine):
        """Test GET /api/stock-selection/history endpoint."""
        with patch('app.api.endpoints.stock_selection.get_selection_engine', return_value=mock_engine):
            response = client.get('/api/stock-selection/history')

            assert response.status_code == 200
            data = response.json()
            assert 'items' in data
            assert 'total' in data
            assert 'page' in data
            assert 'page_size' in data

    def test_get_history_with_filters(self, client, mock_auth, mock_engine):
        """Test GET /api/stock-selection/history with filters."""
        with patch('app.api.endpoints.stock_selection.get_selection_engine', return_value=mock_engine):
            response = client.get(
                '/api/stock-selection/history',
                params={'status': 'completed', 'stock_pool': 'hs300'}
            )

            assert response.status_code == 200
            mock_engine.get_history.assert_called()

    def test_get_history_pagination(self, client, mock_auth, mock_engine):
        """Test GET /api/stock-selection/history pagination."""
        with patch('app.api.endpoints.stock_selection.get_selection_engine', return_value=mock_engine):
            response = client.get(
                '/api/stock-selection/history',
                params={'page': 2, 'page_size': 10}
            )

            assert response.status_code == 200

    def test_get_selection_result(self, client, mock_auth, mock_engine):
        """Test GET /api/stock-selection/{task_id} endpoint."""
        with patch('app.api.endpoints.stock_selection.get_selection_engine', return_value=mock_engine):
            response = client.get('/api/stock-selection/test-task-id')

            assert response.status_code == 200
            data = response.json()
            assert data['task_id'] == 'test-task-id'
            assert data['strategy_type'] == 'ma_cross'
            assert data['stock_pool'] == 'hs300'
            assert data['status'] == 'completed'
            assert len(data['results']) == 1

    def test_get_selection_result_not_found(self, client, mock_auth, mock_engine):
        """Test GET /api/stock-selection/{task_id} with non-existent task."""
        mock_engine.get_task.return_value = None

        with patch('app.api.endpoints.stock_selection.get_selection_engine', return_value=mock_engine):
            response = client.get('/api/stock-selection/nonexistent-id')

            assert response.status_code == 404

    def test_run_selection_invalid_strategy(self, client, mock_auth):
        """Test POST /api/stock-selection/run with invalid strategy."""
        response = client.post(
            '/api/stock-selection/run',
            json={
                'strategy_type': 'invalid_strategy',
                'stock_pool': 'hs300'
            }
        )

        assert response.status_code == 400

    def test_run_selection_invalid_stock_pool(self, client, mock_auth):
        """Test POST /api/stock-selection/run with invalid stock pool."""
        response = client.post(
            '/api/stock-selection/run',
            json={
                'strategy_type': 'ma_cross',
                'stock_pool': 'invalid_pool'
            }
        )

        assert response.status_code == 400

    def test_run_selection_plugin_without_id(self, client, mock_auth):
        """Test POST /api/stock-selection/run with plugin strategy but no plugin_id."""
        response = client.post(
            '/api/stock-selection/run',
            json={
                'strategy_type': 'plugin',
                'stock_pool': 'hs300'
            }
        )

        assert response.status_code == 400
        assert 'plugin_id' in response.json()['detail'].lower()

    def test_unauthorized_access(self, client):
        """Test that endpoints require authentication."""
        endpoints = [
            ('GET', '/api/stock-selection/pools'),
            ('GET', '/api/stock-selection/history'),
            ('GET', '/api/stock-selection/test-id'),
        ]

        for method, endpoint in endpoints:
            if method == 'GET':
                response = client.get(endpoint)
            assert response.status_code == 401


class TestStockSelectionPermissions:
    """Tests for permission checks on Stock Selection API."""

    def test_run_selection_requires_permission(self, client):
        """Test run selection requires selection:run permission."""
        response = client.post(
            '/api/stock-selection/run',
            json={
                'strategy_type': 'ma_cross',
                'stock_pool': 'hs300'
            }
        )
        # Should return 401 if not authenticated, or 403 if authenticated but no permission
        assert response.status_code in [401, 403]

    def test_view_result_requires_permission(self, client):
        """Test view result requires selection:view permission."""
        response = client.get('/api/stock-selection/test-task-id')
        assert response.status_code in [401, 403]

    def test_view_history_requires_permission(self, client):
        """Test view history requires selection:view permission."""
        response = client.get('/stock-selection/history')
        assert response.status_code in [401, 403]

    def test_view_pools_requires_permission(self, client):
        """Test view pools requires selection:view permission."""
        response = client.get('/stock-selection/pools')
        assert response.status_code in [401, 403]


class TestStockSelectionResponseModels:
    """Tests for response model serialization."""

    def test_stock_result_item_structure(self, client, mock_auth, mock_engine):
        """Test StockResultItem response structure."""
        with patch('app.api.endpoints.stock_selection.get_selection_engine', return_value=mock_engine):
            response = client.get('/api/stock-selection/test-task-id')
            data = response.json()

            # Check result item structure
            result = data['results'][0]
            assert 'code' in result
            assert 'name' in result
            assert 'score' in result
            assert 'signal_type' in result
            assert 'signal_strength' in result
            assert 'confidence' in result
            assert 'industry' in result
            assert 'indicators' in result

    def test_market_trend_structure(self, client, mock_auth, mock_engine):
        """Test MarketTrendItem response structure."""
        with patch('app.api.endpoints.stock_selection.get_selection_engine', return_value=mock_engine):
            response = client.get('/api/stock-selection/test-task-id')
            data = response.json()

            # Check market trend structure
            mt = data['market_trend']
            assert 'total_stocks' in mt
            assert 'macd_golden_cross_count' in mt
            assert 'macd_golden_cross_ratio' in mt
            assert 'trend_direction' in mt
            assert 'trend_strength' in mt
