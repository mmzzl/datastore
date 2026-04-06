"""
AI Analyzer

Analyzes stock selection results using LLM to generate investment insights.
"""

import json
import logging
from typing import Dict, List, Any, Optional

from ..schemas.stock_selection import (
    StockSelectionTask,
    SelectionAIResult,
    StockAIAnalysis,
    MarketTrendData,
)
from ..collector.llm_client import LLMClient

logger = logging.getLogger(__name__)


STOCK_ANALYSIS_PROMPT = """你是一位专业的A股投资顾问，拥有丰富的技术分析和行业研究经验。
请根据以下选股结果，生成详细的投资分析报告。

## 选股信息
- 选股策略: {strategy_name}
- 股票池: {stock_pool}
- 选股日期: {date}
- 选出股票数量: {selected_count}只

## 市场趋势数据
{market_trend_data}

## 选出的股票详情
{stocks_detail}

## 行业分类数据
{industry_data}

请按以下JSON结构返回分析结果：
{{
  "market_trend": {{
    "direction": "看多/看空/震荡",
    "strength": "强/中/弱",
    "analysis": "市场趋势分析(50字以内，结合金叉比例、多头排列比例等技术指标)"
  }},
  "stock_analyses": [
    {{
      "code": "股票代码",
      "name": "股票名称",
      "sector": "所属行业(证监会分类简化名称，如'银行'、'白酒'、'电力'等)",
      "sector_features": "该行业近期特征描述(30字以内，包括行业走势、资金流向、政策影响等)",
      "risk_factors": ["风险1", "风险2", "风险3"],
      "operation_suggestion": "具体操作建议(50字以内，包括入场时机、仓位建议、止盈止损参考)",
      "brief_analysis": "技术面简要分析(30字以内)"
    }}
  ],
  "summary": "本次选股整体分析(50字以内，包括选出股票的行业分布、整体技术特征)",
  "sector_overview": "选出股票所属行业的整体特征分析(80字以内，包括行业轮动情况、资金偏好等)",
  "market_risk": "当前市场环境下的主要风险提示(50字以内)"
}}

## 分析要求

### 1. 市场趋势判断（核心指标）
根据提供的市场趋势数据分析当前市场强弱：

**金叉判断标准：**
- MACD金叉：MACD线上穿信号线
- MA金叉：短期均线上穿长期均线（如MA5上穿MA10、MA10上穿MA20）

**多头排列判断标准：**
- 完整多头排列：MA5 > MA10 > MA20
- 部分多头排列：至少满足MA5 > MA10

**趋势强弱参考：**
| 指标 | 看多信号占比 | 市场判断 |
|------|-------------|---------|
| 金叉比例 | > 60% | 强势市场 |
| 金叉比例 | 40%-60% | 震荡偏强 |
| 金叉比例 | < 40% | 弱势市场 |
| 多头排列比例 | > 50% | 趋势向上 |
| 多头排列比例 | 30%-50% | 结构分化 |
| 多头排列比例 | < 30% | 趋势向下 |

**综合判断逻辑：**
- 金叉比例 > 60% 且 多头排列 > 50% → 强势看多
- 金叉比例 40%-60% 且 多头排列 30%-50% → 震荡偏强
- 金叉比例 < 40% 或 多头排列 < 30% → 弱势震荡或看空

### 2. 板块特征分析
- 使用提供的行业分类数据识别每只股票所属行业
- 分析该行业近期表现：走势、资金流向、与大盘联动性
- 关注行业政策面和消息面影响
- 结合市场趋势判断行业的相对强弱

### 3. 风险提示（每只股票列出2-3条）
- **技术面风险**：压力位、量价背离、超买超卖、均线压力等
- **基本面风险**：估值水平、业绩预期、财务健康度等
- **市场环境风险**：大盘走势、政策变化、行业周期等
- **特别注意**：如果市场趋势判断为弱势，需重点提示系统性风险

### 4. 操作建议（每只股票）
- **入场时机**：回调位置、突破确认、支撑位参考
- **仓位建议**：首次仓位、是否分批建仓（弱势市场建议轻仓）
- **止盈止损**：具体价位或百分比参考
- **市场联动**：结合市场趋势给出差异化建议（强势可激进，弱势需谨慎）

### 5. 格式要求
- 所有文字简洁专业，避免空泛表述
- 风险提示具体化，不要泛泛而谈
- 操作建议可执行，给出明确参考价位
- 市场趋势判断要有数据支撑
- 只返回JSON，无其他内容

请开始分析："""


class AIAnalyzer:
    """
    AI Analyzer for stock selection results.

    Uses LLM to generate investment insights including:
    - Sector characteristics
    - Risk factors
    - Operation suggestions
    - Market trend analysis
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize AIAnalyzer.

        Args:
            llm_client: LLM client for API calls
        """
        self.llm_client = llm_client

    def analyze_selection(
        self,
        task: StockSelectionTask,
        market_trend: MarketTrendData,
    ) -> Optional[SelectionAIResult]:
        """
        Analyze selection results using LLM.

        Args:
            task: Selection task with results
            market_trend: Market trend analysis data

        Returns:
            SelectionAIResult or None if analysis fails
        """
        if not task.results:
            logger.warning("No results to analyze")
            return None

        try:
            # Build prompt
            prompt = self._build_prompt(task, market_trend)

            # Call LLM
            response = self.llm_client.chat(prompt)

            # Parse response
            ai_result = self._parse_response(response, task.results)

            logger.info(f"AI analysis completed for task {task.id}")
            return ai_result

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return None

    def _build_prompt(
        self,
        task: StockSelectionTask,
        market_trend: MarketTrendData,
    ) -> str:
        """
        Build analysis prompt.

        Args:
            task: Selection task
            market_trend: Market trend data

        Returns:
            Formatted prompt string
        """
        # Market trend data
        market_data = self._format_market_trend(market_trend)

        # Stock details
        stocks_detail = self._format_stocks_detail(task.results)

        # Industry data
        industry_data = self._format_industry_data(task.results)

        # Strategy name
        strategy_name = task.strategy_type
        if task.plugin_id:
            strategy_name = f"插件策略({task.plugin_id[:8]})"

        return STOCK_ANALYSIS_PROMPT.format(
            strategy_name=strategy_name,
            stock_pool=task.stock_pool.value,
            date=task.created_at.strftime("%Y-%m-%d"),
            selected_count=len(task.results),
            market_trend_data=market_data,
            stocks_detail=stocks_detail,
            industry_data=industry_data,
        )

    def _format_market_trend(self, trend: MarketTrendData) -> str:
        """Format market trend data for prompt."""
        return f"""总股票数: {trend.total_stocks}
MACD金叉: {trend.macd_golden_cross_count}只 ({trend.macd_golden_cross_ratio}%)
均线金叉: {trend.ma_golden_cross_count}只 ({trend.ma_golden_cross_ratio}%)
完整多头排列: {trend.full_bullish_alignment_count}只 ({trend.full_bullish_alignment_ratio}%)
部分多头排列: {trend.partial_bullish_alignment_count}只 ({trend.partial_bullish_alignment_ratio}%)
RSI分布: 超卖{trend.rsi_oversold_count}只 | 中性{trend.rsi_neutral_count}只 | 超买{trend.rsi_overbought_count}只
趋势判断: {trend.trend_direction} ({trend.trend_strength})"""

    def _format_stocks_detail(self, results: List[Any]) -> str:
        """Format stock details for prompt."""
        details = []
        for r in results[:20]:  # Limit to top 20
            ind = r.indicators
            detail = {
                "code": r.code,
                "name": r.name,
                "score": r.score,
                "signal_strength": r.signal_strength,
                "industry": r.industry,
                "indicators": {
                    "ma5": ind.ma5,
                    "ma10": ind.ma10,
                    "ma20": ind.ma20,
                    "rsi": ind.rsi,
                    "macd": ind.macd,
                    "macd_hist": ind.macd_hist,
                }
            }
            details.append(detail)
        return json.dumps(details, ensure_ascii=False, indent=2)

    def _format_industry_data(self, results: List[Any]) -> str:
        """Format industry data for prompt."""
        industries = {}
        for r in results:
            if r.industry and r.industry not in industries:
                industries[r.industry] = {"stocks": [], "avg_score": 0}
            if r.industry:
                industries[r.industry]["stocks"].append(r.code)
                industries[r.industry]["avg_score"] = sum(
                    x.score for x in results if x.industry == r.industry
                ) / len([x for x in results if x.industry == r.industry])
        return json.dumps(industries, ensure_ascii=False, indent=2)

    def _parse_response(
        self,
        response: str,
        results: List[Any],
    ) -> SelectionAIResult:
        """
        Parse LLM response into SelectionAIResult.

        Args:
            response: LLM response string
            results: Original selection results

        Returns:
            SelectionAIResult object
        """
        try:
            # Extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON found in response")

            json_str = response[start:end]
            data = json.loads(json_str)

            # Parse stock analyses
            stock_analyses = []
            for sa in data.get("stock_analyses", []):
                stock_analyses.append(StockAIAnalysis(
                    code=sa.get("code", ""),
                    name=sa.get("name", ""),
                    sector=sa.get("sector", ""),
                    sector_features=sa.get("sector_features", ""),
                    risk_factors=sa.get("risk_factors", []),
                    operation_suggestion=sa.get("operation_suggestion", ""),
                    brief_analysis=sa.get("brief_analysis", ""),
                ))

            return SelectionAIResult(
                stock_analyses=stock_analyses,
                summary=data.get("summary", ""),
                sector_overview=data.get("sector_overview", ""),
                market_risk=data.get("market_risk", ""),
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return SelectionAIResult(
                summary="AI分析结果解析失败",
                sector_overview="",
                market_risk="",
            )
