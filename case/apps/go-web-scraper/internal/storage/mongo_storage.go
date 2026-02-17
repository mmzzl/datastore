package storage

import (
	"context"
	"fmt"
	"log"
	"time"

	"go-web-scraper/internal/model"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type MongoDBStorage struct {
	client     *mongo.Client
	collection *mongo.Collection
	database   *mongo.Database
}

func NewMongoStorage(uri, database, collection string) (*MongoDBStorage, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	client, err := mongo.Connect(ctx, options.Client().ApplyURI(uri))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to MongoDB: %w", err)
	}

	err = client.Ping(ctx, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to ping MongoDB: %w", err)
	}

	db := client.Database(database)
	coll := db.Collection(collection)

	log.Printf("Connected to MongoDB: %s, database: %s, collection: %s", uri, database, collection)

	return &MongoDBStorage{
		client:     client,
		collection: coll,
		database:   db,
	}, nil
}

func (m *MongoDBStorage) Save(ctx context.Context, data interface{}) error {
	if itemMap, ok := data.(map[string]interface{}); ok {
		if id, exists := itemMap["id"].(string); exists {
			filter := bson.M{"id": id}
			count, err := m.collection.CountDocuments(ctx, filter)
			if err != nil {
				return fmt.Errorf("failed to check document existence: %w", err)
			}
			if count > 0 {
				log.Printf("Document with id %s already exists, skipping", id)
				return nil
			}
		}
	}

	_, err := m.collection.InsertOne(ctx, data)
	if err != nil {
		return fmt.Errorf("failed to insert document: %w", err)
	}
	return nil
}

func (m *MongoDBStorage) BatchSave(ctx context.Context, batch []interface{}) error {
	if len(batch) == 0 {
		return nil
	}

	var documents []interface{}
	var skippedCount int

	for _, item := range batch {
		var id string
		
		if itemMap, ok := item.(map[string]interface{}); ok {
			if idValue, exists := itemMap["id"].(string); exists {
				id = idValue
			}
		} else if news, ok := item.(model.EastMoneyNews); ok {
			id = news.ID
		} else if newsPtr, ok := item.(*model.EastMoneyNews); ok {
			id = newsPtr.ID
		}
		
		if id != "" {
			filter := bson.M{"id": id}
			count, err := m.collection.CountDocuments(ctx, filter)
			if err != nil {
				log.Printf("Failed to check document existence for id %s: %v", id, err)
				documents = append(documents, item)
			} else if count > 0 {
				skippedCount++
				log.Printf("Document with id %s already exists, skipping", id)
			} else {
				documents = append(documents, item)
			}
		} else {
			log.Printf("Warning: item has no id, will be inserted")
			documents = append(documents, item)
		}
	}

	if len(documents) > 0 {
		_, err := m.collection.InsertMany(ctx, documents)
		if err != nil {
			return fmt.Errorf("failed to insert documents: %w", err)
		}
		log.Printf("Inserted %d new documents", len(documents))
	}

	if skippedCount > 0 {
		log.Printf("Skipped %d duplicate documents", skippedCount)
	}

	return nil
}

func (m *MongoDBStorage) Close() error {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	return m.client.Disconnect(ctx)
}

func (m *MongoDBStorage) GetCollection() *mongo.Collection {
	return m.collection
}
