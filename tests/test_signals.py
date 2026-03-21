from fastapi import FastAPI
from fastapi.testclient import TestClient
from case.apps.api.app.monitor.market_signals import router as signals_router


def build_app():
    app = FastAPI()
    app.include_router(signals_router, prefix="/api")
    return app


def test_latest_signals_empty():
    app = build_app()
    client = TestClient(app)
    resp = client.get("/api/signals/latest")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
