# Proposal: backfill-followups-to-issues

**Date**: 2026-08-22
**Status**: Shipped (2026-08-22)
**Base**: `origin/main`

## Goal

Ship `minerva:backfill-followups` — a reusable skill that migrates a project's existing
`.minerva/work/*/followups.md` backlog into GitHub issues using the protocol shipped in
`minerva:promote`'s `references/github-issues.md`, **assessing whether each item is still
relevant before filing it** — and run it on this repo.

## Why

`minerva:promote` now files *newly* kept TODOs as prioritized issues. Existing files were
deliberately left alone, which is issue #69. This repo holds 24 `followups.md` files (2
empty, 70 top-level bullets), and the backlog's own record says why that matters:
`2026-08-11-close-the-followups` observed that much of it had already shipped and that
**nothing marks a followup as done**, so every scoping pass re-reads all of it to re-derive
the same answer. Reading the corpus for this proposal confirmed it immediately — the Phase B
`minerva:lint` skill, the Phase B.3 fix-applier, Phase C synthesis, and the four-rung ladder
prose are all shipped, and one item is already struck through by its own author.

A GitHub issue has the state the file lacks. The relevance pass is what stops the migration
from turning a stale file backlog into a stale *issue* backlog.

## Approach

A **seven**-step skill protocol (a `Report` step joined the six designed here). Steps 1-4 are
**read-only**; step 4 is a hard gate; only steps 5-6 mutate, and step 7 reports. That plan→confirm→apply shape is deliberate and mirrors `migrate-fix`'s own
internal structure. This is **one** skill rather than the `lint`/`lint-fix`,
`migrate`/`migrate-fix` detector-plus-applier *pair* because those are recurring
health-checks a project re-runs forever, whereas this is a **one-time migration** per
project — splitting it would ship a detector whose only consumer is its own applier.

1. **Discover** — enumerate `.minerva/work/*/followups.md` plus `.minerva/worktrees/*/`
   copies. Deterministic. Degrades silently when `worktrees/` is absent or empty.
2. **Extract items** — the LLM reads each file and identifies discrete actionable items.
   Explicitly **not** a regex: the corpus mixes prose bullets, `- [ ]` checklists,
   paste-blurbs and `## Decided: skip` sections. **Atomization rule:** one item = one
   top-level bullet, or one `##` subsection that proposes a distinct action. A bullet
   offering two alternative fixes for one problem stays **one** item. Anything judged a
   non-item is recorded with a reason, never silently dropped.
3. **Assess relevance** — classify each item, with **cited evidence** (a file path plus a
   grep hit, a `.minerva/knowledge/` entry, or a git log line):
   - `open` — still real. File it.
   - `manual` — needs a human acting outside the repo (submit a web form, re-check a
     third-party listing). **No evidence source can ever verify these**, so they are
     grouped at the gate for a single keep-or-drop call rather than auto-filed.
   - `shipped` — the work exists now. Cite where.
   - `obsolete` — the reason it existed is gone. Say why.
   - `not-an-item` — a paste-blurb, a header, an author's explicit skip decision.
   - `unsure` → **treated as `open` and filed.** The skill fails **open**: a wrongly-filed
     issue is closed in one click; a wrongly-dropped item is gone silently.
4. **Gate — batched per source file.** Present each file's items with classification,
   evidence and proposed priority; accept subset approval. Nothing is created before this.
   Batching is deliberate: a single 70-row table invites rubber-stamping, which would
   forfeit the gate's whole value.
5. **File** — delegate verbatim to `promote/references/github-issues.md` (capability probe,
   label bootstrap, duplicate check, per-item fail-soft, `followups.md` fallback). No `gh`
   mechanics are restated here.
6. **Record** — **append** a `## Backfill disposition (YYYY-MM-DD)` section to each
   `followups.md`, one line per item, carrying the item's **verbatim first line** as its
   stable anchor plus its disposition (`→ #NN` / `shipped (…)` / `obsolete (…)` /
   `manual` / `not-an-item`). Never rewrite an item line and never delete the file —
   `2026-06-02-constraint-promote-narrowed-never-overwrite` makes append-only the precedent.

**Idempotency.** `github-issues.md`'s duplicate check is three-tier, and its tier 2 is "the
unit's `proposal.md` `## Deferred work` section". Backfill spans ~20 source units and does
not own their proposals, so **backfill's tier-2 ledger is the `## Backfill disposition`
section instead** — one of three documented divergences from that protocol (the others being
cosmetic: the back-link names this skill, and a kept `manual` item says no code change will
close it). The verbatim first line is what a re-run matches on, which is why step 2's
atomization rule has to be stated rather than left to taste.

A disposition is additionally **terminal** or **non-terminal**, and only terminal ones are
skipped on a re-run. `open (…) — not filed` is non-terminal and is re-offered every run —
including the case where the repo simply cannot host issues. Review caught that the original
"skip anything with a disposition line" rule would have stranded all 25 not-filed items
permanently, reproducing this skill's own target failure one layer up
([[2026-08-22-pattern-a-ledger-line-is-not-a-resolution]]).

### Rejected alternatives

- **Triage-only skill, filing delegated to `minerva:promote`.** Promote's TODO gate is
  scoped to one unit's scratchpad and its Mode A stops early on an already-promoted unit —
  and every one of these units is already promoted.
- **A one-off script, no skill.** The user asked for something usable on other projects.
- **Rewriting item lines in place.** Breaks the append-only precedent, produces noisy
  gate diffs, and leaves a re-run fuzzy-matching rewritten text instead of a stable anchor.

## Success criteria

1. `plugins/minerva/skills/backfill-followups/SKILL.md` exists, ≤9216 bytes, description
   ≤1024 chars in house style, with detail in `references/protocol.md`.
2. `references/protocol.md` specifies all six steps as runnable commands where mechanical,
   names the five dispositions plus the fail-open `unsure` rule, states the atomization
   rule, and names `publish-minerva-to-plugin-directories` as the worked heterogeneity
   example (blurb / `- [ ]` manual items / `## Decided: skip` in one file).
3. `evals/backfill-followups/contract.json` exists with non-vacuous anchors —
   `tests/test_skill_contracts.py` enumerates skill dirs and fails on a missing contract.
4. Catalog surfaces carry the skill: root `README.md`, `plugins/minerva/README.md`,
   `using-minerva/SKILL.md` body (the `cross_surface` surface), `pages/index.md` (enforced
   by `tests/test_site_catalog.py`), and `using-minerva/references/guide.md`.
5. `using-minerva/SKILL.md` stays within the 9216-byte budget — it currently sits at 9179,
   so the over-long `propose-ship-balanced` matrix row (514 bytes vs its sibling
   orchestrator rows at ~250) is trimmed to match before the new row lands.
6. The skill is run on this repo: every one of the 70 bullets reaches a disposition, issues
   are filed for `open` (and kept `manual`) items, and each `followups.md` carries its
   appended `## Backfill disposition` section.
7. No fenced block in the new skill is wired into `tests/test_skill_snippets.py` — it
   **executes** what it extracts, and these are mutating `gh` commands (issue #70).
8. The full test suite passes.

## Open questions

None blocking. Two calls are recorded rather than deferred: the per-item triage is the
highest-volume judgment here and falls outside this orchestrator's fixed reviewer gates, so
the completion-verification Verifier is pointed specifically at the `shipped`/`obsolete`
classifications — the only ones that can lose work — on top of the mandatory user gate and
the fail-open rule. Escalating the whole unit to `propose-ship-auto` was considered and
declined on that basis.

## Deferred work

- #85 — Let the pointer gate express a cross-skill reference (priority: low)

## Outcome

The skill was run on this repo. All 70 top-level bullets plus subsection items — 79
disposition lines across 24 files — reached an evidence-cited disposition:

| Disposition | Count |
|---|---|
| `shipped` | 24 |
| `obsolete` | 3 |
| `not-an-item` | 9 |
| `open` | 33 (11 filed as #74-#84, 25 recorded non-terminal, 3 of them `manual`) |

Roughly a third of the backlog was already done — `minerva:lint`, `lint-fix`, `synthesize`,
the Phase B.3 fix-applier, the four-rung ladder prose, `pages.yml`, the CI-watch cadence
re-derivation, and the eight stale in-flight units. Stem identity dissolved *both*
duplicate-NNN items rather than fixing them. Two items were already struck through by their
own authors, and `close-the-followups`' "the backlog is stale" item — which proposed exactly
this tool — resolved to `shipped (this run)`.
