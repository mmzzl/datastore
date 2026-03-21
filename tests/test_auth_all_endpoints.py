from fastapi import FastAPI
from fastapi.testclient import TestClient
from case.apps.api.app.api_holdings import router as holdings_router
from case.apps.api.app.auth import create_token
from case.apps.api.app.auth_guard_demo import router as guard_router
from case.apps.api.app.api_auth import router as auth_router
from case.apps.api.app.monitor.market_signals import router as signals_router


def build_app():
    app = FastAPI()
    app.include_router(holdings_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(guard_router, prefix="/api")
    app.include_router(signals_router, prefix="/api")
    return app


def test_guard_demo_unauthorized():
    app = build_app()
    client = TestClient(app)
    resp = client.get("/api/guard_demo")
    assert resp.status_code == 401 or resp.status_code == 422


def test_guard_demo_authorized():
    app = build_app()
    client = TestClient(app)
    token = create_token("default")
    resp = client.get("/api/guard_demo", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("user") == "default"
