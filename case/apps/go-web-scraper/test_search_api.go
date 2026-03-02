package main

import (
	"encoding/json"
	"fmt"
	"log"

	"go-web-scraper/internal/api"
)

func main() {
	client := api.NewSearchClient()
	news, totalHits, err := client.SearchNews("贵州茅台", 1, 5)
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
		
		title, content := client.ExtractTitleAndContent(item.DocuReader)
		fmt.Printf("    Extracted Title: %s\n", title)
		fmt.Printf("    Content: %s\n", content)
		fmt.Println()
		
		jsonData, _ := json.MarshalIndent(item, "", "  ")
		fmt.Printf("Full JSON:\n%s\n\n", string(jsonData))
	}
}
