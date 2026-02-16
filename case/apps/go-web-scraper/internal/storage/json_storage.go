package storage

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

type JSONStorage struct {
	filePath string
	mu       sync.Mutex
}

func NewJSONStorage(filePath string) *JSONStorage {
	dir := filepath.Dir(filePath)
	if dir != "" {
		os.MkdirAll(dir, 0755)
	}
	return &JSONStorage{
		filePath: filePath,
	}
}

func (s *JSONStorage) Save(ctx context.Context, data interface{}) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	var existingData []interface{}
	if fileData, err := os.ReadFile(s.filePath); err == nil {
		json.Unmarshal(fileData, &existingData)
	}

	existingData = append(existingData, data)

	jsonData, err := json.MarshalIndent(existingData, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal data: %w", err)
	}

	return os.WriteFile(s.filePath, jsonData, 0644)
}

func (s *JSONStorage) BatchSave(ctx context.Context, batch []interface{}) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	var existingData []interface{}
	if fileData, err := os.ReadFile(s.filePath); err == nil {
		json.Unmarshal(fileData, &existingData)
	}

	existingData = append(existingData, batch...)

	jsonData, err := json.MarshalIndent(existingData, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal data: %w", err)
	}

	return os.WriteFile(s.filePath, jsonData, 0644)
}

func (s *JSONStorage) Close() error {
	return nil
}

type DailyJSONStorage struct {
	baseDir string
	mu      sync.Mutex
}

func NewDailyJSONStorage(baseDir string) *DailyJSONStorage {
	os.MkdirAll(baseDir, 0755)
	return &DailyJSONStorage{
		baseDir: baseDir,
	}
}

func (s *DailyJSONStorage) getFilePath() string {
	date := time.Now().Format("2006-01-02")
	return filepath.Join(s.baseDir, fmt.Sprintf("eastmoney_news_%s.json", date))
}

func (s *DailyJSONStorage) Save(ctx context.Context, data interface{}) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	filePath := s.getFilePath()

	var existingData []interface{}
	if fileData, err := os.ReadFile(filePath); err == nil {
		json.Unmarshal(fileData, &existingData)
	}

	existingData = append(existingData, data)

	jsonData, err := json.MarshalIndent(existingData, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal data: %w", err)
	}

	return os.WriteFile(filePath, jsonData, 0644)
}

func (s *DailyJSONStorage) BatchSave(ctx context.Context, batch []interface{}) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	filePath := s.getFilePath()

	var existingData []interface{}
	if fileData, err := os.ReadFile(filePath); err == nil {
		json.Unmarshal(fileData, &existingData)
	}

	idSet := make(map[string]bool)
	for _, item := range existingData {
		if m, ok := item.(map[string]interface{}); ok {
			if id, exists := m["id"].(string); exists {
				idSet[id] = true
			}
		}
	}

	for _, item := range batch {
		if m, ok := item.(map[string]interface{}); ok {
			if id, exists := m["id"].(string); exists {
				if !idSet[id] {
					existingData = append(existingData, item)
					idSet[id] = true
				}
			} else {
				existingData = append(existingData, item)
			}
		} else {
			existingData = append(existingData, item)
		}
	}

	jsonData, err := json.MarshalIndent(existingData, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal data: %w", err)
	}

	return os.WriteFile(filePath, jsonData, 0644)
}

func (s *DailyJSONStorage) Close() error {
	return nil
}
