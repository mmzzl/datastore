package crawler

import (
	"container/heap"
	"sync"
	"time"
)

type priorityTask struct {
	task     *Task
	index    int
}

type priorityQueue []*priorityTask

func (pq priorityQueue) Len() int { return len(pq) }

func (pq priorityQueue) Less(i, j int) bool {
	return pq[i].task.Priority > pq[j].task.Priority
}

func (pq priorityQueue) Swap(i, j int) {
	pq[i], pq[j] = pq[j], pq[i]
	pq[i].index = i
	pq[j].index = j
}

func (pq *priorityQueue) Push(x interface{}) {
	n := len(*pq)
	item := x.(*priorityTask)
	item.index = n
	*pq = append(*pq, item)
}

func (pq *priorityQueue) Pop() interface{} {
	old := *pq
	n := len(old)
	item := old[n-1]
	old[n-1] = nil
	item.index = -1
	*pq = old[0 : n-1]
	return item
}

type PriorityTaskScheduler struct {
	queue      priorityQueue
	mu         sync.Mutex
	taskChan   chan *Task
	shutdown   bool
	wg         sync.WaitGroup
}

func NewPriorityTaskScheduler() *PriorityTaskScheduler {
	s := &PriorityTaskScheduler{
		queue:    make(priorityQueue, 0),
		taskChan: make(chan *Task, 1000),
	}
	heap.Init(&s.queue)
	
	s.wg.Add(1)
	go s.run()
	
	return s
}

func (s *PriorityTaskScheduler) Submit(task *Task) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	
	if s.shutdown {
		return nil
	}
	
	heap.Push(&s.queue, &priorityTask{task: task})
	return nil
}

func (s *PriorityTaskScheduler) SubmitBatch(tasks []*Task) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	
	if s.shutdown {
		return nil
	}
	
	for _, task := range tasks {
		heap.Push(&s.queue, &priorityTask{task: task})
	}
	return nil
}

func (s *PriorityTaskScheduler) GetTask() (*Task, error) {
	task, ok := <-s.taskChan
	if !ok {
		return nil, nil
	}
	return task, nil
}

func (s *PriorityTaskScheduler) run() {
	defer s.wg.Done()
	
	for {
		s.mu.Lock()
		if s.shutdown {
			s.mu.Unlock()
			break
		}
		
		if s.queue.Len() == 0 {
			s.mu.Unlock()
			time.Sleep(100 * time.Millisecond)
			continue
		}
		
		item := heap.Pop(&s.queue).(*priorityTask)
		s.mu.Unlock()
		
		select {
		case s.taskChan <- item.task:
		default:
			s.mu.Lock()
			heap.Push(&s.queue, item)
			s.mu.Unlock()
			time.Sleep(10 * time.Millisecond)
		}
	}
}

func (s *PriorityTaskScheduler) Shutdown() {
	s.mu.Lock()
	s.shutdown = true
	s.mu.Unlock()
	
	close(s.taskChan)
	s.wg.Wait()
}

func (s *PriorityTaskScheduler) Size() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.queue.Len()
}
