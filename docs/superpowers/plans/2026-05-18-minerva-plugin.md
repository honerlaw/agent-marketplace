# minerva Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `minerva` Claude Code plugin — four slash commands (`/propose`, `/replan`, `/work`, `/promote`) that implement the durable-record discipline described in `docs/superpowers/specs/2026-05-18-minerva-plugin-design.md`.

**Architecture:** Pure-markdown plugin (no scripts). Each command is a `commands/*.md` file whose body is natural-language protocol Claude follows when the slash command fires. Tests are structural — they verify file existence, JSON validity, frontmatter presence, and that key behavior keywords appear in the command bodies. Functional behavior depends on Claude executing the prompts and can't be unit-tested.

**Tech Stack:** Markdown command files, JSON metadata, Python `pytest` for structural validation. No new runtime dependencies.

---

## File Structure

**Created:**
- `plugins/minerva/.claude-plugin/plugin.json` — plugin metadata
- `plugins/minerva/README.md` — plugin readme
- `plugins/minerva/commands/propose.md` — `/propose <slug>` command
- `plugins/minerva/commands/replan.md` — `/replan [target]` command
- `plugins/minerva/commands/work.md` — `/work [target]` command
- `plugins/minerva/commands/promote.md` — `/promote [item]` command
- `tests/test_minerva.py` — structural validation tests

**Modified:**
- `.claude-plugin/marketplace.json` — replace `feature-cycle` entry with `minerva`
- `README.md` (root) — replace `feature-cycle` row with `minerva` row

**Deleted:**
- `plugins/feature-cycle/` — superseded by minerva (spec line: "The existing `plugins/feature-cycle/` directory from the earlier iteration is removed; nothing else depended on it.")

---

## Task 0: Reset stale in-progress state

The prior `feature-cycle` plugin work left uncommitted changes that need to be cleared before building `minerva` on a clean baseline.

**Files:**
- Modify: `.claude-plugin/marketplace.json` (revert)
- Modify: `README.md` (revert)
- Delete: `plugins/feature-cycle/` (rm -rf, untracked)

- [ ] **Step 1: Confirm the state we're resetting**

Run:
```bash
git status
```
Expected output includes:
```
modified:   .claude-plugin/marketplace.json
modified:   README.md
Untracked files:
        plugins/feature-cycle/
```

- [ ] **Step 2: Revert tracked file modifications**

Run:
```bash
git checkout .claude-plugin/marketplace.json README.md
```
Expected: no output. Both files return to their last committed state.

- [ ] **Step 3: Remove the untracked feature-cycle plugin**

Run:
```bash
rm -rf plugins/feature-cycle
```
Expected: no output.

- [ ] **Step 4: Verify clean working tree**

Run:
```bash
git status
```
Expected:
```
On branch main
nothing to commit, working tree clean
```

No commit for this task — it just removes uncommitted state.

---

## Task 1: Scaffold plugin directory and plugin.json (TDD)

**Files:**
- Create: `plugins/minerva/.claude-plugin/plugin.json`
- Create: `tests/test_minerva.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_minerva.py` with this content:

```python
"""Structural validation for the minerva plugin.

These tests verify file layout, JSON validity, and the presence of key
frontmatter / behavior keywords. They do not exercise runtime behavior —
the plugin is pure-markdown protocol executed by Claude.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "plugins" / "minerva"


def test_plugin_json_exists_and_parses():
    plugin_json = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
    assert plugin_json.is_file(), f"missing: {plugin_json}"
    data = json.loads(plugin_json.read_text())
    assert data["name"] == "minerva"
    assert "description" in data and data["description"]
    assert data["author"]["name"] == "Derek Honerlaw"
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_minerva.py -v
```
Expected: FAIL with `FileNotFoundError` or `AssertionError: missing: .../plugins/minerva/.claude-plugin/plugin.json`.

- [ ] **Step 3: Create plugin.json**

Create `plugins/minerva/.claude-plugin/plugin.json`:
```json
{
  "name": "minerva",
  "description": "Durable record discipline for software work — promotion, not accumulation. Implements a persistence hierarchy of proposals, replans, scratchpads, and decisions.",
  "author": {
    "name": "Derek Honerlaw"
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_minerva.py -v
```
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add tests/test_minerva.py plugins/minerva/.claude-plugin/plugin.json
git commit -m "feat(minerva): scaffold plugin.json with structural test"
```

---

## Task 2: Marketplace registration (TDD)

**Files:**
- Modify: `.claude-plugin/marketplace.json`
- Modify: `tests/test_minerva.py` (add test)

- [ ] **Step 1: Add the failing test**

Append to `tests/test_minerva.py`:

```python
def test_marketplace_lists_minerva():
    marketplace = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text())
    entries = {p["name"]: p for p in marketplace["plugins"]}
    assert "minerva" in entries, "minerva not registered in marketplace.json"
    assert entries["minerva"]["source"] == "./plugins/minerva"
    assert entries["minerva"]["description"], "minerva entry must have a description"


def test_marketplace_does_not_list_feature_cycle():
    marketplace = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text())
    names = {p["name"] for p in marketplace["plugins"]}
    assert "feature-cycle" not in names, "feature-cycle was superseded by minerva"
```

- [ ] **Step 2: Run tests to verify the new ones fail**

Run:
```bash
pytest tests/test_minerva.py -v
```
Expected: `test_marketplace_lists_minerva` fails (`AssertionError: minerva not registered`); `test_marketplace_does_not_list_feature_cycle` passes (feature-cycle was reverted in Task 0).

- [ ] **Step 3: Edit `.claude-plugin/marketplace.json`**

Read the current file. It looks like:
```json
{
  "name": "agent-marketplace",
  "owner": {
    "name": "Derek Honerlaw"
  },
  "metadata": {
    "description": "Personal plugin marketplace for AI coding agents"
  },
  "plugins": [
    {
      "name": "financials",
      "source": "./plugins/financials",
      "description": "Pull and analyze personal finances from Truist, Amex, and Citi"
    }
  ]
}
```

Replace the `plugins` array with:
```json
  "plugins": [
    {
      "name": "financials",
      "source": "./plugins/financials",
      "description": "Pull and analyze personal finances from Truist, Amex, and Citi"
    },
    {
      "name": "minerva",
      "source": "./plugins/minerva",
      "description": "Durable record discipline for software work — promotion, not accumulation. Proposal → work → replan → promote, with a persistence hierarchy of decisions, proposals, and scratchpads."
    }
  ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_minerva.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add .claude-plugin/marketplace.json tests/test_minerva.py
git commit -m "feat(minerva): register plugin in marketplace.json"
```

---

## Task 3: Root README update (TDD)

**Files:**
- Modify: `README.md` (root)
- Modify: `tests/test_minerva.py` (add test)

- [ ] **Step 1: Add the failing test**

Append to `tests/test_minerva.py`:

```python
def test_root_readme_mentions_minerva():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "minerva" in readme, "root README must list minerva in the plugin table"
    for command in ["/propose", "/replan", "/work", "/promote"]:
        assert command in readme, f"root README must mention {command}"


def test_root_readme_does_not_mention_feature_cycle():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "feature-cycle" not in readme, "feature-cycle was superseded by minerva"
```

- [ ] **Step 2: Run tests to verify the new ones fail**

Run:
```bash
pytest tests/test_minerva.py -v
```
Expected: `test_root_readme_mentions_minerva` fails; `test_root_readme_does_not_mention_feature_cycle` passes.

- [ ] **Step 3: Edit `README.md`**

Current Plugins table ends with the `financials` row. Add a `minerva` row immediately after, so the section reads:

```markdown
## Plugins

| Plugin | Skills | Description |
|--------|--------|-------------|
| financials | `/pull-finances` `/spending-summary` `/spending-breakdown` `/recurring-expenses` `/cross-account` | Pull and analyze personal finances from Truist, Amex, Citi |
| minerva | `/propose` `/replan` `/work` `/promote` | Durable record discipline for software work — proposal → work → replan → promote, with a persistence hierarchy of decisions, proposals, and scratchpads |
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_minerva.py -v
```
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add README.md tests/test_minerva.py
git commit -m "docs(minerva): list plugin in root README"
```

---

## Task 4: `/propose` command (TDD)

**Files:**
- Create: `plugins/minerva/commands/propose.md`
- Modify: `tests/test_minerva.py` (add test)

- [ ] **Step 1: Add the failing test**

Append to `tests/test_minerva.py`:

```python
COMMANDS_DIR = PLUGIN_DIR / "commands"


def _read_command(name: str) -> tuple[dict, str]:
    """Parse a command markdown file's frontmatter and body."""
    text = (COMMANDS_DIR / f"{name}.md").read_text()
    assert text.startswith("---\n"), f"{name}.md missing frontmatter"
    _, frontmatter, body = text.split("---\n", 2)
    fm = {}
    for line in frontmatter.strip().splitlines():
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip()
    return fm, body


def test_propose_command_exists_with_frontmatter():
    fm, body = _read_command("propose")
    assert fm.get("description"), "propose.md must have a description in frontmatter"
    # Key behaviors from the spec
    assert "proposal.md" in body
    assert "work/" in body
    assert "brainstorm" in body.lower() or "questions one at a time" in body.lower()
    assert "scratchpad.md" in body  # the empty scratchpad is created alongside
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_minerva.py::test_propose_command_exists_with_frontmatter -v
```
Expected: FAIL with `FileNotFoundError` (commands dir doesn't exist yet).

- [ ] **Step 3: Create `plugins/minerva/commands/propose.md`**

Write the file with this exact content:

````markdown
---
description: Brainstorm-style proposal authoring for a new unit of work. Asks clarifying questions one at a time, proposes 2-3 approaches with tradeoffs, presents the design in sections, and writes the approved design to work/NNN-slug/proposal.md.
---

Start a new work unit by brainstorming and writing its proposal.

## Usage

- `/propose add-payments` — brainstorms a new work unit, writes `work/NNN-add-payments/proposal.md`
- `/propose "rate limit overhaul"` — same; slug is normalized

## Slug normalization

Lowercase, replace whitespace/underscores with `-`, strip everything outside `[a-z0-9-]`.

## Pre-flight check

If `work/` already contains an entry matching the normalized slug (any `work/NNN-<slug>/`), do **not** start a new proposal. Tell the user the existing path and suggest `/replan` if they want to course-correct an in-flight work unit.

## Protocol

This command mirrors the `superpowers:brainstorming` flow but writes to `work/NNN-<slug>/proposal.md` instead of a generic spec path.

1. **Explore project context first.** Read `CLAUDE.md` if present, skim `decisions/`, glance at recent `work/NNN-*/proposal.md` files for tone and conventions. This informs the questions you'll ask.
2. **Ask clarifying questions one at a time.** Cover purpose, constraints, and success criteria. Prefer multiple-choice. Don't batch.
3. **Propose 2–3 approaches** with tradeoffs and a recommendation. Lead with the recommendation. Iterate based on user feedback.
4. **Present the design in sections** (Goal, Why, Approach, Open Questions). Get approval per section before moving on.
5. **Hard gate:** do not write any file until the user has explicitly approved the design.

## On approval — file writes

1. Compute the next NNN under `work/`:
   - List entries matching `^[0-9]{3}-` in `work/`.
   - Take `max + 1`, padded to 3 digits.
   - If `work/` doesn't exist, create it and start at `001`.
2. Create `work/NNN-<slug>/`.
3. Write `proposal.md` using the approved content, structured as:

   ```markdown
   # Proposal: <slug>

   **Date**: YYYY-MM-DD
   **Status**: Draft

   ## Goal
   <approved goal>

   ## Why
   <approved motivation>

   ## Approach
   <approved approach — will be rewritten by /promote to describe what shipped>

   ## Open Questions
   - <any remaining items>
   ```

4. Write `scratchpad.md` with this header and nothing else:

   ```markdown
   # Scratchpad: <slug>

   > **Ephemeral working memory.** Most of what lands here is noise — small
   > decisions that don't matter, dead ends, momentary confusion. At feature
   > completion, run `/promote`: significant items get promoted to
   > `decisions/`, `proposal.md` gets updated to match reality, and the raw
   > scratchpad is archived.

   ```

5. Report the created path. Suggest `/work` as the next step.

## Out of scope

This command stops at writing the files. It does **not** invoke any implementation skill — `/work` is the next phase.
````

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_minerva.py::test_propose_command_exists_with_frontmatter -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/minerva/commands/propose.md tests/test_minerva.py
git commit -m "feat(minerva): /propose command — brainstorm-style proposal authoring"
```

---

## Task 5: `/replan` command (TDD)

**Files:**
- Create: `plugins/minerva/commands/replan.md`
- Modify: `tests/test_minerva.py` (add test)

- [ ] **Step 1: Add the failing test**

Append to `tests/test_minerva.py`:

```python
def test_replan_command_exists_with_frontmatter():
    fm, body = _read_command("replan")
    assert fm.get("description"), "replan.md must have a description in frontmatter"
    assert "replan.md" in body
    assert "Original plan" in body
    assert "What changed" in body
    assert "New plan" in body
    assert "most-recently-modified" in body.lower() or "most recently modified" in body.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_minerva.py::test_replan_command_exists_with_frontmatter -v
```
Expected: FAIL with `FileNotFoundError`.

- [ ] **Step 3: Create `plugins/minerva/commands/replan.md`**

Write the file with this exact content:

````markdown
---
description: Capture a divergence from the proposal in the current work unit. Same brainstorm-style flow as /propose, but appends a dated entry to work/NNN-slug/replan.md rather than starting a new work unit.
---

Append a dated replan entry to the current work unit when reality has diverged from the proposal.

## Usage

- `/replan` — operates on the most-recently-modified `work/NNN-*/`
- `/replan 003-add-payments` — explicit work directory
- `/replan add-payments` — substring match against existing work dirs

## Target resolution

1. If the user passed an exact directory name (e.g. `003-add-payments`), use `work/<that>/`.
2. Otherwise substring match against existing `work/NNN-*/` entries. If exactly one match, use it; if multiple, list them and ask which.
3. If no argument, use the most-recently-modified `work/NNN-*/` by directory mtime.
4. If no `work/` directory exists or it's empty, report "no work units found — run `/propose <slug>` first" and stop.

## Protocol

Same brainstorming pattern as `/propose`, but framed around divergence:

1. **Read the existing context first.** Read `proposal.md`, any prior `replan.md` entries, and the current `scratchpad.md`. The brainstorm must be grounded in what actually happened.
2. **Frame the replan around three pieces:**
   - **Original plan** — what the proposal (or latest prior replan) said the approach was
   - **What changed** — what was discovered, what broke, what assumption was wrong
   - **New plan** — the revised approach
3. **Ask clarifying questions one at a time** to fill in any of the three pieces that aren't already obvious from the conversation or files.
4. **Propose 2–3 alternative new plans** if the path forward isn't already settled. Iterate.
5. **Present the resulting entry** for approval before writing.
6. **Hard gate:** do not append to the file until the user has approved the entry.

## On approval — file write

1. If `replan.md` doesn't exist yet, create it with this header:

   ```markdown
   # Replan log: <slug>

   ```

2. Append a new entry using this exact template (today's date in `YYYY-MM-DD`):

   ```markdown
   ## YYYY-MM-DD — <short, declarative title>

   **Original plan**: <one or two sentences>
   **What changed**: <what was discovered, what broke, what assumption was wrong>
   **New plan**: <one or two sentences>
   ```

3. Report the path and the title of the appended entry. Suggest resuming `/work` next.

## Out of scope

This command stops at appending to `replan.md`. It does **not** invoke implementation — return control to `/work` (or its in-progress session) after writing.
````

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_minerva.py::test_replan_command_exists_with_frontmatter -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/minerva/commands/replan.md tests/test_minerva.py
git commit -m "feat(minerva): /replan command — divergence capture for active work"
```

---

## Task 6: `/work` command (TDD)

**Files:**
- Create: `plugins/minerva/commands/work.md`
- Modify: `tests/test_minerva.py` (add test)

- [ ] **Step 1: Add the failing test**

Append to `tests/test_minerva.py`:

```python
def test_work_command_exists_with_frontmatter():
    fm, body = _read_command("work")
    assert fm.get("description"), "work.md must have a description in frontmatter"
    # Core behaviors per spec
    assert "scratchpad.md" in body
    assert "proposal.md" in body
    assert "replan.md" in body
    # Auto-trigger of /replan on divergence
    assert "/replan" in body
    assert "diverge" in body.lower() or "divergence" in body.lower()
    # Smart resume language
    assert "resume" in body.lower() or "left off" in body.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_minerva.py::test_work_command_exists_with_frontmatter -v
```
Expected: FAIL with `FileNotFoundError`.

- [ ] **Step 3: Create `plugins/minerva/commands/work.md`**

Write the file with this exact content:

````markdown
---
description: Enter implementation mode for a work unit. Reads its proposal and any replans, maintains a live scratchpad, watches for divergence from the plan, and auto-invokes the /replan protocol when reality drifts in a load-bearing way.
---

Implement the active work unit while maintaining the scratchpad and honoring the persistence hierarchy.

## Usage

- `/work` — resume the most-recently-modified `work/NNN-*/`
- `/work 003-add-payments` — explicit work directory
- `/work add-payments` — substring match

## Target resolution

Identical to `/replan`:
1. Exact directory match: `work/<arg>/`.
2. Substring match against `work/NNN-*/`; single match wins, multiple → list and ask.
3. No argument → most-recently-modified `work/NNN-*/` by mtime.
4. No `work/` or empty → report "no work units found — run `/propose <slug>` first" and stop.

## Setup (run at the start of every `/work` invocation)

1. Read `proposal.md`.
2. Read **all** `replan.md` entries chronologically. When the latest replan conflicts with the original proposal, the replan wins.
3. Read `scratchpad.md` to figure out where work left off.
4. Glance at `git status` and the last 3 commits to corroborate.
5. **Summarize the resumption point** to the user in one short paragraph before doing anything else: what the goal is, what's been done, what's next. Confirm before proceeding.

## Implementation protocol — apply throughout the session

### Scratchpad maintenance

As you work, log to `scratchpad.md`. The bar for an entry is: **a future-self might want to see this**. Examples:

- An approach that was tried and dropped (with why)
- A surprising constraint or gotcha
- A decision that might be durable but isn't yet certain
- A breadcrumb pointing at code you'll return to

**Do not** log:
- A transcript of every action
- Tactical implementation details that the diff already shows
- Routine debugging steps

The scratchpad is **ephemeral working memory**. `/promote` will later partition it into "promote / merge into proposal / discard." Keep signal-to-noise high.

### Divergence detection

Continuously check: does the approach I'm taking still match `proposal.md` (as superseded by the latest `replan.md`)?

**Auto-trigger the `/replan` protocol** when reality diverges in a load-bearing way:
- A core assumption from the proposal turns out to be wrong.
- The approach itself is changing (not just an implementation detail within the approach).
- Scope is shifting (in or out of the work unit).

**Do not trigger** for:
- Routine implementation choices (which library, which helper to extract, how to structure a function).
- Small refactors along the way.
- Edge-case handling that wasn't in the proposal but doesn't change the approach.

**On trigger:** pause implementation. Tell the user "this looks like a load-bearing divergence — running the replan protocol." Then read `plugins/minerva/commands/replan.md` and follow its protocol inline (it's just instructions — there's no separate tool invocation). Once the replan entry is written, resume implementation with the new plan in context.

### Completion signal

When you believe implementation is done (the proposal's success criteria are met, any tests pass, the visible scope is delivered), surface `/promote` as the next step. Do not run it automatically — that's the user's call.

## Out of scope

`/work` is a setup-and-protocol command, not a one-shot operation. After the initial resumption summary it hands control back to normal conversation; the protocols above apply for the rest of the session.
````

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_minerva.py::test_work_command_exists_with_frontmatter -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/minerva/commands/work.md tests/test_minerva.py
git commit -m "feat(minerva): /work command — implementation mode with auto-replan"
```

---

## Task 7: `/promote` command (TDD)

**Files:**
- Create: `plugins/minerva/commands/promote.md`
- Modify: `tests/test_minerva.py` (add test)

- [ ] **Step 1: Add the failing test**

Append to `tests/test_minerva.py`:

```python
def test_promote_command_exists_with_frontmatter():
    fm, body = _read_command("promote")
    assert fm.get("description"), "promote.md must have a description in frontmatter"
    # Both modes
    assert "end-of-work" in body.lower() or "end of work" in body.lower()
    assert "single-item" in body.lower() or "single item" in body.lower() or "with argument" in body.lower()
    # Three-way partition language
    assert "PROMOTE" in body
    assert "DISCARD" in body
    # Idempotency
    assert "idempotent" in body.lower()
    # Decision file destination
    assert "decisions/" in body
    # Heuristic from the spec / image
    assert "new engineer" in body.lower() or "year" in body.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_minerva.py::test_promote_command_exists_with_frontmatter -v
```
Expected: FAIL with `FileNotFoundError`.

- [ ] **Step 3: Create `plugins/minerva/commands/promote.md`**

Write the file with this exact content:

````markdown
---
description: Extract durable decisions and finalize a work unit. No argument runs the end-of-work full pass (promote significant scratchpad items to decisions/, rewrite proposal.md to match reality, archive the raw scratchpad). With an argument, promotes a single mid-work item. Idempotent.
---

Promote durable items from `scratchpad.md` to `decisions/`, and (in the end-of-work pass) reshape the work unit's persistent record to match what shipped.

## The heuristic

> **Artifacts get promoted, not just accumulated.** Apply this to every scratchpad entry: *would a new engineer (or new agent) joining the project in a year benefit from reading this?* If yes, promote. If no, discard. Scratchpads almost always fail; decisions almost always pass; proposals are between.

## Target resolution

Same as `/replan` and `/work`:
1. Exact directory match.
2. Substring match against `work/NNN-*/`; single match wins.
3. No argument → most-recently-modified `work/NNN-*/`.
4. No `work/` or empty → report and stop.

## Two modes

### Mode A — no argument (end-of-work full pass)

1. Read `proposal.md`, `scratchpad.md`, and `replan.md` (if present).
2. **Idempotency check:** if `scratchpad.md` is the one-line `Summarized at /promote on YYYY-MM-DD — see archive/.` marker, report "already promoted" and stop.
3. Propose a three-way partition of the scratchpad entries:
   - **PROMOTE** → durable architectural/design choices, surprising constraints, tradeoffs worth recording, gotchas a future reader needs.
   - **MERGE INTO PROPOSAL** → places where the actual approach diverged from the original; the proposal's `## Approach` must end up describing what got built.
   - **DISCARD** → dead ends, momentary confusion, debugging digressions, choices that don't matter.
   Skip entries already marked `→ promoted to decisions/...` — they were promoted mid-work.
4. Present the partition as a numbered list with each entry's classification and a one-line justification. Wait for confirmation or edits.
5. **Hard gate:** do not write files until the user confirms.
6. On confirmation:
   - **For each PROMOTE item:** write `decisions/NNN-<slug>.md` using the decision template below. Auto-increment NNN across the whole `decisions/` directory (3-digit pad). If `decisions/` doesn't exist, create it and start at `001`. Each entry must stand alone.
   - **Rewrite `proposal.md`:** the `## Approach` section (and any other section that's out of date) describes reality, not the original plan. Don't preserve obsolete planning prose just because it was there.
   - **Archive the scratchpad:** create `work/<target>/archive/` if needed, move `scratchpad.md` to `archive/scratchpad.md`, then write a new `scratchpad.md` containing exactly:
     ```
     Summarized at /promote on YYYY-MM-DD — see archive/.
     ```
7. Report: items promoted (with paths), whether the proposal was updated and a one-line summary of the change, scratchpad disposition.

### Mode B — with argument (single-item mid-work promote)

`/promote "use postgres listen/notify for cache invalidation"`

1. Read `scratchpad.md`.
2. Locate the block matching the argument (substring or fuzzy match on the entry text). If multiple candidates, list them and ask which.
3. **Idempotency check:** if the matched block already has a `→ promoted to decisions/...` trailing line, report the existing decision file path and stop.
4. Confirm with the user that you've identified the right block and show the proposed decision entry. Wait for approval.
5. On approval:
   - Determine the next NNN under `decisions/` (max+1, 3-digit pad; start at `001` if dir is missing).
   - Write `decisions/NNN-<slug>.md` using the decision template.
   - In `scratchpad.md`, append `→ promoted to decisions/NNN-<slug>.md` to the matched block so the end-of-work pass won't re-promote it.
6. Report the decision file path.

## Idempotency summary

- Mode A re-run: scratchpad marker → stops early.
- Mode B re-run on a marked block: existing decision file → stops early.
- Decision files are never overwritten — auto-incremented NNN guarantees uniqueness.

If a user manually edits the scratchpad to remove markers, re-running `/promote` could duplicate entries. This is a known footgun; not defended against.

## Decision entry template

```markdown
# <Short, declarative title — what was decided>

**Date**: YYYY-MM-DD
**Context**: work/NNN-<slug>

## Context
The situation that forced this choice. Constraints, prior state, or the
problem we hit. Enough that a reader cold to the project understands why
this was even a question.

## Decision
What we chose. Stated as a declarative.

## Consequences
What this implies going forward — invariants other code now relies on,
things future work has to honor, tradeoffs we accepted.
```
````

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_minerva.py::test_promote_command_exists_with_frontmatter -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/minerva/commands/promote.md tests/test_minerva.py
git commit -m "feat(minerva): /promote command — decision extraction and finalization"
```

---

## Task 8: Plugin README (TDD)

**Files:**
- Create: `plugins/minerva/README.md`
- Modify: `tests/test_minerva.py` (add test)

- [ ] **Step 1: Add the failing test**

Append to `tests/test_minerva.py`:

```python
def test_plugin_readme_lists_all_four_commands():
    readme = (PLUGIN_DIR / "README.md").read_text()
    for command in ["/propose", "/replan", "/work", "/promote"]:
        assert command in readme, f"plugin README must list {command}"
    # Persistence hierarchy concept should be present
    assert "decisions" in readme.lower()
    assert "scratchpad" in readme.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_minerva.py::test_plugin_readme_lists_all_four_commands -v
```
Expected: FAIL with `FileNotFoundError`.

- [ ] **Step 3: Create `plugins/minerva/README.md`**

Write the file with this exact content:

````markdown
# minerva plugin

Durable record discipline for software work. Encodes a persistence hierarchy where **artifacts get promoted, not just accumulated** — significant scratchpad items become `decisions/` entries; proposals get rewritten to describe what shipped; raw scratchpads are archived.

## The hierarchy

| Tier | Files | When read |
|------|-------|-----------|
| Always-read | `CLAUDE.md`, `decisions/` | Loaded for every new piece of work |
| Searchable-on-demand | `work/NNN-slug/proposal.md`, `work/NNN-slug/replan.md` | Grep when relevant |
| Ephemeral | `work/NNN-slug/scratchpad.md` | Gone after `/promote` |

The heuristic for what to keep: **would a new engineer (or new agent) joining the project in a year benefit from reading this?** If yes, keep it. If no, summarize and discard.

## Commands

| Skill | Description |
|-------|-------------|
| `/propose <slug>` | Brainstorm-style proposal authoring for a new work unit. Asks clarifying questions, proposes approaches, writes `work/NNN-slug/proposal.md` once approved. |
| `/replan [target]` | Same brainstorm flow, but appends a dated divergence entry to `work/NNN-slug/replan.md` for an in-flight work unit. |
| `/work [target]` | Enter implementation mode. Reads the proposal + replans, maintains `scratchpad.md`, auto-triggers `/replan` on load-bearing divergence. |
| `/promote [item]` | No-arg: end-of-work full pass (promote significant items → `decisions/`, rewrite proposal to match reality, archive scratchpad). With arg: single-item mid-work promote. Idempotent. |

## Typical flow

```text
/propose add-payments              # work/001-add-payments/ + proposal.md
/work                              # implementation begins, scratchpad live
   → /replan triggers on real     # work/001-add-payments/replan.md appended
/promote                           # end-of-work: decisions/, proposal rewritten, scratchpad archived
```

## File layout produced

```
<project-root>/
├── CLAUDE.md                       (your responsibility)
├── decisions/
│   └── NNN-<slug>.md               (written by /promote)
└── work/
    └── NNN-<slug>/
        ├── proposal.md             (written by /propose, rewritten by /promote)
        ├── replan.md               (written by /replan when needed)
        ├── scratchpad.md           (live during /work, replaced by a one-line marker at /promote)
        └── archive/
            └── scratchpad.md       (raw scratchpad moved here by /promote)
```

Numbering for `work/` and `decisions/` is independent — each layer grows at its own pace. Decision files link back to their work unit via a `Context:` field in the body.

## Setup

This plugin is pure markdown — no Python dependencies, no Playwright. The standard installer handles registration:

```bash
./install.sh minerva
```

Restart Claude Code (or run `/reload-plugins`) and the four commands are available in any project.
````

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_minerva.py::test_plugin_readme_lists_all_four_commands -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/minerva/README.md tests/test_minerva.py
git commit -m "docs(minerva): plugin README"
```

---

## Task 9: Run the full test suite

Verify nothing regressed in the financials tests and the full minerva suite is green.

- [ ] **Step 1: Run the entire test suite**

Run:
```bash
pytest -v
```
Expected: all tests pass — existing `test_browser.py`, `test_pull.py`, `test_storage.py` plus the new `test_minerva.py` (9 tests). Specifically:
- `test_plugin_json_exists_and_parses`
- `test_marketplace_lists_minerva`
- `test_marketplace_does_not_list_feature_cycle`
- `test_root_readme_mentions_minerva`
- `test_root_readme_does_not_mention_feature_cycle`
- `test_propose_command_exists_with_frontmatter`
- `test_replan_command_exists_with_frontmatter`
- `test_work_command_exists_with_frontmatter`
- `test_promote_command_exists_with_frontmatter`
- `test_plugin_readme_lists_all_four_commands`

If anything fails, stop and diagnose before moving on. Do not commit a workaround.

No commit — this step is verification only.

---

## Task 10: Install and smoke-test the plugin

The installer is the integration boundary. Run it and confirm the symlink, settings, and command discovery all line up.

- [ ] **Step 1: Run the installer**

Run from the repo root:
```bash
./install.sh minerva
```
Expected output (last lines):
```
✓ Linked minerva → /Users/<user>/.claude/plugins/minerva
✓ Enabled minerva@agent-marketplace in settings.json
✓ Marketplace agent-marketplace already registered
✓ Registered minerva@agent-marketplace in installed_plugins.json
✓ Linked marketplace → /Users/<user>/.claude/plugins/marketplaces/agent-marketplace

Done! Run /reload-plugins in Claude Code to activate. Commands available:
  /promote
  /propose
  /replan
  /work
```

If the four commands aren't listed, the `commands/*.md` files weren't picked up — diagnose before continuing.

- [ ] **Step 2: Verify the symlink resolves**

Run:
```bash
ls -la ~/.claude/plugins/minerva && ls ~/.claude/plugins/minerva/commands/
```
Expected: symlink points at `<repo>/plugins/minerva`; `commands/` lists all four `.md` files.

- [ ] **Step 3: Verify settings.json has minerva enabled**

Run:
```bash
python3 -c "import json; s = json.load(open('$HOME/.claude/settings.json')); print(s.get('enabledPlugins', {}).get('minerva@agent-marketplace'))"
```
Expected: `True`.

- [ ] **Step 4: Verify installed_plugins.json has the entry**

Run:
```bash
python3 -c "import json; ip = json.load(open('$HOME/.claude/plugins/installed_plugins.json')); print('minerva@agent-marketplace' in ip['plugins'])"
```
Expected: `True`.

No commit — installation is local state.

---

## Self-Review

(Performed after writing this plan; issues fixed inline before handoff.)

**Spec coverage check** — every spec section maps to at least one task:

| Spec section | Task(s) |
|---|---|
| File layout | Tasks 1, 4–8 (creates all listed paths) |
| `/propose <slug>` behavior | Task 4 |
| `/replan [target]` behavior | Task 5 |
| `/work [target]` behavior | Task 6 |
| `/promote [item]` both modes + idempotency | Task 7 |
| Decision/proposal/scratchpad/replan templates | Tasks 4, 5, 7 (templates embedded in command bodies) |
| Plugin layout + plugin.json | Task 1 |
| Marketplace registration | Task 2 |
| Numbering rules (independent, max+1, 3-digit) | Tasks 4, 5, 7 (encoded in command bodies) |
| Target resolution (exact → substring → most-recent) | Tasks 5, 6, 7 (encoded in each command body) |
| Brainstorm flow shared by /propose and /replan | Tasks 4, 5 (encoded in command bodies) |
| Non-goals (no init, no grep, no auto-CLAUDE.md) | Task 4 (no init step), absence elsewhere |
| Removing feature-cycle | Task 0 |

**Placeholder scan:** none. Every step has either exact content or an exact command + expected output.

**Type consistency:** command file names (`propose.md`, `replan.md`, `work.md`, `promote.md`) match across tasks and tests; the `_read_command` test helper introduced in Task 4 is reused in Tasks 5–7. JSON field names match the spec. The marketplace entry source path `./plugins/minerva` matches the directory created in Task 1.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-18-minerva-plugin.md`. Two execution options:

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — execute tasks in this session using `executing-plans`, batch execution with checkpoints.
