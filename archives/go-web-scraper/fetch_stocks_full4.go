package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

type StockListResponse struct {
	Data struct {
		Diff []struct {
			F12 string `json:"f12"`
		F14 string `json:"f14"`
		} `json:"diff"`
		Total int `json:"total"`
	} `json:"data"`
}

func fetchStockList(market string) ([]string, error) {
	var allStocks []string
	page := 1
	pageSize := 100
	
	for {
		url := fmt.Sprintf("http://80.push2.eastmoney.com/api/qt/clist/get?pn=%d&pz=%d&po=1&np=1&fltt=2&invt=2&fid=f3&fs=%s&fields=f12,f14", page, pageSize, market)
		
		client := &http.Client{Timeout: 10 * time.Second}
		resp, err := client.Get(url)
		if err != nil {
			return nil, fmt.Errorf("failed to fetch stock list: %w", err)
		}
		defer resp.Body.Close()
		
		body, err := io.ReadAll(resp.Body)
		if err != nil {
			return nil, fmt.Errorf("failed to read response: %w", err)
		}
		
		var result StockListResponse
		if err := json.Unmarshal(body, &result); err != nil {
			return nil, fmt.Errorf("failed to parse response: %w", err)
		}
		
		if len(result.Data.Diff) == 0 {
			break
		}
		
		for _, stock := range result.Data.Diff {
			allStocks = append(allStocks, fmt.Sprintf("%s|%s", stock.F12, stock.F14))
		}
		
		if page == 1 {
			fmt.Printf("  Total stocks in API: %d\n", result.Data.Total)
		}
		fmt.Printf("  Page %d: fetched %d stocks (total: %d)\n", page, len(result.Data.Diff), len(allStocks))
		
		if len(result.Data.Diff) < pageSize {
			break
		}
		
		page++
	}
	
	return allStocks, nil
}

func main() {
	file, err := os.Create("configs/stock_codes_full.txt")
	if err != nil {
		fmt.Printf("Failed to create file: %v\n", err)
		return
	}
	defer file.Close()
	
	file.WriteString("# 股票代码列表配置\n")
	file.WriteString("# 格式: 股票代码|股票名称\n")
	file.WriteString("# 生成时间: " + time.Now().Format("2006-01-02 15:04:05") + "\n\n")
	
	fmt.Println("Fetching A-share stock list...")
	aShareStocks, err := fetchStockList("m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23")
	if err != nil {
		fmt.Printf("Failed to fetch A-share stocks: %v\n", err)
	} else {
		fmt.Printf("\nTotal A-share stocks: %d\n", len(aShareStocks))
		for _, stock := range aShareStocks {
			file.WriteString(stock + "\n")
		}
	}
	
	fmt.Println("\nFetching Hong Kong stock list...")
	hkStocks, err := fetchStockList("m:116+t:2")
	if err != nil {
		fmt.Printf("Failed to fetch Hong Kong stocks: %v\n", err)
	} else {
		fmt.Printf("\nTotal Hong Kong stocks: %d\n", len(hkStocks))
		for _, stock := range hkStocks {
			file.WriteString(stock + "\n")
		}
	}
	
	fmt.Printf("\nTotal stocks written to configs/stock_codes_full.txt: %d\n", len(aShareStocks)+len(hkStocks))
}
