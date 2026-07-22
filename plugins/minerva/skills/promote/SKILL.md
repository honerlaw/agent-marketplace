---
name: promote
description: Finalizes a minerva work unit's record — promotes durable knowledge to `.minerva/knowledge/`, rewrites `proposal.md` to match reality, and archives the scratchpad; forward-looking TODOs are offered as `followups.md` or a new-proposal seed, never silently discarded. Also captures a significant mid-work decision/bug/pattern immediately. Use when implementation is done and the record needs finalizing, when a review has completed and the scratchpad holds unpromoted notes, or when the user invokes `minerva:promote`. Idempotent.
---

Promote durable items from `scratchpad.md` to `.minerva/knowledge/`, and (in the end-of-work pass) reshape the work unit's persistent record to match what shipped.

## The heuristic

> **Artifacts get promoted, not just accumulated.** Apply this to every scratchpad entry: *would a new engineer (or new agent) joining the project in a year benefit from reading this?* Only concrete, past-tense facts qualify — things that happened, were decided, were fixed, or were discovered. If yes, promote. If no, discard (with the TODO escape hatch in Mode A step 4). Scratchpads almost always fail; concrete past-tense facts almost always pass; proposals are between.

## Target resolution

Same pattern used by `minerva:work`, `minerva:replan`, `minerva:review`, `minerva:ship`, `minerva:cleanup`. **Keep all six blocks in sync if you edit one.**

1. **Explicit argument** — slug or path. Look in both `.minerva/work/<NNN-slug>/` and `.minerva/worktrees/<NNN-slug>/.minerva/work/<NNN-slug>/`.
2. **Current-session context** — explicit mention in this session.
3. **Most-recently-modified across both locations** — scan `.minerva/work/NNN-*/` AND `.minerva/worktrees/NNN-*/.minerva/work/NNN-*/` by directory mtime.
4. **Ambiguity** → list candidates, ask.
5. **None found** → report and stop.

`minerva:promote "exponential backoff for retries"` (Mode B) — when the first argument matches a scratchpad block, Mode B kicks in on the resolved unit.

## Worktree addressing

After resolving the target and before reading or writing any files:

- **Do not call `EnterWorktree`** — minerva worktrees live under `.minerva/worktrees/`, which that tool does not reliably enter; the session's working directory stays the parent repo.
- If the resolved target's docs live at `.minerva/worktrees/<NNN-slug>/.minerva/work/<NNN-slug>/`, address the worktree explicitly: prefix every file path this skill reads or writes with `.minerva/worktrees/<NNN-slug>/`, and run every git command as `git -C .minerva/worktrees/<NNN-slug> …`. Relative paths resolve to the parent repo and silently misroute edits onto the wrong branch (see `.minerva/knowledge/008-constraint-enter-worktree-absolute-paths.md`).
- If the docs live only on the default branch (a shipped unit being promoted retrospectively), operate on the parent repo directly.

Knowledge files written by promote (`.minerva/knowledge/NNN-<type>-<slug>.md`) must use the same prefix — written to `.minerva/worktrees/<NNN-slug>/.minerva/knowledge/…` so they're committed on the work-unit branch and merged into the default branch via the PR.

## Two modes

The full mode protocols — **Mode A (end-of-work)**, the default full-scratchpad partition, and **Mode B (single-item)**, the mid-work immediate promotion — live verbatim in `references/modes.md`. **Read it before executing either mode.** The knowledge-entry template and the wiki-maintenance protocol (index catalog line, `## Related` cross-references, watermark bump) live in `references/wiki-maintenance.md`. **Read it before writing or editing any `.minerva/knowledge/` entry.**

## Idempotency summary

- Mode A re-run: scratchpad marker → stops early.
- Mode B re-run on a marked block: existing knowledge file → stops early.
- Knowledge files are **append-only in their body** — auto-incremented NNN guarantees each new entry is unique, and the body of an existing entry (its `# H1`/metadata block and the `## Context` / `## Finding` / `## Implications` sections) is **never rewritten**. The *only* machine-managed mutable surfaces are the delimited `## Related` block and the supersession-banner span — both edited idempotently by the [Wiki maintenance](#wiki-maintenance-index--cross-references) step. This narrowed invariant is what makes bidirectional cross-references safe: promoting a new entry can add a backlink to an older one without ever touching that older entry's recorded finding.

If a user manually edits the scratchpad to remove markers, re-running `minerva:promote` could duplicate entries. This is a known footgun; not defended against.

