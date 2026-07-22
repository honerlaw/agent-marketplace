---
name: lint-fix
description: Applies the deterministically-repairable subset of `minerva:lint` findings — MUTATES the `.minerva/knowledge/` wiki behind a confirmation gate (index watermark, stale catalog lines, wrong Type-section placement, missing reciprocal `## Related` links) via the tested `scripts/knowledge_fix.py`. Never touches entry bodies and never auto-fixes judgment calls (missing catalog summaries, broken links, contradictions/staleness) — those it surfaces to handle by hand. Use after a lint run when the user asks to apply the safe/reported fixes or auto-repair the wiki, or when they invoke `minerva:lint-fix`. The read-only companion is `minerva:lint`.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

Apply the mechanically-repairable fixes to the `.minerva/knowledge/` wiki, behind a
confirmation gate. `minerva:lint-fix` is the **mutating** companion to the read-only
`minerva:lint`: where `minerva:lint` reports drift, this skill repairs the subset
that is deterministically fixable. **All mutation happens inside the unit-tested
`scripts/knowledge_fix.py`** — this skill orchestrates and gates; it does not edit
files itself (its `allowed-tools` omits `Edit`/`Write`).

> This skill **changes files**. It is not read-only. Every change is shown as a
> plan and applied only after you confirm.

## Target

The `.minerva/knowledge/` corpus of the **current working tree**, resolved by the
fixer from `git rev-parse --show-toplevel` — the same per-branch semantics as the
unit-021 CI drift gate and `minerva:lint`.

## Step 1 — Plan (dry run, no writes)

Show what would change, via the fixer's `--dry-run`:

```bash
ROOT="$(git rev-parse --show-toplevel)"; PLUGIN_SCRIPTS=$(find -L "${HOME}/.claude/plugins/minerva" "${HOME}/.claude/plugins/cache/agent-marketplace/minerva" -maxdepth 2 -type d -name "scripts" 2>/dev/null | head -1); python3 "${PLUGIN_SCRIPTS:-$ROOT/scripts}/knowledge_fix.py" --dry-run "$ROOT/.minerva/knowledge"
```

It re-derives every edit from the detector's structured output (`parse_index` /
`parse_entry`), never from message text. The plan lists, per item: an `index.md`
rewrite (watermark / stale-line / Type-section / NNN-order) and/or per-entry
reciprocal-link additions, plus any `REFUSED` items (e.g. a forward `## Related`
label outside the closed vocabulary).

## Step 2 — Gate

Present the plan to the user and **wait for explicit confirmation** before applying.
If the plan is empty (`no mechanical fixes needed`), report that and stop.

## Step 3 — Apply

On confirmation, apply (the script **recomputes** the batch from the live corpus, so
the plan can't go stale between dry-run and apply):

```bash
ROOT="$(git rev-parse --show-toplevel)"; PLUGIN_SCRIPTS=$(find -L "${HOME}/.claude/plugins/minerva" "${HOME}/.claude/plugins/cache/agent-marketplace/minerva" -maxdepth 2 -type d -name "scripts" 2>/dev/null | head -1); python3 "${PLUGIN_SCRIPTS:-$ROOT/scripts}/knowledge_fix.py" "$ROOT/.minerva/knowledge"
```

The script applies the batch atomically and then re-runs the detector to verify the
corpus is clean. Report the result.

## What it fixes vs. surfaces

**Auto-fixed (deterministic, gated):**
- **Index watermark** out of sync with the max entry NNN.
- **Stale catalog line** — an `index.md` entry whose NNN has no file.
- **Wrong Type section** — a catalog line under the wrong `## Type` header (relocated
  verbatim, summary preserved, NNN-sorted).
- **Missing reciprocal** — a one-way `## Related` link; the reciprocal label is
  derived from the forward label (`builds on`→`see also`; `supersedes`↔`superseded
  by`; `contradicts`/`see also` symmetric). A supersession also writes the banner.

**Safety:** entry edits change only the `## Related` block / banner span (a
`body_complement` byte-identity guard aborts the run otherwise — knowledge 016);
`index.md` edits preserve the canonical skeleton (H1 + the four headers incl. the
empty `## Patterns`) and ascending-NNN order.

**NOT auto-fixed — surfaced for you to handle by hand:**
- **Missing catalog line** — needs a one-line summary (a judgment call).
- **Broken `## Related` link** — the target doesn't exist; remove it or create the entry.
- **Orphans / contradictions / stale claims** — the LLM-judged advisory dimensions
  from `minerva:lint`; advisory only, never auto-applied (knowledge 013).

## Out of scope

- Editing the frozen detector (`scripts/knowledge_lint.py`) or the read-only
  `minerva:lint` skill.
- Running in CI / auto-applying without the gate.
- Synthesis / `log.md` (Phase C).
