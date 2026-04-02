"""
测试插件 - 双均线策略
"""

from app.backtest.strategies.base import BaseStrategy, Signal, SignalType
import pandas as pd


class DualMA(BaseStrategy):
    """
    双均线策略
    当短期均线上穿长期均线时买入，下穿时卖出
    """
    
    def __init__(self, fast_period=5, slow_period=20, **kwargs):
        """
        初始化策略
        
        Args:
            fast_period: 短期均线周期
            slow_period: 长期均线周期
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.name = f"DualMA_{fast_period}_{slow_period}"
    
    def get_name(self) -> str:
        """获取策略名称"""
        return self.name
    
    def get_required_data_points(self) -> int:
        """获取所需数据点数"""
        return max(self.fast_period, self.slow_period)
    
    def generate_signals(self, data: pd.DataFrame) -> Signal:
        """
        生成交易信号
        
        Args:
            data: 股票数据
        
        Returns:
            交易信号
        """
        if len(data) < self.get_required_data_points():
            return Signal(SignalType.HOLD, 0)
        
        # 计算均线
        data['fast_ma'] = data['close'].rolling(self.fast_period).mean()
        data['slow_ma'] = data['close'].rolling(self.slow_period).mean()
        
        # 信号生成
        if data['fast_ma'].iloc[-1] > data['slow_ma'].iloc[-1] and data['fast_ma'].iloc[-2] <= data['slow_ma'].iloc[-2]:
            return Signal(SignalType.BUY, 1.0)
        elif data['fast_ma'].iloc[-1] < data['slow_ma'].iloc[-1] and data['fast_ma'].iloc[-2] >= data['slow_ma'].iloc[-2]:
            return Signal(SignalType.SELL, 1.0)
        else:
            return Signal(SignalType.HOLD, 0)
    
    def get_default_params(self, **kwargs) -> dict:
        """获取默认参数"""
        return {
            "fast_period": 5,
            "slow_period": 20
        }