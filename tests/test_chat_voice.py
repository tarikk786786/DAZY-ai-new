import asyncio
import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_chat_interaction_and_always_listening():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to dashboard (skip gracefully if server is offline)
        try:
            response = await page.goto("http://127.0.0.1:8080/", timeout=5000)
        except Exception as exc:
            await browser.close()
            pytest.skip(f"Dashboard server is not currently running on http://127.0.0.1:8080/: {exc}")

        # Handle login if needed
        key_input = page.locator("#key")
        if await key_input.count() > 0 and await key_input.first.is_visible():
            await key_input.first.fill("786786")
            await page.wait_for_timeout(2000)

        # Ensure chat page is open
        chat_btn = page.locator("[data-page='chat']")
        if await chat_btn.count() > 0:
            await chat_btn.click()
            await page.wait_for_timeout(500)

        # Check Always Listening button exists
        always_btn = page.locator("#alwaysListeningBtn")
        assert await always_btn.count() > 0, "Always Listening button should be in composer"
        btn_text = await always_btn.text_content()
        print("Initial Always Listening button text:", btn_text)

        # Send a message to DAZY
        chat_input = page.locator("#chatInput")
        await chat_input.fill("Hello DAZY, reply in three words.")
        send_btn = page.locator("#sendBtn")
        await send_btn.click()

        # Wait for reply from assistant
        print("Waiting for DAZY assistant message...")
        assistant_msg = page.locator(".message.assistant .message-body")
        
        # Wait up to 15 seconds for reply to arrive
        for _ in range(15):
            await page.wait_for_timeout(1000)
            count = await assistant_msg.count()
            if count > 0:
                text = await assistant_msg.last.text_content()
                print("Received message:", text)
                if text and "wrong with the language model" not in text:
                    break

        count = await assistant_msg.count()
        assert count > 0, "DAZY should produce an assistant message"
        final_text = await assistant_msg.last.text_content()
        print("FINAL DAZY RESPONSE:", final_text)
        assert "wrong with the language model" not in final_text, f"Unexpected error in response: {final_text}"

        # Test clicking Always Listening button
        await always_btn.click()
        await page.wait_for_timeout(500)
        toggled_text = await always_btn.text_content()
        print("Toggled button text:", toggled_text)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_chat_interaction_and_always_listening())
