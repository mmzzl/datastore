package crawler

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"time"
)

type HTTPDownloader struct {
	client    *http.Client
	userAgent  string
	timeout   time.Duration
}

func NewHTTPDownloader(timeout time.Duration) *HTTPDownloader {
	return &HTTPDownloader{
		client: &http.Client{
			Timeout: timeout,
			Transport: &http.Transport{
				MaxIdleConns:        100,
				MaxIdleConnsPerHost: 10,
				IdleConnTimeout:     90 * time.Second,
			},
		},
		userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
		timeout:  timeout,
	}
}

func (d *HTTPDownloader) Download(ctx context.Context, task *Task) ([]byte, error) {
	req, err := http.NewRequestWithContext(ctx, task.Method, task.URL, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("User-Agent", d.userAgent)
	for key, value := range task.Headers {
		req.Header.Set(key, value)
	}

	resp, err := d.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to download: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	return data, nil
}

func (d *HTTPDownloader) SetUserAgent(userAgent string) {
	d.userAgent = userAgent
}
