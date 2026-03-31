"""
Async Backtest Engine Module

Provides asynchronous backtesting capabilities for trading strategies.
"""

from .strategies import (
    BaseStrategy,
    Signal,
    SignalType,
    MACrossStrategy,
    RSIStrategy,
    BollingerStrategy,
    MACDStrategy,
    QlibModelStrategy,
    StrategyFactory,
)

from .async_engine import (
    AsyncBacktestEngine,
    BacktestConfig,
    BacktestResult,
    BacktestStatus,
    Position,
    Trade,
)

from .risk_metrics import (
    RiskMetrics,
    RiskMetricsCalculator,
)

from .websocket_handler import (
    ConnectionManager,
    websocket_backtest_endpoint,
    get_connection_manager,
)

__all__ = [
    "BaseStrategy",
    "Signal",
    "SignalType",
    "MACrossStrategy",
    "RSIStrategy",
    "BollingerStrategy",
    "MACDStrategy",
    "QlibModelStrategy",
    "StrategyFactory",
    "AsyncBacktestEngine",
    "BacktestConfig",
    "BacktestResult",
    "BacktestStatus",
    "Position",
    "Trade",
    "RiskMetrics",
    "RiskMetricsCalculator",
    "ConnectionManager",
    "websocket_backtest_endpoint",
    "get_connection_manager",
]
