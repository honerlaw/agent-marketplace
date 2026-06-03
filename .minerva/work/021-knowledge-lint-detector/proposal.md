# Proposal: knowledge-lint-detector

**Date**: 2026-06-02
**Status**: Shipped (2026-06-02)

> **Phase B.1** of the LLM-wiki effort. Phase 1 (navigability) shipped as unit 020.
> The interactive `minerva:lint` skill — LLM-judged contradiction/staleness checks,
> orphan detection, `minerva:review`-style triage, and gated fixes — is **Phase B.2,
> deferred** to its own work unit (see **Out of scope**).

## Goal

Add `scripts/knowledge_lint.py`, a **deterministic, read-only** detector for
*mechanical* coherence defects in the `.minerva/knowledge/` wiki, unit-tested on
fixtures and wired into the `evals.yml` CI gate to lint the live knowledge
directory (drift prevention).

This unit was decomposed from a larger "minerva:lint" proposal along the
deterministic-vs-LLM-judged fault line — mirroring the units 017/018 precedent
(deterministic structural floor as one unit; LLM-judged behavioral layer as a
separate, provisional one) and honoring [[013-decision-behavioral-evals-provisional]]
(LLM-judged output is provisional and must not co-gate with a deterministic floor).

## Why

Unit 020 made `.minerva/knowledge/` a navigable wiki (an `index.md` catalog +
`## Related` cross-references), and `minerva:promote` maintains it at **write** time.
But nothing catches drift introduced outside a promote: a manual or partial edit, a
renamed/deleted entry, an out-of-date watermark, a one-way cross-reference. These
defects are **mechanically** detectable and deserve a deterministic CI gate. Doing so:

- delivers the knowledge-side of the drift-prevention automation
  [[010-constraint-minerva-skill-catalog-sync]] deferred;
- honors [[017-decision-knowledge-wiki-navigability-layer]]'s directive that tooling
  recompute from the corpus rather than trust the index;
- gives the deferred Phase B.2 `minerva:lint` skill a Bash-invocable detector to
  build its interactive, LLM-judged layer on top of.

## Approach

`scripts/knowledge_lint.py` — a deterministic, **read-only** detector. The **corpus
is the source of truth**; `index.md` is never assumed authoritative (per
[[017-decision-knowledge-wiki-navigability-layer]]) — index problems are reported as
the defect. `index.md` itself is **excluded** from the entry set (it is the catalog,
not an entry).

### Checks (all mechanical — no content judgment)

1. **Index drift**
   - watermark (`<!-- index-watermark: NNN -->`) ≠ the max entry NNN on disk;
   - **NNN-keyed bijection** between catalog lines and entry files: an entry file
     whose NNN has no catalog line, or a catalog line whose NNN has no file. The slug
     is cosmetic (per [[015-constraint-knowledge-cross-reference-convention]]) — a
     slug mismatch between catalog and filename for the same NNN is a *stale-slug
     warning*, not a missing-entry error;
   - **Type-section correctness**: each catalog line sits under the plural header
     (`## Decisions` / `## Bugs` / `## Patterns` / `## Constraints`) matching that
     entry's declared `**Type**:` field. Empty groups are legal (e.g. `## Patterns`
     is currently empty).
2. **Broken `## Related` links** — every `[[NNN-type-slug]]` in an entry's
   `## Related` block must resolve **by NNN** to a real entry. Links are extracted
   **only from the `## Related` block, never from prose**, and extraction is
   **fence-aware**: a `## Related` heading or `[[…]]` line inside a ```` ``` ```` code
   fence is ignored (convention docs 015/017 contain exactly such examples).
3. **Missing reciprocals** — if entry A's `## Related` links B, then B must link back
   to A. The check is **bidirectional presence keyed on NNN — never a label match**:
   a `builds on`↔`see also` asymmetric pair is valid (per 015; a label-pairing check
   would yield 7 false positives on the current clean corpus). A back-link counts
   whether it appears in B's `## Related` block **or** in B's supersession banner.

### Parser rules (pinned — deterministic, no markdown library)

- **Block selection:** "the `## Related` block" = the **last non-fenced** `## Related`
  header, spanning to EOF. (015 carries a fenced `## Related` *example* plus the real
  terminal block.)
- **Banner detection:** position+form anchored — a line matching
  `^<!-- superseded-by: (\d{3}) -->$` located **above the first `## ` header**. Never
  a substring scan: entries 015/016 mention the literal `<!-- superseded-by: NNN -->`
  string in prose and are not superseded.
- **Fence tracking:** toggle on lines matching ```` ``` ````; ignore headers/links
  inside fences.
- Line-regex parsing throughout; the em-dash separator ` — ` (U+2014) in catalog and
  `## Related` lines is matched as the literal character.

### Shared span constants

Extract `scripts/knowledge_spans.py` holding the span primitives currently defined
inside `tests/test_promote_invariant.py`: `RELATED_HEADER`, `BANNER_MARKER_RE`,
`BANNER_QUOTE_RE`, `SECTION_RE`, and the "`## Related` is the terminal section" rule.
Both `scripts/knowledge_lint.py` and `tests/test_promote_invariant.py` import these
from the shared module (production → shared; the test is rewritten to import rather
than define them). `conftest.py` already puts `scripts/` on `sys.path`. **Only the
constants move**; the promote-mutation-specific helpers
(`add_related_link` / `add_supersede_banner` / `body_complement`) stay in
`test_promote_invariant.py` and import the constants — the detector does not need
them. This keeps the span model single-sourced ([[016-constraint-promote-narrowed-never-overwrite]]
calls these the spec of record).

### CLI + API

Importable check functions (one per defect family) returning structured findings,
plus a `__main__` CLI that takes a knowledge-dir path, prints findings grouped by
defect family (one greppable line per finding), and **exits non-zero iff any defect
is found**.

### Tests + CI

`tests/test_knowledge_lint.py` — fixture-based (temp dirs / strings; deterministic):
- a **clean** corpus → no findings;
- one fixture per defect flagging it: watermark mismatch; entry missing a catalog
  line; catalog line whose NNN has no file; wrong Type section; broken `## Related`
  link; one-way reciprocal (a **pure missing-back-NNN** case);
- **pass-cases that must NOT flag** (false-positive guards): a `builds on`/`see also`
  asymmetric pair; an entry whose only back-link is in the supersession banner; an
  entry with a fenced `## Related` *example* plus the real block; inline-prose
  `[[NNN]]` outside any `## Related` block;
- `test_live_knowledge_clean` — runs the **same importable function the CLI uses**
  against the real `.minerva/knowledge/` and asserts zero findings.

`evals.yml` — add `tests/test_knowledge_lint.py` to the gated pytest invocation, and
add a step running `python3 scripts/knowledge_lint.py .minerva/knowledge` (the live
drift gate). Both paths call the same function so they cannot disagree on "clean."

**No new skill** → constraints [[010-constraint-minerva-skill-catalog-sync]] (catalog
sync) and [[012-constraint-skill-structural-contracts]] (`contract.json`) do not fire.
The gate runs only deterministic checks, honoring [[013-decision-behavioral-evals-provisional]].

## Success criteria

- `python3 scripts/knowledge_lint.py .minerva/knowledge` exits 0 on the current repo
  (the live wiki is clean: watermark 017, all entries catalogued under correct Type
  sections, `## Related` links reciprocal, no broken links).
- The detector flags each of these on a fixture, each covered by a passing unit test:
  watermark mismatch; entry missing a catalog line; catalog line with no file; wrong
  Type section; broken `## Related` link; one-way (missing-back-NNN) reciprocal.
- False-positive guards pass (no finding): a `builds on`/`see also` asymmetric pair; a
  banner-only back-link; an entry with a fenced `## Related` example plus the real
  block; inline-prose `[[NNN]]` outside `## Related`.
- Reciprocity is presence-keyed on NNN; label-matching is not used (verified by the
  `builds on`/`see also` pass-case).
- `tests/test_knowledge_lint.py` (incl. `test_live_knowledge_clean`) and the live-dir
  CLI step are in the `evals.yml` gate and pass; the live-clean test and the CLI call
  the same importable function.
- `scripts/knowledge_spans.py` exists holding the shared span constants; both
  `scripts/knowledge_lint.py` and `tests/test_promote_invariant.py` import from it,
  and the pre-existing promote-invariant tests still pass.
- `index.md` is excluded from the entry set for the bijection check.

## Open Questions

- Report granularity (per-finding lines vs grouped). **Leaning:** grouped by defect
  family, one greppable line per finding — enough for CI and for Phase B.2 to parse.
- Whether the live-dir gate is a distinct `evals.yml` step or only the
  `test_live_knowledge_clean` pytest. **Leaning:** both — a distinct CLI step (clear
  signal, matches the existing `run_skill_evals.py --dry-run` step shape) plus the
  pytest as a local tripwire.

## Out of scope

- The `minerva:lint` **skill** (Phase B.2): LLM-judged contradiction & staleness
  detection, **orphan detection** (judgment-adjacent), `minerva:review`-style triage,
  and **gated fixes** (index repair + reciprocal insertion respecting
  [[016-constraint-promote-narrowed-never-overwrite]]). Recorded as a followup.
- Linting `.minerva/reference/`.
- Auto-fixing anything — the detector is strictly read-only.
- A pre-commit hook — the CI gate suffices for now.
