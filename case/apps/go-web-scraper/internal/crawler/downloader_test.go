package crawler

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestHTTPDownloader_Download_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("test data"))
	}))
	defer server.Close()

	downloader := NewHTTPDownloader(30 * time.Second)

	task := &Task{
		ID:     "test-1",
		URL:    server.URL,
		Method: "GET",
	}

	ctx := context.Background()
	data, err := downloader.Download(ctx, task)

	if err != nil {
		t.Fatalf("Failed to download: %v", err)
	}

	if string(data) != "test data" {
		t.Errorf("Expected 'test data', got '%s'", string(data))
	}
}

func TestHTTPDownloader_Download_NotFound(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNotFound)
	}))
	defer server.Close()

	downloader := NewHTTPDownloader(30 * time.Second)

	task := &Task{
		ID:     "test-1",
		URL:    server.URL,
		Method: "GET",
	}

	ctx := context.Background()
	_, err := downloader.Download(ctx, task)

	if err == nil {
		t.Fatal("Expected error for 404 response, got nil")
	}
}

func TestHTTPDownloader_Download_Timeout(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(2 * time.Second)
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	downloader := NewHTTPDownloader(100 * time.Millisecond)

	task := &Task{
		ID:     "test-1",
		URL:    server.URL,
		Method: "GET",
	}

	ctx := context.Background()
	_, err := downloader.Download(ctx, task)

	if err == nil {
		t.Fatal("Expected timeout error, got nil")
	}
}

func TestHTTPDownloader_Download_UserAgent(t *testing.T) {
	receivedUserAgent := ""
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		receivedUserAgent = r.Header.Get("User-Agent")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("test data"))
	}))
	defer server.Close()

	downloader := NewHTTPDownloader(30 * time.Second)
	customUserAgent := "CustomAgent/1.0"
	downloader.SetUserAgent(customUserAgent)

	task := &Task{
		ID:     "test-1",
		URL:    server.URL,
		Method: "GET",
	}

	ctx := context.Background()
	_, err := downloader.Download(ctx, task)

	if err != nil {
		t.Fatalf("Failed to download: %v", err)
	}

	if receivedUserAgent != customUserAgent {
		t.Errorf("Expected User-Agent %s, got %s", customUserAgent, receivedUserAgent)
	}
}

func TestHTTPDownloader_Download_CustomHeaders(t *testing.T) {
	receivedCustomHeader := ""
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		receivedCustomHeader = r.Header.Get("X-Custom-Header")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("test data"))
	}))
	defer server.Close()

	downloader := NewHTTPDownloader(30 * time.Second)

	task := &Task{
		ID:     "test-1",
		URL:    server.URL,
		Method: "GET",
		Headers: map[string]string{
			"X-Custom-Header": "CustomValue",
		},
	}

	ctx := context.Background()
	_, err := downloader.Download(ctx, task)

	if err != nil {
		t.Fatalf("Failed to download: %v", err)
	}

	if receivedCustomHeader != "CustomValue" {
		t.Errorf("Expected custom header 'CustomValue', got '%s'", receivedCustomHeader)
	}
}
