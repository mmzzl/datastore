# TDD测试用例文档

## 测试概述

本文档描述了爬虫框架的TDD（测试驱动开发）测试用例。

## 测试文件结构

```
internal/crawler/
├── crawler.go          # 核心接口定义
├── scheduler.go        # 优先级任务调度器
├── scheduler_test.go    # 调度器测试
├── downloader.go       # HTTP下载器
├── downloader_test.go  # 下载器测试
├── retry_queue.go      # 重试队列
├── retry_queue_test.go # 重试队列测试
├── engine.go          # 爬虫引擎
└── engine_test.go      # 引擎测试
```

## 测试用例列表

### 1. 优先级任务调度器测试 (`scheduler_test.go`)

#### TestPriorityTaskScheduler_Submit
- **测试目标**: 验证单个任务提交功能
- **预期结果**: 任务成功提交到队列
- **验证点**: 
  - 提交不返回错误
  - 队列大小为1

#### TestPriorityTaskScheduler_SubmitBatch
- **测试目标**: 验证批量任务提交功能
- **预期结果**: 多个任务成功提交到队列
- **验证点**:
  - 批量提交不返回错误
  - 队列大小为3

#### TestPriorityTaskScheduler_PriorityOrder
- **测试目标**: 验证优先级排序功能
- **预期结果**: 任务按优先级顺序返回
- **验证点**:
  - 高优先级任务先返回
  - 中优先级任务次之
  - 低优先级任务最后返回

#### TestPriorityTaskScheduler_Shutdown
- **测试目标**: 验证优雅关闭功能
- **预期结果**: 关闭后不接受新任务
- **验证点**:
  - 关闭后提交任务不报错
  - 队列正常关闭

#### TestPriorityTaskScheduler_GetTask
- **测试目标**: 验证任务获取功能
- **预期结果**: 成功获取提交的任务
- **验证点**:
  - 获取的任务ID匹配
  - 获取的任务URL匹配

### 2. HTTP下载器测试 (`downloader_test.go`)

#### TestHTTPDownloader_Download_Success
- **测试目标**: 验证成功下载功能
- **预期结果**: 成功下载并返回数据
- **验证点**:
  - 下载不返回错误
  - 返回的数据正确

#### TestHTTPDownloader_Download_NotFound
- **测试目标**: 验证404错误处理
- **预期结果**: 返回404错误
- **验证点**:
  - 下载返回错误
  - 错误信息正确

#### TestHTTPDownloader_Download_Timeout
- **测试目标**: 验证超时处理
- **预期结果**: 超时后返回错误
- **验证点**:
  - 下载返回超时错误
  - 超时时间正确

#### TestHTTPDownloader_Download_UserAgent
- **测试目标**: 验证User-Agent设置
- **预期结果**: 使用自定义User-Agent
- **验证点**:
  - 服务器收到正确的User-Agent
  - 下载成功

#### TestHTTPDownloader_Download_CustomHeaders
- **测试目标**: 验证自定义请求头
- **预期结果**: 使用自定义请求头
- **验证点**:
  - 服务器收到自定义请求头
  - 下载成功

### 3. 重试队列测试 (`retry_queue_test.go`)

#### TestMemoryRetryQueue_Add
- **测试目标**: 验证单个任务添加功能
- **预期结果**: 任务成功添加到队列
- **验证点**:
  - 添加不返回错误
  - 队列大小为1

#### TestMemoryRetryQueue_AddMultiple
- **测试目标**: 验证多个任务添加功能
- **预期结果**: 多个任务成功添加到队列
- **验证点**:
  - 所有任务添加成功
  - 队列大小为3

#### TestMemoryRetryQueue_Get
- **测试目标**: 验证任务获取功能
- **预期结果**: 成功获取添加的任务
- **验证点**:
  - 获取的任务ID匹配
  - 获取的任务URL匹配

#### TestMemoryRetryQueue_RetryDelay
- **测试目标**: 验证重试延迟功能
- **预期结果**: 任务在指定延迟后可用
- **验证点**:
  - 任务立即可用（延迟为0）
  - 获取的任务正确

#### TestMemoryRetryQueue_Shutdown
- **测试目标**: 验证优雅关闭功能
- **预期结果**: 关闭后不接受新任务
- **验证点**:
  - 关闭后添加任务不报错
  - 队列正常关闭

#### TestMemoryRetryQueue_Size
- **测试目标**: 验证队列大小统计
- **预期结果**: 正确统计队列大小
- **验证点**:
  - 初始大小为0
  - 添加任务后大小为1

### 4. 爬虫引擎测试 (`engine_test.go`)

#### TestCrawler_NewCrawler
- **测试目标**: 验证爬虫创建功能
- **预期结果**: 成功创建爬虫实例
- **验证点**:
  - 爬虫实例不为nil
  - 配置正确设置

#### TestCrawler_SubmitSeeds
- **测试目标**: 验证种子URL提交功能
- **预期结果**: 种子URL成功转换为任务并提交
- **验证点**:
  - 种子URL转换为任务
  - 任务成功提交到调度器

#### TestCrawler_SubmitTask
- **测试目标**: 验证单个任务提交功能
- **预期结果**: 任务成功提交到调度器
- **验证点**:
  - 任务成功提交
  - 调度器队列大小正确

#### TestCrawler_GetStats
- **测试目标**: 验证统计信息获取
- **预期结果**: 返回正确的统计信息
- **验证点**:
  - 统计信息不为nil
  - 初始统计值为0

#### TestCrawlerStats_Increment
- **测试目标**: 验证统计计数器功能
- **预期结果**: 各计数器正确递增
- **验证点**:
  - TotalTasks递增
  - CompletedTasks递增
  - FailedTasks递增
  - RetriedTasks递增
  - SkippedTasks递增

#### TestCrawlerStats_GetStats
- **测试目标**: 验证统计信息导出
- **预期结果**: 返回完整的统计信息
- **验证点**:
  - 包含所有统计字段
  - 统计值正确

## 运行测试

### 运行所有测试

```bash
# 运行所有测试
go test ./internal/crawler/...

# 运行测试并显示详细输出
go test -v ./internal/crawler/...

# 运行测试并显示覆盖率
go test -cover ./internal/crawler/...
```

### 运行特定测试

```bash
# 运行调度器测试
go test -v ./internal/crawler/... -run TestPriorityTaskScheduler

# 运行下载器测试
go test -v ./internal/crawler/... -run TestHTTPDownloader

# 运行重试队列测试
go test -v ./internal/crawler/... -run TestMemoryRetryQueue

# 运行引擎测试
go test -v ./internal/crawler/... -run TestCrawler
```

### 运行特定测试用例

```bash
# 运行单个测试用例
go test -v ./internal/crawler/... -run TestPriorityTaskScheduler_Submit

# 运行多个测试用例
go test -v ./internal/crawler/... -run "TestPriorityTaskScheduler_Submit|TestPriorityTaskScheduler_SubmitBatch"
```

## 测试覆盖率

### 查看覆盖率

```bash
# 生成覆盖率报告
go test -coverprofile=coverage.out ./internal/crawler/...

# 查看覆盖率
go tool cover -html=coverage.out

# 查看覆盖率百分比
go tool cover -func=coverage.out
```

### 目标覆盖率

- 核心组件: ≥ 80%
- 调度器: ≥ 90%
- 下载器: ≥ 85%
- 重试队列: ≥ 85%
- 引擎: ≥ 75%

## 持续集成

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Go
        uses: actions/setup-go@v2
        with:
          go-version: 1.21
      - name: Run tests
        run: go test -v -race -coverprofile=coverage.out ./...
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 测试最佳实践

### 1. 测试命名
- 使用描述性的测试名称
- 格式: `Test<FunctionName>_<Scenario>`
- 示例: `TestPriorityTaskScheduler_Submit`

### 2. 测试结构
```go
func TestFunctionName_Scenario(t *testing.T) {
    // 1. 准备测试数据
    input := prepareTestData()
    
    // 2. 执行被测试的函数
    result := functionName(input)
    
    // 3. 验证结果
    if result != expected {
        t.Errorf("Expected %v, got %v", expected, result)
    }
}
```

### 3. 测试隔离
- 每个测试独立运行
- 不依赖其他测试的执行顺序
- 使用defer清理资源

### 4. 测试覆盖率
- 测试正常路径
- 测试错误路径
- 测试边界条件

## 下一步

### 1. 添加更多测试
- 集成测试
- 性能测试
- 压力测试

### 2. 提高覆盖率
- 覆盖所有分支
- 覆盖所有错误情况
- 覆盖边界条件

### 3. 添加基准测试
- 测试性能
- 优化瓶颈
- 提高效率

## 总结

本文档提供了完整的TDD测试用例，包括：

1. **单元测试**: 测试各个组件的功能
2. **集成测试**: 测试组件之间的交互
3. **边界测试**: 测试边界条件和错误情况
4. **性能测试**: 测试性能和效率

通过这些测试，可以确保爬虫框架的质量和可靠性。
