# Proposal: workstream-status-skill

**Date**: 2026-08-28
**Status**: Draft

## Goal

A new read-only skill `minerva:status` that prints the current overall state of the
project's minerva workstream as a small set of markdown tables — which work units are in
flight and what each one's **next lifecycle step** is, knowledge-wiki health, and the
deferred backlog — so a human or an agent resuming the project can orient in one screen
without opening `.minerva/` by hand.

## Why

No single surface answers "where does everything stand?". Today that means reading every
`.minerva/work/*/proposal.md` `**Status**` field, cross-checking `git branch` and
`gh pr list`, skimming `.minerva/knowledge/index.md`, and listing open `minerva:followup`
issues — five reads whose join exists only in someone's head.

The state is already computable and already single-sourced. `work_status.unit_state()` is
the in-flight predicate four SKILL.md files were once restating in prose;
`work_status.read_phases`/`phase_progress` (shipped in #101) own phase topology;
`synthesis_status()` and `knowledge_lint.lint_knowledge()` own wiki health. Nothing
aggregates them, so the one question a resuming agent actually asks — *what should I do
next?* — is the one question the corpus cannot answer directly.

The table's **Next step** column is the point of the skill. A status dump that reports
state without naming the action is the shape
`2026-08-22-pattern-a-ledger-line-is-not-a-resolution` warns about: a record that marks
work as handled without separating decided-and-done from decided-to-wait buries it.

## Approach

A hermetic aggregator script wrapped by a prose skill that layers opportunistic `git`/`gh`
enrichment — the same split `work_status.phase_progress()` already uses, where the module
is a pure reader and the caller passes in the `git branch --merged` result.

### 1. `plugins/minerva/scripts/workstream_status.py` (+ a `scripts/` symlink)

`scripts/*.py` in this repo are **symlinks** into `plugins/minerva/scripts/`, not copies —
verified via `git ls-tree` (mode `120000`). The real file lands in the plugin; `scripts/`
gains one symlink, matching every sibling module.

Public API: `workstream_status(root, merged_branches=()) -> dict`. Pure filesystem reads —
no subprocess, no network — so its tests need no repo, no auth and no fixtures.

- **Walk.** `<root>/.minerva/work/*/` **and** `<root>/.minerva/worktrees/*/.minerva/work/*/`.
  Deduped by slug: the main-tree record wins (it is the authoritative post-merge copy) and
  the unit is additionally flagged `worktree_present`.
- **Per unit.** `slug`, every key `unit_state()` already returns (imported, never
  re-derived), `worktree_present`, `stage`, and — for a unit declaring `## Phases` —
  `phase_progress(read_phases(...), merged_branches, slug)` verbatim.
- **`stage`** is a filesystem-only 4-value vocabulary with an explicitly named
  discriminator for each boundary:
  | Stage | Discriminator |
  |---|---|
  | `shipped` | `unit_state()["status"]` starts with `Shipped` |
  | `promoted` | `unit_state()["promoted"]` is true (the tolerant marker read) |
  | `in-progress` | not promoted, and `scratchpad.md` has content past the header block |
  | `draft` | not promoted, and the scratchpad is header-only or absent |
  The `draft`/`in-progress` boundary is the one the corpus does not already expose, so its
  signal is named here rather than left to the implementation: `minerva:propose` writes a
  header-only scratchpad and `minerva:work` appends to it, which makes "has a body" the
  authored declaration that work started. It is unit-tested in both directions.
- **Knowledge block.** Entry count by type, `synthesis_status()` (`unsynthesized` /
  `link_rot` / `overview_exists`), and the `lint_knowledge()` finding count — each via its
  existing importable API.
- A `main()` CLI prints the dict as JSON; the skill consumes the importable API.

### 2. `plugins/minerva/skills/status/SKILL.md` (+ one `references/` file)

Resolves two **separate** roots, because they answer different questions:

```bash
WORK_ROOT="$(cd "$(dirname "$(git rev-parse --git-common-dir)")" && pwd)"
PLUGIN_SCRIPTS=$(find -L "${HOME}/.claude/plugins/minerva" "${HOME}/.claude/plugins/cache/agent-marketplace/minerva" -maxdepth 2 -type d -name "scripts" 2>/dev/null | head -1)
```

**`WORK_ROOT` deliberately does not use `git rev-parse --show-toplevel`**, and the skill
says so in prose so a later editor cannot "correct" it back
(`2026-06-06-pattern-rejected-alternative-reinvented-at-runtime`). Every other minerva
skill anchors on `--show-toplevel` for *per-branch* semantics, which is right when the
target is the worktree-local `.minerva/knowledge/`. It is wrong here: inside a linked
worktree `--show-toplevel` returns the worktree, which contains no `.minerva/worktrees/`
directory at all, so a status walk invoked from a worktree — where `minerva:work` sessions
live, and exactly the "resuming agent" case in the Goal — would silently report every
sibling unit as absent. A falsely-clean status table renders as "nothing in flight", which
is the worst failure available to this skill.

The `cd … && pwd` wrapper is not decoration: bare `dirname "$(git rev-parse
--git-common-dir)"` returns `.` from the primary checkout and `../../..` from a
subdirectory, absolute only from inside a linked worktree. Verified from all three.

`PLUGIN_SCRIPTS` follows the plugin-cache-first rule from
`2026-06-03-constraint-skill-wraps-script-via-importable-api` verbatim, `find -L` included.

The skill then runs three **read-only** enrichment commands behind the capability probe
`minerva:promote` owns — `git branch --list`, `git branch --merged <default>`, and
`gh pr list --state all --json number,state,headRefName` — and joins them to units.

**The join resolves branch names through `phase_branch()`, never string equality.** A
phased unit ships one PR per phase: phase 1 on the bare `<date-slug>`, phases 2+ on
`<date-slug>-phase-N`. `cleanup/references/phased-units.md` is explicit that merge
detection is exact-match on `<date-slug>` and "can never match a `-phase-N` branch", and
that the topology must be asked of the module, never inferred from the name.

### 3. Ownership split for **Next step**

The script owns the coarse, always-available `stage` and the phase arithmetic. The skill
layer refines them into the action using the enrichment facts when present. When `gh` is
unavailable the PR column renders `—` and Next step falls back to the stage-only mapping:
coarser, never wrong.

The mapping is phase-aware, because the naive rule is falsified by the live corpus:

- `phased` and not `complete` → **`minerva:work` on phase N+1** — *not* cleanup. A
  phase-1-merged unit keeps its worktree **by design**; `phased-units.md` defers teardown
  until the final phase because removing the worktree between phases destroys the
  workspace the remaining phases are cut in. `worktree_present` therefore does **not** mean
  cleanup is overdue.
- `promoted`, no open PR → `minerva:ship`
- PR `MERGED`, worktree present, unphased or `complete` → `minerva:cleanup`
- `in-progress`, not promoted → `minerva:review` then `minerva:promote`
- `draft` → `minerva:work`

### 4. Tables

Three, in one screen: **Active units** (the units that are not finished — slug, stage,
phase, branch, PR, next step), a **rollup** (totals, worktrees present, open followup
issues), and **knowledge health** (entries, lint findings, unsynthesized, link rot).
Finished units are counted in the rollup, not listed — a 64-row table is not consumable.

### 5. Supporting surfaces

`tests/test_workstream_status.py` (CI runs the whole `tests/` dir, so no enumeration step),
`evals/status/contract.json`, and the four catalog surfaces that tests and convention
force: root `README.md`, `plugins/minerva/README.md`, `pages/index.md` between the
`skills-catalog` markers (under *The utilities*), and `using-minerva/SKILL.md`.

**Rejected alternatives.**
*Everything in the script, including subprocess `git`/`gh`* — no minerva reader module
shells out; it is what lets their tests run with no repo, network or fixtures, and it would
re-implement in Python the `gh` capability probe that already exists as prose. The newest
code in this exact area (`phase_progress`) takes the merged set as an argument for
precisely this reason.
*Skill-only, no new script* — the walk, the dedup rule and the stage mapping would live
only in prose: untestable, and the shape
`2026-08-11-pattern-an-unenforced-constraint-is-aspirational` names. A 64-unit corpus
formatted by eyeball is where a silent miscount lands.
*Deferring the phase column until #101 merged* — moot; #101 merged mid-intake, so the
column ships in the first cut rather than shipping a table that misreports the one unit
currently in flight.

## Success criteria

- `plugins/minerva/scripts/workstream_status.py` exists, exposes
  `workstream_status(root, merged_branches=())`, and imports `unit_state`, `read_phases`,
  `phase_progress` and `phase_branch` from `work_status` rather than re-deriving any of
  them; `scripts/workstream_status.py` is a **symlink** to it (git mode `120000`).
- The walk covers both `.minerva/work/*/` and
  `.minerva/worktrees/*/.minerva/work/*/`, dedupes by slug with the main-tree record
  winning, and sets `worktree_present`.
- `stage` returns each of `draft` / `in-progress` / `promoted` / `shipped`, with the
  `draft` vs `in-progress` boundary decided by scratchpad content past the header.
- A phased unit's record carries `phase_progress` output; phase branch names are resolved
  through `phase_branch()` and never rebuilt as strings.
- `tests/test_workstream_status.py` covers: dedup across the two roots, each of the four
  stage values, `worktree_present`, a phased unit mid-progress, an empty `.minerva/`, and a
  malformed unit directory. The full pytest suite passes.
- `plugins/minerva/skills/status/SKILL.md` exists, is ≤9216 bytes, states in prose why
  `WORK_ROOT` uses `--git-common-dir` instead of `--show-toplevel`, uses the absolutized
  `cd … && pwd` form, carries the `PLUGIN_SCRIPTS` plugin-cache-first resolution, and
  states that `worktree_present` on an incomplete phased unit is not a cleanup signal.
- Every `references/` file it adds is pointed to from `SKILL.md` on a line carrying a read
  directive (the orphan check in `tests/test_skill_budget.py`).
- `evals/status/contract.json` exists and `tests/test_skill_contracts.py` passes,
  including the `cross_surface` clause for all three enforced surfaces.
- `minerva:status` appears in root `README.md`, `plugins/minerva/README.md`,
  `pages/index.md` between the `skills-catalog` markers, and `using-minerva/SKILL.md`;
  `tests/test_site_catalog.py` passes.
- Running the skill's own command against this repo prints the three tables and correctly
  reports the in-flight `2026-08-27-deferral-cost-model` unit's phase state.

## Open Questions

- Whether the primary checkout being **stale relative to `origin`** should be reported.
  The walk reads files, so it reports whatever the checkout is on; a not-yet-pulled main
  can show a merged unit as unshipped. Current answer: the skill runs `git fetch` before
  the enrichment reads and prints the checkout's HEAD alongside `origin/<default>` in the
  rollup, so a stale tree is visible rather than silently misreported.
