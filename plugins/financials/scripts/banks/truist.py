import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.browser import launch_browser, pause_for_login, pause_for_2fa, agent_loop, set_status

LOGIN_URL = "https://www.truist.com/login"


def _is_2fa_page(page) -> bool:
    return any([
        page.query_selector("[id*='otp']") is not None,
        page.query_selector("[class*='mfa']") is not None,
        "authentication" in page.url.lower(),
        "verify" in page.url.lower(),
    ])


def pull(snapshot_dir: str) -> str:
    download_path = Path(snapshot_dir) / "truist_checking.csv"

    pw, browser, page = launch_browser(headless=False)
    try:
        set_status("[Truist] Opening login page...")
        page.goto(LOGIN_URL, wait_until="load", timeout=60000)
        pause_for_login(page, "Truist")

        if _is_2fa_page(page):
            pause_for_2fa(page, "Truist")

        return agent_loop(page, "Truist", download_path)
    finally:
        browser.close()
        pw.stop()
