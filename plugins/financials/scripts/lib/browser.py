import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

SIGNAL_FILE = Path("/tmp/financials-continue")
STATUS_FILE = Path("/tmp/financials-status")


def _wait_for_signal() -> None:
    SIGNAL_FILE.unlink(missing_ok=True)
    while not SIGNAL_FILE.exists():
        time.sleep(0.5)
    SIGNAL_FILE.unlink(missing_ok=True)


def set_status(msg: str) -> None:
    STATUS_FILE.write_text(msg)
    print(msg, flush=True)


def launch_browser(headless: bool = False):
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=headless,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
    )
    page = browser.new_page(
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    )
    return pw, browser, page


def pause_for_login(page: Page, bank_name: str) -> None:
    page.bring_to_front()
    set_status(f"[{bank_name}] WAITING_LOGIN — log in to the browser window, then tell Claude you're done")
    _wait_for_signal()


def pause_for_2fa(page: Page, bank_name: str) -> None:
    page.bring_to_front()
    set_status(f"[{bank_name}] WAITING_2FA — complete 2FA in the browser window, then tell Claude you're done")
    _wait_for_signal()
