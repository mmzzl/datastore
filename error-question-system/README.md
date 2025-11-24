# 错题本系统 (Error Question System)

一个基于uni-app和Django的智能错题本系统，帮助学生收集、整理、解答和复习错题。

## 功能特性

- **错题录入**: 支持拍照、手动输入等方式录入错题
- **智能解答**: 基于AI的错题解答和解析
- **分类管理**: 按学科、难度、知识点等维度分类错题
- **智能检索**: 支持关键词、标签、时间等多维度检索
- **统计分析**: 错题趋势分析和学习建议
- **多端同步**: 支持手机、平板、电脑等多端数据同步

## 技术栈

### 后端
- **框架**: Django 4.2
- **API**: Django REST Framework
- **数据库**: MySQL 8.0
- **缓存**: Redis
- **任务队列**: Celery
- **认证**: JWT
- **文档**: drf-spectacular (Swagger/OpenAPI)

### 前端
- **框架**: uni-app
- **UI组件**: uView UI
- **状态管理**: Vuex
- **网络请求**: uni.request

### 部署
- **容器化**: Docker & Docker Compose
- **Web服务器**: Nginx
- **进程管理**: Gunicorn

## 项目结构

```
error-question-system/
├── backend/                 # Django后端
│   ├── apps/                # 应用模块
│   │   ├── authentication/  # 认证模块
│   │   ├── questions/       # 题目模块
│   │   ├── answers/         # 答案模块
│   │   ├── categories/      # 分类模块
│   │   ├── search/          # 搜索模块
│   │   └── common/          # 公共模块
│   ├── config/              # 项目配置
│   ├── logs/                # 日志文件
│   ├── media/               # 媒体文件
│   ├── static/              # 静态文件
│   └── tests/               # 测试文件
├── frontend/                # uni-app前端
│   ├── pages/               # 页面
│   ├── components/          # 组件
│   ├── utils/               # 工具函数
│   ├── static/              # 静态资源
│   ├── api/                 # API接口
│   └── store/               # 状态管理
├── docs/                    # 项目文档
│   ├── api/                 # API文档
│   ├── deployment/          # 部署文档
│   └── user-guide/          # 用户指南
├── nginx/                   # Nginx配置
└── docker-compose.yml       # Docker编排
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 16+
- MySQL 8.0+
- Redis 6.0+
- Docker & Docker Compose (可选)

### 本地开发

1. **克隆项目**
   ```bash
   git clone https://github.com/yourusername/error-question-system.git
   cd error-question-system
   ```

2. **后端设置**
   ```bash
   cd backend
   
   # 创建虚拟环境
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   
   # 安装依赖
   pip install -r requirements.txt
   
   # 配置环境变量
   cp .env.example .env
   # 编辑.env文件，配置数据库等信息
   
   # 数据库迁移
   python manage.py makemigrations
   python manage.py migrate
   
   # 创建超级用户
   python manage.py createsuperuser
   
   # 启动开发服务器
   python manage.py runserver
   ```

3. **前端设置**
   ```bash
   cd frontend
   
   # 安装依赖（注意使用--legacy-peer-deps解决依赖冲突）
   npm install --legacy-peer-deps
   
   # 启动开发服务器
   npx vite
   # 或
   npm run serve
   ```

### Docker部署

1. **使用Docker Compose启动所有服务**
   ```bash
   docker-compose up -d
   ```

2. **数据库迁移**
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

3. **创建超级用户**
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

## API文档

启动后端服务后，可以通过以下地址访问API文档：

- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## 常见问题与解决方案

### 1. TypeError: Cannot set properties of null (setting 'exmid')

**问题描述**：在某些浏览器或环境下启动应用时出现此错误。

**解决方案**：
- 系统已修复此问题，通过在`index.html`中添加安全的DOM操作代理
- 确保所有DOM操作前进行空值检查

### 2. 依赖安装失败

**问题描述**：npm install 出现 peer dependency conflicts

**解决方案**：
- 使用 `npm install --legacy-peer-deps` 命令安装依赖

## 使用教程

### 添加错题

1. 在首页点击「添加错题」按钮
2. 填写题目标题、选择分类
3. 输入题目内容，可以上传题目图片（最多3张）
4. 填写题目答案和解题思路
5. 设置难度等级和掌握状态
6. 点击「保存」按钮完成添加

### 管理错题

1. 在首页点击「错题列表」查看所有错题
2. 可以按分类、状态、难度筛选错题
3. 点击错题项进入详情页面
4. 在详情页面可以编辑或删除错题

### 搜索错题

1. 在首页点击「搜索错题」按钮
2. 在搜索框输入关键词
3. 搜索结果会实时显示

### 分类管理

1. 在首页点击「错题分类」进入分类管理
2. 可以创建新分类、编辑或删除现有分类
3. 点击分类可以查看该分类下的所有错题

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

- 项目维护者: [Your Name](mailto:your.email@example.com)
- 项目链接: [https://github.com/yourusername/error-question-system](https://github.com/yourusername/error-question-system)