package api

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"regexp"
	"strconv"
	"time"
)

const (
	SearchAPIBaseURL = "https://search-api-web.eastmoney.com/search/jsonp"
)

type SearchRequest struct {
	UID           string                 `json:"uid"`
	Keyword       string                 `json:"keyword"`
	Type          []string               `json:"type"`
	Client        string                 `json:"client"`
	ClientVersion string                 `json:"clientVersion"`
	ClientType    string                 `json:"clientType"`
	Param         map[string]interface{} `json:"param"`
}

type SearchParam struct {
	Column       string `json:"column"`
	CmsColumnList string `json:"cmsColumnList"`
	PageIndex    int    `json:"pageIndex"`
	PageSize     int    `json:"pageSize"`
}

type SearchResponse struct {
	BizCode  string `json:"bizCode"`
	BizMsg   string `json:"bizMsg"`
	Code     int    `json:"code"`
	Extra    map[string]interface{} `json:"extra"`
	HitsTotal int   `json:"hitsTotal"`
	Msg      string `json:"msg"`
	Result   SearchResult `json:"result"`
	SearchID string `json:"searchId"`
}

type SearchResult struct {
	CmsArticleWebFast []SearchNewsItem `json:"cmsArticleWebFast"`
}

type SearchNewsItem struct {
	Date             string   `json:"date"`
	CommentNum       int      `json:"commentNum"`
	Code             string   `json:"code"`
	DocuReader       string   `json:"docuReader"`
	TitleColor       int      `json:"titleColor"`
	RelationStockTags []string `json:"relationStockTags"`
	UniqueURL        string   `json:"uniqueUrl"`
	Column           string   `json:"column"`
	ColumnList       string   `json:"columnList"`
	Title            string   `json:"title"`
}

type SearchClient struct {
	Client *http.Client
}

func NewSearchClient() *SearchClient {
	return &SearchClient{
		Client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func (c *SearchClient) SearchNews(keyword string, pageIndex int, pageSize int) ([]SearchNewsItem, int, error) {
	searchParam := SearchParam{
		Column:       "103",
		CmsColumnList: "",
		PageIndex:    pageIndex,
		PageSize:     pageSize,
	}

	searchRequest := SearchRequest{
		UID:           "",
		Keyword:       keyword,
		Type:          []string{"cmsArticleWebFast"},
		Client:        "web",
		ClientVersion: "1.0",
		ClientType:    "kuaixun",
		Param: map[string]interface{}{
			"cmsArticleWebFast": searchParam,
		},
	}

	jsonData, err := json.Marshal(searchRequest)
	if err != nil {
		return nil, 0, fmt.Errorf("marshal request failed: %w", err)
	}

	params := url.Values{}
	params.Set("param", string(jsonData))
	params.Set("cb", fmt.Sprintf("jQuery18302794068499798268_%d", time.Now().UnixNano()))
	params.Set("_", strconv.FormatInt(time.Now().UnixNano(), 10))

	fullURL := SearchAPIBaseURL + "?" + params.Encode()

	req, err := http.NewRequest("GET", fullURL, nil)
	if err != nil {
		return nil, 0, fmt.Errorf("create request failed: %w", err)
	}

	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
	req.Header.Set("Referer", "https://kuaixun.eastmoney.com/")
	req.Header.Set("Accept", "*/*")

	resp, err := c.Client.Do(req)
	if err != nil {
		return nil, 0, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, 0, fmt.Errorf("read response failed: %w", err)
	}

	jsonStr := c.extractJSON(string(body))
	if jsonStr == "" {
		return nil, 0, fmt.Errorf("failed to extract JSON from response, body: %s", string(body))
	}

	var response SearchResponse
	if err := json.Unmarshal([]byte(jsonStr), &response); err != nil {
		return nil, 0, fmt.Errorf("parse JSON failed: %w, json: %s", err, jsonStr)
	}

	if response.Code != 0 {
		return nil, 0, fmt.Errorf("API returned error code: %d, message: %s", response.Code, response.Msg)
	}

	return response.Result.CmsArticleWebFast, response.HitsTotal, nil
}

func (c *SearchClient) SearchAllNews(keyword string, maxCount int) ([]SearchNewsItem, int, error) {
	var allNews []SearchNewsItem
	pageIndex := 1
	pageSize := 50
	totalHits := 0

	for maxCount <= 0 || len(allNews) < maxCount {
		news, hits, err := c.SearchNews(keyword, pageIndex, pageSize)
		if err != nil {
			return allNews, totalHits, err
		}

		if hits > 0 && totalHits == 0 {
			totalHits = hits
		}

		if len(news) == 0 {
			break
		}

		allNews = append(allNews, news...)

		if len(news) < pageSize || len(allNews) >= totalHits {
			break
		}

		pageIndex++
		time.Sleep(500 * time.Millisecond)
	}

	if maxCount > 0 && len(allNews) > maxCount {
		allNews = allNews[:maxCount]
	}

	return allNews, totalHits, nil
}

func (c *SearchClient) extractJSON(body string) string {
	re := regexp.MustCompile(`jQuery\d+_\d+\((.*)\)`)
	matches := re.FindStringSubmatch(body)
	if len(matches) > 1 {
		return matches[1]
	}
	return ""
}

func (c *SearchClient) ExtractTitleAndContent(docuReader string) (string, string) {
	re := regexp.MustCompile(`【(.*?)】`)
	matches := re.FindStringSubmatch(docuReader)
	if len(matches) > 1 {
		title := matches[1]
		content := re.ReplaceAllString(docuReader, "")
		return title, content
	}
	return "", docuReader
}
