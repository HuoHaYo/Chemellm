"""Open the DSH Web GUI, open the ChemELLM panel, and capture a screenshot.

Usage: python scripts/verify_ui.py [url] [output.png]
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5396"
OUTPUT = Path(sys.argv[2] if len(sys.argv) > 2 else "data/qa/ui-panel.png")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def main():
    console_errors: list[str] = []
    with sync_playwright() as playground:
        browser = None
        for channel in ("msedge", None):
            try:
                browser = playground.chromium.launch(channel=channel, headless=True) if channel \
                    else playground.chromium.launch(headless=True)
                break
            except Exception as error:  # noqa: BLE001 - try next channel
                print(f"launch channel={channel} failed: {error}")
        if browser is None:
            raise SystemExit("no chromium available")
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("console", lambda message: console_errors.append(message.text)
                if message.type == "error" else None)
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)

        labels = page.evaluate("""() => Array.from(document.querySelectorAll('button'))
            .map(b => (b.getAttribute('aria-label') || b.title || b.textContent || '').trim())
            .filter(Boolean).slice(0, 60)""")
        print("buttons:", labels)

        target = page.locator("button[aria-label='化工工程']")
        if target.count() == 0:
            target = page.get_by_role("button", name="化工工程")
        print("panel button count:", target.count())
        if target.count() == 0:
            page.screenshot(path=str(OUTPUT))
            print("CHEMELLM PANEL BUTTON NOT FOUND; screenshot:", OUTPUT)
            browser.close()
            raise SystemExit(2)

        target.first.click()
        page.wait_for_timeout(2500)
        text = page.inner_text("body")
        for keyword in ("化工工程", "新建项目", "概览"):
            print(f"contains {keyword!r}:", keyword in text)
        page.screenshot(path=str(OUTPUT), full_page=False)
        print("screenshot:", OUTPUT)
        print("console errors:", len(console_errors))
        for error in console_errors[:10]:
            print("  -", error[:300])
        browser.close()


if __name__ == "__main__":
    main()
