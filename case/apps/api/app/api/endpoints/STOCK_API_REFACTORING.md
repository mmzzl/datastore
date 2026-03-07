# stock.py API端点重构说明

## 重构概述

本次重构主要针对 `stock.py` API端点的大数据量查询问题，通过分页查询、流式传输、数据导出等功能，解决数据量大时查询超时、内存溢出等问题。

## 主要问题分析

### 原有代码存在的问题

1. **大数据量直接返回**
   - 所有查询都直接返回完整数据，没有分页机制
   - 可能导致响应超时或内存溢出

2. **缺少数据量限制**
   - 虽然有 `limit` 参数，但默认值和最大值可能仍然过大
   - 没有针对不同场景的合理限制

3. **内存风险**
   - `get_all_stocks_klines` 接口可能在内存中加载大量数据
   - 没有使用流式处理或游标

4. **缺少数据导出功能**
   - 用户无法将大数据量导出为文件
   - 不便于离线分析

5. **超时风险**
   - 大数据量查询可能导致请求超时
   - 没有超时控制和优化

## 重构解决方案

### 1. 分页查询功能

#### 新增分页参数类
```python
@dataclass
class PaginationParams:
    """分页参数"""
    page: int = 1
    page_size: int = QueryConfig.DEFAULT_PAGE_SIZE
    
    @property
    def skip(self) -> int:
        """计算跳过的记录数"""
        return (self.page - 1) * self.page_size
```

#### 新增分页接口
- `get_stock_kline_paginated` - 单个股票K线分页查询
- `get_all_stocks_kline_paginated` - 所有股票K线分页查询
- `get_all_stocks_klines_paginated` - 全量数据分页查询

#### 分页响应格式
```json
{
  "success": true,
  "count": 100,
  "total": 1000,
  "page": 1,
  "page_size": 100,
  "total_pages": 10,
  "has_next": true,
  "has_prev": false,
  "data": [...]
}
```

### 2. 数据导出功能

#### 支持的导出格式
- **CSV** - 通用格式，兼容性好
- **JSON** - 结构化数据，便于程序处理
- **Excel** - 便于人工查看和分析

#### 导出接口
- `export_all_stocks_klines` - 导出所有股票K线数据
- `export_stock_kline` - 导出指定股票K线数据

#### 使用示例
```bash
# 导出为CSV
GET /stock/klines/export?start_date=2024-01-01&end_date=2024-01-31&format=csv

# 导出为JSON
GET /stock/kline/SH600000/export?start_date=2024-01-01&end_date=2024-01-31&format=json

# 导出为Excel
GET /stock/klines/export?start_date=2024-01-01&end_date=2024-01-31&format=excel
```

### 3. 数据验证和限制

#### QueryConfig 配置类
```python
@dataclass
class QueryConfig:
    """查询配置"""
    DEFAULT_PAGE_SIZE = 100          # 默认分页大小
    MAX_PAGE_SIZE = 1000             # 最大分页大小
    MAX_SINGLE_QUERY_RECORDS = 5000  # 单次查询最大记录数
    STREAM_BATCH_SIZE = 1000         # 流式查询每批大小
    MAX_EXPORT_RECORDS = 100000      # 导出功能最大记录数
    QUERY_TIMEOUT = 30               # 查询超时时间（秒）
```

#### DataValidator 验证器
- 日期范围验证
- Limit参数验证
- 导出数据量验证
- 参数合法性检查

### 4. 响应构建器

#### ResponseBuilder 类
- 统一的响应格式
- 成功响应构建
- 分页响应构建
- 错误响应构建

#### 标准响应格式
```json
{
  "success": true,
  "count": 100,
  "total": 1000,
  "data": [...],
  "params": {...}
}
```

### 5. 数据导出器

#### DataExporter 类
- CSV导出（支持UTF-8-BOM编码）
- JSON导出（格式化输出）
- Excel导出（使用openpyxl）
- 自动生成文件名（带时间戳）

## API接口清单

### 原有接口（保持兼容）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/stock/kline/{code}` | GET | 获取股票K线数据 |
| `/stock/kline/all/{date}` | GET | 获取指定日期所有股票K线数据 |
| `/stock/kline/{code}/{date}` | GET | 获取指定日期的股票K线数据 |
| `/stock/klines` | GET | 获取所有股票K线数据 |

### 新增接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/stock/kline/{code}/paginated` | GET | 获取股票K线数据（分页） |
| `/stock/kline/all/{date}/paginated` | GET | 获取指定日期所有股票K线数据（分页） |
| `/stock/klines/paginated` | GET | 获取所有股票K线数据（分页） |
| `/stock/klines/export` | GET | 导出所有股票K线数据 |
| `/stock/kline/{code}/export` | GET | 导出指定股票K线数据 |
| `/stock/stats` | GET | 获取数据库统计信息 |

## 使用指南

### 1. 基本查询（小数据量）

```bash
# 获取单个股票K线数据
GET /stock/kline/SH600000?start_date=2024-01-01&end_date=2024-01-31&limit=100

# 获取指定日期所有股票K线数据
GET /stock/kline/all/2024-01-15?limit=1000
```

### 2. 分页查询（大数据量推荐）

```bash
# 获取单个股票K线数据（分页）
GET /stock/kline/SH600000/paginated?start_date=2024-01-01&end_date=2024-01-31&page=1&page_size=100

# 获取所有股票K线数据（分页）
GET /stock/klines/paginated?start_date=2024-01-01&end_date=2024-01-31&page=1&page_size=1000
```

### 3. 数据导出

```bash
# 导出为CSV
GET /stock/klines/export?start_date=2024-01-01&end_date=2024-01-31&format=csv

# 导出为JSON
GET /stock/kline/SH600000/export?start_date=2024-01-01&end_date=2024-01-31&format=json

# 导出为Excel
GET /stock/klines/export?start_date=2024-01-01&end_date=2024-01-31&format=excel
```

### 4. 获取统计信息

```bash
# 获取数据库统计信息
GET /stock/stats
```

## 参数说明

### 分页参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码，从1开始 |
| page_size | int | 100 | 每页数量，最大1000 |

### 导出参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| format | enum | csv | 导出格式：csv/json/excel |

### 通用参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| start_date | string | null | 开始日期 (YYYY-MM-DD) |
| end_date | string | null | 结束日期 (YYYY-MM-DD) |
| limit | int | 100 | 返回数量限制，最大5000 |

## 性能优化

### 1. 分页查询
- 减少单次查询的数据量
- 降低内存占用
- 提高响应速度

### 2. 流式传输
- 导出功能使用流式响应
- 避免内存中存储大量数据
- 支持大文件下载

### 3. 查询限制
- 单次查询最大5000条记录
- 分页查询最大1000条/页
- 导出最大100000条记录

### 4. 参数验证
- 日期格式验证
- 参数范围验证
- 数据量限制验证

## 错误处理

### 标准错误响应
```json
{
  "success": false,
  "error": "错误信息",
  "timestamp": "2024-01-15T10:30:00"
}
```

### 常见错误码

| 状态码 | 说明 |
|--------|------|
| 400 | 参数错误 |
| 404 | 数据不存在 |
| 500 | 服务器错误 |

### 错误示例

```json
// 日期格式错误
{
  "success": false,
  "error": "日期格式错误，请使用 YYYY-MM-DD 格式"
}

// 导出数据量超限
{
  "success": false,
  "error": "导出数据量 150000 超过最大限制 100000，请缩小查询范围或使用分页查询"
}

// 数据不存在
{
  "success": false,
  "error": "数据不存在"
}
```

## 兼容性说明

### 向后兼容
- ✅ 保留所有原有接口
- ✅ 原有接口参数和响应格式不变
- ✅ 现有客户端无需修改

### 新增功能
- ✅ 分页查询接口
- ✅ 数据导出接口
- ✅ 统计信息接口
- ✅ 更严格的参数验证

## 最佳实践

### 1. 小数据量查询
- 使用原有接口
- 设置合理的limit参数
- 适用于数据量 < 5000条

### 2. 大数据量查询
- 使用分页接口
- 每页100-1000条记录
- 适用于数据量 > 5000条

### 3. 数据导出
- 使用导出接口
- 选择合适的格式
- 注意数据量限制

### 4. 性能优化建议
- 尽量缩小日期范围
- 使用分页查询
- 缓存常用查询结果
- 避免频繁的大数据量查询

## 后续优化建议

### 1. 缓存机制
- 实现查询结果缓存
- 减少数据库查询
- 提高响应速度

### 2. 异步处理
- 大数据量导出使用异步任务
- 提供任务状态查询接口
- 支持任务取消

### 3. 数据压缩
- 支持gzip压缩
- 减少网络传输量
- 提高传输速度

### 4. 权限控制
- 添加用户认证
- 实现访问权限控制
- 记录查询日志

### 5. 监控和告警
- 监控查询性能
- 记录慢查询
- 设置告警阈值

## 测试建议

### 1. 单元测试
- 测试参数验证
- 测试分页逻辑
- 测试导出功能

### 2. 集成测试
- 测试完整查询流程
- 测试大数据量场景
- 测试错误处理

### 3. 性能测试
- 测试不同数据量的响应时间
- 测试并发查询性能
- 测试内存使用情况

### 4. 压力测试
- 测试系统极限
- 测试并发导出
- 测试长时间运行稳定性

## 总结

本次重构显著提升了API的性能和可用性：

✅ **解决了大数据量查询问题** - 通过分页和导出功能
✅ **提高了响应速度** - 减少单次查询数据量
✅ **降低了内存占用** - 使用流式传输
✅ **增强了错误处理** - 统一的错误格式和验证
✅ **保持了向后兼容** - 所有原有接口正常工作
✅ **提供了更好的用户体验** - 支持数据导出和分页浏览

重构后的API更加健壮、高效、易用，能够很好地应对大数据量查询场景。
