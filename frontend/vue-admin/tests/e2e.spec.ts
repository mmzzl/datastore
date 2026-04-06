import { test, expect } from '@playwright/test';

test.describe('Trading System E2E Tests', () => {
  const API_BASE = 'http://localhost:8000';
  const FRONTEND_BASE = 'http://localhost:5173';

  test.beforeEach(async ({ page }) => {
    await page.goto(FRONTEND_BASE);
  });

  test.describe('Authentication', () => {
    test('Login with valid credentials', async ({ page }) => {
      await page.goto(`${FRONTEND_BASE}/login`);
      
      await page.fill('input[type="text"]', 'admin');
      await page.fill('input[type="password"]', 'aa123aaqqA@');
      await page.click('button[type="submit"]');
      
      await page.waitForURL('**/dashboard', { timeout: 10000 });
      await expect(page.locator('text=仪表盘')).toBeVisible({ timeout: 5000 });
    });

    test('Login shows error with invalid credentials', async ({ page }) => {
      await page.goto(`${FRONTEND_BASE}/login`);
      
      await page.fill('input[type="text"]', 'admin');
      await page.fill('input[type="password"]', 'wrongpassword');
      await page.click('button[type="submit"]');
      
      await page.waitForSelector('.error-msg', { timeout: 5000 });
      await expect(page.locator('.error-msg')).toBeVisible();
    });

    test('Logout works correctly', async ({ page }) => {
      await page.goto(`${FRONTEND_BASE}/login`);
      await page.fill('input[type="text"]', 'admin');
      await page.fill('input[type="password"]', 'aa123aaqqA@');
      await page.click('button[type="submit"]');
      await page.waitForURL('**/dashboard');
      
      await page.click('text=退出登录');
      await page.waitForURL('**/login');
    });
  });

  test.describe('Dashboard', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto(`${FRONTEND_BASE}/login`);
      await page.fill('input[type="text"]', 'admin');
      await page.fill('input[type="password"]', 'aa123aaqqA@');
      await page.click('button[type="submit"]');
      await page.waitForURL('**/dashboard');
    });

    test('Dashboard loads successfully', async ({ page }) => {
      await expect(page.locator('h1:has-text("仪表盘")')).toBeVisible();
    });

    test('Dashboard shows portfolio summary', async ({ page }) => {
      await page.waitForSelector('.n-card, .n-data-table, .summary-card', { timeout: 10000 });
      const hasContent = await page.locator('.n-card, .n-data-table, .summary-card, .n-empty').first().isVisible();
      expect(hasContent).toBeTruthy();
    });
  });

  test.describe('Holdings Management', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto(`${FRONTEND_BASE}/login`);
      await page.fill('input[type="text"]', 'admin');
      await page.fill('input[type="password"]', 'aa123aaqqA@');
      await page.click('button[type="submit"]');
      await page.waitForURL('**/dashboard');
    });

    test('Navigate to Holdings page', async ({ page }) => {
      await page.click('text=持仓');
      await page.waitForURL('**/holdings');
      await expect(page.locator('h1:has-text("持仓管理")')).toBeVisible();
    });

    test('Holdings page shows holdings table or empty state', async ({ page }) => {
      await page.click('text=持仓');
      await page.waitForURL('**/holdings');
      
      await page.waitForSelector('.n-data-table, .n-empty, table', { timeout: 10000 });
      const hasContent = await page.locator('.n-data-table, .n-empty, table').first().isVisible();
      expect(hasContent).toBeTruthy();
    });
  });

  test.describe('Settings', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto(`${FRONTEND_BASE}/login`);
      await page.fill('input[type="text"]', 'admin');
      await page.fill('input[type="password"]', 'aa123aaqqA@');
      await page.click('button[type="submit"]');
      await page.waitForURL('**/dashboard');
    });

    test('Navigate to Settings page', async ({ page }) => {
      await page.click('text=设置');
      await page.waitForURL('**/settings');
    });

    test('Save settings works', async ({ page }) => {
      await page.click('text=设置');
      await page.waitForSelector('input', { timeout: 5000 });
      
      const firstInput = page.locator('input').first();
      await firstInput.fill('SH600000,SH600519');
      
      await page.click('button:has-text("保存")');
      await expect(page.locator('text=保存成功')).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('API Integration', () => {
    test('Health check endpoint responds', async ({ page }) => {
      const response = await page.request.get(`${API_BASE}/health`);
      expect(response.ok()).toBeTruthy();
    });

    test('Login API works via request', async ({ page }) => {
      const response = await page.request.post(`${API_BASE}/api/login`, {
        data: { username: 'admin', password: 'aa123aaqqA@' }
      });
      expect(response.ok()).toBeTruthy();
      const data = await response.json();
      expect(data).toHaveProperty('token');
    });

    test('Holdings API works with auth', async ({ page }) => {
      const loginRes = await page.request.post(`${API_BASE}/api/login`, {
        data: { username: 'admin', password: 'aa123aaqqA@' }
      });
      const token = (await loginRes.json()).token;
      
      const holdingsRes = await page.request.get(`${API_BASE}/api/holdings/admin`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      expect(holdingsRes.ok()).toBeTruthy();
    });

    test('Settings API works with auth', async ({ page }) => {
      const loginRes = await page.request.post(`${API_BASE}/api/login`, {
        data: { username: 'admin', password: 'aa123aaqqA@' }
      });
      const token = (await loginRes.json()).token;
      
      const settingsRes = await page.request.get(`${API_BASE}/api/settings/admin`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      expect(settingsRes.ok()).toBeTruthy();
    });

    test('Portfolio API works with auth', async ({ page }) => {
      const loginRes = await page.request.post(`${API_BASE}/api/login`, {
        data: { username: 'admin', password: 'aa123aaqqA@' }
      });
      const token = (await loginRes.json()).token;
      
      const portfolioRes = await page.request.get(`${API_BASE}/api/portfolio/admin`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      expect(portfolioRes.ok()).toBeTruthy();
    });
  });

  test.describe('Error Handling', () => {
    test('Unauthenticated access to protected route redirects to login', async ({ page }) => {
      await page.goto(`${FRONTEND_BASE}/dashboard`);
      await page.waitForURL('**/login');
    });

    test('Invalid token shows error', async ({ page }) => {
      await page.request.setExtraHTTPHeaders({
        Authorization: 'Bearer invalid-token'
      });
      const response = await page.request.get(`${API_BASE}/api/holdings/admin`);
      expect(response.status()).toBe(401);
    });
  });
});
