---
name: lint
description: Use when the user invokes `minerva:lint`, asks to health-check / audit the `.minerva/knowledge/` wiki, wants to know why the knowledge-lint CI gate is failing, or wants to surface orphaned / contradictory / stale knowledge entries. Read-only — it runs the deterministic detector for mechanical defects (index drift, broken `## Related` links, missing reciprocals) and adds LLM-judged advisory findings (orphans, contradictions, stale/superseded claims), presenting everything in `minerva:review`'s finding format. It never edits files; it reports. Durable repairs are applied by hand or by the gated fix path (Phase B.3), not by this skill.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

Health-check the `.minerva/knowledge/` wiki and report its coherence problems.
`minerva:lint` is **read-only**: it surfaces findings and stops. It is the
interactive, human-facing companion to the deterministic drift gate
(`scripts/knowledge_lint.py`, shipped in work unit 021) — it makes that gate's
mechanical failures *actionable* and adds the LLM-judged dimensions the gate
deliberately can't compute.

> **Read-only contract.** This skill must not modify any file. Its `allowed-tools`
> omits `Edit` / `Write` / `MultiEdit` by design. It proposes no FIX disposition and
> offers no "apply"/"write" affordance. Durable repairs are made by hand or by the
> gated fix path (Phase B.3); index/scratchpad knowledge writes go through
> `minerva:promote`, never through this skill.

## Target

The `.minerva/knowledge/` corpus of the **current working tree**, resolved from
`git rev-parse --show-toplevel`. Run from the main repo it audits the canonical
wiki; run from inside a worktree (mid-lifecycle) it audits that branch's corpus —
the same per-branch semantics the unit-021 CI drift gate uses. `minerva:lint` takes
no work-unit argument and reads no scratchpad — it audits the whole knowledge base
of the working tree you are in.

## Step 1 — Mechanical pass (deterministic, high-confidence)

Run the frozen unit-021 detector through its **importable Python API** and read the
**full** findings list — *including warning-severity findings*. Do **not** branch on
the CLI exit code: `scripts/knowledge_lint.py` exits 0 when only warnings are
present (e.g. a stale-slug warning), so the exit code would hide them.

Call it with `Bash`, anchoring **both** the `scripts/` import path and the corpus
path to the current working tree's root (`git rev-parse --show-toplevel`) so it works
from any subdirectory and audits the corpus of the tree you're in:

```bash
ROOT="$(git rev-parse --show-toplevel)"; python3 -c "import sys, json; sys.path.insert(0, '$ROOT/scripts'); \
from knowledge_lint import lint_knowledge; \
print(json.dumps([f._asdict() for f in lint_knowledge('$ROOT/.minerva/knowledge')]))"
```

Each `Finding` has `family` (`index` / `broken-link` / `reciprocal`), `severity`
(`error` / `warning`), and `message`. Treat all of them as **high-confidence
mechanical** findings. The detector and its span module (`scripts/knowledge_lint.py`,
`scripts/knowledge_spans.py`) are **frozen** — invoke them, never edit them.

## Step 2 — Judged pass (LLM, advisory)

Read the corpus once (`Read`/`Grep` over `.minerva/knowledge/*.md`) and surface
three **advisory** dimensions. These are LLM judgment — they are **never CI-gated**
(see `.minerva/knowledge/013-decision-behavioral-evals-provisional.md`) and must be
framed **"spot-checked, not exhaustive"** (a single-context read; reliable up to
roughly low-hundreds of entries — contradiction detection is inherently O(n²) in
attention, so a clean result is not a guarantee).

- **Orphans.** Derive the link graph from the detector's **own** parser so the edge
  model can't drift from the gated one:

  ```bash
  ROOT="$(git rev-parse --show-toplevel)"; python3 -c "import sys, json; sys.path.insert(0, '$ROOT/scripts'); \
  from pathlib import Path; from knowledge_lint import parse_entry, ENTRY_RE; \
  E={p.name: parse_entry(p) for p in Path('$ROOT/.minerva/knowledge').glob('*.md') if ENTRY_RE.match(p.name)}; \
  inbound={e['nnn']: set() for e in E.values()}; \
  [inbound[t].add(e['nnn']) for e in E.values() for t in e['backlinks'] if t in inbound]; \
  print(json.dumps(sorted(n for n,e in ((v['nnn'],v) for v in E.values()) if not e['backlinks'] and not inbound[n])))"
  ```

  An entry with no outbound and no inbound edge — where an edge is a `## Related`
  link **or** a supersession-banner back-link, matching the detector's `backlinks`
  edge model — is an **orphan candidate for cross-linking**, *not* a defect. Whether
  an orphan should be linked (and to what) is the only LLM judgment here; many
  entries legitimately stand alone.

- **Contradictions.** Two entries whose findings disagree with no `contradicts` link
  or supersession between them. Report the pair and the apparent conflict.

- **Stale / superseded claims.** An entry whose finding a newer entry supersedes,
  with no `<!-- superseded-by: NNN -->` banner. Report the older/newer pair.

## Step 3 — Present (read-only)

Present findings in `minerva:review`'s **finding presentation** format — numbered
items, a severity tag, a one-line description, and the entry reference. Reuse only
the *presentation*; do **not** run review's FIX / SUGGEST / IGNORE disposition
machinery (that path writes files and assumes a work-unit scratchpad — out of scope
here). Two grouped sections:

```
## Mechanical findings (deterministic — these fail the CI drift gate)
1. [error] index — <message>  (entry NNN)
2. [warning] index — <message>  (entry NNN)
...

## Advisory findings (LLM-judged — spot-checked, not exhaustive; never CI-gated)
1. [orphan] NNN — no inbound/outbound `## Related`; candidate for cross-linking
2. [contradiction] NNN ↔ MMM — <apparent conflict>
3. [stale] NNN superseded by MMM — no supersession banner
...
```

Then **stop**. For each finding, state how it would be *remediated* — but do not
apply it:

- **Mechanical** findings (index drift, broken links, missing reciprocals) are
  repaired within the `## Related` / banner spans per
  `.minerva/knowledge/016-constraint-promote-narrowed-never-overwrite.md`. Until the
  gated fix path (Phase B.3) lands, the user applies them by hand (or re-runs
  `minerva:promote`, which maintains the index + reciprocals when it ingests).
- **Advisory** findings are suggestions for the user to act on; never auto-apply
  them.

If both passes are clean, report: `knowledge-lint: <N> entries, no mechanical
findings; advisory pass surfaced nothing (spot-checked).`

## Out of scope

- **Any file mutation.** The gated, span-confined fix-applier is Phase B.3 — it will
  import the span constants from `scripts/knowledge_spans.py`
  (`.minerva/knowledge/019-constraint-knowledge-span-model-single-sourced.md`) and
  apply repairs behind a confirmation gate.
- **Editing the detector.** `scripts/knowledge_lint.py` is frozen; consume its API.
- **Linting `.minerva/reference/`** (present-tense operational docs, different shape).
- **CI-gating the advisory dimensions.** They are provisional and advisory only.
