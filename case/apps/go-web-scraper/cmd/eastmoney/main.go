package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"regexp"
	"strings"
	"sync"
	"syscall"
	"time"

	"go-web-scraper/internal/model"
	"go-web-scraper/internal/storage"
	"go-web-scraper/internal/utils"

	"github.com/PuerkitoBio/goquery"
	"github.com/chromedp/chromedp"
	"gopkg.in/yaml.v3"
)

const (
	BaseURL        = "https://kuaixun.eastmoney.com/"
	DefaultTimeout = 60 * time.Second
)

type YAMLConfig struct {
	Storage struct {
		Mongo struct {
			URI        string `yaml:"uri"`
			Database   string `yaml:"database"`
			Collection string `yaml:"collection"`
		} `yaml:"mongo"`
		JSON struct {
			OutputDir string `yaml:"output_dir"`
		} `yaml:"json"`
	} `yaml:"storage"`
}

type Config struct {
	Interval      time.Duration
	OutputDir     string
	MaxRetries    int
	Timeout       time.Duration
	Headless      bool
	MongoURI      string
	MongoDB       string
	MongoColl     string
	UseMongoDB    bool
}

type Crawler struct {
	config   *Config
	storage  storage.Storage
	seenIDs  map[string]bool
	mu       sync.RWMutex
	stopChan chan struct{}
}

func NewCrawler(cfg *Config) (*Crawler, error) {
	if cfg.Timeout == 0 {
		cfg.Timeout = DefaultTimeout
	}
	if cfg.Interval == 0 {
		cfg.Interval = 5 * time.Minute
	}
	if cfg.OutputDir == "" {
		cfg.OutputDir = "./data/eastmoney"
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

	return &Crawler{
		config:   cfg,
		storage:  store,
		seenIDs:  make(map[string]bool),
		stopChan: make(chan struct{}),
	}, nil
}

func (c *Crawler) fetchWithChrome(ctx context.Context) (string, error) {
	opts := []chromedp.ExecAllocatorOption{
		chromedp.Flag("headless", c.config.Headless),
		chromedp.Flag("disable-gpu", true),
		chromedp.Flag("no-sandbox", true),
		chromedp.Flag("disable-dev-shm-usage", true),
		chromedp.UserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
	}

	if chromePath := utils.GetChromePath(); chromePath != "" {
		opts = append(opts, chromedp.ExecPath(chromePath))
		log.Printf("Using Chrome at: %s", chromePath)
	} else {
		log.Printf("Warning: Chrome not found, using system default")
	}

	allocCtx, cancel := chromedp.NewExecAllocator(ctx, opts...)
	defer cancel()

	browserCtx, cancel := chromedp.NewContext(allocCtx)
	defer cancel()

	timeoutCtx, cancel := context.WithTimeout(browserCtx, c.config.Timeout)
	defer cancel()

	var htmlContent string
	err := chromedp.Run(timeoutCtx,
		chromedp.Navigate(BaseURL),
		chromedp.Sleep(5*time.Second),
		chromedp.WaitReady(".news_item", chromedp.ByQuery),
		chromedp.Sleep(2*time.Second),
		chromedp.OuterHTML("html", &htmlContent),
	)

	if err != nil {
		return "", fmt.Errorf("chromedp run failed: %w", err)
	}

	return htmlContent, nil
}

var timePattern = regexp.MustCompile(`^\s*(\d{1,2}:\d{2})\s*$`)

func (c *Crawler) parseNews(html string) []model.EastMoneyNews {
	var newsList []model.EastMoneyNews
	today := time.Now().Format("2006-01-02")

	doc, err := goquery.NewDocumentFromReader(strings.NewReader(html))
	if err != nil {
		log.Printf("Failed to parse HTML: %v", err)
		return newsList
	}

	doc.Find(".news_item").Each(func(i int, s *goquery.Selection) {
		news := c.parseNewsItem(s, today)
		if news != nil {
			newsList = append(newsList, *news)
		}
	})

	return newsList
}

func (c *Crawler) parseNewsItem(s *goquery.Selection, today string) *model.EastMoneyNews {
	timeText := strings.TrimSpace(s.Find(".news_time").Text())
	
	detailText := s.Find(".news_detail_text").Text()
	detailText = strings.ReplaceAll(detailText, "[点击查看全文]", "")
	detailText = strings.TrimSpace(detailText)
	
	href, _ := s.Find(".news_detail_link").Attr("href")
	if href != "" && !strings.HasPrefix(href, "http") {
		if strings.HasPrefix(href, "//") {
			href = "https:" + href
		} else {
			href = "https://kuaixun.eastmoney.com" + href
		}
	}

	if detailText == "" {
		return nil
	}

	title, content := extractTitleAndContent(detailText, "")

	if title == "" {
		title = detailText
		if len(title) > 50 {
			title = title[:50]
		}
	}

	if !isValidNewsItem(title, content, href) {
		return nil
	}

	news := &model.EastMoneyNews{
		ID:          generateID(today, timeText, title),
		Title:       title,
		Content:     content,
		URL:         href,
		PublishTime: formatPublishTime(timeText, today),
		Source:      "东方财富快讯",
		CreatedAt:   time.Now(),
	}

	return news
}

func isValidNewsItem(title, content, url string) bool {
	if len(title) < 5 {
		return false
	}

	if strings.Contains(title, "评论") && len(title) < 10 {
		return false
	}

	return true
}

func (c *Crawler) parseTextFormat(doc *goquery.Document, today string) []model.EastMoneyNews {
	var newsList []model.EastMoneyNews

	bodyText := doc.Find("body").Text()
	lines := strings.Split(bodyText, "\n")

	var currentNews *model.EastMoneyNews

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		if timePattern.MatchString(line) {
			if currentNews != nil && currentNews.Title != "" {
				currentNews.ID = generateID(today, currentNews.PublishTime, currentNews.Title)
				newsList = append(newsList, *currentNews)
			}

			timeMatch := timePattern.FindStringSubmatch(line)
			if len(timeMatch) > 1 {
				currentNews = &model.EastMoneyNews{
					PublishTime: formatPublishTime(timeMatch[1], today),
					Source:      "东方财富快讯",
					CreatedAt:   time.Now(),
				}
			}
		} else if currentNews != nil {
			if strings.Contains(line, "点击查看全文") || strings.Contains(line, "查看全文") {
				continue
			}

			if currentNews.Title == "" {
				title, content := extractTitleAndContent(line, "")
				currentNews.Title = title
				if content != "" {
					currentNews.Content = content
				}
			} else if currentNews.Content == "" && len(line) > 15 {
				currentNews.Content = strings.ReplaceAll(line, "[点击查看全文]", "")
			}
		}
	}

	if currentNews != nil && currentNews.Title != "" {
		currentNews.ID = generateID(today, currentNews.PublishTime, currentNews.Title)
		newsList = append(newsList, *currentNews)
	}

	return newsList
}

func extractTitleAndContent(titleText, contentText string) (string, string) {
	title := titleText
	content := contentText

	if strings.Contains(title, "【") && strings.Contains(title, "】") {
		start := strings.Index(title, "【")
		end := strings.Index(title, "】")
		if end > start {
			title = strings.TrimSpace(title[start+3 : end])
			afterTitle := titleText[end+3:]
			if content == "" {
				content = strings.TrimSpace(afterTitle)
			}
		}
	}

	content = strings.ReplaceAll(content, "[点击查看全文]", "")
	content = strings.ReplaceAll(content, "点击查看全文", "")
	content = strings.TrimSpace(content)

	return title, content
}

func formatPublishTime(timeText, today string) string {
	if timeText == "" {
		return today + " " + time.Now().Format("15:04")
	}

	timeText = strings.TrimSpace(timeText)
	if len(timeText) == 5 && strings.Contains(timeText, ":") {
		return today + " " + timeText
	}

	return timeText
}

func (c *Crawler) isSeen(id string) bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.seenIDs[id]
}

func (c *Crawler) markSeen(id string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.seenIDs[id] = true
}

func (c *Crawler) crawlOnce() (int, error) {
	ctx := context.Background()

	html, err := c.fetchWithChrome(ctx)
	if err != nil {
		return 0, fmt.Errorf("fetch HTML failed: %w", err)
	}

	log.Printf("HTML fetched, size: %d bytes", len(html))

	newsList := c.parseNews(html)
	log.Printf("Parsed %d news items", len(newsList))

	var newNews []interface{}
	for _, news := range newsList {
		if news.ID == "" {
			news.ID = generateID(time.Now().Format("2006-01-02"), news.PublishTime, news.Title)
		}
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

func (c *Crawler) Start() {
	log.Printf("Starting EastMoney News Crawler...")
	log.Printf("Target URL: %s", BaseURL)
	log.Printf("Output Directory: %s", c.config.OutputDir)
	log.Printf("Crawl Interval: %v", c.config.Interval)
	log.Printf("Headless Mode: %v", c.config.Headless)

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
			log.Println("Crawler stopped")
			return
		}
	}
}

func (c *Crawler) Stop() {
	close(c.stopChan)
	c.storage.Close()
}

var idCleanRegex = regexp.MustCompile(`[^\w\x{4e00}-\x{9fa5}]`)

func generateID(date, timeStr, title string) string {
	if len(title) > 20 {
		title = title[:20]
	}
	title = idCleanRegex.ReplaceAllString(title, "")
	return date + "_" + strings.ReplaceAll(timeStr, " ", "_") + "_" + title
}

func main() {
	cfg := &Config{
		Interval:   getEnvDuration("CRAWL_INTERVAL", 5*time.Minute),
		OutputDir:  getEnvString("OUTPUT_DIR", "./data/eastmoney"),
		MaxRetries: 3,
		Timeout:    DefaultTimeout,
		Headless:   getEnvBool("HEADLESS", true),
	}

	configFile := getEnvString("CONFIG_FILE", "./configs/config.yaml")
	if yamlData, err := os.ReadFile(configFile); err == nil {
		var yamlConfig YAMLConfig
		if err := yaml.Unmarshal(yamlData, &yamlConfig); err == nil {
			cfg.MongoURI = yamlConfig.Storage.Mongo.URI
			cfg.MongoDB = yamlConfig.Storage.Mongo.Database
			cfg.MongoColl = yamlConfig.Storage.Mongo.Collection
			if yamlConfig.Storage.JSON.OutputDir != "" {
				cfg.OutputDir = yamlConfig.Storage.JSON.OutputDir
			}
			if cfg.MongoURI != "" {
				cfg.UseMongoDB = true
			}
		}
	}

	crawler, err := NewCrawler(cfg)
	if err != nil {
		log.Fatalf("Failed to create crawler: %v", err)
	}

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigChan
		log.Println("\nReceived shutdown signal, stopping crawler...")
		crawler.Stop()
		os.Exit(0)
	}()

	crawler.Start()
}

func getEnvDuration(key string, defaultVal time.Duration) time.Duration {
	if val := os.Getenv(key); val != "" {
		if d, err := time.ParseDuration(val); err == nil {
			return d
		}
	}
	return defaultVal
}

func getEnvString(key string, defaultVal string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return defaultVal
}

func getEnvBool(key string, defaultVal bool) bool {
	if val := os.Getenv(key); val != "" {
		return strings.ToLower(val) == "true" || val == "1"
	}
	return defaultVal
}
