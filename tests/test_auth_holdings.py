from fastapi import FastAPI
from case.apps.api.app.api_holdings import router as holdings_router
from fastapi import Depends
from starlette.testclient import TestClient
from case.apps.api.app.auth import create_token


def build_app():
    app = FastAPI()
    app.include_router(holdings_router, prefix="/api")
    return app


def test_holdings_unauthorized():
    app = build_app()
    client = TestClient(app)
    resp = client.get("/api/holdings/default")
    assert resp.status_code == 422 or resp.status_code == 401 or resp.status_code == 403


def test_holdings_authorized():
    app = build_app()
    client = TestClient(app)
    token = create_token("default")
    resp = client.get(
        "/api/holdings/default", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
