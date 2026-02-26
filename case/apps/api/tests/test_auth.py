from fastapi.testclient import TestClient
from app.core.security import security
from main import app

client = TestClient(app)

def test_login_for_access_token():
    """测试获取访问令牌"""
    response = client.post(
        "/api/auth/token",
        json={"username": "admin", "password": "admin"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_with_invalid_credentials():
    """测试使用无效凭证登录"""
    response = client.post(
        "/api/auth/token",
        json={"username": "wrong", "password": "wrong"}
    )
    assert response.status_code == 401
