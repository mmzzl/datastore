package main

import (
	"fmt"
	"strings"
)

func parseStockTag(tag string) (string, string) {
	parts := strings.Split(tag, ".")
	if len(parts) < 2 {
		return "", ""
	}
	
	code := parts[1]
	
	if strings.HasPrefix(code, "BK") {
		return "", ""
	}
	
	stockCode := code
	
	if len(code) == 4 && strings.HasPrefix(code, "0") {
		stockCode = strings.TrimPrefix(code, "0")
	} else if len(code) == 5 && strings.HasPrefix(code, "0") {
		stockCode = strings.TrimPrefix(code, "0")
	}
	
	name := stockCode
	
	return stockCode, name
}

func main() {
	tags := []string{"116.01810", "116.01093", "116.03690", "116.03696", "116.09988"}
	
	for _, tag := range tags {
		code, name := parseStockTag(tag)
		fmt.Printf("Tag: %s -> Code: %s, Name: %s\n", tag, code, name)
	}
}
