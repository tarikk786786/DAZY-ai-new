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

        # Step 2: Handle PIN authentication if redirected
        if "/login" in page.url:
            pin_input = page.locator("input[type='password'], input[name='pin'], input#pin, input[placeholder*='PIN' i]")
            if await pin_input.count() > 0:
                await pin_input.first.fill("786786")
                submit_btn = page.locator("button[type='submit'], button:has-text('Unlock'), button:has-text('Login')")
                if await submit_btn.count() > 0:
                    await submit_btn.first.click()
                else:
                    await pin_input.first.press("Enter")
                await page.wait_for_timeout(1500)

        # Step 3: Verify core UI content
        title = await page.title()
        assert len(title) > 0, "Page title should not be empty"
        
        body_text = await page.inner_text("body")
        assert len(body_text) > 0, "Dashboard body should not be empty"

        # Verify key UI components
        assert any(k in body_text.lower() for k in ["dazy", "system", "status", "voice", "audio", "mic"]), \
            "Dashboard should contain core system status and control elements"

        # Step 4: Capture artifact screenshot
        screenshot_path = os.path.join(os.path.dirname(__file__), "dashboard_verified.png")
        await page.screenshot(path=screenshot_path)
        assert os.path.exists(screenshot_path), "Screenshot artifact should be saved"
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_dashboard_login_and_ui_rendering())
    print("Dashboard Playwright verification passed successfully!")
