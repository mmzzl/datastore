package main

import (
	"fmt"
	"log"

	"go-web-scraper/internal/api"
)

func main() {
	client := api.NewSearchClient()
	
	news1, _, err := client.SearchNews("掌阅科技", 1, 1)
	if err != nil {
		log.Fatalf("Failed to search news: %v", err)
	}
	
	if len(news1) > 0 {
		fmt.Printf("掌阅科技:\n")
		fmt.Printf("  Title: %s\n", news1[0].Title)
		fmt.Printf("  RelationStockTags: %v\n", news1[0].RelationStockTags)
		fmt.Println()
	}
	
	news2, _, err := client.SearchNews("石四药集团", 1, 1)
	if err != nil {
		log.Fatalf("Failed to search news: %v", err)
	}
	
	if len(news2) > 0 {
		fmt.Printf("石四药集团:\n")
		fmt.Printf("  Title: %s\n", news2[0].Title)
		fmt.Printf("  RelationStockTags: %v\n", news2[0].RelationStockTags)
		fmt.Println()
	}
	
	news3, _, err := client.SearchNews("上海小南国", 1, 1)
	if err != nil {
		log.Fatalf("Failed to search news: %v", err)
	}
	
	if len(news3) > 0 {
		fmt.Printf("上海小南国:\n")
		fmt.Printf("  Title: %s\n", news3[0].Title)
		fmt.Printf("  RelationStockTags: %v\n", news3[0].RelationStockTags)
		fmt.Println()
	}
	
	news4, _, err := client.SearchNews("华虹半导体", 1, 1)
	if err != nil {
		log.Fatalf("Failed to search news: %v", err)
	}
	
	if len(news4) > 0 {
		fmt.Printf("华虹半导体:\n")
		fmt.Printf("  Title: %s\n", news4[0].Title)
		fmt.Printf("  RelationStockTags: %v\n", news4[0].RelationStockTags)
		fmt.Println()
	}
	
	news5, _, err := client.SearchNews("联想集团", 1, 1)
	if err != nil {
		log.Fatalf("Failed to search news: %v", err)
	}
	
	if len(news5) > 0 {
		fmt.Printf("联想集团:\n")
		fmt.Printf("  Title: %s\n", news5[0].Title)
		fmt.Printf("  RelationStockTags: %v\n", news5[0].RelationStockTags)
		fmt.Println()
	}
}
