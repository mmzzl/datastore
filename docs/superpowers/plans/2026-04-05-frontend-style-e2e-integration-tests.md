# 前端风格 E2E 集成测试实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建前端风格的 E2E 集成测试，直接模拟前端 API 调用方式，解决前后端集成时的路径不匹配、数据格式不一致、认证问题

**Architecture:** 创建独立的集成测试模块，每个测试文件完全模拟对应前端 service 的调用方式，使用标准化 fixtures

**Tech Stack:** pytest, pytest-asyncio, httpx

---

## Chunk 1: 基础测试框架

### Task 1: 创建集成测试目录和 conftest.py

**Files:**
- Create: `apps/api/tests/integration/__init__.py`
- Create: `apps/api/tests/integration/conftest.py`
- Test: `apps/api/tests/integration/conftest.py`

- [ ] **Step 1: 创建 __init__.py**

```bash
touch apps/api/tests/integration/__init__.py
```

- [ ] **Step 2: 创建 conftest.py 基础结构**

```python
# apps/api/tests/integration/conftest.py
import pytest

@pytest.fixture
def test_user():
    return {
        "username": "admin",
        "password": "aa123aaqqA@",
        "role_id": "role_superuser"
    }
```

Run: `py -3.12 -m pytest apps/api/tests/integration/ --co -q`
Expected: 收集成功，无错误

- [ ] **Step 3: 添加 api_client fixture**

- [ ] **Step 4: 测试 conftest.py**

- [ ] **Step 5: Commit**

```bash
git add apps/api/tests/integration/
git commit -m "test: create integration test directory and conftest.py"
```

---

## Chunk 2: 认证 API 测试

### Task 2: 创建 test_api_auth.py

**Files:**
- Create: `apps/api/tests/integration/test_api_auth.py`
- Test: `apps/api/tests/integration/test_api_auth.py`

- [ ] **Step 1: 写入 test_api_auth.py**

```python
"""
测试认证 API - 完全模拟 frontend/vue-admin/src/services/api_auth.ts
"""

def test_login_success(async_client, test_user):
    """模拟 apiAuthNew.login(username, password)"""
    response = async_client.post("/api/auth/token", json={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "user_id" in data
    assert "username" in data

- [ ] **Step 2: 运行测试验证**

Run: `py -3.12 -m pytest apps/api/tests/integration/test_api_auth.py -v`
Expected: PASS

- [ ] **Step 3: 添加更多认证测试用例**

- [ ] **Step 4: Commit**
```

---

## Chunk 3: 持仓 API 测试

### Task 3: 创建 test_api_holdings.py

**Files:**
- Create: `apps/api/tests/integration/test_api_holdings.py`
- Test: `apps/api/tests/integration/test_api_holdings.py`

- [ ] **Step 1: 写入 test_api_holdings.py**

```python
"""
测试持仓 API - 完全模拟 api_holdings.ts
"""

def test_get_holdings_pagination(api_client):
    """模拟 api_holdings.getHoldings(userId, page, pageSize)"""
    response = api_client.get("/api/holdings/admin", params={"page": 1, "page_size": 10})
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data

def test_upsert_holding(api_client):
    """模拟 api_holdings.upsertHolding"""
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

def test_remove_holding(api_client):
    """模拟 api_holdings.removeHolding"""
    response = api_client.delete("/api/holdings/admin/SH600000")
    assert response.status_code == 200

def test_get_portfolio(api_client):
    """模拟 api_holdings.getPortfolio"""
    response = api_client.get("/api/portfolio/admin")
    assert response.status_code == 200
    data = response.json()
    assert "total_cost" in data
    assert "market_value" in data
```

- [ ] **Step 2: 运行测试**

Run: `py -3.12 -m pytest apps/api/tests/integration/test_api_holdings.py -v`
Expected: 检查是否有 404 或字段不匹配错误

- [ ] **Step 3: 修复发现的问题**

- [ ] **Step 4: Commit**

---

## Chunk 4: 用户和角色 API 测试

### Task 4: 创建 test_api_users.py 和 test_api_roles.py

**Files:**
- Create: `apps/api/tests/integration/test_api_users.py`
- Create: `apps/api/tests/integration/test_api_roles.py`

- [ ] **Step 1: 创建 test_api_users.py**

```python
"""测试用户 API - 模拟 api_users.ts"""

def test_list_users(api_client):
    response = api_client.get("/api/users")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

def test_get_user(api_client):
    response = api_client.get("/api/users/admin")
    assert response.status_code == 200

def test_create_user(api_client):
    response = api_client.post(
        "/api/users",
        json={
            "username": "testuser",
            "password": "test123",
            "display_name": "测试用户",
            "role_id": "role_viewer"
        }
    )
    assert response.status_code in [200, 201, 400]  # 400 如果用户已存在
```

- [ ] **Step 2: 创建 test_api_roles.py**

```python
"""测试角色 API - 模拟 api_roles.ts"""

def test_list_roles(api_client):
    response = api_client.get("/api/roles")
    assert response.status_code == 200

def test_get_role(api_client):
    response = api_client.get("/api/roles/role_admin")
    assert response.status_code in [200, 404]
```

- [ ] **Step 3: 运行测试并修复**

- [ ] **Step 4: Commit**

---

## Chunk 5: 其他核心 API 测试

### Task 5: 创建剩余测试文件

**Files:**
- Create: `apps/api/tests/integration/test_api_scheduler.py`
- Create: `apps/api/tests/integration/test_api_qlib.py`
- Create: `apps/api/tests/integration/test_api_backtest.py`

- [ ] **Step 1: test_api_scheduler.py**

- [ ] **Step 2: test_api_qlib.py**

- [ ] **Step 3: test_api_backtest.py**

- [ ] **Step 4: 运行所有测试**

Run: `py -3.12 -m pytest apps/api/tests/integration/ -v`

- [ ] **Step 5: Commit**

---

## Chunk 6: CI/CD 集成

### Task 6: 添加测试命令到项目

- [ ] **Step 1: 更新 pytest.ini 或 pyproject.toml**

```ini
[tool.pytest.ini_options]
testpaths = ["tests/integration"]
```

- [ ] **Step 2: 添加 Makefile 或脚本**

- [ ] **Step 3: Commit**

---

## 验收标准

1. 所有集成测试可以通过 `py -3.12 -m pytest apps/api/tests/integration/ -v` 运行
2. 每个前端 apiXXX.ts 都有对应的测试覆盖
3. 测试失败时能直接定位到前端调用问题
4. 运行时间 < 5 分钟
