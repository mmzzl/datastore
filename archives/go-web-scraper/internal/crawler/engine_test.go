package crawler

import (
	"context"
	"testing"
	"time"
)

type MockDownloader struct {
	data     []byte
	err       error
	callCount int
}

func (m *MockDownloader) Download(ctx context.Context, task *Task) ([]byte, error) {
	m.callCount++
	if m.err != nil {
		return nil, m.err
	}
	return m.data, nil
}

type MockProcessor struct {
	data     interface{}
	err       error
	callCount int
}

func (m *MockProcessor) Process(ctx context.Context, data []byte, task *Task) (interface{}, error) {
	m.callCount++
	if m.err != nil {
		return nil, m.err
	}
	return m.data, nil
}

type MockStorage struct {
	data     []interface{}
	err       error
	callCount int
}

func (m *MockStorage) Save(ctx context.Context, data interface{}) error {
	m.callCount++
	if m.err != nil {
		return m.err
	}
	if items, ok := data.([]interface{}); ok {
		m.data = append(m.data, items...)
	}
	return nil
}

func TestCrawler_NewCrawler(t *testing.T) {
	config := CrawlerConfig{
		WorkerCount:     5,
		MaxRetry:       3,
		RetryDelay:     2 * time.Second,
		RequestTimeout:  30 * time.Second,
		EnableRetry:    true,
		EnableDedup:    true,
		MaxConcurrency:  10,
	}

	scheduler := NewPriorityTaskScheduler()
	downloader := &MockDownloader{data: []byte("test data")}
	processor := &MockProcessor{data: []interface{}{"item1", "item2"}}
	storage := &MockStorage{}

	crawler := NewCrawler(scheduler, downloader, processor, storage, config)

	if crawler == nil {
		t.Fatal("Expected crawler to be created, got nil")
	}

	if crawler.config.WorkerCount != 5 {
		t.Errorf("Expected WorkerCount 5, got %d", crawler.config.WorkerCount)
	}
}

func TestCrawler_SubmitSeeds(t *testing.T) {
	config := CrawlerConfig{
		WorkerCount:     5,
		MaxRetry:       3,
		RetryDelay:     2 * time.Second,
		RequestTimeout:  30 * time.Second,
		EnableRetry:    true,
		EnableDedup:    true,
		MaxConcurrency:  10,
	}

	scheduler := NewPriorityTaskScheduler()
	downloader := &MockDownloader{data: []byte("test data")}
	processor := &MockProcessor{data: []interface{}{"item1", "item2"}}
	storage := &MockStorage{}

	crawler := NewCrawler(scheduler, downloader, processor, storage, config)

	seeds := []URLSeed{
		{URL: "http://example.com/1", Priority: 10},
		{URL: "http://example.com/2", Priority: 20},
		{URL: "http://example.com/3", Priority: 5},
	}

	err := crawler.SubmitSeeds(seeds)
	if err != nil {
		t.Fatalf("Failed to submit seeds: %v", err)
	}

	if scheduler.Size() != 3 {
		t.Errorf("Expected 3 tasks in scheduler, got %d", scheduler.Size())
	}
}

func TestCrawler_SubmitTask(t *testing.T) {
	config := CrawlerConfig{
		WorkerCount:     5,
		MaxRetry:       3,
		RetryDelay:     2 * time.Second,
		RequestTimeout:  30 * time.Second,
		EnableRetry:    true,
		EnableDedup:    true,
		MaxConcurrency:  10,
	}

	scheduler := NewPriorityTaskScheduler()
	downloader := &MockDownloader{data: []byte("test data")}
	processor := &MockProcessor{data: []interface{}{"item1", "item2"}}
	storage := &MockStorage{}

	crawler := NewCrawler(scheduler, downloader, processor, storage, config)

	task := &Task{
		ID:       "test-1",
		URL:      "http://example.com",
		Priority: 10,
	}

	err := crawler.SubmitTask(task)
	if err != nil {
		t.Fatalf("Failed to submit task: %v", err)
	}

	if scheduler.Size() != 1 {
		t.Errorf("Expected 1 task in scheduler, got %d", scheduler.Size())
	}
}

func TestCrawler_GetStats(t *testing.T) {
	config := CrawlerConfig{
		WorkerCount:     5,
		MaxRetry:       3,
		RetryDelay:     2 * time.Second,
		RequestTimeout:  30 * time.Second,
		EnableRetry:    true,
		EnableDedup:    true,
		MaxConcurrency:  10,
	}

	scheduler := NewPriorityTaskScheduler()
	downloader := &MockDownloader{data: []byte("test data")}
	processor := &MockProcessor{data: []interface{}{"item1", "item2"}}
	storage := &MockStorage{}

	crawler := NewCrawler(scheduler, downloader, processor, storage, config)

	stats := crawler.GetStats()

	if stats == nil {
		t.Fatal("Expected stats to be returned, got nil")
	}

	if stats["total_tasks"] != int64(0) {
		t.Errorf("Expected total_tasks 0, got %v", stats["total_tasks"])
	}

	if stats["completed_tasks"] != int64(0) {
		t.Errorf("Expected completed_tasks 0, got %v", stats["completed_tasks"])
	}
}

func TestCrawlerStats_Increment(t *testing.T) {
	stats := &CrawlerStats{}

	stats.IncrementTotal()
	if stats.TotalTasks != 1 {
		t.Errorf("Expected TotalTasks 1, got %d", stats.TotalTasks)
	}

	stats.IncrementCompleted()
	if stats.CompletedTasks != 1 {
		t.Errorf("Expected CompletedTasks 1, got %d", stats.CompletedTasks)
	}

	stats.IncrementFailed()
	if stats.FailedTasks != 1 {
		t.Errorf("Expected FailedTasks 1, got %d", stats.FailedTasks)
	}

	stats.IncrementRetried()
	if stats.RetriedTasks != 1 {
		t.Errorf("Expected RetriedTasks 1, got %d", stats.RetriedTasks)
	}

	stats.IncrementSkipped()
	if stats.SkippedTasks != 1 {
		t.Errorf("Expected SkippedTasks 1, got %d", stats.SkippedTasks)
	}
}

func TestCrawlerStats_GetStats(t *testing.T) {
	stats := &CrawlerStats{
		StartTime: time.Now(),
	}

	stats.IncrementTotal()
	stats.IncrementCompleted()
	stats.IncrementFailed()

	result := stats.GetStats()

	if result["total_tasks"] != int64(1) {
		t.Errorf("Expected total_tasks 1, got %v", result["total_tasks"])
	}

	if result["completed_tasks"] != int64(1) {
		t.Errorf("Expected completed_tasks 1, got %v", result["completed_tasks"])
	}

	if result["failed_tasks"] != int64(1) {
		t.Errorf("Expected failed_tasks 1, got %v", result["failed_tasks"])
	}

	if _, ok := result["start_time"]; !ok {
		t.Error("Expected start_time in stats")
	}

	if _, ok := result["end_time"]; !ok {
		t.Error("Expected end_time in stats")
	}
}
