from fastapi import FastAPI
from fastapi.testclient import TestClient
from case.apps.api.app.api_holdings import router as holdings_router
from case.apps.api.app.auth import create_token
from case.apps.api.app.auth_guard_demo import router as guard_router


def build_app():
    app = FastAPI()
    app.include_router(holdings_router, prefix="/api")
    app.include_router(guard_router, prefix="/api")
    return app


def test_holdings_cross_user_forbidden():
    app = build_app()
    client = TestClient(app)
    token_default = create_token("default")
    resp = client.get(
        "/api/holdings/other", headers={"Authorization": f"Bearer {token_default}"}
    )
    assert resp.status_code in (401, 403)


def test_guard_demo_authorized():
    app = build_app()
    client = TestClient(app)
    token = create_token("default")
    resp = client.get("/api/guard_demo", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
