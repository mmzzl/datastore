"""
Risk Metrics Calculator

Calculates various risk and performance metrics for backtesting.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """
    Container for risk metrics.
    
    Attributes:
        total_return: Total portfolio return
        annual_return: Annualized return
        sharpe_ratio: Sharpe ratio (annualized, risk-free rate = 0)
        max_drawdown: Maximum drawdown from peak
        win_rate: Percentage of profitable trades
        total_trades: Total number of trades
        profitable_trades: Number of profitable trades
        var_95: Value at Risk at 95% confidence
        avg_profit: Average profit per trade
        avg_loss: Average loss per trade
        profit_factor: Gross profit / Gross loss
    """
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profitable_trades: int
    var_95: float
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0


class RiskMetricsCalculator:
    """
    Calculates risk metrics for backtest results.
    
    Metrics calculated:
    - Sharpe ratio (annualized)
    - Maximum drawdown
    - Win rate
    - Total return, annual return
    - VaR (95% confidence)
    """
    
    TRADING_DAYS_PER_YEAR = 252
    
    @classmethod
    def calculate(
        cls,
        portfolio_values: List[float],
        returns: Optional[List[float]] = None,
        trades: Optional[List[Dict[str, Any]]] = None,
    ) -> RiskMetrics:
        """
        Calculate all risk metrics.
        
        Args:
            portfolio_values: Time series of portfolio values
            returns: Optional pre-calculated returns
            trades: Optional list of trade dictionaries with 'pnl' field
        
        Returns:
            RiskMetrics object with all calculated metrics
        """
        if len(portfolio_values) < 2:
            return RiskMetrics(
                total_return=0.0,
                annual_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                total_trades=0,
                profitable_trades=0,
                var_95=0.0,
            )
        
        values = np.array(portfolio_values)
        
        if returns is None:
            returns_arr = cls._calculate_returns(values)
        else:
            returns_arr = np.array(returns)
        
        total_return = cls._calculate_total_return(values)
        annual_return = cls._calculate_annual_return(returns_arr)
        sharpe_ratio = cls._calculate_sharpe_ratio(returns_arr)
        max_drawdown = cls._calculate_max_drawdown(values)
        var_95 = cls._calculate_var_95(returns_arr)
        
        trade_metrics = cls._calculate_trade_metrics(trades) if trades else {}
        
        return RiskMetrics(
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=trade_metrics.get("win_rate", 0.0),
            total_trades=trade_metrics.get("total_trades", 0),
            profitable_trades=trade_metrics.get("profitable_trades", 0),
            var_95=var_95,
            avg_profit=trade_metrics.get("avg_profit", 0.0),
            avg_loss=trade_metrics.get("avg_loss", 0.0),
            profit_factor=trade_metrics.get("profit_factor", 0.0),
        )
    
    @classmethod
    def _calculate_returns(cls, values: np.ndarray) -> np.ndarray:
        """
        Calculate period returns.
        
        Args:
            values: Array of portfolio values
        
        Returns:
            Array of returns
        """
        if len(values) < 2:
            return np.array([])
        
        returns = np.diff(values) / values[:-1]
        returns = returns[np.isfinite(returns)]
        return returns
    
    @classmethod
    def _calculate_total_return(cls, values: np.ndarray) -> float:
        """
        Calculate total return.
        
        Args:
            values: Array of portfolio values
        
        Returns:
            Total return as decimal
        """
        if len(values) < 2 or values[0] == 0:
            return 0.0
        
        return (values[-1] - values[0]) / values[0]
    
    @classmethod
    def _calculate_annual_return(cls, returns: np.ndarray) -> float:
        """
        Calculate annualized return.
        
        Args:
            returns: Array of period returns
        
        Returns:
            Annualized return as decimal
        """
        if len(returns) == 0:
            return 0.0
        
        total_return = np.prod(1 + returns) - 1
        num_periods = len(returns)
        
        if num_periods == 0:
            return 0.0
        
        years = num_periods / cls.TRADING_DAYS_PER_YEAR
        
        if years <= 0:
            return total_return
        
        annual_return = (1 + total_return) ** (1 / years) - 1
        return annual_return if np.isfinite(annual_return) else 0.0
    
    @classmethod
    def _calculate_sharpe_ratio(cls, returns: np.ndarray) -> float:
        """
        Calculate annualized Sharpe ratio (risk-free rate = 0).
        
        Args:
            returns: Array of period returns
        
        Returns:
            Annualized Sharpe ratio
        """
        if len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)
        
        if std_return == 0 or not np.isfinite(std_return):
            return 0.0
        
        sharpe = mean_return / std_return * np.sqrt(cls.TRADING_DAYS_PER_YEAR)
        return sharpe if np.isfinite(sharpe) else 0.0
    
    @classmethod
    def _calculate_max_drawdown(cls, values: np.ndarray) -> float:
        """
        Calculate maximum drawdown from peak.
        
        Args:
            values: Array of portfolio values
        
        Returns:
            Maximum drawdown as positive decimal
        """
        if len(values) < 2:
            return 0.0
        
        peak = np.maximum.accumulate(values)
        drawdowns = (peak - values) / peak
        drawdowns = np.where(np.isfinite(drawdowns), drawdowns, 0)
        
        max_dd = np.max(drawdowns)
        return max_dd if np.isfinite(max_dd) else 0.0
    
    @classmethod
    def _calculate_var_95(cls, returns: np.ndarray) -> float:
        """
        Calculate Value at Risk at 95% confidence.
        
        Args:
            returns: Array of period returns
        
        Returns:
            VaR as positive decimal (loss)
        """
        if len(returns) < 5:
            return 0.0
        
        var = np.percentile(returns, 5)
        return abs(var) if np.isfinite(var) else 0.0
    
    @classmethod
    def _calculate_trade_metrics(
        cls,
        trades: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Calculate trade-based metrics.
        
        Args:
            trades: List of trade dictionaries with 'pnl' field
        
        Returns:
            Dictionary with win_rate, total_trades, profitable_trades
        """
        if not trades:
            return {
                "win_rate": 0.0,
                "total_trades": 0,
                "profitable_trades": 0,
            }
        
        pnls = [t.get("pnl", 0) for t in trades if "pnl" in t]
        
        if not pnls:
            return {
                "win_rate": 0.0,
                "total_trades": len(trades),
                "profitable_trades": 0,
            }
        
        pnls_arr = np.array(pnls)
        total_trades = len(pnls)
        profitable_trades = int(np.sum(pnls_arr > 0))
        
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0.0
        
        profits = pnls_arr[pnls_arr > 0]
        losses = pnls_arr[pnls_arr < 0]
        
        avg_profit = np.mean(profits) if len(profits) > 0 else 0.0
        avg_loss = np.mean(np.abs(losses)) if len(losses) > 0 else 0.0
        
        gross_profit = np.sum(profits) if len(profits) > 0 else 0.0
        gross_loss = np.sum(np.abs(losses)) if len(losses) > 0 else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
        
        return {
            "win_rate": win_rate,
            "total_trades": total_trades,
            "profitable_trades": profitable_trades,
            "avg_profit": avg_profit if np.isfinite(avg_profit) else 0.0,
            "avg_loss": avg_loss if np.isfinite(avg_loss) else 0.0,
            "profit_factor": profit_factor if np.isfinite(profit_factor) else 0.0,
        }
    
    @classmethod
    def calculate_from_series(
        cls,
        portfolio_series: pd.Series,
    ) -> RiskMetrics:
        """
        Calculate metrics from pandas Series.
        
        Args:
            portfolio_series: Series of portfolio values with date index
        
        Returns:
            RiskMetrics object
        """
        values = portfolio_series.values.tolist()
        return cls.calculate(values)
    
    @classmethod
    def to_dict(cls, metrics: RiskMetrics) -> Dict[str, Any]:
        """
        Convert RiskMetrics to dictionary.
        
        Args:
            metrics: RiskMetrics object
        
        Returns:
            Dictionary representation
        """
        return {
            "total_return": metrics.total_return,
            "annual_return": metrics.annual_return,
            "sharpe_ratio": metrics.sharpe_ratio,
            "max_drawdown": metrics.max_drawdown,
            "win_rate": metrics.win_rate,
            "total_trades": metrics.total_trades,
            "profitable_trades": metrics.profitable_trades,
            "var_95": metrics.var_95,
            "avg_profit": metrics.avg_profit,
            "avg_loss": metrics.avg_loss,
            "profit_factor": metrics.profit_factor,
        }
