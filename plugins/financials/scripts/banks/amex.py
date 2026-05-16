import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
from lib.browser import launch_browser, pause_for_login, pause_for_2fa, agent_loop, set_status

LOGIN_URL = "https://www.americanexpress.com/en-us/account/login"


def _is_2fa_page(page) -> bool:
    return any([
        page.query_selector("[id*='eui-challenge']") is not None,
        page.query_selector("[class*='two-factor']") is not None,
        "challenge" in page.url.lower(),
    ])


def pull(snapshot_dir: str) -> str:
    download_path = Path(snapshot_dir) / "amex_credit.csv"

    pw, browser, page = launch_browser(headless=False)
    try:
        set_status("[Amex] Opening login page...")
        page.goto(LOGIN_URL, wait_until="load", timeout=60000)
        pause_for_login(page, "Amex")

        if _is_2fa_page(page):
            pause_for_2fa(page, "Amex")

        return agent_loop(page, "Amex", download_path)
    finally:
        browser.close()
        pw.stop()
