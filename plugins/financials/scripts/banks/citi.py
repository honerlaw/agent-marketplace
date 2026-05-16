import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.browser import launch_browser, pause_for_login, pause_for_2fa, agent_loop, set_status

LOGIN_URL = "https://online.citi.com/US/login.do"


def _is_2fa_page(page) -> bool:
    return any([
        page.query_selector("[id*='otp']") is not None,
        page.query_selector("[id*='stepup']") is not None,
        "stepup" in page.url.lower(),
        "otp" in page.url.lower(),
    ])


def pull(snapshot_dir: str) -> str:
    download_path = Path(snapshot_dir) / "citi_credit.csv"

    pw, browser, page = launch_browser(headless=False)
    try:
        set_status("[Citi] Opening login page...")
        page.goto(LOGIN_URL, wait_until="load", timeout=60000)
        pause_for_login(page, "Citi")

        if _is_2fa_page(page):
            pause_for_2fa(page, "Citi")

        return agent_loop(page, "Citi", download_path)
    finally:
        browser.close()
        pw.stop()
