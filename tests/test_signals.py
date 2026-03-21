from fastapi import FastAPI
from fastapi.testclient import TestClient
from case.apps.api.app.monitor.market_signals import router as signals_router
from case.apps.api.app.auth import create_token


def build_app():
    app = FastAPI()
    app.include_router(signals_router, prefix="/api")
    return app


def test_latest_signals_empty():
    app = build_app()
    client = TestClient(app)
    token = create_token("test_user")
    resp = client.get(
        "/api/signals/latest", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
