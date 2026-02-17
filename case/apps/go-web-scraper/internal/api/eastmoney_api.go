package api

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"regexp"
	"strconv"
	"strings"
	"time"
)

const (
	APIBaseURL = "https://np-weblist.eastmoney.com/comm/web/getFastNewsList"
)

type FastNewsItem struct {
	Code        string   `json:"code"`
	ShowTime    string   `json:"showTime"`
	Title       string   `json:"title"`
	Summary     string   `json:"summary"`
	StockList   []string `json:"stockList"`
	PinglunNum  int      `json:"pinglun_Num"`
	Share       int      `json:"share"`
	Image       []string `json:"image"`
	TitleColor  int      `json:"titleColor"`
	RealSort    string   `json:"realSort"`
}

type FastNewsResponse struct {
	Code    string `json:"code"`
	Message string `json:"message"`
	Data    struct {
		FastNewsList []FastNewsItem `json:"fastNewsList"`
		Index       int            `json:"index"`
		Size        int            `json:"size"`
		SortEnd     string         `json:"sortEnd"`
		Total       int            `json:"total"`
	} `json:"data"`
}

type FastNewsClient struct {
	Client      *http.Client
	Biz         string
	FastColumn  string
}

func NewFastNewsClient() *FastNewsClient {
	return &FastNewsClient{
		Client: &http.Client{
			Timeout: 30 * time.Second,
		},
		Biz:       "web_724",
		FastColumn: "102",
	}
}

func NewFastNewsClientWithColumn(fastColumn string) *FastNewsClient {
	return &FastNewsClient{
		Client: &http.Client{
			Timeout: 30 * time.Second,
		},
		Biz:       "web_724",
		FastColumn: fastColumn,
	}
}

func (c *FastNewsClient) GetFastNews(pageSize int, sortEnd string) ([]FastNewsItem, string, error) {
	params := url.Values{}
	params.Set("client", "web")
	params.Set("biz", c.Biz)
	params.Set("fastColumn", c.FastColumn)
	params.Set("pageSize", strconv.Itoa(pageSize))
	params.Set("sortEnd", sortEnd)
	params.Set("req_trace", strconv.FormatInt(time.Now().UnixNano(), 10))
	params.Set("_", strconv.FormatInt(time.Now().UnixNano(), 10))

	fullURL := APIBaseURL + "?" + params.Encode()

	req, err := http.NewRequest("GET", fullURL, nil)
	if err != nil {
		return nil, "", fmt.Errorf("create request failed: %w", err)
	}

	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
	req.Header.Set("Referer", "https://kuaixun.eastmoney.com/")
	req.Header.Set("Accept", "*/*")

	resp, err := c.Client.Do(req)
	if err != nil {
		return nil, "", fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, "", fmt.Errorf("read response failed: %w", err)
	}

	jsonStr := c.extractJSON(string(body))
	if jsonStr == "" {
		return nil, "", fmt.Errorf("failed to extract JSON from response, body: %s", string(body))
	}

	var response FastNewsResponse
	if err := json.Unmarshal([]byte(jsonStr), &response); err != nil {
		return nil, "", fmt.Errorf("parse JSON failed: %w, json: %s", err, jsonStr)
	}

	if response.Code != "1" {
		return nil, "", fmt.Errorf("API returned error code: %s, message: %s", response.Code, response.Message)
	}

	return response.Data.FastNewsList, response.Data.SortEnd, nil
}

func (c *FastNewsClient) extractJSON(response string) string {
	re := regexp.MustCompile(`jQuery\d+_\d+\((.*)\)`)
	matches := re.FindStringSubmatch(response)
	if len(matches) > 1 {
		return matches[1]
	}
	
	re2 := regexp.MustCompile(`^\{.*\}$`)
	if re2.MatchString(response) {
		return response
	}
	
	return ""
}

func (c *FastNewsClient) GetAllNews(maxCount int) ([]FastNewsItem, error) {
	return c.GetAllNewsFrom(maxCount, "")
}

func (c *FastNewsClient) GetAllNewsFrom(maxCount int, lastSort string) ([]FastNewsItem, error) {
	var allNews []FastNewsItem
	pageSize := 50
	sortEnd := lastSort

	for len(allNews) < maxCount {
		news, newSortEnd, err := c.GetFastNews(pageSize, sortEnd)
		if err != nil {
			return allNews, err
		}

		if len(news) == 0 {
			break
		}

		allNews = append(allNews, news...)

		if len(news) < pageSize {
			break
		}

		sortEnd = newSortEnd
		time.Sleep(500 * time.Millisecond)
	}

	if len(allNews) > maxCount {
		allNews = allNews[:maxCount]
	}

	return allNews, nil
}

func (c *FastNewsClient) ParseStockList(stockList []string) []string {
	var stocks []string
	for _, stock := range stockList {
		if strings.Contains(stock, ".") {
			stocks = append(stocks, stock)
		}
	}
	return stocks
}

func (c *FastNewsClient) ExtractTitleAndContent(summary string) (string, string) {
	summary = strings.TrimSpace(summary)
	
	if strings.Contains(summary, "【") && strings.Contains(summary, "】") {
		start := strings.Index(summary, "【")
		end := strings.Index(summary, "】")
		if end > start {
			title := strings.TrimSpace(summary[start+3 : end])
			content := strings.TrimSpace(summary[end+3:])
			return title, content
		}
	}

	return summary, ""
}
