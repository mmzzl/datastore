# Error Question System API 文档

## 概述

Error Question System 是一个错题管理和学习系统，提供错题记录、解答、分类、搜索等功能。本文档详细描述了系统的API接口。

## 基础信息

- **基础URL**: `http://127.0.0.1:8000/api/`
- **认证方式**: JWT Token
- **数据格式**: JSON
- **API版本**: v1

## 认证

大部分API需要在请求头中包含JWT Token：

```
Authorization: Bearer <your-jwt-token>
```

## API 端点

### 1. 认证模块 (Authentication)

#### 1.1 用户注册
- **URL**: `/api/auth/register/`
- **方法**: POST
- **描述**: 注册新用户
- **请求体**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "password_confirm": "string",
  "phone": "string (可选)",
  "nickname": "string (可选)"
}
```
- **响应**:
```json
{
  "user": {
    "id": "integer",
    "username": "string",
    "email": "string",
    "nickname": "string",
    "phone": "string",
    "is_verified": "boolean",
    "created_at": "datetime"
  },
  "tokens": {
    "refresh": "string",
    "access": "string"
  }
}
```

#### 1.2 用户登录
- **URL**: `/api/auth/login/`
- **方法**: POST
- **描述**: 用户登录获取Token
- **请求体**:
```json
{
  "email": "string",
  "password": "string"
}
```
- **响应**:
```json
{
  "user": {
    "id": "integer",
    "username": "string",
    "email": "string",
    "nickname": "string",
    "is_verified": "boolean"
  },
  "tokens": {
    "refresh": "string",
    "access": "string"
  }
}
```

#### 1.3 刷新Token
- **URL**: `/api/auth/token/refresh/`
- **方法**: POST
- **描述**: 使用刷新Token获取新的访问Token
- **请求体**:
```json
{
  "refresh": "string"
}
```
- **响应**:
```json
{
  "access": "string"
}
```

#### 1.4 用户登出
- **URL**: `/api/auth/logout/`
- **方法**: POST
- **描述**: 用户登出，使Token失效
- **请求头**: 需要认证
- **响应**:
```json
{
  "message": "成功登出"
}
```

#### 1.5 获取用户资料
- **URL**: `/api/auth/profile/`
- **方法**: GET
- **描述**: 获取当前用户的详细资料
- **请求头**: 需要认证
- **响应**:
```json
{
  "id": "integer",
  "username": "string",
  "email": "string",
  "nickname": "string",
  "phone": "string",
  "avatar": "string",
  "bio": "string",
  "birth_date": "date",
  "gender": "string",
  "school": "string",
  "grade": "string",
  "is_verified": "boolean",
  "profile": {
    "study_subjects": ["array"],
    "difficulty_preference": "integer",
    "daily_target": "integer",
    "total_questions": "integer",
    "solved_questions": "integer",
    "study_days": "integer",
    "consecutive_days": "integer",
    "accuracy_rate": "float"
  }
}
```

#### 1.6 更新用户资料
- **URL**: `/api/auth/profile/`
- **方法**: PUT/PATCH
- **描述**: 更新当前用户的资料
- **请求头**: 需要认证
- **请求体**:
```json
{
  "nickname": "string (可选)",
  "phone": "string (可选)",
  "bio": "string (可选)",
  "birth_date": "date (可选)",
  "gender": "string (可选)",
  "school": "string (可选)",
  "grade": "string (可选)",
  "profile": {
    "study_subjects": ["array"] (可选),
    "difficulty_preference": "integer" (可选),
    "daily_target": "integer" (可选)
  }
}
```

#### 1.7 修改密码
- **URL**: `/api/auth/change-password/`
- **方法**: POST
- **描述**: 修改用户密码
- **请求头**: 需要认证
- **请求体**:
```json
{
  "old_password": "string",
  "new_password": "string",
  "new_password_confirm": "string"
}
```

#### 1.8 登录历史
- **URL**: `/api/auth/login-history/`
- **方法**: GET
- **描述**: 获取用户登录历史记录
- **请求头**: 需要认证
- **响应**:
```json
{
  "count": "integer",
  "results": [
    {
      "id": "integer",
      "ip_address": "string",
      "device": "string",
      "browser": "string",
      "os": "string",
      "location": "string",
      "login_time": "datetime",
      "logout_time": "datetime"
    }
  ]
}
```

### 2. 问题模块 (Questions)

#### 2.1 学科列表
- **URL**: `/api/questions/subjects/`
- **方法**: GET
- **描述**: 获取所有学科列表
- **响应**:
```json
{
  "count": "integer",
  "results": [
    {
      "id": "integer",
      "name": "string",
      "icon": "string",
      "description": "string",
      "color": "string",
      "is_active": "boolean",
      "sort_order": "integer"
    }
  ]
}
```

#### 2.2 知识点列表
- **URL**: `/api/questions/knowledge-points/`
- **方法**: GET
- **描述**: 获取所有知识点列表
- **查询参数**:
  - `subject_id`: 学科ID (可选)
  - `parent_id`: 父知识点ID (可选)
- **响应**:
```json
{
  "count": "integer",
  "results": [
    {
      "id": "integer",
      "subject": {
        "id": "integer",
        "name": "string"
      },
      "name": "string",
      "parent": {
        "id": "integer",
        "name": "string"
      },
      "level": "integer",
      "description": "string",
      "is_active": "boolean",
      "sort_order": "integer"
    }
  ]
}
```

#### 2.3 问题列表
- **URL**: `/api/questions/questions/`
- **方法**: GET
- **描述**: 获取问题列表
- **查询参数**:
  - `subject`: 学科ID (可选)
  - `knowledge_points`: 知识点ID (可选)
  - `difficulty`: 难度 (1-3) (可选)
  - `question_type`: 题目类型 (可选)
  - `is_solved`: 是否已解决 (可选)
  - `is_marked`: 是否已标记 (可选)
  - `search`: 搜索关键词 (可选)
- **请求头**: 需要认证
- **响应**:
```json
{
  "count": "integer",
  "next": "string",
  "previous": "string",
  "results": [
    {
      "id": "integer",
      "user": {
        "id": "integer",
        "username": "string",
        "nickname": "string"
      },
      "subject": {
        "id": "integer",
        "name": "string",
        "color": "string"
      },
      "knowledge_points": [
        {
          "id": "integer",
          "name": "string"
        }
      ],
      "title": "string",
      "content": "string",
      "question_type": "string",
      "options": "object",
      "correct_answer": "string",
      "user_answer": "string",
      "analysis": "string",
      "difficulty": "integer",
      "source": "string",
      "source_detail": "string",
      "tags": "array",
      "images": "array",
      "is_solved": "boolean",
      "is_marked": "boolean",
      "view_count": "integer",
      "created_at": "datetime",
      "updated_at": "datetime",
      "last_reviewed_at": "datetime",
      "review_count": "integer"
    }
  ]
}
```

#### 2.4 创建问题
- **URL**: `/api/questions/questions/`
- **方法**: POST
- **描述**: 创建新问题
- **请求头**: 需要认证
- **请求体**:
```json
{
  "subject": "integer",
  "knowledge_points": ["array"],
  "title": "string",
  "content": "string",
  "question_type": "string",
  "options": "object (可选)",
  "correct_answer": "string (可选)",
  "user_answer": "string (可选)",
  "analysis": "string (可选)",
  "difficulty": "integer",
  "source": "string (可选)",
  "source_detail": "string (可选)",
  "tags": "array (可选)",
  "images": "array (可选)",
  "is_solved": "boolean (可选)",
  "is_marked": "boolean (可选)"
}
```

#### 2.5 问题详情
- **URL**: `/api/questions/questions/{id}/`
- **方法**: GET
- **描述**: 获取问题详情
- **请求头**: 需要认证
- **响应**: 同问题列表中的单个问题对象

#### 2.6 更新问题
- **URL**: `/api/questions/questions/{id}/`
- **方法**: PUT/PATCH
- **描述**: 更新问题
- **请求头**: 需要认证
- **请求体**: 同创建问题

#### 2.7 删除问题
- **URL**: `/api/questions/questions/{id}/`
- **方法**: DELETE
- **描述**: 删除问题
- **请求头**: 需要认证

#### 2.8 问题标签列表
- **URL**: `/api/questions/tags/`
- **方法**: GET
- **描述**: 获取所有问题标签
- **响应**:
```json
{
  "count": "integer",
  "results": [
    {
      "id": "integer",
      "name": "string",
      "color": "string",
      "usage_count": "integer"
    }
  ]
}
```

### 3. 答案模块 (Answers)

#### 3.1 答案列表
- **URL**: `/api/answers/answers/`
- **方法**: GET
- **描述**: 获取答案列表
- **查询参数**:
  - `question`: 问题ID (可选)
  - `user`: 用户ID (可选)
  - `is_verified`: 是否已验证 (可选)
  - `is_public`: 是否公开 (可选)
- **请求头**: 需要认证
- **响应**:
```json
{
  "count": "integer",
  "next": "string",
  "previous": "string",
  "results": [
    {
      "id": "integer",
      "question": {
        "id": "integer",
        "title": "string"
      },
      "user": {
        "id": "integer",
        "username": "string",
        "nickname": "string"
      },
      "content": "string",
      "explanation": "string",
      "steps": "array",
      "images": "array",
      "source": "string",
      "is_verified": "boolean",
      "is_public": "boolean",
      "likes_count": "integer",
      "views_count": "integer",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  ]
}
```

#### 3.2 创建答案
- **URL**: `/api/answers/answers/`
- **方法**: POST
- **描述**: 为问题创建答案
- **请求头**: 需要认证
- **请求体**:
```json
{
  "question": "integer",
  "content": "string",
  "explanation": "string (可选)",
  "steps": "array (可选)",
  "images": "array (可选)",
  "source": "string (可选)",
  "is_public": "boolean (可选)"
}
```

#### 3.3 答案详情
- **URL**: `/api/answers/answers/{id}/`
- **方法**: GET
- **描述**: 获取答案详情
- **请求头**: 需要认证
- **响应**: 同答案列表中的单个答案对象

#### 3.4 更新答案
- **URL**: `/api/answers/answers/{id}/`
- **方法**: PUT/PATCH
- **描述**: 更新答案
- **请求头**: 需要认证
- **请求体**: 同创建答案

#### 3.5 删除答案
- **URL**: `/api/answers/answers/{id}/`
- **方法**: DELETE
- **描述**: 删除答案
- **请求头**: 需要认证

#### 3.6 答案评论列表
- **URL**: `/api/answers/comments/`
- **方法**: GET
- **描述**: 获取答案评论列表
- **查询参数**:
  - `answer`: 答案ID (可选)
  - `user`: 用户ID (可选)
  - `parent`: 父评论ID (可选)
- **请求头**: 需要认证
- **响应**:
```json
{
  "count": "integer",
  "next": "string",
  "previous": "string",
  "results": [
    {
      "id": "integer",
      "answer": {
        "id": "integer",
        "question": {
          "id": "integer",
          "title": "string"
        }
      },
      "user": {
        "id": "integer",
        "username": "string",
        "nickname": "string"
      },
      "parent": {
        "id": "integer",
        "content": "string"
      },
      "content": "string",
      "is_deleted": "boolean",
      "likes_count": "integer",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  ]
}
```

#### 3.7 创建评论
- **URL**: `/api/answers/comments/`
- **方法**: POST
- **描述**: 为答案创建评论
- **请求头**: 需要认证
- **请求体**:
```json
{
  "answer": "integer",
  "content": "string",
  "parent": "integer (可选)"
}
```

#### 3.8 点赞答案
- **URL**: `/api/answers/answers/{id}/like/`
- **方法**: POST
- **描述**: 点赞答案
- **请求头**: 需要认证

#### 3.9 取消点赞答案
- **URL**: `/api/answers/answers/{id}/unlike/`
- **方法**: POST
- **描述**: 取消点赞答案
- **请求头**: 需要认证

### 4. 分类模块 (Categories)

#### 4.1 分类列表
- **URL**: `/api/categories/categories/`
- **方法**: GET
- **描述**: 获取分类列表
- **查询参数**:
  - `parent`: 父分类ID (可选)
  - `is_system`: 是否系统分类 (可选)
  - `is_active`: 是否启用 (可选)
- **请求头**: 需要认证
- **响应**:
```json
{
  "count": "integer",
  "results": [
    {
      "id": "integer",
      "user": {
        "id": "integer",
        "username": "string"
      },
      "name": "string",
      "description": "string",
      "color": "string",
      "icon": "string",
      "parent": {
        "id": "integer",
        "name": "string"
      },
      "level": "integer",
      "sort_order": "integer",
      "is_system": "boolean",
      "is_active": "boolean",
      "created_at": "datetime",
      "updated_at": "datetime",
      "children_count": "integer",
      "questions_count": "integer"
    }
  ]
}
```

#### 4.2 创建分类
- **URL**: `/api/categories/categories/`
- **方法**: POST
- **描述**: 创建新分类
- **请求头**: 需要认证
- **请求体**:
```json
{
  "name": "string",
  "description": "string (可选)",
  "color": "string (可选)",
  "icon": "string (可选)",
  "parent": "integer (可选)",
  "sort_order": "integer (可选)",
  "is_system": "boolean (可选)",
  "is_active": "boolean (可选)"
}
```

#### 4.3 分类详情
- **URL**: `/api/categories/categories/{id}/`
- **方法**: GET
- **描述**: 获取分类详情
- **请求头**: 需要认证
- **响应**: 同分类列表中的单个分类对象

#### 4.4 更新分类
- **URL**: `/api/categories/categories/{id}/`
- **方法**: PUT/PATCH
- **描述**: 更新分类
- **请求头**: 需要认证
- **请求体**: 同创建分类

#### 4.5 删除分类
- **URL**: `/api/categories/categories/{id}/`
- **方法**: DELETE
- **描述**: 删除分类
- **请求头**: 需要认证

#### 4.6 问题分类关联
- **URL**: `/api/categories/question-categories/`
- **方法**: GET
- **描述**: 获取问题与分类的关联关系
- **查询参数**:
  - `question`: 问题ID (可选)
  - `category`: 分类ID (可选)
- **请求头**: 需要认证
- **响应**:
```json
{
  "count": "integer",
  "results": [
    {
      "id": "integer",
      "question": {
        "id": "integer",
        "title": "string"
      },
      "category": {
        "id": "integer",
        "name": "string"
      },
      "created_at": "datetime"
    }
  ]
}
```

#### 4.7 添加问题到分类
- **URL**: `/api/categories/question-categories/`
- **方法**: POST
- **描述**: 将问题添加到分类
- **请求头**: 需要认证
- **请求体**:
```json
{
  "question": "integer",
  "category": "integer"
}
```

#### 4.8 从分类中移除问题
- **URL**: `/api/categories/question-categories/{id}/`
- **方法**: DELETE
- **描述**: 从分类中移除问题
- **请求头**: 需要认证

### 5. 搜索模块 (Search)

#### 5.1 搜索问题
- **URL**: `/api/search/search/`
- **方法**: GET
- **描述**: 搜索问题
- **查询参数**:
  - `q`: 搜索关键词
  - `subject`: 学科ID (可选)
  - `knowledge_points`: 知识点ID (可选)
  - `difficulty`: 难度 (1-3) (可选)
  - `question_type`: 题目类型 (可选)
  - `is_solved`: 是否已解决 (可选)
- **请求头**: 需要认证
- **响应**:
```json
{
  "count": "integer",
  "next": "string",
  "previous": "string",
  "results": [
    {
      "id": "integer",
      "user": {
        "id": "integer",
        "username": "string",
        "nickname": "string"
      },
      "subject": {
        "id": "integer",
        "name": "string",
        "color": "string"
      },
      "knowledge_points": [
        {
          "id": "integer",
          "name": "string"
        }
      ],
      "title": "string",
      "content": "string",
      "question_type": "string",
      "difficulty": "integer",
      "is_solved": "boolean",
      "is_marked": "boolean",
      "created_at": "datetime",
      "relevance_score": "float"
    }
  ]
}
```

#### 5.2 搜索历史
- **URL**: `/api/search/history/`
- **方法**: GET
- **描述**: 获取用户搜索历史
- **请求头**: 需要认证
- **响应**:
```json
{
  "count": "integer",
  "results": [
    {
      "id": "string",
      "query": "string",
      "filters": "object",
      "results_count": "integer",
      "ip_address": "string",
      "user_agent": "string",
      "search_time": "float",
      "created_at": "datetime"
    }
  ]
}
```

#### 5.3 记录搜索历史
- **URL**: `/api/search/history/`
- **方法**: POST
- **描述**: 记录搜索历史
- **请求头**: 需要认证
- **请求体**:
```json
{
  "query": "string",
  "filters": "object (可选)",
  "results_count": "integer",
  "ip_address": "string (可选)",
  "user_agent": "string (可选)",
  "search_time": "float (可选)"
}
```

#### 5.4 搜索建议
- **URL**: `/api/search/suggestions/`
- **方法**: GET
- **描述**: 获取搜索建议
- **查询参数**:
  - `q`: 搜索关键词前缀
- **响应**:
```json
{
  "count": "integer",
  "results": [
    {
      "id": "string",
      "keyword": "string",
      "frequency": "integer",
      "is_active": "boolean"
    }
  ]
}
```

#### 5.5 热门搜索
- **URL**: `/api/search/popular/`
- **方法**: GET
- **描述**: 获取热门搜索关键词
- **响应**:
```json
{
  "count": "integer",
  "results": [
    {
      "id": "string",
      "keyword": "string",
      "search_count": "integer",
      "last_searched_at": "datetime",
      "is_active": "boolean"
    }
  ]
}
```

### 6. API文档端点

#### 6.1 API Schema
- **URL**: `/api/schema/`
- **方法**: GET
- **描述**: 获取OpenAPI 3.0规范的API Schema

#### 6.2 Swagger UI
- **URL**: `/api/swagger-ui/`
- **方法**: GET
- **描述**: 访问Swagger UI界面

#### 6.3 ReDoc
- **URL**: `/api/redoc/`
- **方法**: GET
- **描述**: 访问ReDoc文档界面

## 错误响应

所有API在出错时会返回标准的错误响应格式：

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object (可选)"
  }
}
```

常见错误代码：
- `400`: 请求参数错误
- `401`: 未认证或Token无效
- `403`: 权限不足
- `404`: 资源不存在
- `429`: 请求频率限制
- `500`: 服务器内部错误

## 分页

列表API默认使用分页，每页默认20条记录。可以通过以下查询参数控制分页：

- `page`: 页码 (默认: 1)
- `page_size`: 每页记录数 (默认: 20, 最大: 100)

分页响应包含以下字段：

```json
{
  "count": "integer",  // 总记录数
  "next": "string",   // 下一页链接
  "previous": "string", // 上一页链接
  "results": "array"  // 当前页数据
}
```

## 限流

API实施了请求频率限制：
- 未认证用户: 每分钟100次请求
- 已认证用户: 每分钟1000次请求

超出限制将返回`429`状态码。

## 版本控制

当前API版本为v1。未来版本将通过URL路径进行版本控制，例如：
- v1: `/api/v1/...`
- v2: `/api/v2/...`

## 开发工具

### 在线文档
- Swagger UI: `http://127.0.0.1:8000/api/swagger-ui/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`

### API Schema
- OpenAPI 3.0 Schema: `http://127.0.0.1:8000/api/schema/`