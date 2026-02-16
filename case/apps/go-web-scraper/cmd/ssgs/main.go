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
	SSGSURL        = "https://kuaixun.eastmoney.com/ssgs.html"
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
	config   *Config
	storage  storage.Storage
	seenIDs  map[string]bool
	mu       sync.RWMutex
	stopChan chan struct{}
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

	return &SSGSCrawler{
		config:   cfg,
		storage:  store,
		seenIDs:  make(map[string]bool),
		stopChan: make(chan struct{}),
	}, nil
}

func (c *SSGSCrawler) fetchWithChrome(ctx context.Context) (string, error) {
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
		chromedp.Navigate(SSGSURL),
		chromedp.Sleep(5*time.Second),
		chromedp.WaitReady(".news_item", chromedp.ByQuery),
		chromedp.Sleep(2*time.Second),
	)

	if err != nil {
		return "", fmt.Errorf("chromedp run failed: %w", err)
	}

	if c.config.MaxNewsItems > 50 {
		log.Printf("Loading more news items (target: %d)...", c.config.MaxNewsItems)
		err := c.loadMoreNews(timeoutCtx, c.config.MaxNewsItems)
		if err != nil {
			log.Printf("Warning: Failed to load more news: %v", err)
		}
	}

	err = chromedp.Run(timeoutCtx,
		chromedp.OuterHTML("html", &htmlContent),
	)

	if err != nil {
		return "", fmt.Errorf("chromedp run failed: %w", err)
	}

	return htmlContent, nil
}

func (c *SSGSCrawler) loadMoreNews(ctx context.Context, targetCount int) error {
	var currentCount int
	maxAttempts := 20
	attempt := 0

	for attempt < maxAttempts {
		attempt++

		log.Printf("Checking for 'load more' button (attempt %d/%d)...", attempt, maxAttempts)

		var hasButton bool
		err := chromedp.Run(ctx,
			chromedp.Evaluate(`
				(function() {
					const button1 = document.querySelector('.search_load_more');
					const button2 = document.querySelector('.load_more');
					const button = button1 || button2;
					return button !== null;
				})()
			`, &hasButton),
		)

		if err != nil {
			log.Printf("Warning: Failed to check button: %v", err)
			break
		}

		if !hasButton {
			log.Printf("No more 'load more' button found, current count: %d", currentCount)
			break
		}

		log.Printf("Found 'load more' button, clicking...")

		err = chromedp.Run(ctx,
			chromedp.Evaluate(`
				(function() {
					const button1 = document.querySelector('.search_load_more');
					const button2 = document.querySelector('.load_more');
					const button = button1 || button2;
					if (button) {
						button.click();
						return true;
					}
					return false;
				})()
			`, nil),
			chromedp.Sleep(2*time.Second),
			chromedp.Evaluate(`window.scrollTo(0, document.body.scrollHeight)`, nil),
			chromedp.Sleep(3*time.Second),
		)

		if err != nil {
			return fmt.Errorf("click button failed: %w", err)
		}

		var count int
		err = chromedp.Run(ctx,
			chromedp.Evaluate(`
				(function() {
					const items = document.querySelectorAll('.news_item');
					return items.length;
				})()
			`, &count),
		)

		if err != nil {
			return fmt.Errorf("count items failed: %w", err)
		}

		if count == currentCount {
			log.Printf("No new items loaded, current count: %d", count)
			break
		}

		currentCount = count
		log.Printf("Loaded %d news items (attempt %d/%d)", currentCount, attempt, maxAttempts)

		if currentCount >= targetCount {
			log.Printf("Reached target count: %d", currentCount)
			break
		}

		time.Sleep(2 * time.Second)
	}

	return nil
}

func (c *SSGSCrawler) parseNews(html string) []model.EastMoneyNews {
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

func (c *SSGSCrawler) parseNewsItem(s *goquery.Selection, today string) *model.EastMoneyNews {
	timeText := strings.TrimSpace(s.Find(".news_time").Text())
	
	shareDiv := s.Find(".share")
	title, _ := shareDiv.Attr("data-title")
	postID, _ := shareDiv.Attr("data-postid")
	content, _ := shareDiv.Attr("data-cont")
	
	var stocks []model.Stock
	s.Find(".stock_item").Each(func(i int, stockSel *goquery.Selection) {
		stockName := strings.TrimSpace(stockSel.Text())
		changeText := strings.TrimSpace(stockSel.Find("span").Text())
		
		if stockName != "" {
			stock := model.Stock{
				Name:   stockName,
				Change: parseChange(changeText),
			}
			stocks = append(stocks, stock)
		}
	})

	if title == "" {
		return nil
	}

	title = strings.ReplaceAll(title, "[点击查看全文]", "")
	title = strings.TrimSpace(title)

	content = strings.ReplaceAll(content, "[点击查看全文]", "")
	content = strings.TrimSpace(content)

	if !isValidNewsItem(title, content, "") {
		return nil
	}

	news := &model.EastMoneyNews{
		ID:          generateID(today, timeText, title, postID),
		Title:       title,
		Content:     content,
		PublishTime: formatPublishTime(timeText, today),
		Source:      "东方财富上市公司快讯",
		Stocks:      stocks,
		CreatedAt:   time.Now(),
	}

	return news
}

func parseChange(text string) float64 {
	text = strings.TrimSpace(text)
	text = strings.TrimSuffix(text, "%")
	text = strings.TrimPrefix(text, "+")
	text = strings.TrimPrefix(text, "-")

	val := 0.0
	fmt.Sscanf(text, "%f", &val)
	return val
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
			news.ID = generateID(time.Now().Format("2006-01-02"), news.PublishTime, news.Title, "")
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

func (c *SSGSCrawler) Start() {
	log.Printf("Starting EastMoney Listed Company News Crawler...")
	log.Printf("Target URL: %s", SSGSURL)
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

func (c *SSGSCrawler) Stop() {
	close(c.stopChan)
	c.storage.Close()
}

var idCleanRegex = regexp.MustCompile(`[^\w\x{4e00}-\x{9fa5}]`)

func generateID(date, timeStr, title, postID string) string {
	if postID != "" {
		return postID
	}
	if len(title) > 20 {
		title = title[:20]
	}
	title = idCleanRegex.ReplaceAllString(title, "")
	return date + "_" + strings.ReplaceAll(timeStr, " ", "_") + "_" + title
}

func main() {
	cfg := &Config{
		Interval:   getEnvDuration("CRAWL_INTERVAL", 5*time.Minute),
		OutputDir:  getEnvString("OUTPUT_DIR", "./data/ssgs"),
		MaxRetries: 3,
		Timeout:    DefaultTimeout,
		Headless:   getEnvBool("HEADLESS", true),
	}

	configFile := getEnvString("CONFIG_FILE", "./configs/config.yaml")
	if yamlData, err := os.ReadFile(configFile); err == nil {
		var yamlConfig YAMLConfig
		if err := yaml.Unmarshal(yamlData, &yamlConfig); err == nil {
			cfg.MongoURI = yamlConfig.Storage.MongoSSGS.URI
			cfg.MongoDB = yamlConfig.Storage.MongoSSGS.Database
			cfg.MongoColl = yamlConfig.Storage.MongoSSGS.Collection
			if yamlConfig.Storage.JSON.OutputDir != "" {
				cfg.OutputDir = yamlConfig.Storage.JSON.OutputDir + "/ssgs"
			}
			if yamlConfig.SSGS.MaxNewsItems > 0 {
				cfg.MaxNewsItems = yamlConfig.SSGS.MaxNewsItems
				log.Printf("Configured max_news_items: %d", cfg.MaxNewsItems)
			}
			if yamlConfig.SSGS.Timeout > 0 {
				cfg.Timeout = time.Duration(yamlConfig.SSGS.Timeout) * time.Second
				log.Printf("Configured timeout: %v", cfg.Timeout)
			}
			if cfg.MongoURI != "" {
				cfg.UseMongoDB = true
			}
		}
	} else {
		log.Printf("Warning: Failed to read config file %s: %v", configFile, err)
	}

	crawler, err := NewSSGSCrawler(cfg)
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
