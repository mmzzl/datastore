# Design: Plugin System and User Management

## Context

### 当前状态

**策略系统：**
- 内置 5 种策略（MA Cross, RSI, Bollinger, MACD, Qlib Model）
- StrategyFactory 已有 PLUGIN 类型占位，但未完整实现
- 上传 API 骨架存在（`/plugins/upload`），但验证逻辑不完善
- 前端已有 "plugin" 选项，但无上传和管理 UI

**用户系统：**
- 单用户模式，配置文件定义（`auth_username`, `auth_password`）
- JWT payload 仅包含 `{sub: username}`
- 无角色概念，无权限控制
- 所有 API 无权限检查

### 约束

1. **向后兼容**：现有 API 不能破坏性变更，需平滑迁移
2. **安全优先**：插件代码需静态检查，用户密码需安全存储
3. **性能考虑**：权限检查不能显著增加延迟
4. **扩展性**：权限系统需支持未来新增资源

## Goals / Non-Goals

**Goals:**

1. 建立标准化的策略插件体系，用户可自助上传和管理策略
2. 实现完整的 RBAC 权限系统，支持多用户协作
3. 提供统一的策略执行入口，便于记录和审计
4. 确保系统安全，包括插件安全检查和用户权限隔离

**Non-Goals:**

1. 不实现插件沙箱隔离（采用权限控制替代）
2. 不实现插件市场/远程下载（仅支持本地 ZIP 上传）
3. 不实现 OAuth/LDAP 等外部认证（仅支持用户名密码）
4. 不实现复杂的参数依赖关系（预留扩展字段）

## Decisions

### 1. 插件存储策略

**决策：** 插件代码存储在文件系统，元数据存储在 MongoDB

**理由：**
- 文件系统便于动态导入（`importlib`）
- MongoDB 便于查询和管理（版本、状态、统计）
- 代码文件需要 Python 解释器加载，放在文件系统更自然

**替代方案：**
- 全部存 MongoDB：需要每次加载时写文件，复杂且性能差
- 全部存文件系统：查询和统计需要遍历目录，效率低

**目录结构：**

```
app/backtest/strategies/plugins/
├── __init__.py
├── turtle_trading/           # v1.0.0
│   ├── __init__.py
│   ├── strategy.py
│   └── manifest.json
├── turtle_trading_1.1.0/     # v1.1.0 (同策略新版本)
│   └── ...
└── double_ma/
    └── ...
```

### 2. 版本管理机制

**决策：** 目录名带版本号，同名插件多版本共存

**版本规则：**

| 场景 | 处理 |
|------|------|
| 新插件（name 不存在） | 创建 `{name}/` |
| 同名，新版本（version > existing） | 创建 `{name}_{version}/` |
| 同名，版本相同 | 拒绝：提示版本已存在 |
| 同名，低版本 | 拒绝：提示已有更高版本 |

**理由：**
- 版本共存便于回滚
- 不覆盖确保稳定性
- 用户可选择使用哪个版本

### 3. 用户密码存储

**决策：** 使用 bcrypt 哈希

**理由：**
- bcrypt 自动加盐，抗彩虹表攻击
- 可配置工作因子，适应算力增长
- Python 标准库支持，无额外依赖

**实现：**

```python
import bcrypt

# 创建
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))

# 验证
bcrypt.checkpw(password.encode(), stored_hash.encode())
```

### 4. 权限检查方式

**决策：** FastAPI 依赖注入 + 装饰器

**理由：**
- 原生支持，与框架集成好
- 便于测试（可 mock）
- 声明式，代码清晰

**实现：**

```python
def require_permission(permission: str):
    async def checker(user = Depends(get_current_user)):
        if user.is_superuser:
            return user
        if permission not in user.permissions:
            raise HTTPException(403, f"Missing permission: {permission}")
        return user
    return checker

@router.post("/plugins/upload")
async def upload(user = Depends(require_permission("plugin:upload"))):
    ...
```

### 5. JWT Payload 结构

**决策：** 包含用户 ID、角色、权限列表

**Payload：**

```json
{
  "sub": "user_id_123",
  "username": "zhang_san",
  "role_id": "role_trader",
  "permissions": ["backtest:run", "backtest:view", ...],
  "is_superuser": false,
  "exp": 1704067200,
  "iat": 1703980800
}
```

**理由：**
- 缓存权限避免每次请求查库
- 前端可根据权限隐藏/禁用功能
- 权限变更需重新登录（简单有效）

**替代方案：**
- 仅存用户 ID：每次请求查库，性能差
- 存完整角色信息：payload 过大

### 6. 统一执行入口设计

**决策：** 实现 `ActionRunner.run_action(action_json)`

**结构：**

```json
{
  "command": "run_backtest",
  "instance": {
    "data_source": "mongodb",
    "stock_pool": "csi300"
  },
  "param": {
    "strategy": "plugin",
    "plugin_id": "turtle_trading",
    "entry_period": 20
  }
}
```

**理由：**
- 统一接口便于审计和日志
- instance 和 param 分离，配置清晰
- 易于扩展新命令

**实现：**

```python
class ActionRunner:
    async def run_action(self, action: dict) -> dict:
        command = action["command"]
        instance = action.get("instance", {})
        params = action.get("param", {})
        
        handlers = {
            "run_backtest": self._run_backtest,
            "run_selection": self._run_selection,
            "validate_plugin": self._validate_plugin,
        }
        
        handler = handlers.get(command)
        if not handler:
            raise ValueError(f"Unknown command: {command}")
        
        return await handler(instance, params)
```

### 7. 系统初始化策略

**决策：** 首次启动时检测用户数，为零则初始化

**流程：**

1. 检查 `users` 集合文档数
2. 若 count == 0：
   - 创建超级管理员角色
   - 创建管理员角色
   - 创建交易员角色
   - 创建观察者角色
   - 创建默认管理员用户（从配置读取）
3. 若 count > 0：跳过初始化

**理由：**
- 幂等操作，多次执行安全
- 支持手动创建用户后跳过初始化
- 配置文件定义默认账号，符合运维习惯

## Risks / Trade-offs

### Risk 1: 插件代码安全风险

**风险：** 恶意用户上传包含危险代码的插件

**缓解措施：**
- AST 静态分析：禁止导入危险模块（os, subprocess, socket, eval, exec）
- 权限控制：仅允许 `plugin:upload` 权限用户上传
- 审计日志：记录所有上传操作
- 代码审查：建议关键系统在生产环境启用人工审核

### Risk 2: JWT 权限缓存导致权限延迟生效

**风险：** 管理员修改用户角色后，用户需重新登录才能生效

**缓解措施：**
- 文档明确说明此行为
- 提供强制登出功能
- 可选：实现 JWT 黑名单（增加复杂度，暂不实现）

### Risk 3: 插件版本冲突

**风险：** 多版本插件可能导致混乱

**缓解措施：**
- 每个插件有明确的 active_version 标记
- 用户可切换版本，但同一时间只有一个版本激活
- 删除插件时删除所有版本

### Risk 4: 迁移期间认证不兼容

**风险：** 现有用户使用旧认证方式无法登录

**缓解措施：**
- 保留配置文件中的默认管理员作为兜底
- 提供迁移脚本：`python scripts/migrate_users.py`
- 文档明确迁移步骤

## Migration Plan

### Phase 1: 数据层准备

1. 创建 MongoDB 集合（users, roles, strategy_plugins, plugin_versions, action_logs）
2. 添加索引
3. 创建预置角色文档

### Phase 2: 后端迁移

1. 实现用户模型和认证逻辑
2. 实现权限检查装饰器
3. 迁移现有 API 端点添加权限检查
4. 实现插件管理 API
5. 实现统一执行入口

### Phase 3: 前端迁移

1. 更新登录逻辑适配新 API
2. 添加权限状态管理
3. 实现用户管理页面
4. 实现角色管理页面
5. 实现插件管理页面
6. 更新回测/选股页面支持插件策略

### Phase 4: 初始化和测试

1. 实现系统初始化逻辑
2. 端到端测试：
   - 默认管理员登录
   - 创建新用户并分配角色
   - 上传插件并执行回测
   - 权限验证（无权限用户被拒绝）

### Rollback Strategy

若出现严重问题：

1. **认证回滚**：恢复 `auth.py` 使用配置文件认证
2. **插件回滚**：禁用插件上传端点，保留内置策略
3. **数据库回滚**：删除新增集合，不影响现有数据

## Open Questions

1. **密码策略？** 
   - 是否强制密码复杂度？
   - 是否设置密码过期时间？
   - 建议：初期简单，后续可扩展

2. **插件审核流程？**
   - 是否需要人工审核后才能激活？
   - 建议：初期自动激活，生产环境可配置审核

3. **多租户隔离？**
   - 用户之间的数据是否需要隔离？
   - 建议：初期共享，后续可扩展租户字段
