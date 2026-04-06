# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: integration.spec.ts >> Trading System Integration Tests >> 5. API Health Check
- Location: tests\integration.spec.ts:82:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3001/
Call log:
  - navigating to "http://localhost:3001/", waiting until "load"

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - generic [ref=e6]:
    - heading "无法访问此网站" [level=1] [ref=e7]
    - paragraph [ref=e8]:
      - strong [ref=e9]: localhost
      - text: 拒绝了我们的连接请求。
    - generic [ref=e10]:
      - paragraph [ref=e11]: 请试试以下办法：
      - list [ref=e12]:
        - listitem [ref=e13]: 检查网络连接
        - listitem [ref=e14]:
          - link "检查代理服务器和防火墙" [ref=e15] [cursor=pointer]:
            - /url: "#buttons"
    - generic [ref=e16]: ERR_CONNECTION_REFUSED
  - generic [ref=e17]:
    - button "重新加载" [ref=e19] [cursor=pointer]
    - button "详情" [ref=e20] [cursor=pointer]
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | test.describe('Trading System Integration Tests', () => {
  4   |   const API_BASE = 'http://localhost:8000';
  5   |   const FRONTEND_BASE = 'http://localhost:3001';
  6   | 
  7   |   test.beforeEach(async ({ page }) => {
> 8   |     await page.goto(FRONTEND_BASE);
      |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3001/
  9   |   });
  10  | 
  11  |   test('1. Login Flow - 登录功能', async ({ page }) => {
  12  |     await page.goto(FRONTEND_BASE);
  13  |     
  14  |     // Should redirect to login
  15  |     await expect(page.locator('input[placeholder="请输入用户名"]')).toBeVisible();
  16  |     
  17  |     // Fill login form
  18  |     await page.fill('input[type="text"]', 'admin');
  19  |     await page.fill('input[type="password"]', 'aa123aaqqA@');
  20  |     await page.click('button[type="submit"]');
  21  |     
  22  |     // Wait for redirect to dashboard
  23  |     await page.waitForURL(/\/dashboard/, { timeout: 10000 });
  24  |     await expect(page.locator('text=仪表盘')).toBeVisible({ timeout: 5000 });
  25  |   });
  26  | 
  27  |   test('2. Dashboard - 仪表盘数据加载', async ({ page }) => {
  28  |     // Login first
  29  |     await page.goto(FRONTEND_BASE);
  30  |     await page.fill('input[type="text"]', 'admin');
  31  |     await page.fill('input[type="password"]', 'aa123aaqqA@');
  32  |     await page.click('button[type="submit"]');
  33  |     await page.waitForURL(/\/dashboard/);
  34  |     
  35  |     // Check dashboard loads
  36  |     await expect(page.locator('text=仪表盘')).toBeVisible();
  37  |     
  38  |     // Should have some content loaded (could be empty)
  39  |     const content = await page.locator('.n-card, .n-data-table, .n-empty').first().isVisible().catch(() => false);
  40  |     expect(content).toBeTruthy();
  41  |   });
  42  | 
  43  |   test('3. Holdings - 持仓管理', async ({ page }) => {
  44  |     // Login first
  45  |     await page.goto(FRONTEND_BASE);
  46  |     await page.fill('input[type="text"]', 'admin');
  47  |     await page.fill('input[type="password"]', 'aa123aaqqA@');
  48  |     await page.click('button[type="submit"]');
  49  |     await page.waitForURL(/\/dashboard/);
  50  |     
  51  |     // Navigate to holdings
  52  |     await page.click('text=持仓');
  53  |     await page.waitForURL(/\/holdings/);
  54  |     
  55  |     // Check page loads
  56  |     await expect(page.locator('text=持仓管理')).toBeVisible();
  57  |   });
  58  | 
  59  |   test('4. Settings - 设置保存', async ({ page }) => {
  60  |     // Login first
  61  |     await page.goto(FRONTEND_BASE);
  62  |     await page.fill('input[type="text"]', 'admin');
  63  |     await page.fill('input[type="password"]', 'aa123aaqqA@');
  64  |     await page.click('button[type="submit"]');
  65  |     await page.waitForURL(/\/dashboard/);
  66  |     
  67  |     // Navigate to settings
  68  |     await page.click('text=设置');
  69  |     await page.waitForURL(/\/settings/);
  70  |     
  71  |     // Fill settings
  72  |     const watchlistInput = page.locator('input').first();
  73  |     await watchlistInput.fill('SH600000,SH600519');
  74  |     
  75  |     // Save settings
  76  |     await page.click('button:has-text("保存")');
  77  |     
  78  |     // Check success message
  79  |     await expect(page.locator('text=保存成功')).toBeVisible({ timeout: 5000 });
  80  |   });
  81  | 
  82  |   test('5. API Health Check', async ({ page }) => {
  83  |     const response = await page.request.get(`${API_BASE}/health`);
  84  |     expect(response.ok()).toBeTruthy();
  85  |     const data = await response.json();
  86  |     expect(data.status).toBe('healthy');
  87  |   });
  88  | 
  89  |   test('6. API Holdings Endpoint', async ({ page }) => {
  90  |     // First get token via API
  91  |     const loginRes = await page.request.post(`${API_BASE}/api/login`, {
  92  |       data: { username: 'admin', password: 'aa123aaqqA@' }
  93  |     });
  94  |     const token = (await loginRes.json()).token;
  95  |     
  96  |     // Test holdings endpoint
  97  |     const holdingsRes = await page.request.get(`${API_BASE}/api/holdings/admin`, {
  98  |       headers: { Authorization: `Bearer ${token}` }
  99  |     });
  100 |     expect(holdingsRes.ok()).toBeTruthy();
  101 |     const holdings = await holdingsRes.json();
  102 |     expect(holdings).toHaveProperty('items');
  103 |   });
  104 | 
  105 |   test('7. API Settings Endpoint', async ({ page }) => {
  106 |     const loginRes = await page.request.post(`${API_BASE}/api/login`, {
  107 |       data: { username: 'admin', password: 'aa123aaqqA@' }
  108 |     });
```