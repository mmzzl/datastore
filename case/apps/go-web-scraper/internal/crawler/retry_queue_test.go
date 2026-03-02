package crawler

import (
	"testing"
	"time"
)

func TestMemoryRetryQueue_Add(t *testing.T) {
	queue := NewMemoryRetryQueue()
	defer queue.Shutdown()

	task := &Task{
		ID:      "test-1",
		URL:     "http://example.com",
		Retry:   1,
		MaxRetry: 3,
	}

	err := queue.Add(task)
	if err != nil {
		t.Fatalf("Failed to add task to retry queue: %v", err)
	}

	if queue.Size() != 1 {
		t.Errorf("Expected 1 task in queue, got %d", queue.Size())
	}
}

func TestMemoryRetryQueue_AddMultiple(t *testing.T) {
	queue := NewMemoryRetryQueue()
	defer queue.Shutdown()

	tasks := []*Task{
		{ID: "test-1", URL: "http://example.com/1", Retry: 1, MaxRetry: 3},
		{ID: "test-2", URL: "http://example.com/2", Retry: 2, MaxRetry: 3},
		{ID: "test-3", URL: "http://example.com/3", Retry: 1, MaxRetry: 3},
	}

	for _, task := range tasks {
		err := queue.Add(task)
		if err != nil {
			t.Fatalf("Failed to add task to retry queue: %v", err)
		}
	}

	if queue.Size() != 3 {
		t.Errorf("Expected 3 tasks in queue, got %d", queue.Size())
	}
}

func TestMemoryRetryQueue_Get(t *testing.T) {
	queue := NewMemoryRetryQueue()
	defer queue.Shutdown()

	task := &Task{
		ID:      "test-1",
		URL:     "http://example.com",
		Retry:   1,
		MaxRetry: 3,
	}

	queue.Add(task)

	receivedTask, err := queue.Get()
	if err != nil {
		t.Fatalf("Failed to get task from retry queue: %v", err)
	}

	if receivedTask == nil {
		t.Fatal("Expected task, got nil")
	}

	if receivedTask.ID != task.ID {
		t.Errorf("Expected task ID %s, got %s", task.ID, receivedTask.ID)
	}
}

func TestMemoryRetryQueue_RetryDelay(t *testing.T) {
	queue := NewMemoryRetryQueue()
	defer queue.Shutdown()

	task := &Task{
		ID:      "test-1",
		URL:     "http://example.com",
		Retry:   1,
		MaxRetry: 3,
	}

	queue.Add(task)

	startTime := time.Now()
	receivedTask, err := queue.Get()
	elapsed := time.Since(startTime)

	if err != nil {
		t.Fatalf("Failed to get task from retry queue: %v", err)
	}

	if receivedTask == nil {
		t.Fatal("Expected task, got nil")
	}

	if elapsed > 2*time.Second {
		t.Errorf("Expected task to be available immediately, got delay of %v", elapsed)
	}
}

func TestMemoryRetryQueue_Shutdown(t *testing.T) {
	queue := NewMemoryRetryQueue()

	task := &Task{
		ID:      "test-1",
		URL:     "http://example.com",
		Retry:   1,
		MaxRetry: 3,
	}

	queue.Add(task)
	queue.Shutdown()

	err := queue.Add(task)
	if err != nil {
		t.Errorf("Expected no error when adding to shutdown queue, got %v", err)
	}

	_, err = queue.Get()
	if err != nil {
		t.Errorf("Expected no error when getting from shutdown queue, got %v", err)
	}
}

func TestMemoryRetryQueue_Size(t *testing.T) {
	queue := NewMemoryRetryQueue()
	defer queue.Shutdown()

	if queue.Size() != 0 {
		t.Errorf("Expected initial size 0, got %d", queue.Size())
	}

	task := &Task{
		ID:      "test-1",
		URL:     "http://example.com",
		Retry:   1,
		MaxRetry: 3,
	}

	queue.Add(task)

	if queue.Size() != 1 {
		t.Errorf("Expected size 1, got %d", queue.Size())
	}
}
