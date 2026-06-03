# Proposal: knowledge-lint-fix

**Date**: 2026-06-03
**Status**: Shipped (2026-06-03)

> **Phase B.3** of the LLM-wiki effort — the gated, span-confined fix-applier.
> Completes Phase B (B.1 = detector, unit 021; B.2 = read-only lint skill, unit 022).
> Phase C (synthesis / `log.md`) remains.

## Goal

Add the gated, idempotent **fix-applier** for the knowledge wiki: a new mutating
`minerva:lint-fix` skill (separate from read-only `minerva:lint`, per
[[020-decision-minerva-lint-read-only]]) that, behind a confirmation gate, applies
the *deterministically-repairable* findings the detector surfaces, via a
deterministic `scripts/knowledge_fix.py`. **All mutation lives in the unit-tested
script**, never in LLM `Edit`.

## Why

B.1 detects drift (the CI gate), B.2 reports it (read-only `minerva:lint`). Repairing
it is still manual. B.3 closes the loop with safe, gated, deterministic fixes for the
mechanical findings — keeping the corpus-mutating logic in a tested script bound by
the [[016-constraint-promote-narrowed-never-overwrite]] body-append-only invariant
and the [[019-constraint-knowledge-span-model-single-sourced]] span module.

## Approach

### Two safety models — one per object type (NOT one blanket "span-confined")

The detector's findings split across two object types that require different,
separately-tested guards:

- **Entry edits** — only the **missing-reciprocal** family edits knowledge entries
  (inserting a reciprocal `## Related` line / supersession banner). Guarded by
  `body_complement` **byte-identity**: everything outside the `## Related` block and
  the banner span is byte-for-byte unchanged
  ([[016-constraint-promote-narrowed-never-overwrite]]).
- **Index edits** — the **watermark**, **stale-catalog-line**, and
  **wrong-Type-section** families edit `.minerva/knowledge/index.md`, which has *no*
  `## Related`/banner spans. Guarded by a separate **skeleton-preserving invariant**:
  the `# Knowledge index` H1, the four `## Decisions` / `## Bugs` / `## Patterns` /
  `## Constraints` headers (including the deliberately-empty `## Patterns`), and
  ascending-NNN order within each section are all preserved, and **no entry file is
  touched**. Verified by a round-trip test (`parse_index(fix(corpus))` is clean and
  the skeleton/order is preserved).

### 1. Single-source the entry-span editors (extends 019)

Move `add_related_link` / `add_supersede_banner` / `body_complement` from
`tests/test_promote_invariant.py` into a **new `scripts/knowledge_edits.py`** that
imports the span *constants* from `scripts/knowledge_spans.py`. `knowledge_spans.py`
stays pure constants (its docstring is updated — it currently says the editors "stay
in the invariant test"). `tests/test_promote_invariant.py` imports the editors
verbatim from `knowledge_edits.py`; its 7 property tests stay green (not weakened —
[[016-constraint-promote-narrowed-never-overwrite]] is still the spec of record). The
frozen detector (`scripts/knowledge_lint.py`) keeps importing only
`knowledge_spans.py` and is **not** edited.

### 2. `scripts/knowledge_fix.py` — deterministic fixer

- Imports the detector's API (`lint_knowledge` / `parse_index` / `parse_entry`) and
  the entry editors; anchors paths to `git rev-parse --show-toplevel`
  ([[021-constraint-skill-wraps-script-via-importable-api]]).
- **Re-derives every edit from `parse_index` / `parse_entry`** structured output —
  **never** parses the `Finding` message string (it's a human-readable f-string).
- Modes: `--dry-run` (print the planned edits) and apply.
- **apply recomputes once**: re-run `lint_knowledge` at apply start, compute the
  batch of fixes, apply atomically, then run a **single** final verify
  (`lint_knowledge` clean for the fixed families). It does **not** loop
  fix→recompute→fix.
- **Auto-fixes (deterministic only):**
  - **watermark** → set `<!-- index-watermark: NNN -->` to the max entry NNN.
  - **stale catalog line** (catalog NNN with no entry file) → remove the line.
  - **wrong Type section** → relocate **the `index.md` catalog line only** (exact
    verbatim line, including its summary), re-inserted at the ascending-NNN position
    under the correct section header (the target header always exists in the skeleton,
    so relocating into the empty `## Patterns` is the trivial insert-after-header
    case). **Never** moves entry-body content.
  - **missing reciprocal** → insert the reciprocal `## Related` line on the neighbor;
    the label comes from a **tested derivation table** keyed off the *forward* label
    (`builds on`→`see also`; `supersedes`↔`superseded by`; `contradicts`/`see also`
    symmetric); **refuse** if the forward label isn't in the closed vocabulary
    ([[015-constraint-knowledge-cross-reference-convention]]). A **supersession**
    entry carries **both** the `<!-- superseded-by: NNN -->` banner **and** the
    `superseded by` `## Related` line (015/016) — the fixer writes/keeps both, never
    suppresses the Related line. Reciprocal **pairs** are computed and validated
    (both labels in vocab; both files pass the terminal-`## Related` guard) **before
    any write**, and refused as a whole if either side is invalid — no partial
    one-direction write.
- **Safety:** after each entry edit, assert `body_complement(after) ==
  body_complement(before)`; treat the terminal-`## Related` `AssertionError` as
  "refuse to fix this entry"; **abort the whole run atomically** on any failure. All
  `index.md` edits are applied as one surgical rewrite computed from the single
  recompute, preserving the skeleton + NNN order.
- **Idempotent:** a second apply makes zero edits.
- **NOT auto-fixed** (left to manual / advisory): **missing catalog line** (needs an
  LLM-authored summary), **broken `## Related` link** (needs a human decision), and
  all **judged dimensions** (orphans / contradictions / staleness — advisory per
  [[013-decision-behavioral-evals-provisional]]).
- Unit-tested in `tests/test_knowledge_fix.py`; added to the `evals.yml` gate.
- Index-editing logic lives **in `knowledge_fix.py`** (fixer-specific — only the
  fixer mechanically edits `index.md`; `minerva:promote` maintains it via its own
  prose), not in the entry-span-scoped `knowledge_edits.py`.

### 3. `minerva:lint-fix` skill

A **new, mutating, gated** skill (`plugins/minerva/skills/lint-fix/SKILL.md`),
separate from read-only `minerva:lint`. Flow: run the detector → show the `--dry-run`
plan → **gate** on user confirmation → Bash-invoke apply (which recomputes).
`allowed-tools: Bash, Read, Grep, Glob` — the tested script does the writes, so no
`Edit`/`Write` is needed. It carries **no** `read-only` anchor or read-only language
(honest about mutating). Names its tools explicitly
([[007-constraint-skills-must-call-tools-not-prose]]).

### 4. Catalog + contract + docs

- **Catalog ([[010-constraint-minerva-skill-catalog-sync]]):** add `minerva:lint-fix`
  to all three surfaces (lifecycle position after `minerva:lint`).
- **Contract ([[012-constraint-skill-structural-contracts]]):** create
  `evals/lint-fix/contract.json` (`skill: "lint-fix"`; positive anchors on stable
  mutating-behavior tokens — `knowledge_fix`, `--dry-run`, `## Related`, the fix
  families; `cross_surface` all three). It carries **no** `read-only` anchor and no
  `FIX`/`SUGGEST`/`IGNORE` triage anchors. `minerva:lint` and its contract are
  untouched. (The `minerva:lint-fix` vs `minerva:lint` token boundary is safe — the
  harness matches on `(?![\w-])`.)
- **Docs:** the `using-minerva` decision-matrix row.

## Success criteria

- `scripts/knowledge_edits.py` exists holding the three editors (importing constants
  from `knowledge_spans.py`); `tests/test_promote_invariant.py` imports them from
  there and its 7 tests still pass; `knowledge_spans.py` is constants-only with an
  updated docstring; `scripts/knowledge_lint.py` is unchanged.
- `python3 scripts/knowledge_fix.py --dry-run` prints planned edits and writes
  nothing; apply fixes the four families and ends with a clean `lint_knowledge`
  verify (no fix-loop).
- **Idempotent:** a second apply produces zero edits.
- **Entry safety:** for every edited entry, bytes outside the `## Related`/banner
  spans are unchanged (`body_complement` byte-identity); a run that would touch a
  body aborts.
- **Index safety:** `index.md` edits preserve the H1, the four section headers (incl.
  empty `## Patterns`), and ascending-NNN order; round-trip `parse_index(fix(corpus))`
  is clean.
- **Supersession** writes both the banner and the `superseded by` `## Related` line;
  reciprocal pairs are atomic (no one-direction partial write); a forward label not
  in the closed vocab is refused.
- The fixer derives edits from `parse_index`/`parse_entry`, not the `Finding` message
  string.
- `tests/test_knowledge_fix.py` covers each fix family + idempotency + entry
  body-preservation + index round-trip + reciprocal-label table + reciprocal-pair
  atomicity + post-fix `lint_knowledge` clean; it is in the `evals.yml` gate.
- `minerva:lint-fix` skill exists (mutating, gated, Bash-only, **no** `read-only`
  anchor); `evals/lint-fix/contract.json` present; `tests/test_skill_contracts.py`
  passes with `lint-fix` enumerated; all three catalog surfaces + the using-minerva
  matrix list `minerva:lint-fix`.

## Open Questions

- Whether the missing-catalog-line fix (needs a summary) ever gets an LLM-assisted
  path. **Leaning:** stays manual — keeps the fixer fully deterministic; the skill
  surfaces it as "needs a manual summary."

## Out of scope

- Phase C (synthesis / concept pages + `log.md`).
- Auto-fixing missing catalog lines (needs a summary), broken `## Related` links, or
  any judged dimension (orphans / contradictions / staleness — advisory per 013).
- Running the fixer in CI / auto-apply — fixes are gated/interactive only.
- Editing the frozen detector (`scripts/knowledge_lint.py`) or the read-only
  `minerva:lint` skill / its contract.
