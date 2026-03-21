from fastapi import FastAPI
from fastapi.testclient import TestClient
from case.apps.api.app.monitor.health import router as health_router
from case.apps.api.app.auth import create_token


def build_app():
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(health_router, prefix="/api")
    return app


def test_health_unauthorized():
    app = build_app()
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code in (401, 403)


def test_health_authorized():
    app = build_app()
    client = TestClient(app)
    token = create_token("default")
    resp = client.get("/api/health", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert data.get("user") == "default"
