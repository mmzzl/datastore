from .stock_monitor import StockMonitor
from .market_watcher import MarketWatcher

try:
    from .market_signals import router as market_signals_router
except Exception:
    market_signals_router = None
from .analysis.technical import TechnicalAnalyzer
from .analysis.signal import SignalGenerator
from .config import MonitorConfig

__all__ = [
    "StockMonitor",
    "MarketWatcher",
    "TechnicalAnalyzer",
    "SignalGenerator",
    "MonitorConfig",
]


def include_routers(app=None):
    if app is None:
        return
    if market_signals_router is not None:
        try:
            app.include_router(market_signals_router, prefix="/api")
        except Exception:
            pass
