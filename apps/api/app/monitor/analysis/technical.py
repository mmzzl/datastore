import pandas as pd
import numpy as np
from typing import Dict, Any, List

class TechnicalAnalyzer:
    """技术指标分析器"""
    
    def __init__(self):
        pass
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """
        计算RSI（相对强弱指标）
        
        参数:
            prices: 价格列表
            period: 计算周期
            
        返回:
            RSI值
        """
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = deltas[deltas > 0]
        losses = -deltas[deltas < 0]
        
        avg_gain = np.mean(gains[:period]) if len(gains) > 0 else 0
        avg_loss = np.mean(losses[:period]) if len(losses) > 0 else 0
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # 计算后续值
        for i in range(period, len(deltas)):
            delta = deltas[i]
            gain = delta if delta > 0 else 0
            loss = -delta if delta < 0 else 0
            
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(self, prices: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, float]:
        """
        计算MACD（移动平均线收敛发散）
        
        参数:
            prices: 价格列表
            fast_period: 快速移动平均周期
            slow_period: 慢速移动平均周期
            signal_period: 信号周期
            
        返回:
            MACD相关值
        """
        if len(prices) < slow_period + signal_period:
            return {
                "macd": 0.0,
                "signal": 0.0,
                "histogram": 0.0
            }
        
        # 计算EMA
        def ema(values, period):
            result = []
            multiplier = 2 / (period + 1)
            # 初始化第一个EMA为第一个价格
            result.append(values[0])
            # 计算后续EMA
            for i in range(1, len(values)):
                current_ema = values[i] * multiplier + result[i-1] * (1 - multiplier)
                result.append(current_ema)
            return result
        
        ema_fast = ema(prices, fast_period)
        ema_slow = ema(prices, slow_period)
        
        # 计算MACD线
        macd_line = [fast - slow for fast, slow in zip(ema_fast, ema_slow)]
        
        # 计算信号线
        signal_line = ema(macd_line, signal_period)
        
        # 计算柱状图
        histogram = [macd - signal for macd, signal in zip(macd_line, signal_line)]
        
        return {
            "macd": macd_line[-1],
            "signal": signal_line[-1],
            "histogram": histogram[-1]
        }
    
    def calculate_kdj(self, prices: List[float], high_prices: List[float], low_prices: List[float], period: int = 9) -> Dict[str, float]:
        """
        计算KDJ（随机指标）
        
        参数:
            prices: 收盘价列表
            high_prices: 最高价列表
            low_prices: 最低价列表
            period: 计算周期
            
        返回:
            KDJ相关值
        """
        if len(prices) < period:
            return {
                "k": 50.0,
                "d": 50.0,
                "j": 50.0
            }
        
        # 计算RSV
        rsv_list = []
        for i in range(period - 1, len(prices)):
            recent_high = max(high_prices[i - period + 1:i + 1])
            recent_low = min(low_prices[i - period + 1:i + 1])
            close = prices[i]
            
            if recent_high == recent_low:
                rsv = 50.0
            else:
                rsv = (close - recent_low) / (recent_high - recent_low) * 100
            
            rsv_list.append(rsv)
        
        # 计算K值和D值
        k_list = []
        d_list = []
        
        # 初始化K和D
        k = 50.0
        d = 50.0
        k_list.append(k)
        d_list.append(d)
        
        for rsv in rsv_list:
            k = (2/3) * k + (1/3) * rsv
            d = (2/3) * d + (1/3) * k
            k_list.append(k)
            d_list.append(d)
        
        # 计算J值
        j_list = [3 * k - 2 * d for k, d in zip(k_list, d_list)]
        
        return {
            "k": k_list[-1],
            "d": d_list[-1],
            "j": j_list[-1]
        }
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, num_std: float = 2.0) -> Dict[str, float]:
        """
        计算布林带
        
        参数:
            prices: 价格列表
            period: 计算周期
            num_std: 标准差倍数
            
        返回:
            布林带相关值
        """
        if len(prices) < period:
            return {
                "upper": 0.0,
                "middle": 0.0,
                "lower": 0.0
            }
        
        # 计算移动平均线
        middle_band = np.mean(prices[-period:])
        
        # 计算标准差
        std_dev = np.std(prices[-period:])
        
        # 计算上下轨
        upper_band = middle_band + (num_std * std_dev)
        lower_band = middle_band - (num_std * std_dev)
        
        return {
            "upper": upper_band,
            "middle": middle_band,
            "lower": lower_band
        }
    
    def analyze_stock(self, stock_data: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        分析股票技术指标
        
        参数:
            stock_data: 股票数据，包含close、high、low等字段
            
        返回:
            技术指标分析结果
        """
        close_prices = stock_data.get("close", [])
        high_prices = stock_data.get("high", close_prices)
        low_prices = stock_data.get("low", close_prices)
        
        if not close_prices:
            return {
                "rsi": 50.0,
                "macd": {
                    "macd": 0.0,
                    "signal": 0.0,
                    "histogram": 0.0
                },
                "kdj": {
                    "k": 50.0,
                    "d": 50.0,
                    "j": 50.0
                },
                "bollinger": {
                    "upper": 0.0,
                    "middle": 0.0,
                    "lower": 0.0
                }
            }
        
        # 计算各项技术指标
        rsi = self.calculate_rsi(close_prices)
        macd = self.calculate_macd(close_prices)
        kdj = self.calculate_kdj(close_prices, high_prices, low_prices)
        bollinger = self.calculate_bollinger_bands(close_prices)
        
        return {
            "rsi": rsi,
            "macd": macd,
            "kdj": kdj,
            "bollinger": bollinger
        }
