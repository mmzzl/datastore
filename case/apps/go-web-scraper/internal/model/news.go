package model

import "time"

type EastMoneyNews struct {
	ID          string    `json:"id"`
	Title       string    `json:"title"`
	Content     string    `json:"content"`
	URL         string    `json:"url"`
	PublishTime string    `json:"publish_time"`
	Source      string    `json:"source"`
	Stocks      []Stock   `json:"stocks,omitempty"`
	CreatedAt   time.Time `json:"created_at"`
}

type Stock struct {
	Name   string  `json:"name"`
	Change float64 `json:"change"`
}
