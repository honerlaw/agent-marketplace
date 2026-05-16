from playwright.sync_api import sync_playwright, Page


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


def pause_for_2fa(page: Page, bank_name: str) -> None:
    page.bring_to_front()
    print(f"\n[{bank_name}] 2FA required — complete it in the browser window.")
    input("Press Enter when you're past the 2FA screen...")
