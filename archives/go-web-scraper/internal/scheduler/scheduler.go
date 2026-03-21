package scheduler

type Scheduler struct {
	taskQueue chan *task  // 任务队列
	dedupSet  *bloom.BloomFilter // 布隆过滤器去重
	rateLimiter *rate.Limiter // 速率限制
	wokers int  // 并发数
}
type Task struct {
	ID string // 任务ID
	URL string // 任务URL
	Method string // 请求方法
	Headers map[string]string // 请求头
	Priority int // 优先级
	Retry int // 重试次数
	ParseFunc func([]byte) // 解析函数
}