package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strings"
	"sync"
	"time"

	"go-web-scraper/internal/crawler"
	"go-web-scraper/internal/storage"
)

type StockNewsProcessor struct {
	stockCodeMap sync.Map
}

func NewStockNewsProcessor(stockCodesFile string) (*StockNewsProcessor, error) {
	processor := &StockNewsProcessor{}
	
	data, err := os.ReadFile(stockCodesFile)
	if err != nil {
		return nil, fmt.Errorf("failed to read stock codes file: %w", err)
	}
	
	lines := strings.Split(string(data), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		
		parts := strings.Split(line, "|")
		if len(parts) >= 2 {
			code := strings.TrimSpace(parts[0])
			name := strings.TrimSpace(parts[1])
			processor.stockCodeMap.Store(code, name)
		}
	}
	
	log.Printf("Loaded %d stock codes", getMapSize(&processor.stockCodeMap))
	
	return processor, nil
}

func getMapSize(m *sync.Map) int {
	count := 0
	m.Range(func(_, _ interface{}) bool {
		count++
		return true
	})
	return count
}

func (p *StockNewsProcessor) Process(ctx context.Context, data []byte, task *crawler.Task) (interface{}, error) {
	var response struct {
		Result struct {
			CmsArticleWebFast []struct {
				Code        string   `json:"code"`
				Title       string   `json:"title"`
				Content     string   `json:"content"`
				Date        string   `json:"date"`
				Source      string   `json:"source"`
				UniqueURL   string   `json:"uniqueurl"`
				RelationStockTags []string `json:"relationStockTags"`
			} `json:"cmsArticleWebFast"`
		} `json:"result"`
		HitsTotal int `json:"hitsTotal"`
	}
	
	if err := json.Unmarshal(data, &response); err != nil {
		return nil, fmt.Errorf("failed to parse JSON: %w", err)
	}
	
	var results []interface{}
	for _, item := range response.Result.CmsArticleWebFast {
		if item.Code == "" {
			continue
		}
		
		stocks := p.parseStockTags(item.RelationStockTags)
		
		news := map[string]interface{}{
			"id":          item.Code,
			"title":       item.Title,
			"content":     item.Content,
			"publish_time": item.Date,
			"source":      item.Source,
			"url":         item.UniqueURL,
			"stocks":      stocks,
			"created_at":  time.Now(),
		}
		
		results = append(results, news)
	}
	
	return results, nil
}

func (p *StockNewsProcessor) parseStockTags(tags []string) []map[string]interface{} {
	var stocks []map[string]interface{}
	
	for _, tag := range tags {
		parts := strings.Split(tag, ".")
		if len(parts) < 2 {
			continue
		}
		
		code := parts[1]
		
		if strings.HasPrefix(code, "BK") {
			continue
		}
		
		stockCode := code
		if len(code) == 4 && strings.HasPrefix(code, "0") {
			stockCode = strings.TrimPrefix(code, "0")
		} else if len(code) == 5 && strings.HasPrefix(code, "0") {
			stockCode = strings.TrimPrefix(code, "0")
		}
		
		name := stockCode
		if value, ok := p.stockCodeMap.Load(stockCode); ok {
			name = value.(string)
		}
		
		stock := map[string]interface{}{
			"code":  stockCode,
			"name":  name,
			"change": 0.0,
		}
		
		stocks = append(stocks, stock)
	}
	
	return stocks
}

type EnhancedMongoStorage struct {
	mongoStorage *storage.MongoStorage
}

func NewEnhancedMongoStorage(uri, database, collection string) (*EnhancedMongoStorage, error) {
	mongoStorage, err := storage.NewMongoStorage(uri, database, collection)
	if err != nil {
		return nil, err
	}
	
	return &EnhancedMongoStorage{
		mongoStorage: mongoStorage,
	}, nil
}

func (s *EnhancedMongoStorage) Save(ctx context.Context, data interface{}) error {
	items, ok := data.([]interface{})
	if !ok {
		return fmt.Errorf("invalid data type")
	}
	
	if len(items) == 0 {
		return nil
	}
	
	for _, item := range items {
		if err := s.mongoStorage.Save(ctx, item); err != nil {
			log.Printf("Failed to save item: %v", err)
			continue
		}
	}
	
	return nil
}

func main() {
	stockCodesFile := "configs/stock_codes_full.txt"
	
	processor, err := NewStockNewsProcessor(stockCodesFile)
	if err != nil {
		log.Fatalf("Failed to create processor: %v", err)
	}
	
	config := crawler.CrawlerConfig{
		WorkerCount:     20,
		MaxRetry:       3,
		RetryDelay:     2 * time.Second,
		RequestTimeout:  30 * time.Second,
		EnableRetry:    true,
		EnableDedup:    true,
		MaxConcurrency:  100,
	}
	
	scheduler := crawler.NewPriorityTaskScheduler()
	downloader := crawler.NewHTTPDownloader(config.RequestTimeout)
	
	mongoStorage, err := NewEnhancedMongoStorage(
		"mongodb://admin:aa123aaqqA!@121.37.47.63:27017",
		"crawler",
		"eastmoney_news_ssgs",
	)
	if err != nil {
		log.Fatalf("Failed to create MongoDB storage: %v", err)
	}
	
	crawlerEngine := crawler.NewCrawler(scheduler, downloader, processor, mongoStorage, config)
	
	data, err := os.ReadFile(stockCodesFile)
	if err != nil {
		log.Fatalf("Failed to read stock codes file: %v", err)
	}
	
	lines := strings.Split(string(data), "\n")
	var seeds []crawler.URLSeed
	
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		
		parts := strings.Split(line, "|")
		if len(parts) >= 2 {
			code := strings.TrimSpace(parts[0])
			name := strings.TrimSpace(parts[1])
			
			url := fmt.Sprintf("https://searchweb.eastmoney.com/api/jsonp?cb=jQuery&param={\"uid\":\"\",\"keyword\":\"%s\",\"type\":\"cmsArticleWebFast\",\"client\":\"web\",\"clientType\":\"web\",\"clientVersion\":\"curr\",\"param\":{\"cmsArticleWebFast\":{\"searchScope\":\"default\",\"sortType\":\"default\",\"pageIndex\":1,\"pageSize\":100,\"preTag\":\"\"}}}", code)
			
			seed := crawler.URLSeed{
				URL: url,
				Priority: 10,
				Metadata: map[string]interface{}{
					"stock_code": code,
					"stock_name": name,
					"type":       "stock_news_list",
				},
			}
			
			seeds = append(seeds, seed)
		}
	}
	
	log.Printf("Generated %d seed URLs", len(seeds))
	
	if err := crawlerEngine.SubmitSeeds(seeds); err != nil {
		log.Fatalf("Failed to submit seeds: %v", err)
	}
	
	if err := crawlerEngine.Start(); err != nil {
		log.Fatalf("Failed to start crawler: %v", err)
	}
	
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	
	for {
		select {
		case <-ticker.C:
			stats := crawlerEngine.GetStats()
			log.Printf("Crawler stats - Total: %d, Completed: %d, Failed: %d, Retried: %d, Skipped: %d",
				stats["total_tasks"],
				stats["completed_tasks"],
				stats["failed_tasks"],
				stats["retried_tasks"],
				stats["skipped_tasks"],
			)
		}
	}
}
