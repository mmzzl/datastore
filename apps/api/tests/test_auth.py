from fastapi.testclient import TestClient
from app.core.security import security
from main import app

client = TestClient(app)


def test_login_for_access_token():
    """测试获取访问令牌"""
    response = client.post(
        "/api/login", json={"username": "admin", "password": "sip@1234"}
    )
    assert response.status_code == 200
    assert "token" in response.json()


def test_login_with_invalid_credentials():
    """测试使用无效凭证登录"""
    response = client.post(
        "/api/login", json={"username": "wrong", "password": "wrong"}
    )
    assert response.status_code == 401
