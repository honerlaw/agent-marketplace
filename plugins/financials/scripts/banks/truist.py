import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
from playwright.sync_api import Page
from lib.browser import launch_browser, pause_for_2fa

LOGIN_URL = "https://www.truist.com/login"


def _is_2fa_page(page: Page) -> bool:
    return any([
        page.query_selector("[id*='otp']") is not None,
        page.query_selector("[class*='mfa']") is not None,
        "authentication" in page.url.lower(),
        "verify" in page.url.lower(),
    ])


def pull(snapshot_dir: str) -> str:
    today = date.today()
    start = today - timedelta(days=90)
    download_path = Path(snapshot_dir) / "truist_checking.csv"

    pw, browser, page = launch_browser(headless=False)
    try:
        print("[Truist] Opening login page...")
        page.goto(LOGIN_URL, wait_until="load", timeout=60000)

        input("[Truist] Enter your username and password, then press Enter...")

        if _is_2fa_page(page):
            pause_for_2fa(page, "Truist")

        page.wait_for_selector("[class*='account'], [id*='account-summary']", timeout=30000)
        print("[Truist] Logged in. Navigating to transaction export...")

        page.click("[class*='account-tile']:first-child, [data-testid*='account']:first-child")
        page.wait_for_load_state("load")

        page.click("[aria-label*='export'], [aria-label*='download'], button:has-text('Export')")
        page.wait_for_selector("[class*='export-modal'], [role='dialog']", timeout=10000)

        start_input = page.query_selector("input[name*='start'], input[aria-label*='Start date']")
        end_input = page.query_selector("input[name*='end'], input[aria-label*='End date']")
        if start_input:
            start_input.fill(start.strftime("%m/%d/%Y"))
        if end_input:
            end_input.fill(today.strftime("%m/%d/%Y"))

        csv_option = page.query_selector("input[value*='csv'], option[value*='csv']")
        if csv_option:
            csv_option.click()

        with page.expect_download() as dl:
            page.click("button:has-text('Download'), button:has-text('Export')")
        dl.value.save_as(str(download_path))
        print(f"[Truist] Saved -> {download_path}")
        return str(download_path)
    finally:
        browser.close()
        pw.stop()
