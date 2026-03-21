from .stock_monitor import StockMonitor
from .market_watcher import MarketWatcher

try:
    from .market_signals import router as market_signals_router
except Exception:
    market_signals_router = None
try:
    from .health import router as health_router
except Exception:
    health_router = None
from ..middleware.auth_middleware import AuthMiddleware  # type: ignore
from .analysis.technical import TechnicalAnalyzer
from .analysis.signal import SignalGenerator
from .config import MonitorConfig

try:
    from .health import router as health_router
except Exception:
    health_router = None

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
    if health_router is not None:
        try:
            app.include_router(health_router, prefix="/api")
        except Exception:
            pass
    try:
        app.add_middleware(AuthMiddleware)
    except Exception:
        pass
    if health_router is not None:
        try:
            app.include_router(health_router, prefix="/api")
        except Exception:
            pass
