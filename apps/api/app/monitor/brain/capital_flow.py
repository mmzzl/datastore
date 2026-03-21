import logging
from typing import Dict, Any
from datetime import datetime, timedelta

from app.data_source import DataSourceManager

logger = logging.getLogger(__name__)


class CapitalFlowAnalyzer:
    """主力资金流向分析器 - 使用统一数据源接口"""

    def __init__(self, data_manager: DataSourceManager = None):
        self.data_manager = data_manager or DataSourceManager()

    def analyze(self, code: str, days: int = 5) -> Dict[str, Any]:
        """
        分析股票资金流向（从市场排名中查找特定股票）

        Args:
            code: 股票代码
            days: 分析天数，用于限制返回的市场排名数量

        Returns:
            资金流向分析结果
        """
        try:
            # 使用统一接口获取市场资金流向排名数据
            # 注意：这里不再使用code参数获取个股数据，而是获取市场排名数据
            market_flow_data = self.data_manager.get_capital_flow(
                code="",  # 传入空字符串，实际不影响市场排名查询
                days=days,  # days参数用于限制返回的排名数量
            )

            if not market_flow_data:
                logger.warning(f"No market capital flow data found")
                return self._get_mock_data(code)

            # 在市场排名数据中查找匹配的股票代码
            # 处理code格式：可能是"sh.600000"或"600000"格式
            target_code = code.split(".")[-1] if "." in code else code

            stock_data = None
            for item in market_flow_data:
                if item.get("code") == target_code:
                    stock_data = item
                    break

            if not stock_data:
                logger.warning(
                    f"No capital flow data found for stock {target_code} in market ranking"
                )
                return self._get_mock_data(code)

            # 提取股票的资金流入净额
            net_inflow = stock_data.get("net_inflow", 0)

            # 判断主力动向
            if net_inflow > 0:
                trend = "流入"
                trend_score = min(0.8, net_inflow / 1000000)  # 转换为合理的得分范围
            else:
                trend = "流出"
                trend_score = max(0.2, 1 - abs(net_inflow) / 1000000)

            return {
                "net_inflow": net_inflow,
                "主力动向": trend,
                "trend_score": trend_score,
                "data_points": 1,  # 只找到一只股票的数据
                "serial": stock_data.get("serial", 0),
                "price": stock_data.get("price", 0),
                "change_pct": stock_data.get("change_pct", 0),
                "turnover_rate": stock_data.get("turnover_rate", 0),
            }

        except Exception as e:
            logger.error(f"Error analyzing capital flow for {code}: {e}")
            return self._get_mock_data(code)

    def _get_mock_data(self, code: str) -> Dict[str, Any]:
        """获取模拟数据（用于测试或数据缺失时）"""
        logger.info(f"Using mock capital flow data for {code}")
        return {
            "net_inflow": 0.0,
            "主力动向": "未知",
            "trend_score": 0.5,
            "data_points": 0,
            "is_mock": True,
        }
