package crawler

import (
	"sync"
	"time"
)

type RetryQueueItem struct {
	task      *Task
	nextRetry time.Time
}

type MemoryRetryQueue struct {
	items    []*RetryQueueItem
	mu       sync.RWMutex
	taskChan chan *Task
	shutdown bool
}

func NewMemoryRetryQueue() *MemoryRetryQueue {
	q := &MemoryRetryQueue{
		items:    make([]*RetryQueueItem, 0),
		taskChan: make(chan *Task, 1000),
	}
	
	go q.run()
	
	return q
}

func (q *MemoryRetryQueue) Add(task *Task) error {
	q.mu.Lock()
	defer q.mu.Unlock()
	
	if q.shutdown {
		return nil
	}
	
	item := &RetryQueueItem{
		task:      task,
		nextRetry: time.Now(),
	}
	
	q.items = append(q.items, item)
	return nil
}

func (q *MemoryRetryQueue) Get() (*Task, error) {
	task, ok := <-q.taskChan
	if !ok {
		return nil, nil
	}
	return task, nil
}

func (q *MemoryRetryQueue) run() {
	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()
	
	for {
		select {
		case <-ticker.C:
			q.processRetryItems()
		}
	}
}

func (q *MemoryRetryQueue) processRetryItems() {
	q.mu.Lock()
	defer q.mu.Unlock()
	
	if q.shutdown {
		return
	}
	
	now := time.Now()
	var remaining []*RetryQueueItem
	
	for _, item := range q.items {
		if now.After(item.nextRetry) || now.Equal(item.nextRetry) {
			select {
			case q.taskChan <- item.task:
			default:
				remaining = append(remaining, item)
			}
		} else {
			remaining = append(remaining, item)
		}
	}
	
	q.items = remaining
}

func (q *MemoryRetryQueue) Size() int {
	q.mu.RLock()
	defer q.mu.RUnlock()
	return len(q.items)
}

func (q *MemoryRetryQueue) Shutdown() {
	q.mu.Lock()
	q.shutdown = true
	q.mu.Unlock()
	
	close(q.taskChan)
}
