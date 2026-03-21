# Datastore 项目

数据存储和市场监控平台，包含后端 API、前端管理界面和相关工具。

## 项目结构

```
datastore/
├── case/                    # 主要后端项目
│   └── apps/
│       └── api/            # FastAPI 后端服务
├── frontend/                # 前端项目
│   └── vue-admin/          # Vue.js 管理界面
├── tests/                   # 集成测试
├── docs/                    # 项目文档
├── data/                    # 数据文件
├── scripts/                 # 工具脚本
├── archives/                # 归档项目（非活跃）
├── docker-compose.yml       # Docker 部署配置
├── pytest.ini               # 测试配置
└── README.md                # 本文件
```

## 快速开始

### 1. 环境要求

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose (可选)

### 2. 使用 Docker 部署（推荐）

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 停止服务
docker-compose down
```

服务端口：
- MongoDB: 27017
- API: 8000
- 前端: 80

### 3. 本地开发

#### 启动后端

```bash
cd case/apps/api
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 启动前端

```bash
cd frontend/vue-admin
npm install
npm run dev
```

### 4. 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行认证测试
pytest tests/test_auth*.py -v
```

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/login` | POST | 用户登录 |
| `/api/health` | GET | 健康检查 |
| `/api/holdings/{user_id}` | GET/POST | 持仓管理 |
| `/api/portfolio/{user_id}` | GET | 组合概览 |
| `/api/settings/{user_id}` | GET/POST | 用户设置 |
| `/api/signals/latest` | GET | 最新信号 |

## 认证

所有 API 端点（除 `/api/login` 和 `/api/health`）需要 Bearer Token 认证。

```bash
# 登录获取 token
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"user_id": "admin", "password": "admin123"}'

# 使用 token 访问受保护的端点
curl http://localhost:8000/api/holdings/default \
  -H "Authorization: Bearer <token>"
```

## 默认账户

- 用户名: `admin`
- 密码: `admin123`

## 开发

### 代码风格

```bash
# 格式化代码
ruff format .

# 检查代码质量
ruff check .
```

### 提交规范

```
feat: 添加新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建/工具链更新
```

## 许可证

MIT License
