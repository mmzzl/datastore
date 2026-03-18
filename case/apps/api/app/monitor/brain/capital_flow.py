import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from app.storage.mongo_client import MongoStorage
from app.core.config import settings

logger = logging.getLogger(__name__)

class CapitalFlowAnalyzer:
    """主力资金流向分析器"""
    
    def __init__(self):
        self.storage = None
        self._init_storage()
    
    def _init_storage(self):
        """初始化存储连接"""
        try:
            self.storage = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_database,
                username=settings.mongodb_username,
                password=settings.mongodb_password
            )
            self.storage.connect()
        except Exception as e:
            logger.error(f"Failed to initialize storage for capital flow: {e}")
            self.storage = None
    
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
            if not self.storage:
                return self._get_mock_data(code)
            
            # 获取资金流向数据
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            # 从MongoDB获取资金流向数据
            capital_flow_data = self.storage.get_capital_flow(
                name=code,  # 注意：这里假设name字段存储代码
                start_date=start_date,
                end_date=end_date,
                limit=days
            )
            
            if not capital_flow_data:
                logger.warning(f"No capital flow data found for {code}")
                return self._get_mock_data(code)
            
            # 计算统计指标
            net_inflows = [d.get('net_inflow', 0) for d in capital_flow_data]
            large_orders = [d.get('large_order_amount', 0) for d in capital_flow_data]
            
            avg_net_inflow = sum(net_inflows) / len(net_inflows) if net_inflows else 0
            total_large_order = sum(large_orders)
            
            # 判断主力动向
            if avg_net_inflow > 0:
                trend = "流入"
                trend_score = min(0.8, avg_net_inflow / 1000000)  # 归一化到0-0.8
            else:
                trend = "流出"
                trend_score = max(0.2, 1 - abs(avg_net_inflow) / 1000000)
            
            return {
                "net_inflow": avg_net_inflow,
                "large_order_ratio": total_large_order,
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
            "large_order_ratio": 0.0,
            "主力动向": "未知",
            "trend_score": 0.5,
            "data_points": 0,
            "is_mock": True
        }
    
    def close(self):
        """关闭连接"""
        if self.storage:
            self.storage.close()
