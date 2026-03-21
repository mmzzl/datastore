package crawler

import (
	"context"
	"fmt"
	"log"
	"time"
)

func NewCrawler(scheduler TaskScheduler, downloader Downloader, processor Processor, storage Storage, config CrawlerConfig) *Crawler {
	ctx, cancel := context.WithCancel(context.Background())
	
	return &Crawler{
		scheduler:  scheduler,
		downloader: downloader,
		processor:  processor,
		storage:    storage,
		retryQueue: NewMemoryRetryQueue(),
		config:     config,
		ctx:        ctx,
		cancel:     cancel,
		stats:      &CrawlerStats{StartTime: time.Now()},
	}
}

func (c *Crawler) Start() error {
	log.Printf("Starting crawler with %d workers", c.config.WorkerCount)
	
	for i := 0; i < c.config.WorkerCount; i++ {
		c.wg.Add(1)
		go c.worker(i)
	}
	
	return nil
}

func (c *Crawler) worker(id int) {
	defer c.wg.Done()
	
	log.Printf("Worker %d started", id)
	
	for {
		select {
		case <-c.ctx.Done():
			log.Printf("Worker %d stopped", id)
			return
		default:
			task, err := c.scheduler.GetTask()
			if err != nil {
				log.Printf("Worker %d failed to get task: %v", id, err)
				continue
			}
			
			if task == nil {
				time.Sleep(100 * time.Millisecond)
				continue
			}
			
			c.processTask(task)
		}
	}
}

func (c *Crawler) processTask(task *Task) {
	c.stats.IncrementTotal()
	
	ctx, cancel := context.WithTimeout(c.ctx, c.config.RequestTimeout)
	defer cancel()
	
	data, err := c.downloader.Download(ctx, task)
	if err != nil {
		c.handleTaskError(task, err)
		return
	}
	
	result, err := c.processor.Process(c.ctx, data, task)
	if err != nil {
		log.Printf("Failed to process task %s: %v", task.ID, err)
		c.stats.IncrementFailed()
		return
	}
	
	if result == nil {
		c.stats.IncrementSkipped()
		return
	}
	
	if err := c.storage.Save(c.ctx, result); err != nil {
		log.Printf("Failed to save result for task %s: %v", task.ID, err)
		c.stats.IncrementFailed()
		return
	}
	
	c.stats.IncrementCompleted()
	log.Printf("Task %s completed successfully", task.ID)
}

func (c *Crawler) handleTaskError(task *Task, err error) {
	log.Printf("Task %s failed: %v", task.ID, err)
	
	if !c.config.EnableRetry || task.Retry >= c.config.MaxRetry {
		log.Printf("Task %s failed after %d retries, giving up", task.ID, task.Retry)
		c.stats.IncrementFailed()
		return
	}
	
	task.Retry++
	c.stats.IncrementRetried()
	
	if c.config.EnableRetry {
		log.Printf("Retrying task %s (attempt %d/%d)", task.ID, task.Retry, c.config.MaxRetry)
		time.Sleep(c.config.RetryDelay)
		c.retryQueue.Add(task)
	}
}

func (c *Crawler) SubmitSeeds(seeds []URLSeed) error {
	tasks := make([]*Task, 0, len(seeds))
	
	for _, seed := range seeds {
		task := &Task{
			ID:       generateTaskID(seed.URL),
			URL:      seed.URL,
			Method:   "GET",
			Priority: seed.Priority,
			Retry:    0,
			MaxRetry: c.config.MaxRetry,
			Data:     seed.Metadata,
		}
		
		if seed.Metadata != nil {
			if headers, ok := seed.Metadata["headers"].(map[string]string); ok {
				task.Headers = headers
			}
		}
		
		tasks = append(tasks, task)
	}
	
	return c.scheduler.SubmitBatch(tasks)
}

func (c *Crawler) SubmitTask(task *Task) error {
	if task.MaxRetry == 0 {
		task.MaxRetry = c.config.MaxRetry
	}
	return c.scheduler.Submit(task)
}

func (c *Crawler) Stop() {
	log.Println("Stopping crawler...")
	
	c.cancel()
	
	c.scheduler.Shutdown()
	c.retryQueue.Shutdown()
	
	c.wg.Wait()
	
	c.stats.EndTime = time.Now()
	
	log.Printf("Crawler stopped. Stats: %+v", c.stats.GetStats())
}

func (c *Crawler) GetStats() map[string]interface{} {
	return c.stats.GetStats()
}

func (c *Crawler) WaitForCompletion() {
	c.wg.Wait()
}

func generateTaskID(url string) string {
	return fmt.Sprintf("%d", time.Now().UnixNano())
}
