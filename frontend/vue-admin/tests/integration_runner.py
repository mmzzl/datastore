from playwright.sync_api import sync_playwright
import subprocess
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path="C:\\Users\\life8\\AppData\\Local\\ms-playwright\\chromium-1140\\chrome-win\\chrome.exe",
        )
        page = browser.new_page()

        errors = []
        passed = 0

        # Test 1: Login Flow
        print("Test 1: Login Flow...")
        try:
            page.goto("http://localhost:3001", wait_until="networkidle", timeout=10000)
            page.fill('input[type="text"]', "admin")
            page.fill('input[type="password"]', "aa123aaqqA@")
            page.click('button[type="submit"]')
            page.wait_for_url("**/dashboard", timeout=10000)
            print("  [PASS] Login successful")
            passed += 1
        except Exception as e:
            errors.append(f"Login Flow: {str(e)}")
            print(f"  [FAIL] Failed: {e}")

        # Test 2: Dashboard
        print("Test 2: Dashboard...")
        try:
            # Already logged in from test 1, just go to dashboard
            page.goto(
                "http://localhost:3001/#/dashboard", wait_until="load", timeout=15000
            )
            page.wait_for_timeout(3000)  # Give time for Vue to render
            content = (
                page.locator(".n-card, .n-data-table, .n-empty, .dashboard")
                .first()
                .is_visible()
            )
            if content:
                print("  [PASS] Dashboard loaded")
                passed += 1
            else:
                errors.append("Dashboard: No content visible")
                print("  [FAIL] No content visible")
        except Exception as e:
            errors.append(f"Dashboard: {str(e)}")
            print(f"  [FAIL] Failed: {e}")

        # Test 3: Holdings
        print("Test 3: Holdings...")
        try:
            page.goto(
                "http://localhost:3001/#/holdings",
                wait_until="networkidle",
                timeout=10000,
            )
            title = page.locator("text=持仓管理").is_visible()
            if title:
                print("  [PASS] Holdings page loaded")
                passed += 1
            else:
                errors.append("Holdings: Title not visible")
                print("  [FAIL] Title not visible")
        except Exception as e:
            errors.append(f"Holdings: {str(e)}")
            print(f"  [FAIL] Failed: {e}")

        # Test 4: Settings
        print("Test 4: Settings...")
        try:
            page.goto(
                "http://localhost:3001/settings",
                wait_until="networkidle",
                timeout=10000,
            )
            inputs = page.locator("input").count()
            if inputs > 0:
                print("  [PASS] Settings page loaded")
                passed += 1
            else:
                errors.append("Settings: No inputs found")
                print("  [FAIL] No inputs found")
        except Exception as e:
            errors.append(f"Settings: {str(e)}")
            print(f"  [FAIL] Failed: {e}")

        # Test 5: API Health
        print("Test 5: API Health Check...")
        try:
            resp = page.request.get("http://localhost:8000/health")
            if resp.ok:
                print("  [PASS] API health check passed")
                passed += 1
            else:
                errors.append(f"Health: Status {resp.status}")
                print(f"  [FAIL] Failed with status {resp.status}")
        except Exception as e:
            errors.append(f"Health: {str(e)}")
            print(f"  [FAIL] Failed: {e}")

        # Test 6: API Holdings
        print("Test 6: API Holdings...")
        try:
            login_resp = page.request.post(
                "http://localhost:8000/api/login",
                data={"username": "admin", "password": "aa123aaqqA@"},
            )
            token = login_resp.json().get("token")
            holdings_resp = page.request.get(
                "http://localhost:8000/api/holdings/admin",
                headers={"Authorization": f"Bearer {token}"},
            )
            if holdings_resp.ok:
                data = holdings_resp.json()
                if "items" in data:
                    print("  [PASS] API Holdings working")
                    passed += 1
                else:
                    errors.append("Holdings API: No items key")
                    print("  [FAIL] No items in response")
            else:
                errors.append(f"Holdings API: Status {holdings_resp.status}")
                print(f"  [FAIL] Failed with status {holdings_resp.status}")
        except Exception as e:
            errors.append(f"Holdings API: {str(e)}")
            print(f"  [FAIL] Failed: {e}")

        # Test 7: API Settings
        print("Test 7: API Settings...")
        try:
            login_resp = page.request.post(
                "http://localhost:8000/api/login",
                data={"username": "admin", "password": "aa123aaqqA@"},
            )
            token = login_resp.json().get("token")
            settings_resp = page.request.get(
                "http://localhost:8000/api/settings/admin",
                headers={"Authorization": f"Bearer {token}"},
            )
            if settings_resp.ok:
                print("  [PASS] API Settings working")
                passed += 1
            else:
                errors.append(f"Settings API: Status {settings_resp.status}")
                print(f"  [FAIL] Failed with status {settings_resp.status}")
        except Exception as e:
            errors.append(f"Settings API: {str(e)}")
            print(f"  [FAIL] Failed: {e}")

        # Test 8: API Portfolio
        print("Test 8: API Portfolio...")
        try:
            login_resp = page.request.post(
                "http://localhost:8000/api/login",
                data={"username": "admin", "password": "aa123aaqqA@"},
            )
            token = login_resp.json().get("token")
            portfolio_resp = page.request.get(
                "http://localhost:8000/api/portfolio/admin",
                headers={"Authorization": f"Bearer {token}"},
            )
            if portfolio_resp.ok:
                data = portfolio_resp.json()
                if "holdings_count" in data:
                    print("  [PASS] API Portfolio working")
                    passed += 1
                else:
                    errors.append("Portfolio API: No holdings_count")
                    print("  [FAIL] No holdings_count in response")
            else:
                errors.append(f"Portfolio API: Status {portfolio_resp.status}")
                print(f"  [FAIL] Failed with status {portfolio_resp.status}")
        except Exception as e:
            errors.append(f"Portfolio API: {str(e)}")
            print(f"  [FAIL] Failed: {e}")

        # Test 9: End-to-End Add Holding
        print("Test 9: End-to-End Add Holding...")
        try:
            login_resp = page.request.post(
                "http://localhost:8000/api/login",
                data={"username": "admin", "password": "aa123aaqqA@"},
            )
            token = login_resp.json().get("token")
            add_resp = page.request.post(
                "http://localhost:8000/api/holdings/admin",
                headers={"Authorization": f"Bearer {token}"},
                data={"code": "SH600000", "quantity": 100, "average_cost": 10.0},
            )
            if add_resp.ok:
                result = add_resp.json()
                if result.get("success"):
                    print("  [PASS] Add holding successful")
                    passed += 1
                else:
                    errors.append("Add Holding: Not successful")
                    print("  [FAIL] Not successful")
            else:
                errors.append(f"Add Holding: Status {add_resp.status}")
                print(f"  [FAIL] Failed with status {add_resp.status}")
        except Exception as e:
            errors.append(f"Add Holding: {str(e)}")
            print(f"  [FAIL] Failed: {e}")

        # Test 10: End-to-End Delete Holding
        print("Test 10: End-to-End Delete Holding...")
        try:
            login_resp = page.request.post(
                "http://localhost:8000/api/login",
                data={"username": "admin", "password": "aa123aaqqA@"},
            )
            token = login_resp.json().get("token")
            delete_resp = page.request.delete(
                "http://localhost:8000/api/holdings/admin/SH600000",
                headers={"Authorization": f"Bearer {token}"},
            )
            if delete_resp.ok:
                print("  [PASS] Delete holding successful")
                passed += 1
            else:
                errors.append(f"Delete Holding: Status {delete_resp.status}")
                print(f"  [FAIL] Failed with status {delete_resp.status}")
        except Exception as e:
            errors.append(f"Delete Holding: {str(e)}")
            print(f"  [FAIL] Failed: {e}")

        browser.close()

        print(f"\n{'=' * 50}")
        print(f"Results: {passed}/10 passed")
        if errors:
            print(f"Errors ({len(errors)}):")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)
        else:
            print("All tests passed!")
            sys.exit(0)


if __name__ == "__main__":
    run_tests()
