package main

import (
	"context"
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

	result, err := collection.DeleteMany(ctx, bson.M{"id": bson.M{"$in": []string{"202602163651194821", "202602163651194443", "202602163651194334", "202602163651192582", "202602163651188695"}}})
	if err != nil {
		log.Fatalf("Failed to delete document: %v", err)
	}

	log.Printf("Deleted %d document(s)", result.DeletedCount)
}
