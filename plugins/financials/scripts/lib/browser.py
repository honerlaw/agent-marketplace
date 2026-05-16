import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

SIGNAL_FILE  = Path("/tmp/financials-continue")
STATUS_FILE  = Path("/tmp/financials-status")
SCREENSHOT   = Path("/tmp/financials-screenshot.png")
COMMAND_FILE = Path("/tmp/financials-command.json")


# ── Signaling ────────────────────────────────────────────────────────────────

def _wait_for_signal() -> None:
    SIGNAL_FILE.unlink(missing_ok=True)
    while not SIGNAL_FILE.exists():
        time.sleep(0.5)
    SIGNAL_FILE.unlink(missing_ok=True)


def set_status(msg: str) -> None:
    STATUS_FILE.write_text(msg)
    print(msg, flush=True)


# ── Browser launch ───────────────────────────────────────────────────────────

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


# ── Login / 2FA pauses ───────────────────────────────────────────────────────

def pause_for_login(page: Page, bank_name: str) -> None:
    page.bring_to_front()
    set_status(f"[{bank_name}] WAITING_LOGIN — log in to the browser window, then tell Claude you're done")
    _wait_for_signal()


def pause_for_2fa(page: Page, bank_name: str) -> None:
    page.bring_to_front()
    set_status(f"[{bank_name}] WAITING_2FA — complete 2FA in the browser window, then tell Claude you're done")
    _wait_for_signal()


# ── Agent loop ───────────────────────────────────────────────────────────────

def _snapshot_page(page: Page) -> dict:
    page.screenshot(path=str(SCREENSHOT))
    try:
        elements = page.evaluate("""() => {
            const results = [];
            const seen = new Set();
            const sel = 'a[href], button, [role="button"], input[type="submit"], input[type="button"], select';
            document.querySelectorAll(sel).forEach(el => {
                const text = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ');
                if (!text || text.length > 120 || seen.has(text)) return;
                seen.add(text);
                results.push({
                    tag: el.tagName.toLowerCase(),
                    text,
                    href: el.href || null,
                });
            });
            return results.slice(0, 60);
        }""")
    except Exception:
        elements = []
    return {"url": page.url, "title": page.title(), "elements": elements}


def agent_loop(page: Page, bank_name: str, download_path: Path) -> str:
    """
    Snapshot the page, write state, wait for a JSON command from Claude,
    execute it. Repeat until the file is downloaded.

    Commands Claude can write to COMMAND_FILE:
      {"action": "click",    "selector": "css-or-text-selector"}
      {"action": "goto",     "url": "https://..."}
      {"action": "select",   "selector": "...", "value": "..."}
      {"action": "download", "selector": "..."}   — expects a file download
    """
    while True:
        page.wait_for_load_state("load")
        state = _snapshot_page(page)
        state["bank"] = bank_name
        state["screenshot"] = str(SCREENSHOT)
        state["download_path"] = str(download_path)

        STATUS_FILE.write_text(json.dumps(state, indent=2))
        COMMAND_FILE.unlink(missing_ok=True)
        print(f"[{bank_name}] AWAITING_COMMAND — screenshot at {SCREENSHOT}", flush=True)

        # wait for Claude to write a command
        while not COMMAND_FILE.exists():
            time.sleep(0.5)
        cmd = json.loads(COMMAND_FILE.read_text())
        COMMAND_FILE.unlink(missing_ok=True)

        action = cmd.get("action")
        print(f"[{bank_name}] executing: {cmd}", flush=True)

        if action == "click":
            page.click(cmd["selector"], timeout=15000)

        elif action == "goto":
            page.goto(cmd["url"], wait_until="load", timeout=60000)

        elif action == "select":
            page.select_option(cmd["selector"], cmd["value"])

        elif action == "fill":
            page.fill(cmd["selector"], cmd["value"])

        elif action == "download":
            with page.expect_download(timeout=60000) as dl_info:
                page.click(cmd["selector"], timeout=15000)
            dl_info.value.save_as(str(download_path))
            print(f"[{bank_name}] saved → {download_path}", flush=True)
            return str(download_path)

        else:
            raise ValueError(f"Unknown action: {action}")
