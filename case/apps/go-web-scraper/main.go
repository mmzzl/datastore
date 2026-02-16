package main 

import (
	"fmt"
	"net/http"
	"regexp"
	"sync"
	"encoding/csv"
	"encoding/json"
	"os"
)
type DataRecord struct {
	Title string `json:"title"`
	URL string `json:"url"`
	Date string `json:"Date"`
}

func saveToCSV(records [] DataRecord, filename string) error {
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()
	//写入CSV标题行
	if err := writer.Write([]string{"Title", "URL", "Date"}); err != nil {
		return err
	}
	// 写入数据记录
	for _, record := range records {
		record := []string{record.Title, record.URL, record.Date}
		if err := writer.Write(record); err != nil {
			return err
		}
	}
	return nil
}
// 保存为JSON
func saveToJSON(records []DataRecord, filename string) error {
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(records); err != nil {
		return err
	}
	return nil
}

func fetchURL(url string, results chan<- URLResult, wg *sync.WaitGroup) {
	defer wg.Done()

	resp, err := http.Get(url)
	if err != nil {
		results <- URLResult{URL: url, Status: 0}
		return 
	}
	defer resp.Body.Close()
	results <- URLResult{URL: url, Status: resp.StatusCode}
}

func extractLinks(content string)[]string {
	//使用正则表达式提取连接
	linkPattern := regexp.MustCompile(`<a href="([^"]+)">`)
	matches := linkPattern.FindAllStringSubmatch(content, -1)
	var links []string
	for _, match := range matches {
		if len(match) > 1 {
			links = append(links, match[1])
		}
	}
	return links
}
type URLResult struct {
	URL string
	Status int
}

func main() {
	url := []string{
		"https://example.com",
		"https://example.org",
		"https://example.net",
	}
	results := make(chan URLResult, len(url))
	wg := sync.WaitGroup{}
	for _, u := range url {
		wg.Add(1)
		go fetchURL(u, results, &wg)
	}
	go func() {
		wg.Wait()
		close(results)
	}()
	for result := range results {
		fmt.Printf("URL: %s, Status: %d\n", result.URL, result.Status)
	}
}