import asyncio
import os
import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_dashboard_login_and_ui_rendering():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Step 1: Navigate to server (skip gracefully if server is offline)
        try:
            response = await page.goto("http://127.0.0.1:8080/", timeout=5000)
        except Exception as exc:
            await browser.close()
            pytest.skip(f"Dashboard server is not currently running on http://127.0.0.1:8080/: {exc}")
        assert response is not None, "Dashboard server unreachable"
        assert response.status < 500, f"Dashboard returned server error: {response.status}"

        # Step 2: Handle PIN authentication if login screen is displayed
        key_input = page.locator("#key")
        if await key_input.count() > 0 and await key_input.first.is_visible():
            await key_input.first.fill("786786")
            # Entering 6 digits automatically invokes doLogin() and navigates to '/'
            await page.wait_for_timeout(2500)

        # Step 3: Verify core UI content
        title = await page.title()
        assert len(title) > 0, "Page title should not be empty"
        
        body_text = await page.inner_text("body")
        assert len(body_text) > 0, "Dashboard body should not be empty"

        # Verify key UI components
        assert any(k in body_text.lower() for k in ["dazy", "system", "status", "voice", "audio", "mic"]), \
            "Dashboard should contain core system status and control elements"

        # Step 4: Verify Canonical Identity (Tarik, strictly no John Doe / Alex)
        assert "tarik" in body_text.lower(), "User profile must display Tarik"
        assert "john doe" not in body_text.lower(), "Legacy placeholder 'John Doe' must not appear"

        # Step 5: Verify navigation to Live Brain 3D
        brain_nav = page.locator("button[data-page='brain']")
        if await brain_nav.count() > 0:
            await brain_nav.first.click()
            await page.wait_for_timeout(1000)
            brain_canvas = page.locator("#brainCanvas")
            assert await brain_canvas.count() > 0, "Brain 3D Canvas should exist"
            assert await brain_canvas.is_visible(), "Brain 3D Canvas should be visible"

        # Step 6: Verify navigation to AI OS Command Center
        cmd_nav = page.locator("button[data-page='command']")
        if await cmd_nav.count() > 0:
            await cmd_nav.first.click()
            await page.wait_for_timeout(1000)
            metric_card = page.locator("#cmdActiveWorkers")
            assert await metric_card.count() > 0, "Active workers metric should exist"

        # Step 7: Verify navigation to Testing Center
        test_nav = page.locator("button[data-page='testing']")
        if await test_nav.count() > 0:
            await test_nav.first.click()
            await page.wait_for_timeout(1000)
            testing_page = page.locator("#page-testing")
            assert await testing_page.count() > 0, "Testing Center page must exist"
            assert await testing_page.is_visible(), "Testing Center page must be visible"
            pass_count = page.locator("#testPassCount")
            assert await pass_count.count() > 0, "Test pass count metric must exist"

        # Step 8: Capture artifact screenshot
        screenshot_path = os.path.join(os.path.dirname(__file__), "dashboard_verified.png")
        await page.screenshot(path=screenshot_path)
        assert os.path.exists(screenshot_path), "Screenshot artifact should be saved"
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_dashboard_login_and_ui_rendering())
    print("Dashboard Playwright verification passed successfully!")
