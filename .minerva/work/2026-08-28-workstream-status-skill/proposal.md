# Proposal: workstream-status-skill

**Date**: 2026-08-28
**Status**: Shipped (2026-08-28)

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
enrichment — the same split `work_status.phase_progress()` already uses, where the module is
a pure reader and the caller passes the `git`-derived facts in.

### What shipped

**`plugins/minerva/scripts/workstream_status.py`**, with `scripts/workstream_status.py` as a
**symlink** to it. The `scripts/` entries in this repo are symlinks (git mode `120000`), not
copies — `diff -q` follows them and reports IDENTICAL, which is what made an earlier draft of
this proposal specify a "mirrored copy" deliverable.

`workstream_status(root, merged_branches=()) -> {units, counts, knowledge}`. Pure filesystem
reads: no subprocess, no network, no git, so its tests need no repo, auth or fixtures.

- **Walk.** `<root>/.minerva/work/*/` then `<root>/.minerva/worktrees/*/.minerva/work/*/`,
  deduped by slug with the main-tree record winning by glob order. The second glob is what
  finds a unit that exists only on an unmerged branch.
- **Per unit.** `slug`, every key `unit_state()` returns (imported, never re-derived),
  `worktree_present`, `stage`, `phases`, and `phase_progress(...)` verbatim. Every phase branch
  name is resolved through `phase_branch()`.
- **`stage`** — `draft` / `in-progress` / `promoted` / `shipped`, a ladder whose rung order is
  load-bearing. `shipped` requires **both** the declared Status and the promote marker: those
  are written in two non-atomic steps, and reading Status alone renders a half-promoted unit as
  done while `in_flight` still counts it live.
- **Knowledge block** via `synthesis_status()` and `lint_knowledge()`.

**`plugins/minerva/skills/status/SKILL.md`** (7.8 KB) **+ `references/tables.md`**, carrying
the three table shapes and the phase-aware **Next step** mapping. It resolves two roots
separately: `PLUGIN_SCRIPTS` plugin-cache-first for the module, and `WORK_ROOT` as the
**primary checkout** for the corpus.

**Tests** — `tests/test_workstream_status.py`, 24 cases. `evals/status/contract.json`, and the
four catalog surfaces.

### What changed from the plan

- **The phase column shipped in the first cut.** The plan was to defer it while PR #101 was
  unmerged; #101 merged mid-intake, so `read_phases` / `phase_progress` / `phase_branch` were
  available and a table that misreports a phased unit was never shipped.
- **Merged-branch sourcing became precedence, not a list of commands.** The plan named
  `git branch --merged` among the enrichment reads. The live smoke run showed it reports a
  squash-merged phase as unmerged, and it also counts a freshly created zero-commit branch as
  merged. Settled on `minerva:cleanup`'s documented order — merged-PR query first, `git branch
  --merged` only as a fallback, never a union. Promoted as
  `2026-08-28-constraint-git-branch-merged-is-wrong-in-both-directions`.
- **The root-resolution rationale is cited, not restated.** The `2026-08-27-deferral-cost-model`
  unit promoted `2026-08-28-constraint-worktree-reaching-paths-anchor-to-the-primary-checkout`
  while this work was in flight, covering the same `--show-toplevel` trap and the relative-`.`
  wrapper. The skill points at it rather than duplicating it.

### What the smoke run and review changed

Two defects only the live corpus could show, both found before review:

- **`worktree_present` read `true` for all 65 units.** It was set from the worktree glob, and
  every linked worktree carries the whole committed `.minerva/work/` history, so one worktree
  makes every unit reachable. It is now a directory test. Promoted as
  `2026-08-28-bug-a-worktree-glob-sees-every-unit-in-the-project`.
- **`git branch --merged` alone misreported phase 1 as unmerged** (above).

Review returned six findings — four fixed, two declined:

- **(high) `_has_scratchpad_body` tested line shapes, not a header prefix**, so a scratchpad
  whose notes are written as blockquotes read as an untouched draft — under-reporting arriving
  through the check written to prevent it. Header is now the leading H1 plus the first
  contiguous blockquote run.
- **(medium) `_stage` read `shipped` off Status alone** — fixed as described above.
- **(medium) a vacuous `isinstance(lint_errors, int)` assertion**, replaced with a corpus that
  produces a real dangling `## Related` link and a real broken overview link.
- **(low) no coverage for the blockquote-body case** — added.

All three fixes were mutation-tested: each revert turns CI red.

Declined, with reasons recorded: knowledge entries are parsed twice per call (85 files; the
alternative contradicts `2026-08-09-pattern-read-authored-metadata-from-where-it-is`), and
`read_text` is unguarded (a crash is loud, and this module's stated enemy is a *silently*
falsely-clean table — a per-file `try/except` would convert a visible abort into the invisible
failure being guarded).

**Rejected alternatives.**
*Everything in the script, including subprocess `git`/`gh`* — no minerva reader module shells
out; that is what lets their tests run with no repo, network or fixtures, and it would
re-implement in Python the `gh` capability probe that already exists as prose.
*Skill-only, no new script* — the walk, the dedupe rule and the stage mapping would live only
in prose: untestable, and the shape
`2026-08-11-pattern-an-unenforced-constraint-is-aspirational` names.

## Deferred work

- Reclaim byte budget in `using-minerva/SKILL.md` (9198 / 9216) so the next skill added can
  carry a real catalog row — filed as
  [#107](https://github.com/honerlaw/agent-marketplace/issues/107) (`priority: medium`).

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
  reports the phased `2026-08-27-deferral-cost-model` unit's phase state. (That unit's
  phase 2 merged mid-run, so the verified reading is `merged 2 of 2, complete: true` with
  both branch names resolved through `phase_branch()`, and its correct exclusion from the
  active-units table — rather than the mid-progress reading the criterion anticipated.)

## Open Questions

- Whether the primary checkout being **stale relative to `origin`** should be reported.
  The walk reads files, so it reports whatever the checkout is on; a not-yet-pulled main
  can show a merged unit as unshipped. Current answer: the skill runs `git fetch` before
  the enrichment reads and prints the checkout's HEAD alongside `origin/<default>` in the
  rollup, so a stale tree is visible rather than silently misreported.
