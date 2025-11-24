# 错题本小程序

一个基于uniapp开发的错题管理小程序，帮助学生记录、管理和复习错题，提高学习效率。

## 功能特点

- 用户注册登录
- 错题添加、编辑、删除
- 错题分类管理
- 错题搜索和筛选
- 错题详情查看
- 解答记录
- 数据统计
- 用户反馈

## 技术栈

- 前端框架：uniapp
- UI组件：uView
- 状态管理：Vuex
- 网络请求：Axios
- 开发工具：HBuilderX

## 项目结构

```
├── api                 # API接口
│   ├── index.js       # API基础配置
│   └── modules.js     # API模块
├── components         # 公共组件
├── pages              # 页面
│   ├── index          # 首页
│   ├── login          # 登录页
│   ├── register       # 注册页
│   ├── profile        # 个人中心
│   ├── questions      # 错题相关
│   ├── category       # 分类管理
│   ├── search         # 搜索页
│   ├── about          # 关于页面
│   └── feedback       # 反馈页面
├── static             # 静态资源
├── store              # 状态管理
│   ├── index.js       # Store入口
│   └── modules        # Store模块
├── utils              # 工具函数
├── App.vue            # 应用入口
├── main.js            # 主入口文件
├── manifest.json      # 应用配置
├── pages.json         # 页面配置
└── uni.scss           # 全局样式
```

## 开发环境搭建

1. 安装HBuilderX开发工具
2. 克隆项目到本地
3. 在HBuilderX中打开项目
4. 安装依赖：
   ```bash
   npm install
   ```
5. 运行项目：
   ```bash
   npm run dev
   ```

## 部署说明

### 小程序部署

1. 在HBuilderX中点击"发行" -> "小程序-微信"
2. 填写小程序相关信息
3. 点击"发行"生成小程序代码包
4. 使用微信开发者工具打开生成的代码包
5. 在微信开发者工具中上传代码

### H5部署

1. 运行构建命令：
   ```bash
   npm run build:h5
   ```
2. 将生成的dist目录下的文件部署到Web服务器

## API接口

项目需要配合后端API使用，API接口文档请参考后端项目。

## 开发规范

1. 使用ESLint进行代码规范检查
2. 组件命名采用PascalCase
3. 文件命名采用kebab-case
4. 使用语义化的Git提交信息

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 发起Pull Request

## 许可证

MIT License