# Proposal: close-remaining-loose-ends

**Date**: 2026-08-11
**Status**: Draft
**Base**: `origin/main`

## Goal

Close every open item left by `2026-08-11-close-silent-reference-gaps`, and where an item
has a *cause* rather than just a symptom, remove the cause.

## Why

The previous unit shipped seven fixes and closed with five named open items. Three more
things have since become known — one from a peer session that ran the fixed code against a
real 637-entry corpus, two surfaced by reviewing this unit's own plan.

The items divide into two kinds, and the split is what makes them one unit:

**Things the tooling does not tell the operator.** A CI job that silently skips test
modules; a reconciliation step that reports "skipping" and strands entries; a migration
that re-dates a malformed directory without saying so; an upgrade that changes a metric
everyone was comparing against. Same theme as the previous unit
([[2026-08-11-pattern-a-gate-blind-to-what-it-checks]]).

**One genuinely new capability** — resolving bare `[[NNN]]` shorthand — which the user
asked for explicitly after being told it roughly doubles the unit's scope.

### The peer's field report

The peer confirmed the previous unit's fixes against their real corpus (idempotence,
shorthand reporting matching their ground truth item-for-item, verification grep
6,005 → 3 with all three legitimate). Two findings from it change what this unit must do:

1. **Defect 7 corrupted their corpus on a *single* run, not a re-run.** Three work units
   created after the date convention landed were already in date form when they migrated,
   so `2026-08-10-x` became `2026-08-10-08-10-x`. The bug is already fixed, but the
   lesson is not addressed: **the dry run displayed the corruption and it was still
   missed** — 3 bad rows among 552, where the corrupted form is visually almost identical
   to a correct one. "Inspect the plan" is not a control at that size.
2. **The unified edge model moved their finding count from 41 to 59.** The extra 18 were
   always real and merely unreportable, so the change is correct — but they had reported
   the migration "exactly finding-neutral, 41 both sides" and merged partly on that basis,
   then got 0 findings before merge and 9 after on byte-identical content. Nothing in the
   repo warns an upgrader that this number is expected to rise.

## Approach

### 1. Delete the dead tests; let CI run bare `pytest`

`tests/test_browser.py`, `tests/test_storage.py` and `tests/test_pull.py` test the
`financials` plugin, **deleted in `20d32e0` (PR #7)**. `git ls-files plugins/financials`
returns zero tracked files; only stray `__pycache__` survives on disk. `conftest.py` still
inserts the now-nonexistent `plugins/financials/scripts` onto `sys.path`.

Delete all three, drop the dead `conftest.py` line, and replace `evals.yml`'s hand-
enumerated module list with a bare `pytest tests/`. Verified: bare `pytest` passes 459.

**This dissolves a documented constraint rather than working around it.**
[[2026-06-11-constraint-ci-test-enumeration-explicit]] exists *only* because bare `pytest`
aborted on these three files. Its failure mode is silent — a new module simply never runs
— and the previous unit was bitten by exactly that, shipping
`tests/test_skill_snippets.py` dark to CI until a follow-up commit caught it. Removing the
cause is strictly better than the guard test the alternative would need, so the entry is
**superseded**, not merely amended.

### 2. Reconciliation: fix the misdiagnosis *and* the silence

`cleanup/references/reconciliation.md` treats a non-fast-forward push to
`minerva/reconcile` as "another reconciliation won the race — skip". In a squash-merging
repo that is usually false: the reconcile branch's own commit never lands on the default
branch and GitHub does not delete the branch, so the *next* run diverges from a stale ref
with no concurrency involved. Hit for real on 2026-08-11.

Two changes, because the review found the second one:

- **Diagnose before concluding.** A race has an **OPEN** reconcile PR; a stale branch has
  none. Check that first, and on the stale path delete the merged remote branch and
  re-push rather than force-pushing (the `NEVER --force` rule protects an open PR's head,
  and there isn't one) — behind user authorization, since it mutates a shared ref.
- **The skip branch must not be silent.** It currently prints "another run is in flight,
  skipping" and exits 0 without populating `Pending, NOT catalogued` — the identical
  silent-deferral shape the step above it was already patched for, citing
  [[2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption]]. Under the
  corrected diagnosis entries could still strand invisibly, just for a different reason.

### 3. Bare `[[NNN]]` resolution — opt-in, fail-closed, and refusing by default

Bare shorthand names an entry by number with no slug. Before a rename a reader resolves it
with `ls .minerva/knowledge/139-*`; after one the number is in no filename at all. The peer
saw 563 across 185 files and resolved 557 **by hand**.

Naive resolution is refuted by their data: of 23 cases where a number named exactly one
entry, **~6 meant something else** — usually the same-numbered *work unit*.

- **Default unchanged.** Counted and reported, never rewritten. Resolution requires
  `--resolve-shorthand`.
- **Fail-closed precondition.** Resolution is sound *only* within a single pass over a
  fully-legacy corpus. Once anything is renamed its legacy id leaves the filesystem, so
  the entry-vs-work-unit collision becomes undetectable and a reference that meant a
  migrated work unit would resolve "safely" to the wrong entry. So: **if any entry or work
  dir already carries a date id, refuse all resolution** and say why. This is enforceable
  — `plan()` already knows what it skipped as already-migrated.
- **Group by legacy id explicitly.** `entries`/`work` are keyed by full old stem, not by
  bare number, so this needs a real `{id: [stems]}` aggregation. It is not a dict lookup,
  and the distinction is load-bearing: this repo's own history has
  `001-gitignore-before-worktree.md` **and** `001-review-lens-ownership.md` — two entries
  that legitimately shared legacy id `001`.
- **Resolve only when** exactly one entry has the id **and** no work unit has it.
- **Refuse everything else**, with the reason distinguished (several entries share the id
  / a work unit also has it / no entry has it / the entry is undated) and per-occurrence
  file+line, because the report's job is to make hand-resolution cheap, not to eliminate
  it.
- **Surface it where the operator already is.** A flag nobody knows about is not a
  feature, so `migrate-fix`'s existing confirmation gate reports how many are resolvable
  and how many refused.

**Not automated:** the "correct slug written beside a wrong number" case. The slug lives in
surrounding prose, not in the reference, so there is no signal to key on. It becomes a
refusal a human resolves — which is how the peer actually worked.

### 4. `plan()` states what it skipped and what it changed

From the peer's sharpest finding: a plan output is a control only if the anomaly is
visually separable at the output's real size, and 3 corrupted rows among 552 are not.

- Report the count of already-migrated paths skipped.
- Report **date-shaped but calendar-invalid** ids (`2026-13-45-foo`) explicitly. This is
  the one still-open edge case from the previous unit: `is_date_id` rejects it, so the
  skip guard does not fire and it is silently re-dated. Behaviour is defensible; doing it
  silently is not.

### 5. The two stale `Draft` units get the real promote treatment

`2026-05-19-add-review-skill` and `2026-06-12-run-context-footprint-estimator` are
demonstrably shipped. **A `Status` edit alone would not fix the problem** — every
orchestrator's pre-flight treats a unit as in-flight when Status is `Draft` **OR** the
scratchpad is not the post-promote marker, and neither unit has an `archive/` or a marker.
So: archive each scratchpad, write the marker, and set `**Status**: Shipped (<date>)`
using the field spelling 51 of 52 proposals actually use.

Their `## Approach` sections are **not** rewritten. Promote reconciles Approach against
what shipped using the unit's own working context, which is long gone; inventing that
reconciliation would fabricate a record. The status line says the record was closed
retroactively.

### 6. An adoption note for the edge-model baseline shift *(added after the user's go-ahead)*

Named as an addition rather than folded in silently: this came from the peer *after* the
"continue on all 5" instruction. `migrate-fix` and `lint` gain a short note that the first
run after upgrading reports **more** findings, that the delta is previously-invisible
findings rather than new damage, and that any pending finding-count comparison must be
re-baselined.

### Also settled, without code changes

- **`MD_LINK_RE` stays un-anchored** (previous unit's review finding 4). It matches
  `WIKILINK_STEM_RE`'s existing whole-repo reach and is bounded by map-lookup-only; a test
  already pins the intent.
- **Peer verification is partial and recorded as such.** #4, #5 and #7 are confirmed on a
  real 637-entry corpus. #1, #2 and #3 cannot be — they need the pre-migration tree, and
  the peer has since repaired those defects by hand. Their offer to reconstruct it was
  declined: it is their user's repo and tokens to spend.

## Success criteria

1. `python3 -m pytest` (bare, no `--ignore`) passes from a clean checkout; CI runs it
   without an enumerated module list.
2. No reference to `plugins/financials` remains in `conftest.py`, `tests/`, or
   `.github/workflows/`.
3. [[2026-06-11-constraint-ci-test-enumeration-explicit]] is superseded, with a banner
   pointing at the entry that replaces it.
4. `reconciliation.md` diagnoses stale-branch vs. race by checking for an OPEN PR, and its
   skip path populates `Pending, NOT catalogued`.
5. With `--resolve-shorthand`: a bare id naming one entry **and** a same-numbered work unit
   is REFUSED; two entries sharing one legacy id is REFUSED; a partially-migrated corpus
   refuses **all** resolution; and only the provably-unambiguous case resolves.
6. Default behaviour is byte-identical without the flag — upgrading cannot start rewriting
   a corpus.
7. `plan()` reports already-migrated skips and calendar-invalid ids; `migrate-fix`'s gate
   surfaces resolvable/refused counts.
8. Both stale units satisfy the pre-flight in-flight predicate on **both** limbs: Status
   is not `Draft` **and** the scratchpad is the post-promote marker.
9. `migrate-fix` and `lint` document the finding-count rise after upgrade.
10. Regression fixtures for each behavioural change, each verified to fail before its fix;
    `knowledge_lint .minerva/knowledge` stays clean.

## Open questions

None blocking. One recorded for later: the orchestrators' pre-flight text says "a
`proposal.md` whose `## Status` is Draft", but 51 of 52 proposals use the inline
`**Status**:` field and only one uses a `## Status` heading — and `promote`'s own
`references/modes.md` says `## Status` too. The prose instruction and the corpus disagree.
It has not caused a miss (the reader is an LLM, which reads both), so it is a follow-up
rather than a fix bundled here.
