package crawler

import (
	"testing"
	"time"
)

func TestPriorityTaskScheduler_Submit(t *testing.T) {
	scheduler := NewPriorityTaskScheduler()
	defer scheduler.Shutdown()

	task := &Task{
		ID:       "test-1",
		URL:      "http://example.com",
		Priority: 10,
	}

	err := scheduler.Submit(task)
	if err != nil {
		t.Fatalf("Failed to submit task: %v", err)
	}

	if scheduler.Size() != 1 {
		t.Errorf("Expected 1 task in queue, got %d", scheduler.Size())
	}
}

func TestPriorityTaskScheduler_SubmitBatch(t *testing.T) {
	scheduler := NewPriorityTaskScheduler()
	defer scheduler.Shutdown()

	tasks := []*Task{
		{ID: "test-1", URL: "http://example.com/1", Priority: 10},
		{ID: "test-2", URL: "http://example.com/2", Priority: 20},
		{ID: "test-3", URL: "http://example.com/3", Priority: 5},
	}

	err := scheduler.SubmitBatch(tasks)
	if err != nil {
		t.Fatalf("Failed to submit batch: %v", err)
	}

	if scheduler.Size() != 3 {
		t.Errorf("Expected 3 tasks in queue, got %d", scheduler.Size())
	}
}

func TestPriorityTaskScheduler_PriorityOrder(t *testing.T) {
	scheduler := NewPriorityTaskScheduler()
	defer scheduler.Shutdown()

	tasks := []*Task{
		{ID: "low", URL: "http://example.com/low", Priority: 5},
		{ID: "high", URL: "http://example.com/high", Priority: 20},
		{ID: "medium", URL: "http://example.com/medium", Priority: 10},
	}

	scheduler.SubmitBatch(tasks)

	receivedTasks := make([]string, 0, 3)
	timeout := time.After(5 * time.Second)
	
	for i := 0; i < 3; i++ {
		select {
		case <-timeout:
			t.Fatalf("Timeout waiting for tasks")
		default:
			task, err := scheduler.GetTask()
			if err != nil {
				t.Fatalf("Failed to get task: %v", err)
			}
			if task != nil {
				receivedTasks = append(receivedTasks, task.ID)
			} else {
				time.Sleep(50 * time.Millisecond)
				i--
			}
		}
	}

	expectedOrder := []string{"high", "medium", "low"}
	if len(receivedTasks) != len(expectedOrder) {
		t.Fatalf("Expected %d tasks, got %d", len(expectedOrder), len(receivedTasks))
	}

	for i, expected := range expectedOrder {
		if receivedTasks[i] != expected {
			t.Errorf("Expected task %s at position %d, got %s", expected, i, receivedTasks[i])
		}
	}
}

func TestPriorityTaskScheduler_Shutdown(t *testing.T) {
	scheduler := NewPriorityTaskScheduler()

	task := &Task{
		ID:       "test-1",
		URL:      "http://example.com",
		Priority: 10,
	}

	scheduler.Submit(task)
	scheduler.Shutdown()

	err := scheduler.Submit(task)
	if err != nil {
		t.Errorf("Expected no error when submitting to shutdown scheduler, got %v", err)
	}
}

func TestPriorityTaskScheduler_GetTask(t *testing.T) {
	scheduler := NewPriorityTaskScheduler()
	defer scheduler.Shutdown()

	task := &Task{
		ID:       "test-1",
		URL:      "http://example.com",
		Priority: 10,
	}

	scheduler.Submit(task)

	receivedTask, err := scheduler.GetTask()
	if err != nil {
		t.Fatalf("Failed to get task: %v", err)
	}

	if receivedTask == nil {
		t.Fatal("Expected task, got nil")
	}

	if receivedTask.ID != task.ID {
		t.Errorf("Expected task ID %s, got %s", task.ID, receivedTask.ID)
	}

	if receivedTask.URL != task.URL {
		t.Errorf("Expected task URL %s, got %s", task.URL, receivedTask.URL)
	}
}
