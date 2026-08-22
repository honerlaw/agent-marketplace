---
name: promote
description: Finalizes a minerva work unit's record — promotes durable knowledge to `.minerva/knowledge/`, rewrites `proposal.md` to match reality, and archives the scratchpad; forward-looking TODOs are filed as prioritized GitHub issues when the repo can host them and fall back to `followups.md` when it cannot, never silently discarded. Also captures a significant mid-work decision/bug/pattern immediately. Use when implementation is done and the record needs finalizing, when a review has completed and the scratchpad holds unpromoted notes, or when the user invokes `minerva:promote`. Idempotent.
---

Promote durable items from `scratchpad.md` to `.minerva/knowledge/`, and (in the end-of-work pass) reshape the work unit's persistent record to match what shipped.

## The heuristic

> **Artifacts get promoted, not just accumulated.** Apply this to every scratchpad entry: *would a new engineer (or new agent) joining the project in a year benefit from reading this?* Only concrete, past-tense facts qualify — things that happened, were decided, were fixed, or were discovered. If yes, promote. If no, discard (with the TODO escape hatch in Mode A step 4). Scratchpads almost always fail; concrete past-tense facts almost always pass; proposals are between.

## Target resolution

Same pattern used by `minerva:work`, `minerva:replan`, `minerva:review`, `minerva:ship`, `minerva:cleanup`. **Keep all six blocks in sync if you edit one.**

1. **Explicit argument** — slug or path. Look in both `.minerva/work/<date-slug>/` and `.minerva/worktrees/<date-slug>/.minerva/work/<date-slug>/`.
2. **Current-session context** — explicit mention in this session.
3. **Most-recently-modified across both locations** — scan `.minerva/work/*/` AND `.minerva/worktrees/*/.minerva/work/*/` by directory mtime — matching **both** id forms, since a digit-anchored glob misses date-named units.
4. **Ambiguity** → list candidates, ask.
5. **None found** → report and stop.

`minerva:promote "exponential backoff for retries"` (Mode B) — when the first argument matches a scratchpad block, Mode B kicks in on the resolved unit.

## Worktree addressing

After resolving the target and before reading or writing any files:

- **Do not call `EnterWorktree`** — minerva worktrees live under `.minerva/worktrees/`, which that tool does not reliably enter; the session's working directory stays the parent repo.
- If the resolved target's docs live at `.minerva/worktrees/<date-slug>/.minerva/work/<date-slug>/`, address the worktree explicitly: prefix every file path this skill reads or writes with `.minerva/worktrees/<date-slug>/`, and run every git command as `git -C .minerva/worktrees/<date-slug> …`. Relative paths resolve to the parent repo and silently misroute edits onto the wrong branch (see `.minerva/knowledge/008-constraint-enter-worktree-absolute-paths.md`).
- If the docs live only on the default branch (a shipped unit being promoted retrospectively), operate on the parent repo directly.

Knowledge files written by promote (`.minerva/knowledge/<YYYY-MM-DD>-<type>-<slug>.md`) must use the same prefix — written to `.minerva/worktrees/<date-slug>/.minerva/knowledge/…` so they're committed on the work-unit branch and merged into the default branch via the PR.

## Two modes

The full mode protocols — **Mode A (end-of-work)**, the default full-scratchpad partition, and **Mode B (single-item)**, the mid-work immediate promotion — live verbatim in `references/modes.md`. **Read it before executing either mode.** The knowledge-entry template (including the required `**Summary**` field), the add-only wiki-maintenance protocol, and entry naming live in `references/wiki-maintenance.md`. **Read it before writing any `.minerva/knowledge/` entry.** The two-path TODO disposition — the GitHub-issue capability probe, the `critical`/`high`/`medium`/`low` priority vocabulary, label bootstrap, the duplicate check, and the per-item fail-soft to `followups.md` — lives in `references/github-issues.md`. **Read it before disposing of any TODO you may keep.**

## Idempotency summary

- Mode A re-run: scratchpad marker → stops early.
- Mode B re-run on a marked block: existing knowledge file → stops early.
- Promote is **add-only**: it writes new `.minerva/knowledge/` entry files and touches no existing file in the corpus — not `index.md`, not the watermark, not a neighbor's `## Related` block, not a supersession banner. A work-unit branch's `.minerva/` footprint is therefore purely additions, which is what lets concurrent PRs merge without conflicting. The reverse direction of every cross-link, and every aggregate, is derived on the default branch — by `minerva:cleanup`'s reconciliation, or by the CI job that owns it in a repo that reconciles on merge. An entry's id is today's date (`date +%F`) — nothing is allocated, and a shared date is normal because identity is the full stem. A duplicate stem is the same path, so git conflicts on it rather than merging it silently. See [Wiki maintenance](#wiki-maintenance-add-only).

If a user manually edits the scratchpad to remove markers, re-running `minerva:promote` could duplicate entries. This is a known footgun; not defended against.

