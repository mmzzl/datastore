from fastapi import FastAPI
from fastapi.testclient import TestClient
from case.apps.api.app.api_auth import router as auth_router
from fastapi import APIRouter


def build_app():
    app = FastAPI()
    app.include_router(auth_router, prefix="/api")
    return app


def test_login_success():
    app = build_app()
    client = TestClient(app)
    resp = client.post(
        "/api/login", json={"user_id": "default", "password": "password"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data


def test_login_fail():
    app = build_app()
    client = TestClient(app)
    resp = client.post("/api/login", json={"user_id": "default", "password": "wrong"})
    assert resp.status_code == 401
