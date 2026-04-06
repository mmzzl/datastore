import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 30000,
  use: {
    baseURL: 'http://localhost:3001',
    headless: true,
    channel: 'chrome',
    executablePath: 'C:\\Users\\life8\\AppData\\Local\\ms-playwright\\chromium-1140\\chrome-win\\chrome.exe',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});