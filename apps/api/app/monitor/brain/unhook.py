import logging
from typing import Dict, Any
from .models import UnhookStrategy

logger = logging.getLogger(__name__)

class UnhookEngine:
    """解套策略引擎"""
    
    def calculate_strategy(self, code: str, current_price: float, cost_price: float, 
                          hold_days: int = 0, market_condition: str = "normal") -> UnhookStrategy:
        """
        计算解套策略
        Args:
            code: 股票代码
            current_price: 当前价格
            cost_price: 持仓成本
            hold_days: 持仓天数
            market_condition: 市场环境 (bull/bear/normal)
        Returns:
            解套策略
        """
        try:
            if cost_price <= 0:
                return UnhookStrategy(
                    code=code,
                    current_price=current_price,
                    cost_price=cost_price,
                    suggestion="无法计算解套策略，持仓成本无效",
                    details={"error": "invalid_cost_price"}
                )
            
            loss_rate = (cost_price - current_price) / cost_price
            
            # 根据亏损程度和市场环境制定策略
            if loss_rate < 0.05:
                # 轻微亏损
                suggestion = "持有观察"
                details = {
                    "action": "hold",
                    "reason": "亏损较小，继续观察",
                    "next_check": "3个交易日"
                }
                expected_time = "1-2周"
                
            elif loss_rate < 0.15:
                # 中等亏损 - 高抛低吸做T
                suggestion = "高抛低吸做T"
                buy_price = current_price * 0.98
                sell_price = current_price * 1.02
                details = {
                    "action": "trade_t",
                    "buy_price": round(buy_price, 2),
                    "sell_price": round(sell_price, 2),
                    "reason": "利用波动降低成本",
                    "target_reduction": f"{loss_rate * 0.3:.1%}"
                }
                expected_time = "2-4周"
                
            elif loss_rate < 0.30:
                # 较大亏损 - 补仓摊平
                suggestion = "补仓摊平"
                buy_price = current_price * 0.95
                buy_ratio = 0.5  # 补仓50%
                new_cost_price = (cost_price + buy_price * buy_ratio) / (1 + buy_ratio)
                
                details = {
                    "action": "buy",
                    "buy_price": round(buy_price, 2),
                    "percentage": buy_ratio,
                    "new_cost_price": round(new_cost_price, 2),
                    "reason": "低位补仓，摊平成本",
                    "expected_reduction": f"{(cost_price - new_cost_price) / cost_price:.1%}"
                }
                expected_time = "1-3个月"
                
            elif loss_rate < 0.50:
                # 严重亏损 - 分析基本面，考虑换股
                suggestion = "分析基本面，考虑换股"
                details = {
                    "action": "research",
                    "steps": [
                        "1. 分析公司基本面是否恶化",
                        "2. 对比同行业其他股票",
                        "3. 考虑是否换到更有潜力的股票",
                        "4. 如决定换股，选择合适时机"
                    ],
                    "reason": "亏损较大，需要重新评估投资逻辑"
                }
                expected_time = "3-6个月"
                
            else:
                # 巨额亏损 - 止损或长期持有
                if market_condition == "bear":
                    suggestion = "止损离场"
                    details = {
                        "action": "stop_loss",
                        "stop_price": current_price,
                        "reason": "熊市环境，止损避免更大损失"
                    }
                else:
                    suggestion = "长期持有等待解套"
                    details = {
                        "action": "hold_long",
                        "reason": "亏损过大，等待市场回暖或公司基本面改善",
                        "suggestions": [
                            "定期关注公司财报",
                            "关注行业政策变化",
                            "考虑分批补仓（如果资金允许）"
                        ]
                    }
                expected_time = "6个月以上"
            
            return UnhookStrategy(
                code=code,
                current_price=current_price,
                cost_price=cost_price,
                suggestion=suggestion,
                details=details,
                expected_recovery_time=expected_time
            )
            
        except Exception as e:
            logger.error(f"Error calculating unhook strategy for {code}: {e}")
            return UnhookStrategy(
                code=code,
                current_price=current_price,
                cost_price=cost_price,
                suggestion="策略计算出错",
                details={"error": str(e)}
            )
    
    def get_recovery_probability(self, code: str, current_price: float, cost_price: float, 
                                hold_days: int = 0) -> Dict[str, Any]:
        """
        计算解套概率
        Args:
            code: 股票代码
            current_price: 当前价格
            cost_price: 持仓成本
            hold_days: 持仓天数
        Returns:
            解套概率分析
        """
        try:
            loss_rate = (cost_price - current_price) / cost_price
            
            # 基于历史数据的解套概率（简化模型）
            if loss_rate < 0.1:
                probability = 0.8  # 80%概率解套
                timeframe = "1个月内"
            elif loss_rate < 0.2:
                probability = 0.6
                timeframe = "3个月内"
            elif loss_rate < 0.3:
                probability = 0.4
                timeframe = "6个月内"
            elif loss_rate < 0.5:
                probability = 0.2
                timeframe = "1年内"
            else:
                probability = 0.1
                timeframe = "1年以上"
            
            # 考虑持仓时间因素
            if hold_days > 180:  # 超过半年
                probability *= 0.9  # 稍微降低概率
                
            return {
                "probability": round(probability, 2),
                "timeframe": timeframe,
                "loss_rate": round(loss_rate, 4),
                "suggestion": "积极采取解套策略" if probability > 0.5 else "考虑止损或换股"
            }
            
        except Exception as e:
            logger.error(f"Error calculating recovery probability for {code}: {e}")
            return {
                "probability": 0.5,
                "timeframe": "未知",
                "loss_rate": 0.0,
                "error": str(e)
            }
