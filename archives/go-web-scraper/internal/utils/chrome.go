package utils

import (
	"fmt"
	"os/exec"
	"runtime"
)

// FindChromePath 查找 Chrome 可执行文件的路径
func FindChromePath() string {
	switch runtime.GOOS {
	case "linux":
		// Linux 上的常见 Chrome 路径
		chromePaths := []string{
			"/usr/bin/google-chrome",
			"/usr/bin/chromium-browser",
			"/usr/bin/chromium",
			"/usr/bin/google-chrome-stable",
			"/snap/bin/chromium",
		}
		for _, path := range chromePaths {
			if _, err := exec.LookPath(path); err == nil {
				return path
			}
		}
	case "windows":
		// Windows 上的 Chrome 路径
		chromePaths := []string{
			"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
			"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
		}
		for _, path := range chromePaths {
			if _, err := exec.LookPath(path); err == nil {
				return path
			}
		}
	case "darwin":
		// macOS 上的 Chrome 路径
		chromePaths := []string{
			"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
		}
		for _, path := range chromePaths {
			if _, err := exec.LookPath(path); err == nil {
				return path
			}
		}
	}
	return ""
}

// GetChromePath 获取 Chrome 路径，如果找不到则返回空字符串
func GetChromePath() string {
	path := FindChromePath()
	if path == "" {
		fmt.Printf("Warning: Chrome not found in system PATH. Please install Chrome or specify the path manually.\n")
	}
	return path
}
