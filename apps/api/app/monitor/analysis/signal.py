from typing import Dict, Any, Optional

class SignalGenerator:
    """信号生成器"""
    
    def __init__(self):
        pass
    
    def generate_buy_signal(self, technical_data: Dict[str, Any], stock_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成买入信号
        
        参数:
            technical_data: 技术分析数据
            stock_config: 股票配置
            
        返回:
            买入信号信息
        """
        signals = []
        signal_strength = 0
        
        # RSI信号
        rsi = technical_data.get("rsi", 50.0)
        rsi_buy_level = stock_config.get("rsi_buy_level", 30)
        if rsi < rsi_buy_level:
            signals.append(f"RSI({rsi:.2f})低于买入阈值({rsi_buy_level})")
            signal_strength += 2
        
        # MACD信号
        macd = technical_data.get("macd", {})
        macd_value = macd.get("macd", 0.0)
        signal_value = macd.get("signal", 0.0)
        histogram = macd.get("histogram", 0.0)
        if macd_value > signal_value and histogram > 0:
            signals.append("MACD金叉，价格动量向上")
            signal_strength += 2
        
        # KDJ信号
        kdj = technical_data.get("kdj", {})
        k_value = kdj.get("k", 50.0)
        d_value = kdj.get("d", 50.0)
        j_value = kdj.get("j", 50.0)
        k_buy_level = stock_config.get("k_buy_level", 20)
        if k_value < k_buy_level and j_value > k_value:
            signals.append(f"KDJ超卖，K值({k_value:.2f})低于买入阈值({k_buy_level})")
            signal_strength += 2
        
        # 布林带信号
        bollinger = technical_data.get("bollinger", {})
        upper = bollinger.get("upper", 0.0)
        middle = bollinger.get("middle", 0.0)
        lower = bollinger.get("lower", 0.0)
        current_price = stock_config.get("current_price", 0.0)
        if current_price and lower > 0 and current_price <= lower:
            signals.append("价格触及布林带下轨，可能反弹")
            signal_strength += 2
        
        # 计算信号强度
        max_strength = 8
        strength_percentage = (signal_strength / max_strength) * 100 if max_strength > 0 else 0
        
        # 判断是否生成买入信号
        buy_threshold = stock_config.get("buy_threshold", 0.05)
        buy_signal = signal_strength >= 4  # 需要至少两个信号
        
        return {
            "signal": "buy" if buy_signal else "hold",
            "strength": signal_strength,
            "strength_percentage": strength_percentage,
            "reasons": signals,
            "suggestion": "建议买入" if buy_signal else "建议持有观望"
        }
    
    def generate_sell_signal(self, technical_data: Dict[str, Any], stock_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成卖出信号
        
        参数:
            technical_data: 技术分析数据
            stock_config: 股票配置
            
        返回:
            卖出信号信息
        """
        signals = []
        signal_strength = 0
        
        # RSI信号
        rsi = technical_data.get("rsi", 50.0)
        rsi_sell_level = stock_config.get("rsi_sell_level", 70)
        if rsi > rsi_sell_level:
            signals.append(f"RSI({rsi:.2f})高于卖出阈值({rsi_sell_level})")
            signal_strength += 2
        
        # MACD信号
        macd = technical_data.get("macd", {})
        macd_value = macd.get("macd", 0.0)
        signal_value = macd.get("signal", 0.0)
        histogram = macd.get("histogram", 0.0)
        if macd_value < signal_value and histogram < 0:
            signals.append("MACD死叉，价格动量向下")
            signal_strength += 2
        
        # KDJ信号
        kdj = technical_data.get("kdj", {})
        k_value = kdj.get("k", 50.0)
        d_value = kdj.get("d", 50.0)
        j_value = kdj.get("j", 50.0)
        k_sell_level = stock_config.get("k_sell_level", 80)
        if k_value > k_sell_level and j_value < k_value:
            signals.append(f"KDJ超买，K值({k_value:.2f})高于卖出阈值({k_sell_level})")
            signal_strength += 2
        
        # 布林带信号
        bollinger = technical_data.get("bollinger", {})
        upper = bollinger.get("upper", 0.0)
        middle = bollinger.get("middle", 0.0)
        lower = bollinger.get("lower", 0.0)
        current_price = stock_config.get("current_price", 0.0)
        if current_price and upper > 0 and current_price >= upper:
            signals.append("价格触及布林带上轨，可能回调")
            signal_strength += 2
        
        # 盈利目标信号
        current_price = stock_config.get("current_price", 0.0)
        cost_price = stock_config.get("cost_price", 0.0)
        profit_target = stock_config.get("profit_target", 0.1)
        if current_price and cost_price and cost_price > 0:
            profit_percentage = (current_price - cost_price) / cost_price
            if profit_percentage >= profit_target:
                signals.append(f"达到盈利目标({profit_target*100:.1f}%)")
                signal_strength += 3  # 盈利目标权重更高
        
        # 止损信号
        stop_loss = stock_config.get("stop_loss", 0.05)
        if current_price and cost_price and cost_price > 0:
            loss_percentage = (cost_price - current_price) / cost_price
            if loss_percentage >= stop_loss:
                signals.append(f"达到止损线({stop_loss*100:.1f}%)")
                signal_strength += 3  # 止损信号权重更高
        
        # 计算信号强度
        max_strength = 13  # 考虑盈利目标和止损的额外权重
        strength_percentage = (signal_strength / max_strength) * 100 if max_strength > 0 else 0
        
        # 判断是否生成卖出信号
        sell_threshold = stock_config.get("sell_threshold", 0.03)
        sell_signal = signal_strength >= 4  # 需要至少两个信号，或一个高权重信号
        
        return {
            "signal": "sell" if sell_signal else "hold",
            "strength": signal_strength,
            "strength_percentage": strength_percentage,
            "reasons": signals,
            "suggestion": "建议卖出" if sell_signal else "建议持有"
        }
    
    def generate_add_position_signal(self, technical_data: Dict[str, Any], stock_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成加仓信号 — 持仓股票出现买入信号时建议加仓

        参数:
            technical_data: 技术分析数据
            stock_config: 股票配置

        返回:
            加仓信号信息
        """
        buy_result = self.generate_buy_signal(technical_data, stock_config)

        # 加仓要求比新买入更高的信号强度 (>= 6/8)
        if buy_result["strength"] < 6:
            return {
                "signal": "hold",
                "strength": buy_result["strength"],
                "strength_percentage": buy_result["strength_percentage"],
                "reasons": buy_result["reasons"],
                "suggestion": "信号强度不足，不建议加仓"
            }

        # 检查盈利水平 — 涨幅过大时提示谨慎
        current_price = stock_config.get("current_price", 0.0)
        cost_price = stock_config.get("cost_price", 0.0)
        if cost_price > 0 and current_price > 0:
            profit_pct = (current_price - cost_price) / cost_price
            if profit_pct > 0.20:
                return {
                    "signal": "hold",
                    "strength": buy_result["strength"],
                    "strength_percentage": buy_result["strength_percentage"],
                    "reasons": buy_result["reasons"] + [f"持仓已盈利{profit_pct*100:.1f}%，追高谨慎"],
                    "suggestion": "涨幅较大，建议持有观望"
                }

        return {
            "signal": "add_position",
            "strength": buy_result["strength"],
            "strength_percentage": buy_result["strength_percentage"],
            "reasons": buy_result["reasons"],
            "suggestion": "建议加仓"
        }

    def generate_signal(self, technical_data: Dict[str, Any], stock_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成最终信号
        
        参数:
            technical_data: 技术分析数据
            stock_config: 股票配置
            
        返回:
            最终信号信息
        """
        is_holding = stock_config.get("hold", False)

        if is_holding:
            # 先检查卖出信号
            sell_result = self.generate_sell_signal(technical_data, stock_config)
            if sell_result["signal"] == "sell":
                return sell_result

            # 无明确卖出信号时检查加仓机会
            add_result = self.generate_add_position_signal(technical_data, stock_config)
            if add_result["signal"] == "add_position":
                return add_result

            return sell_result
        else:
            # 如果未持有，生成买入信号
            return self.generate_buy_signal(technical_data, stock_config)
