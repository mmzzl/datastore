from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # 访问百度
    page.goto("https://www.baidu.com")
    page.wait_for_load_state("networkidle")

    # 搜索
    page.fill("#kw", "OpenCode MCP 浏览器")
    page.click("#su")

    # 等待结果加载
    page.wait_for_load_state("networkidle")

    # 截图
    page.screenshot(path="D:/work/datastore/baidu_search_result.png", full_page=True)
    print("Screenshot saved to D:/work/datastore/baidu_search_result.png")

    browser.close()
