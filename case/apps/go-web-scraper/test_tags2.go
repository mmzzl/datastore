package main

import (
	"fmt"
	"log"

	"go-web-scraper/internal/api"
)

func main() {
	client := api.NewSearchClient()
	
	news1, _, err := client.SearchNews("小米集团", 1, 1)
	if err != nil {
		log.Fatalf("Failed to search news: %v", err)
	}
	
	if len(news1) > 0 {
		fmt.Printf("小米集团:\n")
		fmt.Printf("  Title: %s\n", news1[0].Title)
		fmt.Printf("  RelationStockTags: %v\n", news1[0].RelationStockTags)
		fmt.Println()
	}
	
	news2, _, err := client.SearchNews("石药集团", 1, 1)
	if err != nil {
		log.Fatalf("Failed to search news: %v", err)
	}
	
	if len(news2) > 0 {
		fmt.Printf("石药集团:\n")
		fmt.Printf("  Title: %s\n", news2[0].Title)
		fmt.Printf("  RelationStockTags: %v\n", news2[0].RelationStockTags)
		fmt.Println()
	}
	
	news3, _, err := client.SearchNews("美团", 1, 1)
	if err != nil {
		log.Fatalf("Failed to search news: %v", err)
	}
	
	if len(news3) > 0 {
		fmt.Printf("美团:\n")
		fmt.Printf("  Title: %s\n", news3[0].Title)
		fmt.Printf("  RelationStockTags: %v\n", news3[0].RelationStockTags)
		fmt.Println()
	}
	
	news4, _, err := client.SearchNews("英矽智能", 1, 1)
	if err != nil {
		log.Fatalf("Failed to search news: %v", err)
	}
	
	if len(news4) > 0 {
		fmt.Printf("英矽智能:\n")
		fmt.Printf("  Title: %s\n", news4[0].Title)
		fmt.Printf("  RelationStockTags: %v\n", news4[0].RelationStockTags)
		fmt.Println()
	}
	
	news5, _, err := client.SearchNews("阿里巴巴", 1, 1)
	if err != nil {
		log.Fatalf("Failed to search news: %v", err)
	}
	
	if len(news5) > 0 {
		fmt.Printf("阿里巴巴:\n")
		fmt.Printf("  Title: %s\n", news5[0].Title)
		fmt.Printf("  RelationStockTags: %v\n", news5[0].RelationStockTags)
		fmt.Println()
	}
}
