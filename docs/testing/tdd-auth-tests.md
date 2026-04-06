# 后端认证模块 TDD 测试
# ========================

## RED - 编写失败的测试

我们在已有测试基础上添加更多认证相关测试用例。

### 测试1: 测试正确的用户名和密码能获取token

```python
def test_login_success():
    """正确的用户名和密码应该返回token"""
    response = client.post(
        "/api/login", 
        json={"username": "admin", "password": "sip@1234"}
    )
    assert response.status_code == 200
    assert "token" in response.json()
```

### 测试2: 测试错误的用户名或密码不能登录

```python
def test_login_wrong_password():
    """错误的密码应该返回401"""
    response = client.post(
        "/api/login", 
        json={"username": "admin", "password": "wrong"}
    )
    assert response.status_code == 401
```

### 测试3: 测试空密码不能登录

```python
def test_login_empty_password():
    """空密码应该返回401"""
    response = client.post(
        "/api/login", 
        json={"username": "admin", "password": ""}
    )
    assert response.status_code == 401
```

### 测试4: 测试缺少username字段

```python
def test_login_missing_username():
    """缺少username应该返回422（验证错误）"""
    response = client.post(
        "/api/login", 
        json={"password": "sip@1234"}
    )
    assert response.status_code == 422
```

## 验证测试失败

运行命令验证:
```bash
cd apps/api && python -m pytest tests/test_auth.py -v
```

## GREEN - 编写最小代码通过

当前代码已经通过所有测试。

## REFACTOR - 优化

测试已经是最小形式，无需重构。