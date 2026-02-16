package storage

import "context"

type Storage interface {
	Save(ctx context.Context, data interface{}) error
	BatchSave(ctx context.Context, batch []interface{}) error
	Close() error
}
