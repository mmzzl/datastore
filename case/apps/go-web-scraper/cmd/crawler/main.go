// main.go
package main

import (
    "context"
    "log"
    "time"
    
    "crawler/config"
    "crawler/fetcher"
    "crawler/parser"
    "crawler/pipeline"
    "crawler/scheduler"
    "crawler/storage"
)

func main() {
    // 1. 初始化配置
    cfg := config.Load("config.yaml")
    
    // 2. 初始化存储
    mongoStore, err := storage.NewMongoStorage(cfg.MongoURI, "crawler", "items")
    if err != nil {
        log.Fatal(err)
    }
    defer mongoStore.Close()
    
    // 3. 构建处理管道
    pipe := pipeline.NewPipeline(
        pipeline.NewCleanStage(),      // 清洗
        pipeline.NewValidateStage(),   // 验证
    ).WithSink(mongoStore)
    
    // 4. 初始化解析器
    htmlParser := parser.NewCSSParser()
    
    // 5. 初始化抓取器
    fetch := fetcher.New(
        fetcher.WithProxyPool(cfg.Proxies),
        fetcher.WithTimeout(30*time.Second),
        fetcher.WithRetry(3),
    )
    
    // 6. 创建调度器
    sched := scheduler.New(
        scheduler.WithWorkers(10),
        scheduler.WithRateLimit(5), // 每秒5个请求
        scheduler.WithQueueSize(10000),
    )
    
    // 7. 注册任务处理器
    sched.RegisterHandler("product", func(ctx context.Context, task *scheduler.Task) error {
        // 抓取
        resp, err := fetch.Fetch(ctx, task.URL, fetcher.FetchOptions{
            Headers: task.Headers,
        })
        if err != nil {
            return err
        }
        
        // 解析
        result, err := htmlParser.Parse(resp.Body, task.ParseRule)
        if err != nil {
            return err
        }
        
        // 流经管道
        return pipe.Process(ctx, result)
    })
    
    // 8. 添加种子任务
    sched.Push(&scheduler.Task{
        ID:       "product_001",
        URL:      "https://example.com/products/1",
        Method:   "GET",
        Priority: 1,
        ParseRule: parser.ParseRule{
            Type: "css",
            Rule: ".product-title",
            Attr: "text",
        },
    })
    
    // 9. 启动
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()
    
    if err := sched.Run(ctx); err != nil {
        log.Fatal(err)
    }
}
