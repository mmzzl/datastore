# Proposal: Plugin System and User Management

## Why

当前系统存在两个核心问题：

1. **策略扩展困难**：回测系统只支持内置策略（MA、RSI、Bollinger、MACD），用户无法导入自定义策略。每次新增策略需要修改后端代码并重新部署，缺乏灵活性。

2. **用户管理不完善**：系统仅支持配置文件定义的单用户，无法动态添加用户、分配角色和权限，存在安全隐患。实际生产环境需要多用户协作，不同用户应有不同的操作权限。

这两个问题制约了系统的实用性和安全性，需要建立完整的插件体系和用户权限管理体系。

## What Changes

### 策略插件系统

- 新增策略插件上传功能，支持 ZIP 格式导入
- 定义插件标准规范（manifest.json + strategy.py）
- 实现插件版本管理机制（同名插件多版本共存）
- 建立插件验证体系（文件结构、元数据、代码安全检查）
- 提供统一执行入口 `run_action(action_json)`
- 前端新增插件管理页面（上传、列表、删除、切换版本）

### 用户管理系统

- **BREAKING**：用户从配置文件迁移到 MongoDB 存储
- 实现基于角色的访问控制（RBAC）
- 新增用户管理页面（创建、编辑、禁用、删除）
- 新增角色管理页面（创建、编辑、分配权限）
- 系统初始化时自动创建默认管理员（超级管理员）
- 权限控制贯穿所有 API 端点

## Capabilities

### New Capabilities

- `plugin-upload`: 策略插件上传、验证和安装
- `plugin-management`: 插件列表、版本切换、删除
- `plugin-execution`: 插件策略执行（回测、选股）
- `user-auth`: 用户认证（登录、登出、修改密码）
- `user-management`: 用户 CRUD 操作
- `role-management`: 角色 CRUD 操作及权限分配
- `permission-check`: API 权限检查装饰器
- `system-init`: 系统初始化（默认管理员、预置角色）

### Modified Capabilities

- `backtest`: 增加插件策略类型，增加权限检查
- `stock-selection`: 增加插件策略类型，增加权限检查
- `auth`: 从单用户配置改为数据库认证，JWT payload 增加角色信息

## Impact

### 后端影响

| 模块 | 变更 |
|------|------|
| `app/backtest/plugin/` | **新增** 插件验证、加载、注册模块 |
| `app/backtest/strategies/plugins/` | **新增** 插件存储目录 |
| `app/user/` | **新增** 用户管理模块 |
| `app/role/` | **新增** 角色管理模块 |
| `app/core/permissions.py` | **新增** 权限检查依赖 |
| `app/core/config.py` | **修改** 增加默认管理员配置 |
| `app/api/endpoints/auth.py` | **修改** 改用数据库认证 |
| `app/api/endpoints/backtest.py` | **修改** 增加插件上传端点、权限检查 |
| `app/middleware/auth_middleware.py` | **修改** 支持新的用户模型 |

### 前端影响

| 页面 | 变更 |
|------|------|
| `PluginManagerView.vue` | **新增** 插件管理页面 |
| `UserManagementView.vue` | **新增** 用户管理页面 |
| `RoleManagementView.vue` | **新增** 角色管理页面 |
| `BacktestView.vue` | **修改** 增加插件策略选择 |
| `QlibSelectView.vue` | **修改** 增加插件策略选择 |
| `LoginView.vue` | **修改** 适配新的认证 API |

### 数据库影响

| 集合 | 操作 |
|------|------|
| `users` | **新增** 用户数据集合 |
| `roles` | **新增** 角色数据集合 |
| `strategy_plugins` | **新增** 插件元数据集合 |
| `plugin_versions` | **新增** 插件版本历史集合 |
| `action_logs` | **新增** 统一执行入口日志集合 |

### 依赖影响

| 依赖 | 用途 |
|------|------|
| `bcrypt` | 密码哈希 |
| `python-multipart` | 文件上传支持 |

### API 变更

**新增端点:**

```
POST   /api/plugins/upload           # 上传插件
GET    /api/plugins                   # 列出插件
GET    /api/plugins/{id}              # 获取插件详情
DELETE /api/plugins/{id}              # 删除插件
POST   /api/plugins/{id}/activate     # 激活指定版本

POST   /api/action/run                # 统一执行入口

GET    /api/users                     # 列出用户
POST   /api/users                     # 创建用户
PUT    /api/users/{id}                # 更新用户
DELETE /api/users/{id}                # 删除用户
POST   /api/users/{id}/reset-password # 重置密码

GET    /api/roles                     # 列出角色
POST   /api/roles                     # 创建角色
PUT    /api/roles/{id}                # 更新角色
DELETE /api/roles/{id}                # 删除角色
```

**修改端点:**

```
POST /api/auth/token     # 返回包含角色信息的 JWT
POST /api/backtest/run   # 增加 plugin 策略类型，增加权限检查
POST /api/qlib/select    # 增加 plugin 策略类型，增加权限检查
```
