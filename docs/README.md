# 项目文档

本文档目录包含项目的所有技术文档、API文档、测试报告和开发指南。

## 目录结构

```
docs/
├── api/                    # API 相关文档
│   ├── guides/            # API 开发指南
│   ├── plans/             # API 开发计划
│   ├── REQ-2025-001/      # 需求文档
│   └── superpowers/       # 高级功能文档
├── go-web-scraper/         # Go 爬虫项目文档
├── guides/                 # 通用指南和文档
│   ├── AFTER_MARKET_OVERVIEW.md
│   ├── AKSHARE_FIX_PLAN.md
│   ├── PROJECT_OPTIMIZATION_PLAN.md
│   ├── README_AFTER_MARKET.md
│   ├── README_stock_optimization.md
│   └── SETUP_GUIDE.md
└── testing/                # 测试相关文档
    ├── TDD-WORKFLOW-PROGRESS.md
    ├── 测试用例覆盖分析.md
    └── 错题本系统*.md
```

## 文档说明

### API 文档 (`api/`)
- 包含后端 API 的架构文档、功能说明和开发计划
- 包括数据源统一接口、智能交易系统等高级功能文档
- 包含需求分析文档 (URD, SRD, RDD)

### 爬虫文档 (`go-web-scraper/`)
- Go 语言爬虫框架的开发文档
- 包含 API 分析、TDD 测试用例、部署指南等

### 通用指南 (`guides/`)
- 项目整体概述和优化计划
- 环境搭建指南 (SETUP_GUIDE.md)
- 盘后服务和股票优化相关文档

### 测试文档 (`testing/`)
- TDD 工作流进度跟踪
- 测试用例和覆盖率报告
- 错题本系统测试相关文档
