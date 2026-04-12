## Why

用户需要一个基于策略的选股功能，能够使用内置策略或已上传的插件策略对股票池进行筛选。当前系统已有Qlib选股功能，但仅支持Qlib模型，无法复用用户上传的策略插件。用户需要：

1. 选股时能选择策略（内置策略或上传的插件）
2. 选择股票池范围（沪深300、中证500、全市场）
3. 获取AI分析结果，包括板块特征、风险提示、操作建议和市场趋势判断
4. 查看选股历史记录

## What Changes

### 新增功能
- 新增策略选股API端点，支持启动选股、获取结果、查询历史
- 新增选股引擎，复用现有策略工厂和插件系统
- 新增股票池服务，支持沪深300、中证500、全市场三种范围
- 新增AI分析功能，生成板块特征、风险提示、操作建议
- 新增市场趋势判断，基于金叉比例和多头排列比例分析市场强弱
- 新增前端选股页面，包含选股弹窗、结果展示、历史记录
- 选股结果保存到MongoDB，支持历史查询

### 复用现有组件
- 复用 `StrategyFactory` 创建策略实例
- 复用 `PluginRegistry` 获取已上传的插件策略
- 复用 `LLMClient` 进行AI分析
- 复用 `MongoStorage` 存储选股历史

## Capabilities

### New Capabilities
- `strategy-selection`: 策略选股核心功能 - 支持选择策略和股票池进行选股，返回评分、信号强度、技术指标
- `selection-ai-analysis`: 选股AI分析 - 对选股结果进行AI分析，生成板块特征、风险提示、操作建议
- `market-trend-analysis`: 市场趋势判断 - 基于金叉比例和多头排列比例判断市场强弱
- `selection-history`: 选股历史管理 - 存储和查询选股历史记录

### Modified Capabilities

无。本功能为新增模块，不修改现有capability的需求规格。

## Impact

### 后端影响
- 新增 `apps/api/app/api/endpoints/stock_selection.py` - 选股API端点
- 新增 `apps/api/app/stock_selection/` - 选股服务模块
  - `engine.py` - 选股引擎
  - `stock_pool.py` - 股票池服务
  - `ai_analyzer.py` - AI分析器
- 新增 `apps/api/app/schemas/stock_selection.py` - 选股数据模型
- 新增MongoDB collection: `stock_selections` - 选股历史存储

### 前端影响
- 新增 `StockSelectionView.vue` - 选股主页面
- 新增 `StockSelectionDialog.vue` - 选股配置弹窗
- 新增 `StockResultCard.vue` - 股票结果卡片
- 新增 `stores/stockSelection.ts` - 选股状态管理
- 新增 `services/api_stock_selection.ts` - 选股API服务
- 更新路由配置，添加选股页面路由

### 数据文件
- 使用现有 `hs300_stocks.csv` 和 `zz500_stocks.csv`
- 使用现有 `stock_industry.csv` 获取行业分类

### 权限影响
- 新增权限: `selection:run` - 执行选股
- 新增权限: `selection:view` - 查看选股结果和历史
