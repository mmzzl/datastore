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

	var result struct {
		ID     string `bson:"id"`
		Title  string `bson:"title"`
		Stocks []struct {
			Code string `bson:"code"`
			Name string `bson:"name"`
		} `bson:"stocks"`
	}

	err = collection.FindOne(ctx, bson.M{"id": "202602163651196329"}).Decode(&result)
	if err != nil {
		log.Fatalf("Failed to find document: %v", err)
	}

	fmt.Printf("ID: %s\n", result.ID)
	fmt.Printf("Title: %s\n", result.Title)
	fmt.Printf("Stocks: %v\n", result.Stocks)
	
	cursor, err := collection.Find(ctx, bson.M{"id": "202602163651196329"})
	if err != nil {
		log.Fatalf("Failed to find document: %v", err)
	}
	defer cursor.Close(ctx)

	var rawResult bson.M
	if cursor.Next(ctx) {
		if err := cursor.Decode(&rawResult); err != nil {
			log.Fatalf("Failed to decode: %v", err)
		}
		
		fmt.Printf("\nRaw document:\n")
		for k, v := range rawResult {
			fmt.Printf("  %s: %v\n", k, v)
		}
	}
}
