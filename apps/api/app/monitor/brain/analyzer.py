import logging
from typing import Dict, Any, List
from .models import BrainDecision
from .capital_flow import CapitalFlowAnalyzer
from .sentiment import SentimentAnalyzer

logger = logging.getLogger(__name__)

class BrainAnalyzer:
    """大脑分析器 - 综合多维度分析"""
    
    def __init__(self):
        self.capital_analyzer = CapitalFlowAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def analyze(self, code: str, technical_data: Dict[str, Any], current_price: float = 0.0) -> BrainDecision:
        """
        综合分析股票
        Args:
            code: 股票代码
            technical_data: 技术指标数据
            current_price: 当前价格
        Returns:
            大脑决策
        """
        try:
            # 1. 获取多维度数据
            capital_data = self.capital_analyzer.analyze(code)
            sentiment_data = self.sentiment_analyzer.analyze(code)
            
            # 2. 计算各维度得分
            technical_score = self._calculate_technical_score(technical_data)
            capital_score = self._calculate_capital_score(capital_data)
            sentiment_score = sentiment_data.get("score", 0.5)
            
            # 3. 综合评分 (技术50%, 资金30%, 情绪20%)
            total_score = (technical_score * 0.5 + capital_score * 0.3 + sentiment_score * 0.2)
            
            # 4. 确定操作类型
            action = self._determine_action(total_score, technical_data)
            
            # 5. 计算价格目标
            price_targets = self._calculate_price_targets(code, current_price, technical_data)
            
            # 6. 生成决策原因
            reasons = self._generate_reasons(technical_score, capital_score, sentiment_score, technical_data, capital_data)
            
            return BrainDecision(
                code=code,
                action=action,
                confidence=abs(total_score - 0.5) * 2,  # 转换为0-1的置信度
                target_price=price_targets["target"],
                entry_price=price_targets["entry"],
                stop_loss=price_targets["stop_loss"],
                reasons=reasons
            )
            
        except Exception as e:
            logger.error(f"Error in brain analysis for {code}: {e}")
            # 返回默认决策
            return BrainDecision(
                code=code,
                action="hold",
                confidence=0.5,
                target_price=current_price,
                entry_price=current_price,
                stop_loss=current_price * 0.9,
                reasons=[f"分析出错: {str(e)}"]
            )
    
    def _calculate_technical_score(self, technical_data: Dict[str, Any]) -> float:
        """计算技术指标得分 (0-1)"""
        try:
            scores = []
            
            # RSI得分
            rsi = technical_data.get("rsi", 50.0)
            if rsi < 30:
                scores.append(0.8)  # 超卖，买入信号
            elif rsi > 70:
                scores.append(0.2)  # 超买，卖出信号
            else:
                scores.append(0.5)  # 中性
            
            # MACD得分
            macd = technical_data.get("macd", {})
            macd_value = macd.get("macd", 0.0)
            signal_value = macd.get("signal", 0.0)
            histogram = macd.get("histogram", 0.0)
            
            if macd_value > signal_value and histogram > 0:
                scores.append(0.7)  # 金叉，买入信号
            elif macd_value < signal_value and histogram < 0:
                scores.append(0.3)  # 死叉，卖出信号
            else:
                scores.append(0.5)
            
            # KDJ得分
            kdj = technical_data.get("kdj", {})
            k_value = kdj.get("k", 50.0)
            if k_value < 20:
                scores.append(0.8)
            elif k_value > 80:
                scores.append(0.2)
            else:
                scores.append(0.5)
            
            # 平均得分
            return sum(scores) / len(scores) if scores else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating technical score: {e}")
            return 0.5
    
    def _calculate_capital_score(self, capital_data: Dict[str, Any]) -> float:
        """计算资金流向得分 (0-1)"""
        try:
            net_inflow = capital_data.get("net_inflow", 0)
            trend_score = capital_data.get("trend_score", 0.5)
            
            # 净流入为正，得分高
            if net_inflow > 0:
                return min(0.8, trend_score)
            else:
                return max(0.2, 1 - abs(trend_score))
                
        except Exception as e:
            logger.error(f"Error calculating capital score: {e}")
            return 0.5
    
    def _determine_action(self, total_score: float, technical_data: Dict[str, Any]) -> str:
        """确定操作类型"""
        # 结合技术指标的极端情况
        rsi = technical_data.get("rsi", 50.0)
        
        if total_score > 0.7 or rsi < 25:
            return "buy"
        elif total_score < 0.3 or rsi > 75:
            return "sell"
        else:
            return "hold"
    
    def _calculate_price_targets(self, code: str, current_price: float, technical_data: Dict[str, Any]) -> Dict[str, float]:
        """计算价格目标"""
        try:
            # 使用布林带计算支撑和阻力
            bollinger = technical_data.get("bollinger", {})
            upper = bollinger.get("upper", current_price * 1.1)
            lower = bollinger.get("lower", current_price * 0.9)
            middle = bollinger.get("middle", current_price)
            
            # 如果没有布林带数据，使用默认计算
            if upper == 0 or lower == 0:
                upper = current_price * 1.15
                lower = current_price * 0.85
                middle = current_price
            
            return {
                "target": upper,  # 目标价：布林带上轨
                "entry": lower,   # 入场价：布林带下轨
                "stop_loss": current_price * 0.9  # 止损：当前价的90%
            }
            
        except Exception as e:
            logger.error(f"Error calculating price targets for {code}: {e}")
            return {
                "target": current_price * 1.1,
                "entry": current_price * 0.95,
                "stop_loss": current_price * 0.9
            }
    
    def _generate_reasons(self, tech_score: float, capital_score: float, sentiment_score: float, 
                         technical_data: Dict[str, Any], capital_data: Dict[str, Any]) -> List[str]:
        """生成决策原因"""
        reasons = []
        
        # 技术指标原因
        rsi = technical_data.get("rsi", 50.0)
        if rsi < 30:
            reasons.append(f"RSI({rsi:.1f})超卖，存在反弹机会")
        elif rsi > 70:
            reasons.append(f"RSI({rsi:.1f})超买，存在回调风险")
        
        macd = technical_data.get("macd", {})
        if macd.get("macd", 0) > macd.get("signal", 0):
            reasons.append("MACD金叉，动量向上")
        else:
            reasons.append("MACD死叉，动量向下")
        
        # 资金流向原因
        trend = capital_data.get("主力动向", "未知")
        if trend == "流入":
            reasons.append("主力资金流入")
        elif trend == "流出":
            reasons.append("主力资金流出")
        
        # 综合评分
        total_score = (tech_score * 0.5 + capital_score * 0.3 + sentiment_score * 0.2)
        reasons.append(f"综合评分: {total_score:.2f}")
        
        return reasons
    
    def close(self):
        """关闭资源"""
        try:
            self.capital_analyzer.close()
            self.sentiment_analyzer.close()
        except Exception as e:
            logger.error(f"Error closing brain analyzer resources: {e}")
