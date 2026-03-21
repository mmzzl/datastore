package main

import (
	"fmt"
	"log"

	"go-web-scraper/internal/api"
)

func main() {
	client := api.NewSearchClient()
	news, totalHits, err := client.SearchNews("智谱", 1, 5)
	if err != nil {
		log.Fatalf("Failed to search news: %v", err)
	}

	fmt.Printf("Total hits: %d\n", totalHits)
	fmt.Printf("Found %d news items\n\n", len(news))

	for i, item := range news {
		fmt.Printf("[%d] ID: %s\n", i+1, item.Code)
		fmt.Printf("    Title: %s\n", item.Title)
		fmt.Printf("    Date: %s\n", item.Date)
		fmt.Printf("    RelationStockTags: %v\n", item.RelationStockTags)
		fmt.Printf("    URL: %s\n", item.UniqueURL)
		fmt.Println()
	}
}
