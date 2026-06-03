# Proposal: minerva-lint-skill

**Date**: 2026-06-03
**Status**: Shipped (2026-06-03)

> **Phase B.2** of the LLM-wiki effort, **read-only**. Phase 1 = navigability
> (unit 020); Phase B.1 = the deterministic detector (unit 021). The **gated
> fix-applier is Phase B.3, deferred** — see **Out of scope**.

## Goal

Add `minerva:lint`, a **read-only** wiki health-check skill. Its headline value is
the **LLM-judged advisory dimensions the deterministic detector can't produce** —
orphans, contradictions, and stale/superseded claims — plus making the Phase-B.1 CI
gate's mechanical findings actionable. It invokes the frozen unit-021 detector for
the mechanical findings, runs one read-only advisory pass for the judged dimensions,
and presents everything in `minerva:review`'s finding *presentation* format. It
performs **no file mutation**; the gated fix-applier is Phase B.3.

## Why

Phase B.1 ([[018-decision-phase-b-deterministic-lint-detector]]) shipped the
deterministic detector + CI drift gate. But a red CI check isn't *actionable* — it
reports drift without explaining or surfacing it interactively — and the
judgment dimensions that need an LLM were deliberately deferred. `minerva:lint`
closes both: an on-demand skill that explains the mechanical findings and surfaces
the judged dimensions. Mutation (gated fixes) is split into B.3 per the corpus-
mutation risk seam ([[016-constraint-promote-narrowed-never-overwrite]] /
[[019-constraint-knowledge-span-model-single-sourced]]) and
[[013-decision-behavioral-evals-provisional]] — the judged dimensions are
provisional, so their precision should be validated *before* an auto-fixer acts on
them.

## Approach

New skill `plugins/minerva/skills/lint/SKILL.md` — **read-only**.

### Mechanical pass (high-confidence, from the frozen detector)

Invoke the unit-021 detector through its **importable Python API**, not the CLI
exit code. The CLI returns 0 on warnings-only, so exit-code branching would silently
drop warning-severity findings (e.g. stale-slug). The skill runs a Bash `python3 -c`
snippet that pins the repo-root `scripts/` on `sys.path`, imports
`lint_knowledge`, and emits the **full** `Finding` list (including `warning`
severity) as JSON:

```
python3 -c "import sys, json; sys.path.insert(0, 'scripts'); \
from knowledge_lint import lint_knowledge; \
print(json.dumps([f._asdict() for f in lint_knowledge('.minerva/knowledge')]))"
```

The detector (`scripts/knowledge_lint.py`, `scripts/knowledge_spans.py`) is
**frozen** — consumed via its API, never edited.

### Judged pass (advisory, one read-only LLM read of the corpus)

- **Orphans** — adjacency is derived from the detector's own `parse_entry`
  (`related_out` / `backlinks`) so the lint's edge model **cannot drift** from the
  gated one (fence-aware, NNN-keyed, banner back-links counted). An entry with no
  inbound and no outbound `## Related` edges is surfaced as an advisory **candidate
  for cross-linking** — not a defect. The orphan-as-defect *verdict* is the only LLM
  judgment here (per [[021 / 018]]: orphan-as-defect is judgment, deferred from the
  deterministic gate).
- **Contradictions** — two entries whose findings disagree with no `contradicts`
  link or supersession between them.
- **Stale / superseded claims** — an entry whose finding a newer entry supersedes,
  with no supersession banner.

The judged dimensions are **advisory**, **never CI-gated**
([[013-decision-behavioral-evals-provisional]]), and framed **"spot-checked, not
exhaustive"** (one-context corpus read; feasible up to low-hundreds of entries —
contradiction/staleness is inherently O(n²) attention and a clean result is not a
guarantee).

### Presentation (reuse review's format, not its triage machinery)

Reuse `minerva:review`'s finding **presentation** format — numbered findings,
severity tag, one-line description — but **not** its mutating
FIX / SUGGEST / IGNORE disposition machinery (which assumes file writes + a
work-unit scratchpad). Mechanical findings render as high-confidence; judged
findings render as advisory. The skill **presents findings and stops**. Durable
repairs are routed to **fix-by-hand or the deferred B.3 gated-fix path** — *not*
`minerva:promote`, which is work-unit/scratchpad-bound and has nothing to consume
for a standalone lint over the canonical corpus.

### Read-only enforcement (declaration + body directive)

- The SKILL.md frontmatter carries an `allowed-tools:` list that includes only read
  tools (`Bash`, `Read`, `Grep`, `Glob`) and **omits `Edit` / `Write` / `MultiEdit`**.
- The body carries an explicit **read-only** directive and offers **no FIX
  disposition** and no "apply/fix/write" affordance.
- **Honest limit:** the structural-contract harness (`evals/lint/contract.json`) can
  only *witness* the presence of `allowed-tools` and a `read-only` anchor via
  positive substring matching — it **cannot** mechanically prove `Edit`/`Write` are
  absent. So read-only is enforced by the `allowed-tools` declaration + the body
  directive; the contract witnesses them but does not guarantee non-mutation.
- Tools are named explicitly per [[007-constraint-skills-must-call-tools-not-prose]]
  (Bash for the detector invocation; Read/Grep/Glob for the corpus read).

### Catalog + contract + docs

- **Catalog ([[010-constraint-minerva-skill-catalog-sync]]):** add `minerva:lint`
  to all **three** surfaces in the same commit — `plugins/minerva/README.md` Skills
  table (row text excerpted from lint's `description:` frontmatter, lifecycle
  position after `review`), `plugins/minerva/skills/using-minerva/SKILL.md` decision
  matrix (one row), and the root `README.md` minerva plugin cell.
- **Contract ([[012-constraint-skill-structural-contracts]]):** create
  `evals/lint/contract.json` with `skill: "lint"`, `frontmatter` (required `name`/
  `description`; `contains` witnessing `allowed-tools`), `anchors` (short stable
  positive tokens — e.g. `knowledge_lint`, `read-only`, `## Related`,
  `.minerva/knowledge/`, an `orphan`/`contradiction` advisory token), and
  `cross_surface` (all three true). It **must not** copy review's
  `FIX`/`SUGGEST`/`IGNORE` anchors. `tests/test_skill_contracts.py` enumerates skill
  dirs, so the new `lint/` dir requires this contract or CI fails.
- **Docs:** the using-minerva decision-matrix row doubles as the catalog entry.

## Success criteria

- `plugins/minerva/skills/lint/SKILL.md` exists with a `name: lint` + non-empty
  `description` frontmatter and an `allowed-tools:` list that **omits**
  `Edit`/`Write`/`MultiEdit`.
- The body invokes the detector via the importable `lint_knowledge()` API
  (consuming the full findings list incl. warnings), describes the three judged
  advisory dimensions, derives orphan adjacency from `parse_entry`, and reuses
  review's presentation format **without** FIX/SUGGEST/IGNORE disposition machinery.
- The unit-021 detector files (`scripts/knowledge_lint.py`,
  `scripts/knowledge_spans.py`) are **unchanged** (frozen).
- The body routes durable repairs to fix-by-hand / B.3, **not** `minerva:promote`,
  and contains no file-mutation affordance.
- `evals/lint/contract.json` exists (`skill: "lint"`, witnesses `allowed-tools` +
  a `read-only` anchor, no triage anchors); `python3 -m pytest
  tests/test_skill_contracts.py` passes with `lint` enumerated.
- All three catalog surfaces list `minerva:lint` and the using-minerva matrix has a
  row (010).
- The judged dimensions are documented as advisory / never-CI-gated /
  "spot-checked, not exhaustive" (013).

## Open Questions

- Exact `allowed-tools` set. **Leaning:** `Bash, Read, Grep, Glob` (Bash for the
  `python3 -c` detector call; Read/Grep/Glob for the corpus read).
- Lifecycle position in the plugin-README Skills table. **Leaning:** after `review`
  (both are audit-style), before `cleanup`.

## Out of scope

- **Phase B.3 — the gated, span-confined, idempotent fix-applier** (index repair +
  reciprocal insertion respecting [[016-constraint-promote-narrowed-never-overwrite]]).
  It will import span constants from `scripts/knowledge_spans.py`
  ([[019-constraint-knowledge-span-model-single-sourced]]) and will **amend** (not
  rewrite) this skill's `contract.json`. Recorded as a followup.
- Phase C (synthesis / concept pages + `log.md`).
- Linting `.minerva/reference/`.
- Duplicate-NNN detection (a unit-021 followup).
- **Any file mutation** — this unit is strictly read-only.
