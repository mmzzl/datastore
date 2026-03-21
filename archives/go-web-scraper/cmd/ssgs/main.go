package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"go-web-scraper/internal/api"
	"go-web-scraper/internal/model"
	"go-web-scraper/internal/storage"

	"gopkg.in/yaml.v3"
)

const (
	DefaultTimeout = 60 * time.Second
)

type YAMLConfig struct {
	Storage struct {
		Mongo struct {
			URI        string `yaml:"uri"`
			Database   string `yaml:"database"`
			Collection string `yaml:"collection"`
		} `yaml:"mongo"`
		MongoSSGS struct {
			URI        string `yaml:"uri"`
			Database   string `yaml:"database"`
			Collection string `yaml:"collection"`
		} `yaml:"mongo_ssgs"`
		JSON struct {
			OutputDir string `yaml:"output_dir"`
		} `yaml:"json"`
	} `yaml:"storage"`
	SSGS struct {
		MaxNewsItems int `yaml:"max_news_items"`
		Timeout     int  `yaml:"timeout"`
	} `yaml:"ssgs"`
}

type Config struct {
	Interval     time.Duration
	OutputDir    string
	MaxRetries   int
	Timeout      time.Duration
	Headless     bool
	MongoURI     string
	MongoDB      string
	MongoColl    string
	UseMongoDB   bool
	MaxNewsItems int
}

type SSGSCrawler struct {
	config       *Config
	storage      storage.Storage
	seenIDs      map[string]bool
	mu           sync.RWMutex
	stopChan     chan struct{}
	apiClient    *api.FastNewsClient
	stateManager *storage.CrawlStateManager
}

func NewSSGSCrawler(cfg *Config) (*SSGSCrawler, error) {
	if cfg.Timeout == 0 {
		cfg.Timeout = DefaultTimeout
	}
	if cfg.Interval == 0 {
		cfg.Interval = 5 * time.Minute
	}
	if cfg.OutputDir == "" {
		cfg.OutputDir = "./data/ssgs"
	}

	var store storage.Storage
	var err error

	if cfg.UseMongoDB && cfg.MongoURI != "" {
		store, err = storage.NewMongoStorage(cfg.MongoURI, cfg.MongoDB, cfg.MongoColl)
		if err != nil {
			return nil, fmt.Errorf("failed to create MongoDB storage: %w", err)
		}
	} else {
		store = storage.NewDailyJSONStorage(cfg.OutputDir)
	}

	var stateManager *storage.CrawlStateManager
	if cfg.UseMongoDB && cfg.MongoURI != "" {
		stateManager, err = storage.NewCrawlStateManager(cfg.MongoURI, cfg.MongoDB)
		if err != nil {
			return nil, fmt.Errorf("failed to create crawl state manager: %w", err)
		}
	}

	return &SSGSCrawler{
		config:       cfg,
		storage:      store,
		seenIDs:      make(map[string]bool),
		mu:           sync.RWMutex{},
		stopChan:     make(chan struct{}),
		apiClient:    api.NewFastNewsClientWithColumn("103"),
		stateManager: stateManager,
	}, nil
}

func (c *SSGSCrawler) isSeen(id string) bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.seenIDs[id]
}

func (c *SSGSCrawler) markSeen(id string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.seenIDs[id] = true
}

func (c *SSGSCrawler) crawlOnce() (int, error) {
	apiNews, err := c.apiClient.GetAllNews(c.config.MaxNewsItems)
	if err != nil {
		return 0, fmt.Errorf("API request failed: %w", err)
	}

	if len(apiNews) == 0 {
		log.Printf("No news found")
		return 0, nil
	}

	var newsList []model.EastMoneyNews
	for _, item := range apiNews {
		title, content := c.apiClient.ExtractTitleAndContent(item.Summary)
		if title == "" {
			continue
		}

		news := model.EastMoneyNews{
			ID:          item.Code,
			Title:       title,
			Content:     content,
			PublishTime: item.ShowTime,
			Source:      "东方财富上市公司快讯",
			URL:         fmt.Sprintf("https://finance.eastmoney.com/a/%s.html", item.Code),
			CreatedAt:   time.Now(),
		}

		newsList = append(newsList, news)
	}

	var newNews []interface{}
	for _, news := range newsList {
		if !c.isSeen(news.ID) {
			newNews = append(newNews, news)
			c.markSeen(news.ID)
		}
	}

	if len(newNews) > 0 {
		if err := c.storage.BatchSave(context.Background(), newNews); err != nil {
			return 0, fmt.Errorf("save data failed: %w", err)
		}
		log.Printf("Saved %d new news items", len(newNews))
	}

	return len(newNews), nil
}

func (c *SSGSCrawler) Start() {
	log.Printf("Starting EastMoney Listed Company News Crawler...")
	log.Printf("Output Directory: %s", c.config.OutputDir)
	log.Printf("Crawl Interval: %v", c.config.Interval)
	log.Printf("Max News Items: %d", c.config.MaxNewsItems)

	ticker := time.NewTicker(c.config.Interval)
	defer ticker.Stop()

	count, err := c.crawlOnce()
	if err != nil {
		log.Printf("Initial crawl failed: %v", err)
	} else {
		log.Printf("Initial crawl completed, found %d new items", count)
	}

	for {
		select {
		case <-ticker.C:
			count, err := c.crawlOnce()
			if err != nil {
				log.Printf("Crawl failed: %v", err)
			} else {
				log.Printf("Crawl completed, found %d new items", count)
			}
		case <-c.stopChan:
			log.Printf("Stopping crawler...")
			return
		}
	}
}

func (c *SSGSCrawler) Stop() {
	close(c.stopChan)
}

func main() {
	cfg := loadConfig()

	crawler, err := NewSSGSCrawler(cfg)
	if err != nil {
		log.Fatalf("Failed to create crawler: %v", err)
	}

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigChan
		log.Println("Received shutdown signal")
		crawler.Stop()
	}()

	crawler.Start()
}

func loadConfig() *Config {
	configFile := "configs/config.yaml"
	if envConfig := os.Getenv("CONFIG_FILE"); envConfig != "" {
		configFile = envConfig
	}

	yamlData, err := os.ReadFile(configFile)
	if err != nil {
		log.Printf("Failed to read config file: %v, using default config", err)
		return defaultConfig()
	}

	var yamlConfig YAMLConfig
	if err := yaml.Unmarshal(yamlData, &yamlConfig); err != nil {
		log.Printf("Failed to parse config file: %v, using default config", err)
		return defaultConfig()
	}

	cfg := &Config{
		Interval:     getEnvDuration("SSGS_INTERVAL", 5*time.Minute),
		OutputDir:    yamlConfig.Storage.JSON.OutputDir,
		MaxRetries:   3,
		Timeout:      time.Duration(yamlConfig.SSGS.Timeout) * time.Second,
		Headless:     true,
		MaxNewsItems: yamlConfig.SSGS.MaxNewsItems,
	}

	if yamlConfig.Storage.MongoSSGS.URI != "" {
		cfg.UseMongoDB = true
		cfg.MongoURI = yamlConfig.Storage.MongoSSGS.URI
		cfg.MongoDB = yamlConfig.Storage.MongoSSGS.Database
		cfg.MongoColl = yamlConfig.Storage.MongoSSGS.Collection
	}

	if cfg.MongoURI == "" && yamlConfig.Storage.Mongo.URI != "" {
		cfg.UseMongoDB = true
		cfg.MongoURI = yamlConfig.Storage.Mongo.URI
		cfg.MongoDB = yamlConfig.Storage.Mongo.Database
		cfg.MongoColl = yamlConfig.Storage.Mongo.Collection
	}

	return cfg
}

func defaultConfig() *Config {
	return &Config{
		Interval:     5 * time.Minute,
		OutputDir:    "./data/ssgs",
		MaxRetries:   3,
		Timeout:      DefaultTimeout,
		Headless:     true,
		MaxNewsItems: 200,
	}
}

func getEnvDuration(key string, defaultVal time.Duration) time.Duration {
	if val := os.Getenv(key); val != "" {
		if d, err := time.ParseDuration(val); err == nil {
			return d
		}
	}
	return defaultVal
}
