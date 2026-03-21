from fastapi import FastAPI
from fastapi.testclient import TestClient
from case.apps.api.app.api_holdings import router as holdings_router
from case.apps.api.app.auth import create_token
from case.apps.api.app.monitor.market_signals import router as signals_router
from case.apps.api.app.monitor.health import router as health_router
from case.apps.api.app.api_auth import router as auth_router
from case.apps.api.app.monitor.__init__ import include_routers
from case.apps.api.app.monitor import MarketWatcher


def build_app():
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(holdings_router, prefix="/api")
    app.include_router(health_router, prefix="/api")
    app.include_router(signals_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    # apply middleware via include_routers hook
    include_routers(app)
    return app


def test_endpoints_unauthorized():
    app = build_app()
    client = TestClient(app)
    endpoints = [
        "/api/holdings/default",
        "/api/portfolio/default",
        "/api/signals/latest",
    ]
    for ep in endpoints:
        resp = client.get(ep)
        assert resp.status_code in (401, 403)


def test_health_authorized():
    app = build_app()
    client = TestClient(app)
    token = create_token("default")
    resp = client.get("/api/health", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
