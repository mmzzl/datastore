package crawler

import (
	"context"
	"sync"
	"time"
)

type Task struct {
	ID        string
	URL       string
	Method    string
	Headers   map[string]string
	Priority  int
	Retry     int
	MaxRetry  int
	Data      interface{}
	CreatedAt time.Time
}

type TaskResult struct {
	Task   *Task
	Data   []byte
	Error  error
	Retry  bool
}

type URLSeed struct {
	URL      string
	Priority int
	Metadata map[string]interface{}
}

type TaskScheduler interface {
	Submit(task *Task) error
	SubmitBatch(tasks []*Task) error
	GetTask() (*Task, error)
	Shutdown()
}

type Downloader interface {
	Download(ctx context.Context, task *Task) ([]byte, error)
}

type Processor interface {
	Process(ctx context.Context, data []byte, task *Task) (interface{}, error)
}

type Storage interface {
	Save(ctx context.Context, data interface{}) error
}

type RetryQueue interface {
	Add(task *Task) error
	Get() (*Task, error)
	Size() int
	Shutdown()
}

type CrawlerConfig struct {
	WorkerCount      int
	MaxRetry        int
	RetryDelay      time.Duration
	RequestTimeout   time.Duration
	EnableRetry     bool
	EnableDedup     bool
	MaxConcurrency  int
}

type Crawler struct {
	scheduler  TaskScheduler
	downloader Downloader
	processor  Processor
	storage    Storage
	retryQueue RetryQueue
	config     CrawlerConfig
	ctx        context.Context
	cancel     context.CancelFunc
	wg         sync.WaitGroup
	stats      *CrawlerStats
}

type CrawlerStats struct {
	TotalTasks      int64
	CompletedTasks  int64
	FailedTasks     int64
	RetriedTasks    int64
	SkippedTasks   int64
	StartTime      time.Time
	EndTime        time.Time
	mu             sync.RWMutex
}

func (s *CrawlerStats) IncrementTotal() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.TotalTasks++
}

func (s *CrawlerStats) IncrementCompleted() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.CompletedTasks++
}

func (s *CrawlerStats) IncrementFailed() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.FailedTasks++
}

func (s *CrawlerStats) IncrementRetried() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.RetriedTasks++
}

func (s *CrawlerStats) IncrementSkipped() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.SkippedTasks++
}

func (s *CrawlerStats) GetStats() map[string]interface{} {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return map[string]interface{}{
		"total_tasks":      s.TotalTasks,
		"completed_tasks":  s.CompletedTasks,
		"failed_tasks":     s.FailedTasks,
		"retried_tasks":   s.RetriedTasks,
		"skipped_tasks":   s.SkippedTasks,
		"start_time":       s.StartTime,
		"end_time":        s.EndTime,
		"duration":        s.EndTime.Sub(s.StartTime).String(),
	}
}
