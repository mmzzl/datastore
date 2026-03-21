# 高效数据采集框架

## 架构设计

```
URL种子池 (5000主链接) --> 任务调度器 (优先级队列) --> 并发下载器 (协程/线程) --> 数据处理器 (清洗入库)
                                                                                                    |
                                                                                                    v
                                                                                              错误重试队列
```

## 核心组件

### 1. 任务调度器 (TaskScheduler)
- **优先级队列调度**: 根据任务优先级进行调度
- **批量提交**: 支持批量提交任务
- **优雅关闭**: 支持优雅关闭，确保所有任务完成

### 2. 下载器 (Downloader)
- **HTTP下载器**: 基于标准库的HTTP客户端
- **连接池**: 复用连接，提高性能
- **超时控制**: 支持请求超时设置
- **User-Agent**: 支持自定义User-Agent

### 3. 处理器 (Processor)
- **数据解析**: 解析下载的数据
- **数据清洗**: 清洗和转换数据
- **数据验证**: 验证数据完整性

### 4. 存储 (Storage)
- **MongoDB存储**: 支持MongoDB存储
- **JSON存储**: 支持JSON文件存储
- **批量保存**: 支持批量保存数据

### 5. 重试队列 (RetryQueue)
- **自动重试**: 失败任务自动重试
- **延迟重试**: 支持延迟重试
- **重试限制**: 限制最大重试次数

## 数据采集策略

### 1. 股票新闻采集策略 (StockNewsStrategy)

**特点:**
- 支持大规模股票代码列表
- 自动生成新闻列表URL
- 自动生成新闻详情URL
- 支持股票代码映射

**使用示例:**
```go
strategy := strategy.NewStockNewsStrategy(
    []string{"600519", "000858", "601318"},
    "http://api.example.com/news",
)
seeds, _ := strategy.GenerateSeeds()
```

### 2. 批量采集策略 (BatchCrawlStrategy)

**特点:**
- 批量提交任务
- 控制并发数
- 请求速率限制

**使用示例:**
```go
strategy := strategy.NewBatchCrawlStrategy(
    100,    // 批量大小
    20,     // 最大工作线程
    100*time.Millisecond, // 请求延迟
)
```

### 3. 自适应采集策略 (AdaptiveStrategy)

**特点:**
- 自动调整采集速度
- 监控成功率和响应时间
- 动态调整并发数

**使用示例:**
```go
strategy := strategy.NewAdaptiveStrategy(baseStrategy)
```

## 配置说明

### CrawlerConfig

```go
type CrawlerConfig struct {
    WorkerCount      int           // 工作线程数 (默认: 20)
    MaxRetry        int           // 最大重试次数 (默认: 3)
    RetryDelay      time.Duration // 重试延迟 (默认: 2s)
    RequestTimeout   time.Duration // 请求超时 (默认: 30s)
    EnableRetry     bool          // 启用重试 (默认: true)
    EnableDedup     bool          // 启用去重 (默认: true)
    MaxConcurrency  int           // 最大并发数 (默认: 100)
}
```

## 使用示例

### 基础使用

```go
// 1. 创建配置
config := crawler.CrawlerConfig{
    WorkerCount:     20,
    MaxRetry:       3,
    RetryDelay:     2 * time.Second,
    RequestTimeout:  30 * time.Second,
    EnableRetry:    true,
    EnableDedup:    true,
    MaxConcurrency:  100,
}

// 2. 创建组件
scheduler := crawler.NewPriorityTaskScheduler()
downloader := crawler.NewHTTPDownloader(config.RequestTimeout)
processor := &StockNewsProcessor{}
storage := NewMongoStorage(uri, database, collection)

// 3. 创建爬虫引擎
crawlerEngine := crawler.NewCrawler(scheduler, downloader, processor, storage, config)

// 4. 提交种子URL
seeds := []crawler.URLSeed{
    {URL: "http://example.com/api/news?stock=600519", Priority: 10},
    {URL: "http://example.com/api/news?stock=000858", Priority: 10},
}
crawlerEngine.SubmitSeeds(seeds)

// 5. 启动爬虫
crawlerEngine.Start()

// 6. 监控进度
ticker := time.NewTicker(10 * time.Second)
for range ticker.C {
    stats := crawlerEngine.GetStats()
    log.Printf("Stats: %+v", stats)
}
```

### 高级使用 - 股票新闻采集

```go
// 1. 加载股票代码
stockCodes := loadStockCodes("configs/stock_codes.txt")

// 2. 创建采集策略
strategy := strategy.NewStockNewsStrategy(
    stockCodes,
    "http://api.example.com/news",
)

// 3. 生成种子URL
seeds, _ := strategy.GenerateSeeds()

// 4. 创建处理器
processor := &StockNewsProcessor{
    strategy: strategy,
}

// 5. 启动爬虫
crawlerEngine.SubmitSeeds(seeds)
crawlerEngine.Start()
```

## 性能优化建议

### 1. 并发控制
- **WorkerCount**: 根据CPU核心数设置，建议 10-50
- **MaxConcurrency**: 根据目标服务器承受能力设置，建议 50-200

### 2. 请求速率
- **RetryDelay**: 建议设置 1-5 秒，避免被封禁
- **RequestTimeout**: 根据API响应时间设置，建议 30-60 秒

### 3. 内存管理
- **队列大小**: 适当设置队列大小，避免内存溢出
- **批量保存**: 使用批量保存，减少数据库写入次数

### 4. 错误处理
- **MaxRetry**: 设置合理的重试次数，建议 3-5 次
- **重试延迟**: 使用指数退避算法，避免雪崩效应

## 监控和统计

### 统计指标

```go
type CrawlerStats struct {
    TotalTasks      int64       // 总任务数
    CompletedTasks  int64       // 已完成任务数
    FailedTasks     int64       // 失败任务数
    RetriedTasks    int64       // 重试任务数
    SkippedTasks   int64       // 跳过任务数
    StartTime      time.Time    // 开始时间
    EndTime        time.Time    // 结束时间
}
```

### 获取统计信息

```go
stats := crawlerEngine.GetStats()
log.Printf("Total: %d, Completed: %d, Failed: %d",
    stats["total_tasks"],
    stats["completed_tasks"],
    stats["failed_tasks"],
)
```

## 最佳实践

### 1. 种子URL管理
- 使用优先级区分重要任务
- 批量提交种子URL，提高效率
- 定期更新种子URL列表

### 2. 错误处理
- 实现合理的重试机制
- 记录失败任务，便于后续处理
- 监控错误率，及时调整策略

### 3. 数据去重
- 使用数据库唯一索引去重
- 实现内存去重机制
- 定期清理重复数据

### 4. 性能监控
- 实时监控采集速度
- 监控成功率
- 监控响应时间

## 扩展功能

### 1. 代理支持
```go
type ProxyDownloader struct {
    proxies []string
    current int
}

func (d *ProxyDownloader) Download(ctx context.Context, task *Task) ([]byte, error) {
    proxy := d.proxies[d.current]
    d.current = (d.current + 1) % len(d.proxies)
    // 使用代理下载
}
```

### 2. 分布式采集
```go
type DistributedScheduler struct {
    redisClient *redis.Client
}

func (s *DistributedScheduler) Submit(task *Task) error {
    // 使用Redis队列分发任务
}
```

### 3. 实时监控
```go
type Monitor struct {
    prometheusClient *prometheus.Client
}

func (m *Monitor) RecordStats(stats *CrawlerStats) {
    // 上报监控数据
}
```

## 故障排查

### 1. 采集速度慢
- 检查网络连接
- 增加WorkerCount
- 检查目标服务器限流

### 2. 内存占用高
- 减少队列大小
- 增加批量保存频率
- 检查内存泄漏

### 3. 失败率高
- 检查网络连接
- 增加重试次数
- 检查目标服务器状态

## 总结

这个高效数据采集框架提供了：

1. **高性能**: 支持高并发采集
2. **可靠性**: 自动重试和错误处理
3. **可扩展**: 支持自定义策略和组件
4. **易用**: 简洁的API设计
5. **监控**: 完善的统计和监控

通过合理配置和使用，可以高效、稳定地采集大规模数据。
