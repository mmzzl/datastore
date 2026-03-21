package storage

import (
	"context"
	"fmt"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type CrawlState struct {
	CrawlerName string    `bson:"crawler_name"`
	LastSort   string    `bson:"last_sort"`
	LastTime   time.Time `bson:"last_time"`
	UpdatedAt  time.Time `bson:"updated_at"`
}

type CrawlStateManager struct {
	client     *mongo.Client
	collection *mongo.Collection
}

func NewCrawlStateManager(uri, database string) (*CrawlStateManager, error) {
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
	coll := db.Collection("crawl_state")

	return &CrawlStateManager{
		client:     client,
		collection: coll,
	}, nil
}

func (m *CrawlStateManager) GetLastState(ctx context.Context, crawlerName string) (*CrawlState, error) {
	filter := bson.M{"crawler_name": crawlerName}
	var state CrawlState
	err := m.collection.FindOne(ctx, filter).Decode(&state)
	if err != nil {
		if err == mongo.ErrNoDocuments {
			return nil, nil
		}
		return nil, fmt.Errorf("failed to get crawl state: %w", err)
	}
	return &state, nil
}

func (m *CrawlStateManager) UpdateState(ctx context.Context, crawlerName, lastSort string, lastTime time.Time) error {
	filter := bson.M{"crawler_name": crawlerName}
	update := bson.M{
		"$set": bson.M{
			"last_sort":  lastSort,
			"last_time":  lastTime,
			"updated_at": time.Now(),
		},
	}
	opts := options.Update().SetUpsert(true)
	_, err := m.collection.UpdateOne(ctx, filter, update, opts)
	if err != nil {
		return fmt.Errorf("failed to update crawl state: %w", err)
	}
	return nil
}

func (m *CrawlStateManager) Close() error {
	return m.client.Disconnect(context.Background())
}
