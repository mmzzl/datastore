package model

import "time"

type EastMoneyNews struct {
	ID          string    `json:"id" bson:"id"`
	Title       string    `json:"title" bson:"title"`
	Content     string    `json:"content" bson:"content"`
	URL         string    `json:"url" bson:"url"`
	PublishTime string    `json:"publish_time" bson:"publish_time"`
	Source      string    `json:"source" bson:"source"`
	Stocks      []Stock   `json:"stocks,omitempty" bson:"stocks,omitempty"`
	CreatedAt   time.Time `json:"created_at" bson:"created_at"`
}

func (n *EastMoneyNews) GetID() string {
	return n.ID
}

type Stock struct {
	Name   string  `json:"name" bson:"name"`
	Change float64 `json:"change" bson:"change"`
}
