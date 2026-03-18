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
        分析股票资金流向
        
        Args:
            code: 股票代码
            days: 分析天数
        
        Returns:
            资金流向分析结果
        """
        try:
            # 使用统一接口获取资金流向数据
            capital_flow_data = self.data_manager.get_capital_flow(
                code=code,
                days=days
            )
            
            if not capital_flow_data:
                logger.warning(f"No capital flow data found for {code}")
                return self._get_mock_data(code)
            
            # 计算统计指标
            net_inflows = [d.get('net_inflow', 0) for d in capital_flow_data]
            
            avg_net_inflow = sum(net_inflows) / len(net_inflows) if net_inflows else 0
            
            # 判断主力动向
            if avg_net_inflow > 0:
                trend = "流入"
                trend_score = min(0.8, avg_net_inflow / 1000000)
            else:
                trend = "流出"
                trend_score = max(0.2, 1 - abs(avg_net_inflow) / 1000000)
            
            return {
                "net_inflow": avg_net_inflow,
                "主力动向": trend,
                "trend_score": trend_score,
                "data_points": len(capital_flow_data)
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
            "is_mock": True
        }
