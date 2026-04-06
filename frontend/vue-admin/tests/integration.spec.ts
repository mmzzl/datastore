import { test, expect } from '@playwright/test';

test.describe('Trading System Integration Tests', () => {
  const API_BASE = 'http://localhost:8000';
  const FRONTEND_BASE = 'http://localhost:3001';

  test.beforeEach(async ({ page }) => {
    await page.goto(FRONTEND_BASE);
  });

  test('1. Login Flow - 登录功能', async ({ page }) => {
    await page.goto(FRONTEND_BASE);
    
    // Should redirect to login
    await expect(page.locator('input[placeholder="请输入用户名"]')).toBeVisible();
    
    // Fill login form
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'aa123aaqqA@');
    await page.click('button[type="submit"]');
    
    // Wait for redirect to dashboard
    await page.waitForURL(/\/dashboard/, { timeout: 10000 });
    await expect(page.locator('text=仪表盘')).toBeVisible({ timeout: 5000 });
  });

  test('2. Dashboard - 仪表盘数据加载', async ({ page }) => {
    // Login first
    await page.goto(FRONTEND_BASE);
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'aa123aaqqA@');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/);
    
    // Check dashboard loads
    await expect(page.locator('text=仪表盘')).toBeVisible();
    
    // Should have some content loaded (could be empty)
    const content = await page.locator('.n-card, .n-data-table, .n-empty').first().isVisible().catch(() => false);
    expect(content).toBeTruthy();
  });

  test('3. Holdings - 持仓管理', async ({ page }) => {
    // Login first
    await page.goto(FRONTEND_BASE);
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'aa123aaqqA@');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/);
    
    // Navigate to holdings
    await page.click('text=持仓');
    await page.waitForURL(/\/holdings/);
    
    // Check page loads
    await expect(page.locator('text=持仓管理')).toBeVisible();
  });

  test('4. Settings - 设置保存', async ({ page }) => {
    // Login first
    await page.goto(FRONTEND_BASE);
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'aa123aaqqA@');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/);
    
    // Navigate to settings
    await page.click('text=设置');
    await page.waitForURL(/\/settings/);
    
    // Fill settings
    const watchlistInput = page.locator('input').first();
    await watchlistInput.fill('SH600000,SH600519');
    
    // Save settings
    await page.click('button:has-text("保存")');
    
    // Check success message
    await expect(page.locator('text=保存成功')).toBeVisible({ timeout: 5000 });
  });

  test('5. API Health Check', async ({ page }) => {
    const response = await page.request.get(`${API_BASE}/health`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  test('6. API Holdings Endpoint', async ({ page }) => {
    // First get token via API
    const loginRes = await page.request.post(`${API_BASE}/api/login`, {
      data: { username: 'admin', password: 'aa123aaqqA@' }
    });
    const token = (await loginRes.json()).token;
    
    // Test holdings endpoint
    const holdingsRes = await page.request.get(`${API_BASE}/api/holdings/admin`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(holdingsRes.ok()).toBeTruthy();
    const holdings = await holdingsRes.json();
    expect(holdings).toHaveProperty('items');
  });

  test('7. API Settings Endpoint', async ({ page }) => {
    const loginRes = await page.request.post(`${API_BASE}/api/login`, {
      data: { username: 'admin', password: 'aa123aaqqA@' }
    });
    const token = (await loginRes.json()).token;
    
    // Test settings endpoint
    const settingsRes = await page.request.get(`${API_BASE}/api/settings/admin`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(settingsRes.ok()).toBeTruthy();
    const settings = await settingsRes.json();
    expect(settings).toHaveProperty('watchlist');
  });

  test('8. API Portfolio Endpoint', async ({ page }) => {
    const loginRes = await page.request.post(`${API_BASE}/api/login`, {
      data: { username: 'admin', password: 'aa123aaqqA@' }
    });
    const token = (await loginRes.json()).token;
    
    // Test portfolio endpoint
    const portfolioRes = await page.request.get(`${API_BASE}/api/portfolio/admin`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(portfolioRes.ok()).toBeTruthy();
    const portfolio = await portfolioRes.json();
    expect(portfolio).toHaveProperty('holdings_count');
  });

  test('9. End-to-End: Add Holding', async ({ page }) => {
    const loginRes = await page.request.post(`${API_BASE}/api/login`, {
      data: { username: 'admin', password: 'aa123aaqqA@' }
    });
    const token = (await loginRes.json()).token;
    
    // Add a new holding via API
    const addRes = await page.request.post(`${API_BASE}/api/holdings/admin`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        code: 'SH600000',
        name: '测试股票',
        quantity: 100,
        average_cost: 10.0
      }
    });
    expect(addRes.ok()).toBeTruthy();
    const result = await addRes.json();
    expect(result.success).toBeTruthy();
  });

  test('10. End-to-End: Delete Holding', async ({ page }) => {
    const loginRes = await page.request.post(`${API_BASE}/api/login`, {
      data: { username: 'admin', password: 'aa123aaqqA@' }
    });
    const token = (await loginRes.json()).token;
    
    // Add a holding first
    await page.request.post(`${API_BASE}/api/holdings/admin`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        code: 'SH600001',
        quantity: 200,
        average_cost: 5.0
      }
    });
    
    // Delete the holding
    const deleteRes = await page.request.delete(`${API_BASE}/api/holdings/admin/SH600001`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(deleteRes.ok()).toBeTruthy();
  });
});