"""Unit tests for AIAnalyzer."""

import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.stock_selection.ai_analyzer import AIAnalyzer, STOCK_ANALYSIS_PROMPT
from app.schemas.stock_selection import (
    StockSelectionTask,
    StockPoolType,
    SelectionStatus,
    SelectionStockResult,
    StockIndicator,
    MarketTrendData,
    SelectionAIResult,
    StockAIAnalysis,
)


class TestAIAnalyzer:
    """Tests for AIAnalyzer class."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        return MagicMock()

    @pytest.fixture
    def sample_task(self):
        """Create sample selection task."""
        task = StockSelectionTask(
            id='test-task-id',
            strategy_type='ma_cross',
            strategy_params={'fast_period': 5, 'slow_period': 20},
            stock_pool=StockPoolType.HS300,
            status=SelectionStatus.COMPLETED,
            created_at=datetime.now(),
            results=[
                SelectionStockResult(
                    code='600519',
                    name='贵州茅台',
                    score=85.0,
                    signal_type='buy',
                    signal_strength='强',
                    confidence=0.85,
                    indicators=StockIndicator(
                        ma5=1856.2,
                        ma10=1832.5,
                        ma20=1798.8,
                        rsi=58.2,
                        macd=12.3,
                        macd_hist=5.6
                    ),
                    industry='白酒'
                ),
                SelectionStockResult(
                    code='000858',
                    name='五粮液',
                    score=78.0,
                    signal_type='buy',
                    signal_strength='中',
                    confidence=0.78,
                    indicators=StockIndicator(
                        ma5=156.2,
                        ma10=152.5,
                        ma20=148.8,
                        rsi=52.1,
                        macd=8.3,
                        macd_hist=3.2
                    ),
                    industry='白酒'
                )
            ],
            market_trend=MarketTrendData(
                total_stocks=300,
                macd_golden_cross_count=156,
                macd_golden_cross_ratio=52.0,
                trend_direction='震荡',
                trend_strength='中'
            )
        )
        return task

    def test_ai_analyzer_initialization(self, mock_llm_client):
        """Test AIAnalyzer initialization."""
        analyzer = AIAnalyzer(mock_llm_client)
        assert analyzer.llm_client == mock_llm_client

    def test_format_market_trend(self, mock_llm_client, sample_task):
        """Test market trend data formatting."""
        analyzer = AIAnalyzer(mock_llm_client)
        formatted = analyzer._format_market_trend(sample_task.market_trend)

        assert '总股票数: 300' in formatted
        assert 'MACD金叉: 156只' in formatted
        assert '趋势判断: 震荡' in formatted

    def test_format_stocks_detail(self, mock_llm_client, sample_task):
        """Test stock details formatting."""
        analyzer = AIAnalyzer(mock_llm_client)
        formatted = analyzer._format_stocks_detail(sample_task.results)

        # Should be valid JSON
        data = json.loads(formatted)
        assert len(data) == 2
        assert data[0]['code'] == '600519'
        assert data[0]['name'] == '贵州茅台'
        assert 'indicators' in data[0]

    def test_format_industry_data(self, mock_llm_client, sample_task):
        """Test industry data formatting."""
        analyzer = AIAnalyzer(mock_llm_client)
        formatted = analyzer._format_industry_data(sample_task.results)

        # Should be valid JSON
        data = json.loads(formatted)
        assert '白酒' in data

    def test_build_prompt(self, mock_llm_client, sample_task):
        """Test prompt building."""
        analyzer = AIAnalyzer(mock_llm_client)
        prompt = analyzer._build_prompt(sample_task, sample_task.market_trend)

        # Check prompt contains expected sections
        assert '选股策略: ma_cross' in prompt
        assert '股票池: hs300' in prompt
        assert '市场趋势数据' in prompt
        assert '选出的股票详情' in prompt
        assert '行业分类数据' in prompt

    def test_parse_response_success(self, mock_llm_client, sample_task):
        """Test successful response parsing."""
        analyzer = AIAnalyzer(mock_llm_client)

        # Create mock response
        response = json.dumps({
            "stock_analyses": [
                {
                    "code": "600519",
                    "name": "贵州茅台",
                    "sector": "白酒",
                    "sector_features": "白酒板块表现强劲",
                    "risk_factors": ["估值偏高", "技术压力位"],
                    "operation_suggestion": "回调至1830可轻仓介入",
                    "brief_analysis": "MACD金叉运行中"
                }
            ],
            "summary": "本次选股选出白酒板块龙头",
            "sector_overview": "白酒板块近期表现强势",
            "market_risk": "市场震荡需谨慎"
        })

        result = analyzer._parse_response(response, sample_task.results)

        assert isinstance(result, SelectionAIResult)
        assert len(result.stock_analyses) == 1
        assert result.stock_analyses[0].code == '600519'
        assert result.stock_analyses[0].sector == '白酒'
        assert len(result.stock_analyses[0].risk_factors) == 2
        assert result.summary == '本次选股选出白酒板块龙头'

    def test_parse_response_with_extra_text(self, mock_llm_client, sample_task):
        """Test parsing response with extra text around JSON."""
        analyzer = AIAnalyzer(mock_llm_client)

        # Response with extra text
        response = """
        Here is my analysis:

        {"stock_analyses": [{"code": "600519", "name": "贵州茅台", "sector": "白酒", "sector_features": "", "risk_factors": [], "operation_suggestion": "", "brief_analysis": ""}], "summary": "测试", "sector_overview": "", "market_risk": ""}

        That's my complete analysis.
        """

        result = analyzer._parse_response(response, sample_task.results)

        assert isinstance(result, SelectionAIResult)
        assert result.summary == '测试'

    def test_parse_response_invalid_json(self, mock_llm_client, sample_task):
        """Test handling of invalid JSON response."""
        analyzer = AIAnalyzer(mock_llm_client)

        response = "This is not valid JSON"
        result = analyzer._parse_response(response, sample_task.results)

        # Should return result with error message
        assert isinstance(result, SelectionAIResult)
        assert result.summary == 'AI分析结果解析失败'

    def test_analyze_selection_success(self, mock_llm_client, sample_task):
        """Test successful analysis."""
        # Mock LLM response
        mock_llm_client.chat.return_value = json.dumps({
            "stock_analyses": [
                {
                    "code": "600519",
                    "name": "贵州茅台",
                    "sector": "白酒",
                    "sector_features": "板块强势",
                    "risk_factors": ["估值风险"],
                    "operation_suggestion": "轻仓介入",
                    "brief_analysis": "技术面良好"
                }
            ],
            "summary": "选出白酒龙头",
            "sector_overview": "白酒板块强势",
            "market_risk": "震荡市风险"
        })

        analyzer = AIAnalyzer(mock_llm_client)
        result = analyzer.analyze_selection(sample_task, sample_task.market_trend)

        assert result is not None
        assert isinstance(result, SelectionAIResult)
        mock_llm_client.chat.assert_called_once()

    def test_analyze_selection_no_results(self, mock_llm_client):
        """Test analysis with no results."""
        analyzer = AIAnalyzer(mock_llm_client)

        task = StockSelectionTask(
            id='empty-task',
            strategy_type='ma_cross',
            results=[],
            market_trend=MarketTrendData()
        )

        result = analyzer.analyze_selection(task, task.market_trend)
        assert result is None

    def test_analyze_selection_llm_error(self, mock_llm_client, sample_task):
        """Test handling LLM API error."""
        mock_llm_client.chat.side_effect = Exception("API Error")

        analyzer = AIAnalyzer(mock_llm_client)
        result = analyzer.analyze_selection(sample_task, sample_task.market_trend)

        # Should return None on error
        assert result is None

    def test_stock_ai_analysis_to_dict(self):
        """Test StockAIAnalysis.to_dict method."""
        analysis = StockAIAnalysis(
            code='600519',
            name='贵州茅台',
            sector='白酒',
            sector_features='白酒板块强势',
            risk_factors=['估值偏高', '技术压力'],
            operation_suggestion='回调介入',
            brief_analysis='MACD金叉'
        )

        result = analysis.to_dict()

        assert result['code'] == '600519'
        assert result['sector'] == '白酒'
        assert len(result['risk_factors']) == 2

    def test_selection_ai_result_to_dict(self):
        """Test SelectionAIResult.to_dict method."""
        result = SelectionAIResult(
            stock_analyses=[
                StockAIAnalysis(code='600519', name='茅台', sector='白酒')
            ],
            summary='整体分析',
            sector_overview='板块概况',
            market_risk='风险提示'
        )

        result_dict = result.to_dict()

        assert result_dict['summary'] == '整体分析'
        assert result_dict['sector_overview'] == '板块概况'
        assert len(result_dict['stock_analyses']) == 1

    def test_prompt_template_structure(self):
        """Test that prompt template has required sections."""
        # Check prompt has all required sections
        assert '市场趋势判断' in STOCK_ANALYSIS_PROMPT
        assert '板块特征分析' in STOCK_ANALYSIS_PROMPT
        assert '风险提示' in STOCK_ANALYSIS_PROMPT
        assert '操作建议' in STOCK_ANALYSIS_PROMPT
        assert '金叉比例' in STOCK_ANALYSIS_PROMPT
        assert '多头排列' in STOCK_ANALYSIS_PROMPT
