package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	client, err := mongo.Connect(ctx, options.Client().ApplyURI("mongodb://admin:aa123aaqqA!@121.37.47.63:27017"))
	if err != nil {
		log.Fatalf("Failed to connect to MongoDB: %v", err)
	}
	defer client.Disconnect(ctx)

	collection := client.Database("crawler").Collection("eastmoney_news_ssgs")

	cursor, err := collection.Find(ctx, bson.M{"id": "202602163651185868"})
	if err != nil {
		log.Fatalf("Failed to find document: %v", err)
	}
	defer cursor.Close(ctx)

	var rawResult bson.M
	if cursor.Next(ctx) {
		if err := cursor.Decode(&rawResult); err != nil {
			log.Fatalf("Failed to decode: %v", err)
		}
		
		fmt.Printf("Raw document:\n")
		for k, v := range rawResult {
			fmt.Printf("  %s: %v\n", k, v)
		}
		
		if stocks, ok := rawResult["stocks"].(bson.A); ok {
			fmt.Printf("\nStocks details:\n")
			for i, stock := range stocks {
				if stockMap, ok := stock.(bson.M); ok {
					fmt.Printf("  [%d]\n", i)
					for k, v := range stockMap {
						fmt.Printf("    %s: %v\n", k, v)
					}
				}
			}
		}
	}
}
