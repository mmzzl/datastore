package strategy

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"

	"go-web-scraper/internal/crawler"
)

type CrawlStrategy interface {
	GenerateSeeds() ([]crawler.URLSeed, error)
	ProcessResult(ctx context.Context, data []byte, task *crawler.Task) ([]crawler.URLSeed, []interface{}, error)
	ShouldRetry(task *crawler.Task, err error) bool
}

type StockNewsStrategy struct {
	stockCodes      []string
	apiBaseURL      string
	processedStocks sync.Map
}

func NewStockNewsStrategy(stockCodes []string, apiBaseURL string) *StockNewsStrategy {
	return &StockNewsStrategy{
		stockCodes: stockCodes,
		apiBaseURL: apiBaseURL,
	}
}

func (s *StockNewsStrategy) GenerateSeeds() ([]crawler.URLSeed, error) {
	seeds := make([]crawler.URLSeed, 0, len(s.stockCodes))
	
	for _, code := range s.stockCodes {
		seed := crawler.URLSeed{
			URL: fmt.Sprintf("%s?code=%s", s.apiBaseURL, code),
			Priority: 10,
			Metadata: map[string]interface{}{
				"stock_code": code,
				"type":       "stock_news_list",
			},
		}
		seeds = append(seeds, seed)
	}
	
	return seeds, nil
}

func (s *StockNewsStrategy) ProcessResult(ctx context.Context, data []byte, task *crawler.Task) ([]crawler.URLSeed, []interface{}, error) {
	var newsList []map[string]interface{}
	
	if err := json.Unmarshal(data, &newsList); err != nil {
		return nil, nil, fmt.Errorf("failed to parse news list: %w", err)
	}
	
	var results []interface{}
	var detailSeeds []crawler.URLSeed
	
	for _, news := range newsList {
		if newsID, ok := news["id"].(string); ok && newsID != "" {
			detailURL := fmt.Sprintf("%s/detail?id=%s", s.apiBaseURL, newsID)
			detailSeed := crawler.URLSeed{
				URL: detailURL,
				Priority: 20,
				Metadata: map[string]interface{}{
					"news_id":    newsID,
					"type":       "news_detail",
					"stock_code": task.Data.(map[string]interface{})["stock_code"],
				},
			}
			detailSeeds = append(detailSeeds, detailSeed)
		}
		
		results = append(results, news)
	}
	
	return detailSeeds, results, nil
}

func (s *StockNewsStrategy) ShouldRetry(task *crawler.Task, err error) bool {
	return task.Retry < 3
}

type BatchCrawlStrategy struct {
	batchSize    int
	maxWorkers   int
	requestDelay time.Duration
}

func NewBatchCrawlStrategy(batchSize, maxWorkers int, requestDelay time.Duration) *BatchCrawlStrategy {
	return &BatchCrawlStrategy{
		batchSize:    batchSize,
		maxWorkers:   maxWorkers,
		requestDelay: requestDelay,
	}
}

func (s *BatchCrawlStrategy) GenerateSeeds() ([]crawler.URLSeed, error) {
	return nil, fmt.Errorf("not implemented")
}

func (s *BatchCrawlStrategy) ProcessResult(ctx context.Context, data []byte, task *crawler.Task) ([]crawler.URLSeed, []interface{}, error) {
	return nil, nil, fmt.Errorf("not implemented")
}

func (s *BatchCrawlStrategy) ShouldRetry(task *crawler.Task, err error) bool {
	return task.Retry < 3
}

type AdaptiveStrategy struct {
	strategy CrawlStrategy
	stats    *StrategyStats
}

type StrategyStats struct {
	SuccessCount int64
	FailureCount int64
	AvgResponseTime time.Duration
	mu sync.RWMutex
}

func NewAdaptiveStrategy(strategy CrawlStrategy) *AdaptiveStrategy {
	return &AdaptiveStrategy{
		strategy: strategy,
		stats:    &StrategyStats{},
	}
}

func (s *AdaptiveStrategy) GenerateSeeds() ([]crawler.URLSeed, error) {
	return s.strategy.GenerateSeeds()
}

func (s *AdaptiveStrategy) ProcessResult(ctx context.Context, data []byte, task *crawler.Task) ([]crawler.URLSeed, []interface{}, error) {
	startTime := time.Now()
	
	seeds, results, err := s.strategy.ProcessResult(ctx, data, task)
	
	duration := time.Since(startTime)
	
	s.stats.mu.Lock()
	defer s.stats.mu.Unlock()
	
	if err != nil {
		s.stats.FailureCount++
	} else {
		s.stats.SuccessCount++
		s.stats.AvgResponseTime = (s.stats.AvgResponseTime*time.Duration(s.stats.SuccessCount) + duration) / time.Duration(s.stats.SuccessCount+1)
	}
	
	return seeds, results, err
}

func (s *AdaptiveStrategy) ShouldRetry(task *crawler.Task, err error) bool {
	return s.strategy.ShouldRetry(task, err)
}

func (s *AdaptiveStrategy) GetStats() *StrategyStats {
	s.stats.mu.RLock()
	defer s.stats.mu.RUnlock()
	return s.stats
}
