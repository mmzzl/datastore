import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 100000.0, commission_rate: float = 0.0003):
        """
        初始化回测引擎
        Args:
            initial_capital: 初始资金
            commission_rate: 佣金费率
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
    
    def run(self, data: List[Dict[str, Any]], strategy: str = "buy_and_hold", 
            **strategy_params) -> Dict[str, Any]:
        """
        运行回测
        Args:
            data: 历史数据 [{"date": "2023-01-01", "close": 10.0, ...}, ...]
            strategy: 策略名称
            strategy_params: 策略参数
        Returns:
            回测结果
        """
        try:
            if not data:
                return self._get_empty_result()
            
            # 转换为DataFrame
            df = pd.DataFrame(data)
            if df.empty:
                return self._get_empty_result()
            
            # 确保数据按日期排序
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)
            
            # 根据策略运行回测
            if strategy == "buy_and_hold":
                result = self._backtest_buy_and_hold(df)
            elif strategy == "moving_average":
                result = self._backtest_moving_average(df, **strategy_params)
            elif strategy == "rsi_strategy":
                result = self._backtest_rsi_strategy(df, **strategy_params)
            else:
                result = self._backtest_buy_and_hold(df)
            
            return result
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return self._get_empty_result()
    
    def _backtest_buy_and_hold(self, df: pd.DataFrame) -> Dict[str, Any]:
        """买入持有策略回测"""
        try:
            initial_price = df['close'].iloc[0]
            final_price = df['close'].iloc[-1]
            
            # 计算收益率
            total_return = (final_price - initial_price) / initial_price
            
            # 计算最大回撤
            df['cummax'] = df['close'].cummax()
            df['drawdown'] = (df['close'] - df['cummax']) / df['cummax']
            max_drawdown = df['drawdown'].min()
            
            # 计算年化收益率
            days = (df['date'].iloc[-1] - df['date'].iloc[0]).days
            annual_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
            
            return {
                "strategy": "buy_and_hold",
                "total_return": total_return,
                "annual_return": annual_return,
                "max_drawdown": max_drawdown,
                "sharpe_ratio": self._calculate_sharpe_ratio(df),
                "win_rate": 1.0 if total_return > 0 else 0.0,
                "num_trades": 1,
                "final_capital": self.initial_capital * (1 + total_return)
            }
            
        except Exception as e:
            logger.error(f"Error in buy_and_hold backtest: {e}")
            return self._get_empty_result()
    
    def _backtest_moving_average(self, df: pd.DataFrame, fast_period: int = 5, 
                                slow_period: int = 20) -> Dict[str, Any]:
        """移动平均线策略回测"""
        try:
            # 计算移动平均线
            df['ma_fast'] = df['close'].rolling(window=fast_period).mean()
            df['ma_slow'] = df['close'].rolling(window=slow_period).mean()
            
            # 生成信号
            df['signal'] = 0
            df.loc[df['ma_fast'] > df['ma_slow'], 'signal'] = 1  # 买入
            df.loc[df['ma_fast'] < df['ma_slow'], 'signal'] = -1  # 卖出
            
            # 模拟交易
            capital = self.initial_capital
            position = 0
            trades = []
            
            for i in range(1, len(df)):
                if df['signal'].iloc[i] == 1 and position == 0:
                    # 买入
                    price = df['close'].iloc[i]
                    shares = capital / price
                    capital -= shares * price * (1 + self.commission_rate)
                    position = shares
                    trades.append({"type": "buy", "price": price, "date": df['date'].iloc[i]})
                    
                elif df['signal'].iloc[i] == -1 and position > 0:
                    # 卖出
                    price = df['close'].iloc[i]
                    capital += position * price * (1 - self.commission_rate)
                    position = 0
                    trades.append({"type": "sell", "price": price, "date": df['date'].iloc[i]})
            
            # 最终持仓价值
            final_value = capital + (position * df['close'].iloc[-1] if position > 0 else 0)
            total_return = (final_value - self.initial_capital) / self.initial_capital
            
            return {
                "strategy": "moving_average",
                "total_return": total_return,
                "annual_return": 0,  # 简化处理
                "max_drawdown": 0,
                "sharpe_ratio": 0,
                "win_rate": 1.0 if total_return > 0 else 0.0,
                "num_trades": len(trades),
                "final_capital": final_value,
                "trades": trades
            }
            
        except Exception as e:
            logger.error(f"Error in moving average backtest: {e}")
            return self._get_empty_result()
    
    def _backtest_rsi_strategy(self, df: pd.DataFrame, rsi_period: int = 14, 
                              oversold: int = 30, overbought: int = 70) -> Dict[str, Any]:
        """RSI策略回测"""
        try:
            # 计算RSI
            df['rsi'] = self._calculate_rsi(df['close'], rsi_period)
            
            # 生成信号
            df['signal'] = 0
            df.loc[df['rsi'] < oversold, 'signal'] = 1  # 买入
            df.loc[df['rsi'] > overbought, 'signal'] = -1  # 卖出
            
            # 模拟交易
            capital = self.initial_capital
            position = 0
            trades = []
            
            for i in range(1, len(df)):
                if df['signal'].iloc[i] == 1 and position == 0:
                    # 买入
                    price = df['close'].iloc[i]
                    shares = capital / price
                    capital -= shares * price * (1 + self.commission_rate)
                    position = shares
                    trades.append({"type": "buy", "price": price, "date": df['date'].iloc[i]})
                    
                elif df['signal'].iloc[i] == -1 and position > 0:
                    # 卖出
                    price = df['close'].iloc[i]
                    capital += position * price * (1 - self.commission_rate)
                    position = 0
                    trades.append({"type": "sell", "price": price, "date": df['date'].iloc[i]})
            
            # 最终持仓价值
            final_value = capital + (position * df['close'].iloc[-1] if position > 0 else 0)
            total_return = (final_value - self.initial_capital) / self.initial_capital
            
            return {
                "strategy": "rsi_strategy",
                "total_return": total_return,
                "annual_return": 0,
                "max_drawdown": 0,
                "sharpe_ratio": 0,
                "win_rate": 1.0 if total_return > 0 else 0.0,
                "num_trades": len(trades),
                "final_capital": final_value,
                "trades": trades
            }
            
        except Exception as e:
            logger.error(f"Error in RSI backtest: {e}")
            return self._get_empty_result()
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_sharpe_ratio(self, df: pd.DataFrame, risk_free_rate: float = 0.02) -> float:
        """计算夏普比率"""
        try:
            returns = df['close'].pct_change().dropna()
            if len(returns) == 0:
                return 0.0
            
            excess_returns = returns - (risk_free_rate / 252)  # 日化无风险收益率
            sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
            return sharpe if not np.isnan(sharpe) else 0.0
            
        except Exception:
            return 0.0
    
    def _get_empty_result(self) -> Dict[str, Any]:
        """获取空结果"""
        return {
            "strategy": "unknown",
            "total_return": 0.0,
            "annual_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "win_rate": 0.0,
            "num_trades": 0,
            "final_capital": self.initial_capital
        }
    
    def compare_strategies(self, data: List[Dict[str, Any]], 
                          strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        比较多个策略
        Args:
            data: 历史数据
            strategies: 策略列表 [{"name": "ma", "params": {...}}, ...]
        Returns:
            策略比较结果
        """
        results = {}
        for strategy_info in strategies:
            name = strategy_info.get("name", "unknown")
            params = strategy_info.get("params", {})
            result = self.run(data, name, **params)
            results[name] = result
        
        # 找出最佳策略
        best_strategy = max(results.items(), key=lambda x: x[1]["total_return"])[0] if results else "unknown"
        
        return {
            "best_strategy": best_strategy,
            "results": results
        }
