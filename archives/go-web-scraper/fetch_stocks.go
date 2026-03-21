package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
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
	url := fmt.Sprintf("http://80.push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5000&po=1&np=1&fltt=2&invt=2&fid=f3&fs=%s&fields=f12,f14", market)
	
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
	
	var stocks []string
	for _, stock := range result.Data.Diff {
		stocks = append(stocks, fmt.Sprintf("%s|%s", stock.F12, stock.F14))
	}
	
	return stocks, nil
}

func main() {
	fmt.Println("Fetching A-share stock list...")
	aShareStocks, err := fetchStockList("m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23")
	if err != nil {
		fmt.Printf("Failed to fetch A-share stocks: %v\n", err)
	} else {
		fmt.Printf("Found %d A-share stocks\n", len(aShareStocks))
		for i, stock := range aShareStocks {
			if i < 10 {
				fmt.Printf("  %s\n", stock)
			}
		}
		if len(aShareStocks) > 10 {
			fmt.Printf("  ... and %d more\n", len(aShareStocks)-10)
		}
	}
	
	fmt.Println("\nFetching Hong Kong stock list...")
	hkStocks, err := fetchStockList("m:116+t:2")
	if err != nil {
		fmt.Printf("Failed to fetch Hong Kong stocks: %v\n", err)
	} else {
		fmt.Printf("Found %d Hong Kong stocks\n", len(hkStocks))
		for i, stock := range hkStocks {
			if i < 10 {
				fmt.Printf("  %s\n", stock)
			}
		}
		if len(hkStocks) > 10 {
			fmt.Printf("  ... and %d more\n", len(hkStocks)-10)
		}
	}
}
