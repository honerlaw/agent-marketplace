import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
from playwright.sync_api import Page
from lib.browser import launch_browser, pause_for_2fa

LOGIN_URL = "https://online.citi.com/US/login.do"


def _is_2fa_page(page: Page) -> bool:
    return any([
        page.query_selector("[id*='otp']") is not None,
        page.query_selector("[id*='stepup']") is not None,
        "stepup" in page.url.lower(),
        "otp" in page.url.lower(),
    ])


def pull(snapshot_dir: str) -> str:
    today = date.today()
    start = today - timedelta(days=90)
    download_path = Path(snapshot_dir) / "citi_credit.csv"

    pw, browser, page = launch_browser(headless=False)
    try:
        print("[Citi] Opening login page...")
        page.goto(LOGIN_URL, wait_until="networkidle")

        input("[Citi] Enter your username and password, then press Enter...")

        if _is_2fa_page(page):
            pause_for_2fa(page, "Citi")

        page.wait_for_selector("[class*='account-list'], [id*='accountSummary']", timeout=30000)
        print("[Citi] Logged in. Navigating to transaction download...")

        page.click("[class*='account-tile']:first-child, a[id*='account']:first-child")
        page.wait_for_load_state("networkidle")

        page.click("a:has-text('Download'), button:has-text('Download Transactions')")
        page.wait_for_selector("[class*='download'], [id*='downloadForm']", timeout=10000)

        start_input = page.query_selector("input[id*='fromDate'], input[name*='fromDate']")
        end_input = page.query_selector("input[id*='toDate'], input[name*='toDate']")
        if start_input:
            start_input.fill(start.strftime("%m/%d/%Y"))
        if end_input:
            end_input.fill(today.strftime("%m/%d/%Y"))

        csv_option = page.query_selector("option[value*='csv'], input[value*='csv']")
        if csv_option:
            csv_option.click()

        with page.expect_download() as dl:
            page.click("button:has-text('Download'), input[type='submit']")
        dl.value.save_as(str(download_path))
        print(f"[Citi] Saved -> {download_path}")
        return str(download_path)
    finally:
        browser.close()
        pw.stop()
