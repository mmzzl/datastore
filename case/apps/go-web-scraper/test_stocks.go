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

	cursor, err := collection.Find(ctx, bson.M{"stocks": bson.M{"$ne": nil}}, options.Find().SetLimit(5))
	if err != nil {
		log.Fatalf("Failed to find documents: %v", err)
	}
	defer cursor.Close(ctx)

	var results []struct {
		ID     string `bson:"id"`
		Title  string `bson:"title"`
		Stocks []struct {
			Code string `bson:"code"`
			Name string `bson:"name"`
		} `bson:"stocks"`
	}

	if err = cursor.All(ctx, &results); err != nil {
		log.Fatalf("Failed to decode documents: %v", err)
	}

	fmt.Printf("Found %d documents with stocks\n", len(results))
	for i, result := range results {
		fmt.Printf("\n[%d] ID: %s\n", i+1, result.ID)
		fmt.Printf("    Title: %s\n", result.Title)
		fmt.Printf("    Stocks:\n")
		for _, stock := range result.Stocks {
			fmt.Printf("      - Code: %s, Name: %s\n", stock.Code, stock.Name)
		}
	}
}
