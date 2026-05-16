import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
from playwright.sync_api import Page
from lib.browser import launch_browser, pause_for_2fa

LOGIN_URL = "https://www.americanexpress.com/en-us/account/login"


def _is_2fa_page(page: Page) -> bool:
    return any([
        page.query_selector("[id*='eui-challenge']") is not None,
        page.query_selector("[class*='two-factor']") is not None,
        "challenge" in page.url.lower(),
    ])


def pull(snapshot_dir: str) -> str:
    today = date.today()
    start = today - timedelta(days=90)
    download_path = Path(snapshot_dir) / "amex_credit.csv"

    pw, browser, page = launch_browser(headless=False)
    try:
        print("[Amex] Opening login page...")
        page.goto(LOGIN_URL, wait_until="load", timeout=60000)

        input("[Amex] Enter your username and password, then press Enter...")

        if _is_2fa_page(page):
            pause_for_2fa(page, "Amex")

        page.wait_for_selector("[class*='account-summary'], [class*='dashboard']", timeout=30000)
        print("[Amex] Logged in. Navigating to transaction download...")

        fmt_start = start.strftime("%Y%m%d")
        fmt_end = today.strftime("%Y%m%d")
        with page.expect_download() as dl:
            page.goto(
                f"https://www.americanexpress.com/en-us/account/download-transactions"
                f"?startDate={fmt_start}&endDate={fmt_end}&fileType=csv",
                wait_until="load",
                timeout=60000,
            )
        dl.value.save_as(str(download_path))
        print(f"[Amex] Saved -> {download_path}")
        return str(download_path)
    finally:
        browser.close()
        pw.stop()
