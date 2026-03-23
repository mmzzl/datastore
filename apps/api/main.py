# Apply pandas compatibility patch before any other imports
from app.core.pandas_compat import _patched_fillna

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import auth, news, aftermarket, stock
from app.core.config import settings
from app.core.error import setup_error_handlers
import logging
from logging.handlers import TimedRotatingFileHandler
import os

from app.api_holdings import router as holdings_router
from app.api_settings import router as settings_router
from app.monitor.health import router as health_router
from app.monitor.market_signals import router as signals_router
from app.api_auth import router as market_auth_router
from app.monitor import include_routers

log_file = settings.logging_file
log_dir = os.path.dirname(log_file)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=getattr(logging, settings.logging_level), format=settings.logging_format
)

file_handler = TimedRotatingFileHandler(
    log_file,
    when="midnight",
    interval=1,
    backupCount=settings.logging_backup_count,
    encoding="utf-8",
)
file_handler.setLevel(getattr(logging, settings.logging_level))
file_handler.setFormatter(logging.Formatter(settings.logging_format))
file_handler.suffix = "%Y-%m-%d"

logging.getLogger().addHandler(file_handler)

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_error_handlers(app)

app.include_router(auth.router)
app.include_router(news.router)
app.include_router(aftermarket.router)
app.include_router(stock.router)

app.include_router(holdings_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(signals_router, prefix="/api")
app.include_router(market_auth_router, prefix="/api")

include_routers(app)


@app.get("/")
def read_root():
    return {"message": "News API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
