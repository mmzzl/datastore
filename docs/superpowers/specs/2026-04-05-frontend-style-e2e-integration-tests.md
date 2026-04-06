# 前端风格 E2E 集成测试设计

## 目标

解决前后端集成时的 5 个核心问题：
1. 接口路径不匹配
2. 接口未实现
3. 数据格式不一致
4. 认证流程问题
5. 测试数据准备麻烦

## 核心思路

**每个测试文件完全模拟对应前端 service 的调用方式**，测试即文档，失败时能直接定位问题。

---

## 测试文件结构

```
apps/api/tests/integration/
├── conftest.py                    # 标准化 fixtures
├── test_api_auth.py              # 模拟 api_auth.ts
├── test_api_holdings.py          # 模拟 api_holdings.ts
├── test_api_portfolio.py         # 模拟 api_portfolio.ts
├── test_api_users.py             # 模拟 api_users.ts
├── test_api_roles.py            # 模拟 api_roles.ts
├── test_api_scheduler.py         # 模拟 api_scheduler.ts
├── test_api_qlib.py              # 模拟 api_qlib.ts
├── test_api_backtest.py         # 模拟 api_backtest.ts
└── test_api_stock_selection.py  # 模拟 api_stock_selection.ts
```

---

## 标准化 Fixture 设计

### conftest.py

```python
import pytest

@pytest.fixture
def test_user():
    """标准测试用户"""
    return {
        "username": "admin",
        "password": "aa123aaqqA@",
        "role_id": "role_superuser"
    }

@pytest.fixture
def api_client(async_client, test_user):
    """带认证的 API 客户端 - 模拟前端 axios 实例"""
    # 1. 登录获取 token
    response = async_client.post("/api/auth/token", json={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    token = response.json()["access_token"]
    
    # 2. 返回带认证的 client
    class AuthenticatedClient:
        def __init__(self, client, token):
            self._client = client
            self._token = token
        
        def get(self, path, **kwargs):
            kwargs.setdefault("headers", {})["Authorization"] = f"Bearer {self._token}"
            return self._client.get(path, **kwargs)
        
        def post(self, path, **kwargs):
            kwargs.setdefault("headers", {})["Authorization"] = f"Bearer {self._token}"
            return self._client.post(path, **kwargs)
        
        def put(self, path, **kwargs):
            kwargs.setdefault("headers", {})["Authorization"] = f"Bearer {self._token}"
            return self._client.put(path, **kwargs)
        
        def delete(self, path, **kwargs):
            kwargs.setdefault("headers", {})["Authorization"] = f"Bearer {self._token}"
            return self._client.delete(path, **kwargs)
    
    return AuthenticatedClient(async_client, token)
```

---

## 测试示例

### test_api_holdings.py

完全模拟 `frontend/vue-admin/src/services/api_holdings.ts`

```python
"""
测试持仓 API - 完全模拟 api_holdings.ts
"""

def test_get_holdings_pagination(api_client):
    """模拟 api_holdings.getHoldings(userId, page, pageSize)"""
    response = api_client.get("/api/holdings/admin", params={"page": 1, "page_size": 10})
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证响应格式与前端期望一致
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data

def test_get_holdings_with_filters(api_client):
    """模拟带过滤条件的查询"""
    response = api_client.get(
        "/api/holdings/admin",
        params={"page": 1, "page_size": 10, "sort_by": "code", "order": "asc"}
    )
    
    assert response.status_code == 200

def test_upsert_holding(api_client):
    """模拟 api_holdings.upsertHolding(userId, code, name, quantity, avgCost)"""
    response = api_client.post(
        "/api/holdings/admin",
        json={
            "code": "SH600000",
            "name": "测试股票",
            "quantity": 1000,
            "average_cost": 10.5
        }
    )
    
    assert response.status_code in [200, 201]
    data = response.json()
    assert data.get("success") == True

def test_remove_holding(api_client):
    """模拟 api_holdings.removeHolding(userId, code)"""
    response = api_client.delete("/api/holdings/admin/SH600000")
    
    assert response.status_code == 200

def test_get_portfolio(api_client):
    """模拟 api_holdings.getPortfolio(userId)"""
    response = api_client.get("/api/portfolio/admin")
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证字段与前端 holdings.ts store 期望一致
    assert "total_cost" in data
    assert "market_value" in data
    assert "unrealized_pnl" in data
    assert "profit_rate" in data

def test_get_transactions(api_client):
    """模拟获取交易记录"""
    response = api_client.get("/api/transactions/admin")
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
```

### test_api_auth.py

完全模拟 `frontend/vue-admin/src/services/api_auth.ts`

```python
"""
测试认证 API - 完全模拟 api_auth.ts
"""

def test_login_success(async_client):
    """模拟 apiAuthNew.login(username, password)"""
    response = async_client.post("/api/auth/token", json={
        "username": "admin",
        "password": "aa123aaqqA@"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证与前端 apiAuthNew.login 期望一致
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "user_id" in data
    assert "username" in data
    assert "display_name" in data

def test_login_invalid_password(async_client):
    """测试密码错误"""
    response = async_client.post("/api/auth/token", json={
        "username": "admin",
        "password": "wrong_password"
    })
    
    assert response.status_code == 401

def test_logout(api_client):
    """模拟 apiAuthNew.logout()"""
    response = api_client.post("/api/auth/logout")
    
    assert response.status_code == 200

def test_get_current_user(api_client):
    """模拟 apiAuthNew.getCurrentUser()"""
    response = api_client.get("/api/auth/me")
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证字段与前端期望一致
    assert "id" in data
    assert "username" in data
    assert "display_name" in data
    assert "role_id" in data
    assert "is_superuser" in data
    assert "status" in data
```

---

## 运行方式

```bash
# 运行所有集成测试
py -3.12 -m pytest apps/api/tests/integration/ -v

# 运行特定模块
py -3.12 -m pytest apps/api/tests/integration/test_api_holdings.py -v

# 带覆盖率
py -3.12 -m pytest apps/api/tests/integration/ --cov=app.api.endpoints --cov-report=html
```

---

## 覆盖率目标

| 模块 | 覆盖要求 |
|------|----------|
| holdings | 100% - 核心业务 |
| portfolio | 100% |
| auth | 100% - 认证流程 |
| users | 100% |
| roles | 100% |
| scheduler | 80% |
| qlib | 80% |
| backtest | 80% |
| stock_selection | 80% |

---

## 问题检测能力

这个方案能检测到：

1. ✅ **接口路径不匹配** - 测试直接按前端调用路径
2. ✅ **接口未实现** - 404 错误直接暴露
3. ✅ **请求格式不一致** - 完全模拟前端 JSON 格式
4. ✅ **响应字段不匹配** - 验证前端期望的每个字段
5. ✅ **认证问题** - 所有测试都带 token
6. ✅ **数据没有** - 空数据时的边界情况

---

## 实现计划

1. 创建 `conftest.py` - 标准化 fixtures
2. 创建 `test_api_auth.py` - 认证 API 测试
3. 创建 `test_api_holdings.py` - 持仓 API 测试
4. 创建 `test_api_portfolio.py` - 组合 API 测试
5. 创建 `test_api_users.py` - 用户管理 API 测试
6. 创建 `test_api_roles.py` - 角色管理 API 测试
7. 创建其他模块测试
8. 运行测试并修复问题
9. 添加 CI/CD 集成
