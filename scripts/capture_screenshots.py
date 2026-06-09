from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = ROOT / "docs" / "screenshots"
CHROME_PATH = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
SCREENSHOT_URL = "http://localhost:8501/?exclude_contractors=RHM.DE"


def main() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=str(CHROME_PATH) if CHROME_PATH.exists() else None,
            headless=True,
        )
        page = browser.new_page(viewport={"width": 1600, "height": 1200})
        page.goto(SCREENSHOT_URL, wait_until="domcontentloaded", timeout=120_000)
        page.get_by_text("Defense Spending & Geopolitical Risk Premium").first.wait_for(timeout=120_000)
        page.locator(".js-plotly-plot").first.wait_for(timeout=120_000)
        page.wait_for_timeout(5_000)
        page.screenshot(path=str(SCREENSHOT_DIR / "dashboard-overview.png"), full_page=True)

        page.get_by_text("Derivatives").click()
        page.get_by_text("Math layer:").wait_for(timeout=120_000)
        page.wait_for_timeout(5_000)
        page.screenshot(path=str(SCREENSHOT_DIR / "derivatives-panel.png"), full_page=True)

        page.get_by_text("Scenario & Export").click()
        page.get_by_text("Download Investment Memo").wait_for(timeout=120_000)
        page.wait_for_timeout(5_000)
        page.screenshot(path=str(SCREENSHOT_DIR / "scenario-export.png"), full_page=True)
        browser.close()


if __name__ == "__main__":
    main()
