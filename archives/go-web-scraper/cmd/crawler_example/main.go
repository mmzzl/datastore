package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"

	"go-web-scraper/internal/crawler"
	"go-web-scraper/internal/storage"
)

type StockNewsProcessor struct{}

func (p *StockNewsProcessor) Process(ctx context.Context, data []byte, task *crawler.Task) (interface{}, error) {
	var newsList []map[string]interface{}
	
	if err := json.Unmarshal(data, &newsList); err != nil {
		return nil, fmt.Errorf("failed to parse JSON: %w", err)
	}
	
	var results []interface{}
	for _, news := range newsList {
		if title, ok := news["title"].(string); ok && title != "" {
			results = append(results, news)
		}
	}
	
	return results, nil
}

type MongoStorage struct {
	mongoStorage *storage.MongoStorage
}

func NewMongoStorage(uri, database, collection string) (*MongoStorage, error) {
	mongoStorage, err := storage.NewMongoStorage(uri, database, collection)
	if err != nil {
		return nil, err
	}
	
	return &MongoStorage{
		mongoStorage: mongoStorage,
	}, nil
}

func (s *MongoStorage) Save(ctx context.Context, data interface{}) error {
	items, ok := data.([]interface{})
	if !ok {
		return fmt.Errorf("invalid data type")
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
	processor := &StockNewsProcessor{}
	
	mongoStorage, err := NewMongoStorage(
		"mongodb://admin:aa123aaqqA!@121.37.47.63:27017",
		"crawler",
		"eastmoney_news_ssgs",
	)
	if err != nil {
		log.Fatalf("Failed to create MongoDB storage: %v", err)
	}
	
	crawlerEngine := crawler.NewCrawler(scheduler, downloader, processor, mongoStorage, config)
	
	seeds := []crawler.URLSeed{
		{
			URL:      "http://example.com/api/news?stock=600519",
			Priority: 10,
		},
		{
			URL:      "http://example.com/api/news?stock=000858",
			Priority: 10,
		},
	}
	
	if err := crawlerEngine.SubmitSeeds(seeds); err != nil {
		log.Fatalf("Failed to submit seeds: %v", err)
	}
	
	if err := crawlerEngine.Start(); err != nil {
		log.Fatalf("Failed to start crawler: %v", err)
	}
	
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()
	
	for {
		select {
		case <-ticker.C:
			stats := crawlerEngine.GetStats()
			log.Printf("Crawler stats: %+v", stats)
		}
	}
}
