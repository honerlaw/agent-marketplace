# Financial Aggregator Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `claude-marketplace` monorepo with a `financials` plugin that pulls transaction CSVs from Truist, Amex, and Citi via Playwright and exposes 5 Claude Code skills for financial analysis.

**Architecture:** Python + Playwright scripts handle bank automation (headless browser with 2FA pause), `lib/` modules provide shared browser setup and CSV normalization, and Claude Code skill markdown files wire everything into slash commands. All amounts follow outflow-negative / inflow-positive convention.

**Tech Stack:** Python 3.11+, playwright-python, pandas, pytest

---

## File Map

| File | Responsibility |
|------|---------------|
| `install.sh` | Symlink plugin to `~/.claude/plugins/`, print settings instructions |
| `conftest.py` | Pytest path setup — adds scripts dir to sys.path for all tests |
| `plugins/financials/plugin.json` | Plugin manifest |
| `plugins/financials/scripts/requirements.txt` | Python dependencies |
| `plugins/financials/scripts/lib/storage.py` | Snapshot dirs, CSV normalization, schema mapping |
| `plugins/financials/scripts/lib/browser.py` | Playwright launch + 2FA pause |
| `plugins/financials/scripts/banks/amex.py` | Amex Playwright pull |
| `plugins/financials/scripts/banks/truist.py` | Truist Playwright pull |
| `plugins/financials/scripts/banks/citi.py` | Citi Playwright pull |
| `plugins/financials/scripts/pull.py` | Sequences bank pulls, CLI entry point |
| `plugins/financials/skills/pull-finances.md` | `/pull-finances` skill |
| `plugins/financials/skills/spending-summary.md` | `/spending-summary` skill |
| `plugins/financials/skills/spending-breakdown.md` | `/spending-breakdown` skill |
| `plugins/financials/skills/recurring-expenses.md` | `/recurring-expenses` skill |
| `plugins/financials/skills/cross-account.md` | `/cross-account` skill |
| `tests/test_storage.py` | Unit tests for normalization + snapshot logic |
| `tests/test_pull.py` | Unit tests for runner sequencing |
| `tests/test_browser.py` | Unit tests for browser module |

---

### Task 1: Repo Scaffold

**Files:**
- Create: `README.md`
- Create: `.gitignore`
- Create: `conftest.py`
- Create: `install.sh`
- Create: `plugins/financials/plugin.json`
- Create: `plugins/financials/README.md`
- Create: `plugins/financials/scripts/requirements.txt`
- Create: `plugins/financials/scripts/lib/__init__.py`
- Create: `plugins/financials/scripts/banks/__init__.py`
- Create: `plugins/financials/scripts/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p plugins/financials/scripts/lib \
         plugins/financials/scripts/banks \
         plugins/financials/skills \
         tests
touch plugins/financials/scripts/lib/__init__.py \
      plugins/financials/scripts/banks/__init__.py \
      plugins/financials/scripts/__init__.py \
      tests/__init__.py
```

- [ ] **Step 2: Create `.gitignore`**

```
__pycache__/
*.pyc
.venv/
*.egg-info/
.env
```

- [ ] **Step 3: Create `conftest.py`**

This adds the scripts directory to sys.path so all tests can import `lib.storage`, `pull`, etc. directly without package prefix gymnastics.

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "plugins/financials/scripts"))
```

- [ ] **Step 4: Create `plugins/financials/scripts/requirements.txt`**

```
playwright==1.44.0
pandas==2.2.2
pytest==8.2.0
```

- [ ] **Step 5: Create `plugins/financials/plugin.json`**

```json
{
  "name": "financials",
  "version": "1.0.0",
  "description": "Pull and analyze personal finances from Truist, Amex, and Citi",
  "skills": [
    "skills/pull-finances.md",
    "skills/spending-summary.md",
    "skills/spending-breakdown.md",
    "skills/recurring-expenses.md",
    "skills/cross-account.md"
  ]
}
```

- [ ] **Step 6: Create `install.sh`**

```bash
#!/usr/bin/env bash
set -e

PLUGIN_NAME="${1:-}"
if [ -z "$PLUGIN_NAME" ]; then
  echo "Usage: ./install.sh <plugin-name>"
  echo "Available: $(ls plugins/)"
  exit 1
fi

PLUGIN_DIR="$(pwd)/plugins/$PLUGIN_NAME"
if [ ! -d "$PLUGIN_DIR" ]; then
  echo "Plugin '$PLUGIN_NAME' not found in plugins/"
  exit 1
fi

CLAUDE_PLUGINS_DIR="$HOME/.claude/plugins"
mkdir -p "$CLAUDE_PLUGINS_DIR"

TARGET="$CLAUDE_PLUGINS_DIR/$PLUGIN_NAME"
[ -L "$TARGET" ] && rm "$TARGET"
ln -s "$PLUGIN_DIR" "$TARGET"
echo "✓ Linked plugins/$PLUGIN_NAME → $TARGET"
echo ""
echo "Add to ~/.claude/settings.json:"
echo "  \"plugins\": [\"$TARGET\"]"
echo ""
echo "Skills available after restart:"
for skill in "$PLUGIN_DIR"/skills/*.md; do
  echo "  /$(basename "${skill%.md}")"
done
```

```bash
chmod +x install.sh
```

- [ ] **Step 7: Create `README.md`**

```markdown
# Claude Marketplace

A personal plugin marketplace for Claude Code. Each plugin in `plugins/` is self-contained with its own skills and scripts.

## Install a Plugin

```bash
git clone https://github.com/<you>/claude-marketplace
cd claude-marketplace
./install.sh financials
```

Add the printed path to `~/.claude/settings.json` under `"plugins"`, then restart Claude Code.

## Update

```bash
git pull  # symlink keeps the plugin live immediately
```

## Plugins

| Plugin | Skills | Description |
|--------|--------|-------------|
| financials | `/pull-finances` `/spending-summary` `/spending-breakdown` `/recurring-expenses` `/cross-account` | Pull and analyze personal finances from Truist, Amex, Citi |
```

- [ ] **Step 8: Create `plugins/financials/README.md`**

```markdown
# financials plugin

Pulls transaction CSVs from Truist, Amex, and Citi via Playwright and provides Claude Code skills for financial analysis.

## Setup

```bash
cd plugins/financials/scripts
pip install -r requirements.txt
python -m playwright install chromium
```

## Skills

| Skill | Description |
|-------|-------------|
| `/pull-finances [bank]` | Pull 90 days of transactions. Optional: `truist`, `amex`, or `citi` |
| `/spending-summary [date]` | Monthly totals, top merchants, categories, per-person breakdown |
| `/spending-breakdown [date]` | Spending by category — no targets, just actuals |
| `/recurring-expenses [date]` | Bills, subscriptions, and regular transfers |
| `/cross-account [date]` | Net cash flow across all accounts |

## Data

Snapshots saved to `~/Documents/financials/snapshots/YYYY-MM-DD/`.

## First Run Notes

On first pull, check the downloaded CSVs for Truist and Citi to confirm the cardholder column name. Update `BANK_SCHEMA` in `scripts/lib/storage.py` if the column exists.
```

- [ ] **Step 9: Install Python dependencies**

```bash
cd plugins/financials/scripts
pip install -r requirements.txt
python -m playwright install chromium
```

Expected: packages install cleanly, Chromium browser downloaded.

- [ ] **Step 10: Commit**

```bash
cd /Users/derekhonerlaw/Development/financials-tmp
git add .
git commit -m "feat: add repo scaffold and financials plugin structure"
```

---

### Task 2: lib/storage.py

**Files:**
- Create: `plugins/financials/scripts/lib/storage.py`
- Create: `tests/test_storage.py`

Amount convention throughout: **outflow = negative, inflow = positive**.
- Amex CSV exports purchases as positive → negate them.
- Truist CSV already uses negative for debits → pass through.
- Citi CSV has separate `Debit` / `Credit` columns → `credit - debit`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_storage.py`:

```python
import io
import pytest
import pandas as pd
from pathlib import Path
from datetime import date
from lib.storage import normalize_csv, get_snapshot_dir, load_snapshot, latest_snapshot

AMEX_CSV = """Date,Description,Amount,Card Member,Account #
2026-04-15,WHOLE FOODS MARKET,45.23,DEREK HONERLAW,12345
2026-04-16,NETFLIX,15.99,DEREK HONERLAW,12345
2026-04-17,AMAZON PRIME,12.00,WIFE HONERLAW,67890
2026-04-18,PAYMENT -THANK YOU,-500.00,DEREK HONERLAW,12345
"""

TRUIST_CSV = """Date,Description,Transaction Type,Amount
2026-04-15,PAYCHECK,Credit,2500.00
2026-04-16,RENT CHECK,Debit,-1200.00
"""

CITI_CSV = """Transaction Date,Description,Debit,Credit
2026-04-15,STARBUCKS,5.50,
2026-04-16,PAYCHECK,,500.00
"""


def test_normalize_amex_columns():
    df = pd.read_csv(io.StringIO(AMEX_CSV))
    result = normalize_csv(df, "amex")
    assert list(result.columns) == ["date", "description", "amount", "type", "person", "bank"]


def test_normalize_amex_person():
    df = pd.read_csv(io.StringIO(AMEX_CSV))
    result = normalize_csv(df, "amex")
    assert result.iloc[0]["person"] == "DEREK HONERLAW"
    assert result.iloc[2]["person"] == "WIFE HONERLAW"


def test_normalize_amex_amounts():
    df = pd.read_csv(io.StringIO(AMEX_CSV))
    result = normalize_csv(df, "amex")
    assert result.iloc[0]["amount"] == pytest.approx(-45.23)   # purchase → negative
    assert result.iloc[3]["amount"] == pytest.approx(500.00)   # payment → positive


def test_normalize_truist_columns():
    df = pd.read_csv(io.StringIO(TRUIST_CSV))
    result = normalize_csv(df, "truist")
    assert list(result.columns) == ["date", "description", "amount", "type", "person", "bank"]


def test_normalize_truist_amounts():
    df = pd.read_csv(io.StringIO(TRUIST_CSV))
    result = normalize_csv(df, "truist")
    assert result.iloc[0]["amount"] == pytest.approx(2500.00)
    assert result.iloc[1]["amount"] == pytest.approx(-1200.00)


def test_normalize_truist_person_is_none():
    df = pd.read_csv(io.StringIO(TRUIST_CSV))
    result = normalize_csv(df, "truist")
    assert result["person"].isna().all()


def test_normalize_citi_columns():
    df = pd.read_csv(io.StringIO(CITI_CSV))
    result = normalize_csv(df, "citi")
    assert list(result.columns) == ["date", "description", "amount", "type", "person", "bank"]


def test_normalize_citi_amounts():
    df = pd.read_csv(io.StringIO(CITI_CSV))
    result = normalize_csv(df, "citi")
    assert result.iloc[0]["amount"] == pytest.approx(-5.50)   # debit → negative
    assert result.iloc[1]["amount"] == pytest.approx(500.00)  # credit → positive


def test_normalize_bank_field():
    df = pd.read_csv(io.StringIO(AMEX_CSV))
    result = normalize_csv(df, "amex")
    assert (result["bank"] == "amex").all()


def test_get_snapshot_dir_creates_folder(tmp_path):
    d = get_snapshot_dir(str(tmp_path), "2026-05-16")
    assert Path(d).exists()
    assert Path(d).name == "2026-05-16"


def test_get_snapshot_dir_defaults_to_today(tmp_path):
    d = get_snapshot_dir(str(tmp_path))
    assert Path(d).name == date.today().isoformat()


def test_get_snapshot_dir_idempotent(tmp_path):
    get_snapshot_dir(str(tmp_path), "2026-05-16")
    get_snapshot_dir(str(tmp_path), "2026-05-16")  # no error on second call
    assert (tmp_path / "2026-05-16").exists()


def test_load_snapshot(tmp_path):
    snap = tmp_path / "2026-05-16"
    snap.mkdir()
    (snap / "amex_credit.csv").write_text(AMEX_CSV)
    result = load_snapshot(str(snap))
    assert len(result) == 4
    assert set(result.columns) == {"date", "description", "amount", "person", "bank"}
    assert (result["bank"] == "amex").all()


def test_load_snapshot_multiple_banks(tmp_path):
    snap = tmp_path / "2026-05-16"
    snap.mkdir()
    (snap / "amex_credit.csv").write_text(AMEX_CSV)
    (snap / "truist_checking.csv").write_text(TRUIST_CSV)
    result = load_snapshot(str(snap))
    assert set(result["bank"].unique()) == {"amex", "truist"}
    assert len(result) == 6


def test_latest_snapshot(tmp_path):
    (tmp_path / "2026-04-01").mkdir()
    (tmp_path / "2026-05-15").mkdir()
    (tmp_path / "2026-05-16").mkdir()
    assert Path(latest_snapshot(str(tmp_path))).name == "2026-05-16"


def test_latest_snapshot_raises_when_empty(tmp_path):
    with pytest.raises(FileNotFoundError):
        latest_snapshot(str(tmp_path))
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/derekhonerlaw/Development/financials-tmp
python -m pytest tests/test_storage.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'lib'`

- [ ] **Step 3: Implement `lib/storage.py`**

```python
from pathlib import Path
from datetime import date
import pandas as pd

BANK_SCHEMA = {
    "amex": {
        "date": "Date",
        "description": "Description",
        "amount": "Amount",
        "type": "Type",
        "person": "Card Member",
    },
    "truist": {
        "date": "Date",
        "description": "Description",
        "amount": "Amount",
        "type": "Type",
        "person": None,  # update if cardholder column exists after first pull
    },
    "citi": {
        "date": "Transaction Date",
        "description": "Description",
        "amount": None,  # computed from Debit/Credit columns
        "type": "Transaction Type",
        "person": None,  # update if cardholder column exists after first pull
    },
}


def get_snapshot_dir(base_dir: str, snapshot_date: str = None) -> str:
    d = snapshot_date or date.today().isoformat()
    path = Path(base_dir) / d
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def normalize_csv(df: pd.DataFrame, bank: str) -> pd.DataFrame:
    schema = BANK_SCHEMA[bank]
    result = pd.DataFrame()
    result["date"] = df[schema["date"]]
    result["description"] = df[schema["description"]]

    if bank == "citi":
        debit = pd.to_numeric(df.get("Debit", pd.Series(0, index=df.index)), errors="coerce").fillna(0)
        credit = pd.to_numeric(df.get("Credit", pd.Series(0, index=df.index)), errors="coerce").fillna(0)
        result["amount"] = credit - debit
    elif bank == "amex":
        # Amex exports purchases as positive amounts; negate so outflow is negative
        result["amount"] = -pd.to_numeric(df[schema["amount"]], errors="coerce")
    else:
        result["amount"] = pd.to_numeric(df[schema["amount"]], errors="coerce")

    person_col = schema.get("person")
    type_col = schema.get("type")
    result["type"] = df[type_col] if (type_col and type_col in df.columns) else None
    person_col = schema.get("person")
    result["person"] = df[person_col] if (person_col and person_col in df.columns) else None
    result["bank"] = bank
    return result


def load_snapshot(snapshot_dir: str) -> pd.DataFrame:
    frames = []
    for csv_file in sorted(Path(snapshot_dir).glob("*.csv")):
        bank = csv_file.stem.split("_")[0]  # "amex" from "amex_credit.csv"
        frames.append(normalize_csv(pd.read_csv(csv_file), bank))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def latest_snapshot(base_dir: str) -> str:
    snapshots = sorted(Path(base_dir).glob("????-??-??"), reverse=True)
    if not snapshots:
        raise FileNotFoundError(f"No snapshots found in {base_dir}")
    return str(snapshots[0])
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_storage.py -v
```

Expected: 15 tests, all PASSED.

- [ ] **Step 5: Commit**

```bash
git add plugins/financials/scripts/lib/storage.py tests/test_storage.py
git commit -m "feat: add storage module with CSV normalization and snapshot management"
```

---

### Task 3: lib/browser.py

**Files:**
- Create: `plugins/financials/scripts/lib/browser.py`
- Create: `tests/test_browser.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_browser.py`:

```python
import pytest
from unittest.mock import patch
from lib.browser import launch_browser, pause_for_2fa


def test_launch_browser_returns_page():
    pw, browser, page = launch_browser(headless=True)
    try:
        page.goto("about:blank")
        assert page.url == "about:blank"
    finally:
        browser.close()
        pw.stop()


def test_pause_for_2fa_prints_bank_name(capsys):
    class MockPage:
        def bring_to_front(self):
            pass

    with patch("builtins.input", return_value=""):
        pause_for_2fa(MockPage(), "Test Bank")

    captured = capsys.readouterr()
    assert "Test Bank" in captured.out
    assert "2FA" in captured.out
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_browser.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'lib.browser'`

- [ ] **Step 3: Implement `lib/browser.py`**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_browser.py -v
```

Expected: both tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add plugins/financials/scripts/lib/browser.py tests/test_browser.py
git commit -m "feat: add browser module with Playwright launch and 2FA pause"
```

---

### Task 4: banks/amex.py

**Files:**
- Create: `plugins/financials/scripts/banks/amex.py`

This drives a live website. Selectors are based on Amex's current UI. If the pull fails at a navigation step on first run, open browser DevTools to find the correct selector and update accordingly.

- [ ] **Step 1: Create `banks/amex.py`**

```python
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
        page.goto(LOGIN_URL, wait_until="networkidle")

        input("[Amex] Enter your username and password, then press Enter...")

        if _is_2fa_page(page):
            pause_for_2fa(page, "Amex")

        page.wait_for_selector("[class*='account-summary'], [class*='dashboard']", timeout=30000)
        print("[Amex] Logged in. Navigating to transaction download...")

        # Amex direct CSV download endpoint
        fmt_start = start.strftime("%Y%m%d")
        fmt_end = today.strftime("%Y%m%d")
        with page.expect_download() as dl:
            page.goto(
                f"https://www.americanexpress.com/en-us/account/download-transactions"
                f"?startDate={fmt_start}&endDate={fmt_end}&fileType=csv",
                wait_until="networkidle",
            )
        dl.value.save_as(str(download_path))
        print(f"[Amex] Saved → {download_path}")
        return str(download_path)
    finally:
        browser.close()
        pw.stop()
```

- [ ] **Step 2: Verify the module imports cleanly**

```bash
cd plugins/financials/scripts
python -c "from banks.amex import pull; print('amex: OK')"
```

Expected: `amex: OK`

- [ ] **Step 3: Commit**

```bash
cd /Users/derekhonerlaw/Development/financials-tmp
git add plugins/financials/scripts/banks/amex.py
git commit -m "feat: add Amex Playwright pull module"
```

---

### Task 5: banks/truist.py

**Files:**
- Create: `plugins/financials/scripts/banks/truist.py`

- [ ] **Step 1: Create `banks/truist.py`**

```python
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
        page.goto(LOGIN_URL, wait_until="networkidle")

        input("[Truist] Enter your username and password, then press Enter...")

        if _is_2fa_page(page):
            pause_for_2fa(page, "Truist")

        page.wait_for_selector("[class*='account'], [id*='account-summary']", timeout=30000)
        print("[Truist] Logged in. Navigating to transaction export...")

        # Click into the checking account tile
        page.click("[class*='account-tile']:first-child, [data-testid*='account']:first-child")
        page.wait_for_load_state("networkidle")

        # Open export dialog
        page.click("[aria-label*='export'], [aria-label*='download'], button:has-text('Export')")
        page.wait_for_selector("[class*='export-modal'], [role='dialog']", timeout=10000)

        # Set date range
        start_input = page.query_selector("input[name*='start'], input[aria-label*='Start date']")
        end_input = page.query_selector("input[name*='end'], input[aria-label*='End date']")
        if start_input:
            start_input.fill(start.strftime("%m/%d/%Y"))
        if end_input:
            end_input.fill(today.strftime("%m/%d/%Y"))

        # Select CSV if format option is present
        csv_option = page.query_selector("input[value*='csv'], option[value*='csv']")
        if csv_option:
            csv_option.click()

        with page.expect_download() as dl:
            page.click("button:has-text('Download'), button:has-text('Export')")
        dl.value.save_as(str(download_path))
        print(f"[Truist] Saved → {download_path}")
        return str(download_path)
    finally:
        browser.close()
        pw.stop()
```

- [ ] **Step 2: Verify the module imports cleanly**

```bash
cd plugins/financials/scripts
python -c "from banks.truist import pull; print('truist: OK')"
```

Expected: `truist: OK`

- [ ] **Step 3: Commit**

```bash
cd /Users/derekhonerlaw/Development/financials-tmp
git add plugins/financials/scripts/banks/truist.py
git commit -m "feat: add Truist Playwright pull module"
```

---

### Task 6: banks/citi.py

**Files:**
- Create: `plugins/financials/scripts/banks/citi.py`

- [ ] **Step 1: Create `banks/citi.py`**

```python
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

        # Click into first credit account
        page.click("[class*='account-tile']:first-child, a[id*='account']:first-child")
        page.wait_for_load_state("networkidle")

        # Open download section
        page.click("a:has-text('Download'), button:has-text('Download Transactions')")
        page.wait_for_selector("[class*='download'], [id*='downloadForm']", timeout=10000)

        # Set date range
        start_input = page.query_selector("input[id*='fromDate'], input[name*='fromDate']")
        end_input = page.query_selector("input[id*='toDate'], input[name*='toDate']")
        if start_input:
            start_input.fill(start.strftime("%m/%d/%Y"))
        if end_input:
            end_input.fill(today.strftime("%m/%d/%Y"))

        # Select CSV format
        csv_option = page.query_selector("option[value*='csv'], input[value*='csv']")
        if csv_option:
            csv_option.click()

        with page.expect_download() as dl:
            page.click("button:has-text('Download'), input[type='submit']")
        dl.value.save_as(str(download_path))
        print(f"[Citi] Saved → {download_path}")
        return str(download_path)
    finally:
        browser.close()
        pw.stop()
```

- [ ] **Step 2: Verify the module imports cleanly**

```bash
cd plugins/financials/scripts
python -c "from banks.citi import pull; print('citi: OK')"
```

Expected: `citi: OK`

- [ ] **Step 3: Commit**

```bash
cd /Users/derekhonerlaw/Development/financials-tmp
git add plugins/financials/scripts/banks/citi.py
git commit -m "feat: add Citi Playwright pull module"
```

---

### Task 7: scripts/pull.py

**Files:**
- Create: `plugins/financials/scripts/pull.py`
- Create: `tests/test_pull.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_pull.py`:

```python
import pytest
from unittest.mock import patch, MagicMock


def test_pull_all_banks(tmp_path):
    with patch("pull.amex") as mock_amex, \
         patch("pull.truist") as mock_truist, \
         patch("pull.citi") as mock_citi, \
         patch("pull.get_snapshot_dir", return_value=str(tmp_path)):
        mock_amex.pull.return_value = str(tmp_path / "amex_credit.csv")
        mock_truist.pull.return_value = str(tmp_path / "truist_checking.csv")
        mock_citi.pull.return_value = str(tmp_path / "citi_credit.csv")

        from pull import run
        results = run(banks=None)

        mock_amex.pull.assert_called_once_with(str(tmp_path))
        mock_truist.pull.assert_called_once_with(str(tmp_path))
        mock_citi.pull.assert_called_once_with(str(tmp_path))
        assert all(status == "ok" for status, _ in results.values())


def test_pull_single_bank(tmp_path):
    with patch("pull.amex") as mock_amex, \
         patch("pull.truist") as mock_truist, \
         patch("pull.get_snapshot_dir", return_value=str(tmp_path)):
        mock_amex.pull.return_value = str(tmp_path / "amex_credit.csv")

        from pull import run
        results = run(banks=["amex"])

        mock_amex.pull.assert_called_once()
        mock_truist.pull.assert_not_called()


def test_pull_unknown_bank_raises():
    from pull import run
    with pytest.raises(ValueError, match="Unknown bank"):
        run(banks=["unknown"])


def test_pull_bank_error_captured(tmp_path):
    with patch("pull.amex") as mock_amex, \
         patch("pull.get_snapshot_dir", return_value=str(tmp_path)):
        mock_amex.pull.side_effect = Exception("login failed")

        from pull import run
        results = run(banks=["amex"])

        status, detail = results["amex"]
        assert status == "error"
        assert "login failed" in detail
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/derekhonerlaw/Development/financials-tmp
python -m pytest tests/test_pull.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'pull'`

- [ ] **Step 3: Implement `pull.py`**

```python
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from banks import amex, truist, citi
from lib.storage import get_snapshot_dir

SNAPSHOT_BASE = os.path.expanduser("~/Documents/financials/snapshots")

BANK_MODULES = {
    "amex": amex,
    "truist": truist,
    "citi": citi,
}


def run(banks=None):
    targets = banks or list(BANK_MODULES.keys())
    for bank in targets:
        if bank not in BANK_MODULES:
            raise ValueError(f"Unknown bank: {bank}. Valid: {list(BANK_MODULES.keys())}")

    snapshot_dir = get_snapshot_dir(SNAPSHOT_BASE)
    print(f"Saving to: {snapshot_dir}\n")

    results = {}
    for bank in targets:
        try:
            path = BANK_MODULES[bank].pull(snapshot_dir)
            results[bank] = ("ok", path)
        except Exception as e:
            results[bank] = ("error", str(e))
            print(f"[{bank}] ERROR: {e}")

    print("\n--- Summary ---")
    for bank, (status, detail) in results.items():
        icon = "✓" if status == "ok" else "✗"
        print(f"{icon} {bank}: {detail}")

    return results


if __name__ == "__main__":
    banks_arg = sys.argv[1:] or None
    run(banks=banks_arg)
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_pull.py -v
```

Expected: 4 tests, all PASSED.

- [ ] **Step 5: Commit**

```bash
git add plugins/financials/scripts/pull.py tests/test_pull.py
git commit -m "feat: add pull runner with per-bank sequencing and error handling"
```

---

### Task 8: Skill Files

**Files:**
- Create: `plugins/financials/skills/pull-finances.md`
- Create: `plugins/financials/skills/spending-summary.md`
- Create: `plugins/financials/skills/spending-breakdown.md`
- Create: `plugins/financials/skills/recurring-expenses.md`
- Create: `plugins/financials/skills/cross-account.md`

- [ ] **Step 1: Create `skills/pull-finances.md`**

```markdown
---
description: Pull 90 days of transaction CSVs from Truist, Amex, and Citi. Run all three banks or name one: truist, amex, or citi.
---

Pull financial transactions from bank accounts and save a dated snapshot locally.

## Usage

- `/pull-finances` — pull all three banks in sequence
- `/pull-finances amex` — pull only Amex
- `/pull-finances truist` — pull only Truist
- `/pull-finances citi` — pull only Citi

## Steps

1. Check the user's message for a bank name argument. If present, pass it to the script. Otherwise omit it to pull all three.

2. Run the pull script:
   ```bash
   cd ~/.claude/plugins/financials/scripts && python pull.py [bank_name]
   ```

3. A browser window will open for each bank. The script will pause at each 2FA prompt and print instructions to the terminal. Tell the user to watch the browser window — they'll complete 2FA there, then press Enter in the terminal to continue.

4. When complete, report which banks succeeded, which (if any) errored, and the full path to the snapshot folder.
```

- [ ] **Step 2: Create `skills/spending-summary.md`**

```markdown
---
description: Summarize spending from the latest snapshot (or a given date). Shows monthly totals, top merchants, category breakdown, month-over-month delta, and per-person spend.
---

Analyze the latest transaction snapshot and produce a spending summary.

## Usage

- `/spending-summary` — use the most recent snapshot
- `/spending-summary 2026-04-01` — use the snapshot from that date

## Steps

1. Determine the snapshot directory:
   - If the user provided a date, use `~/Documents/financials/snapshots/<date>/`
   - Otherwise find the most recently dated folder in `~/Documents/financials/snapshots/`

2. Read all CSV files in that folder with the Bash tool.

3. Normalize amounts: outflows are negative, inflows are positive.

4. Produce a markdown report with these sections:

   **Monthly Totals** — total spend (sum of negative amounts, shown as positive) per calendar month in the snapshot

   **Top 10 Merchants** — ranked by absolute spend, descending, with total amount

   **Category Breakdown** — infer category from the description field using your judgment. Group totals by category.

   **Month-over-Month Delta** — % change in total spend between the two most recent complete months

   **By Person** — total spend per unique value in the `person` column; skip rows where person is null
```

- [ ] **Step 3: Create `skills/spending-breakdown.md`**

```markdown
---
description: Show spending organized by category for the latest snapshot — no targets, just actuals. Categories inferred by Claude from transaction descriptions.
---

Break down spending by category for the latest snapshot (or a given date).

## Usage

- `/spending-breakdown` — use the most recent snapshot
- `/spending-breakdown 2026-04-01` — use the snapshot from that date

## Steps

1. Determine the snapshot directory:
   - If the user provided a date, use `~/Documents/financials/snapshots/<date>/`
   - Otherwise find the most recently dated folder in `~/Documents/financials/snapshots/`

2. Read all CSV files in that folder.

3. For each transaction, infer a category from the description field. Examples:
   - Whole Foods, Kroger, Trader Joe's, Publix → Groceries
   - Restaurants, cafes, DoorDash, Uber Eats → Dining
   - Airlines, hotels, Airbnb, Uber, Lyft → Travel
   - Shell, BP, ExxonMobil → Gas & Auto
   - Netflix, Spotify, Adobe, Apple subscriptions → Subscriptions
   - CVS, Walgreens, doctor/hospital names → Medical
   - Amazon, Target, retail → Shopping
   - Utilities, insurance providers → Bills
   - Transfers, payments, Venmo, Zelle → Transfers
   - Everything else → Other

4. Produce a table sorted by total spend descending:

   | Category | Transactions | Total Spent |
   |----------|-------------|-------------|

5. List any transactions you couldn't confidently categorize at the bottom for user review.
```

- [ ] **Step 4: Create `skills/recurring-expenses.md`**

```markdown
---
description: Identify recurring transactions — bills, subscriptions, and regular transfers — from the latest snapshot. Shows estimated monthly recurring total.
---

Scan transaction history for recurring charges.

## Usage

- `/recurring-expenses` — use the most recent snapshot
- `/recurring-expenses 2026-04-01` — use the snapshot from that date

## Steps

1. Determine the snapshot directory:
   - If the user provided a date, use `~/Documents/financials/snapshots/<date>/`
   - Otherwise find the most recently dated folder in `~/Documents/financials/snapshots/`

2. Read all CSV files in that folder.

3. Identify recurring transactions: same merchant (or very similar description) appearing in 2+ different calendar months with a similar amount (within 10%).

4. Group into three buckets:

   **Bills** — utilities, insurance, mortgage/rent, phone, internet

   **Subscriptions** — streaming, software/SaaS, memberships, news sites

   **Regular Transfers** — recurring transfers that aren't vendor charges (e.g. Venmo to a specific person monthly)

5. For each recurring item show: merchant name, typical amount, how many months it appeared, which account, and which person (if person field is populated).

6. End with an estimated monthly recurring total across all buckets.
```

- [ ] **Step 5: Create `skills/cross-account.md`**

```markdown
---
description: Net cash flow view across all accounts (Truist, Amex, Citi) for the latest snapshot. Shows total inflow vs outflow, per-account breakdown, and 3-month trend.
---

Produce a cross-account cash flow summary.

## Usage

- `/cross-account` — use the most recent snapshot
- `/cross-account 2026-04-01` — use the snapshot from that date

## Steps

1. Determine the snapshot directory:
   - If the user provided a date, use `~/Documents/financials/snapshots/<date>/`
   - Otherwise find the most recently dated folder in `~/Documents/financials/snapshots/`

2. Read all CSV files in that folder. The `bank` column identifies which account each transaction belongs to.

3. Produce this report:

   **Total Inflow vs Outflow** — sum of all positive amounts (inflow) and absolute sum of all negative amounts (outflow) across all accounts. Net = inflow − outflow.

   **Per-Account Summary** — for each bank: total inflow, total outflow, net

   **Spend Distribution** — which account carries what % of total spend

   **3-Month Trend** — if the snapshot spans multiple months, show net cash flow per month as a simple table

4. Call out any notable patterns (e.g. a month where outflow significantly exceeds inflow, or one account dominating spend).
```

- [ ] **Step 6: Commit**

```bash
git add plugins/financials/skills/
git commit -m "feat: add all five financials skill files"
```

---

### Task 9: Integration Smoke Test

**Files:** none new

- [ ] **Step 1: Run all unit tests**

```bash
cd /Users/derekhonerlaw/Development/financials-tmp
python -m pytest tests/ -v
```

Expected: all tests PASSED, no failures.

- [ ] **Step 2: Verify install.sh produces the symlink**

```bash
./install.sh financials
ls -la ~/.claude/plugins/financials/skills/
```

Expected: 5 `.md` skill files listed, resolving through the symlink to the repo.

- [ ] **Step 3: Verify pull.py CLI entry point**

```bash
cd plugins/financials/scripts
python pull.py --help 2>&1 || python -c "from pull import run; print('pull: OK')"
```

Expected: `pull: OK`

- [ ] **Step 4: Final commit**

```bash
cd /Users/derekhonerlaw/Development/financials-tmp
git add .
git status
git commit -m "chore: smoke test and finalize financials plugin" --allow-empty
```
