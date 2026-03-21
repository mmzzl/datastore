from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def get_access_token():
    """获取访问令牌"""
    response = client.post(
        "/api/auth/token",
        json={"username": "admin", "password": "admin"}
    )
    return response.json()["access_token"]

def test_get_daily_news():
    """测试查询当日新闻"""
    token = get_access_token()
    response = client.get(
        "/api/news/daily",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "total" in response.json()
    assert "items" in response.json()

def test_get_weekly_news():
    """测试查询本周新闻"""
    token = get_access_token()
    response = client.get(
        "/api/news/weekly",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "total" in response.json()
    assert "items" in response.json()

def test_get_monthly_news():
    """测试查询本月新闻"""
    token = get_access_token()
    response = client.get(
        "/api/news/monthly",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "total" in response.json()
    assert "items" in response.json()

def test_news_without_token():
    """测试无token访问新闻接口"""
    response = client.get("/api/news/daily")
    assert response.status_code == 401
