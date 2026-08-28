---
name: lint
description: Health-checks the `.minerva/knowledge/` wiki — runs the deterministic detector for mechanical defects (index drift, broken `## Related` links, missing reciprocals) and adds LLM-judged advisory findings (orphans, contradictions, stale/superseded claims), presenting everything in `minerva:review`'s finding format. Read-only — it reports; deterministic repairs are applied via `minerva:lint-fix`, judgment-call repairs by hand. Use when the knowledge-lint CI gate is failing, the user asks to health-check / audit the wiki, or wants to surface orphaned / contradictory / stale knowledge entries, or when they invoke `minerva:lint`.
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
> offers no "apply"/"write" affordance. Durable repairs in the deterministic subset
> are applied by invoking the `minerva:lint-fix` skill via the `Skill` tool; the
> rest by hand. Index/scratchpad knowledge writes go through
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
ROOT="$(git rev-parse --show-toplevel)"; PLUGIN_SCRIPTS=$(find -L "${HOME}/.claude/plugins/minerva" "${HOME}/.claude/plugins/cache/agent-marketplace/minerva" -maxdepth 2 -type d -name "scripts" 2>/dev/null | head -1); [ -n "$PLUGIN_SCRIPTS" ] && { python3 "$PLUGIN_SCRIPTS/plugin_guard.py" || exit 1; }; python3 -c "import sys, json; sys.path.insert(0, '${PLUGIN_SCRIPTS:-$ROOT/scripts}'); \
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

> **After upgrading minerva, expect a higher count.** The `## Related` edge model was
> unified so this linter and `knowledge_fix` read one edge set; the old detector saw only
> a line's first wikilink, so extra targets on a shared line were invisible. One corpus
> went 41 → 59 findings on the upgrade. The delta is previously-unreportable findings, not
> new damage — but re-baseline any pending finding-count comparison, because a
> "finding-neutral" claim measured under the old detector will not hold.

- **Orphans.** Derive the link graph from the detector's **own** parser so the edge
  model can't drift from the gated one:

  ```bash
  ROOT="$(git rev-parse --show-toplevel)"; PLUGIN_SCRIPTS=$(find -L "${HOME}/.claude/plugins/minerva" "${HOME}/.claude/plugins/cache/agent-marketplace/minerva" -maxdepth 2 -type d -name "scripts" 2>/dev/null | head -1); [ -n "$PLUGIN_SCRIPTS" ] && { python3 "$PLUGIN_SCRIPTS/plugin_guard.py" || exit 1; }; python3 -c "import sys, json; sys.path.insert(0, '${PLUGIN_SCRIPTS:-$ROOT/scripts}'); \
  from pathlib import Path; from knowledge_lint import parse_entry, ENTRY_RE; \
  E={p.name: parse_entry(p) for p in Path('$ROOT/.minerva/knowledge').glob('*.md') if ENTRY_RE.match(p.name)}; \
  inbound={e['stem']: set() for e in E.values()}; \
  [inbound[t].add(e['stem']) for e in E.values() for t in e['backlink_stems'] if t in inbound]; \
  print(json.dumps(sorted(s for s,e in ((v['stem'],v) for v in E.values()) if not e['backlink_stems'] and not inbound[s])))"
  ```

  Keyed on the entry's **stem**, never on `nnn`. Under date ids `nnn` is the DATE, so an
  `nnn`-keyed graph collapses every entry sharing a day into one bucket and almost
  nothing can look orphaned — 0 reported against 14 real ones, on the corpus where this
  was caught. `parse_entry` exposes `backlink_stems` for exactly this reason.

  An entry with no outbound and no inbound edge — where an edge is a `## Related`
  link **or** a supersession-banner back-link, matching the detector's `backlink_stems`
  edge model — is an **orphan candidate for cross-linking**, *not* a defect. Whether
  an orphan should be linked (and to what) is the only LLM judgment here; many
  entries legitimately stand alone.

- **Contradictions.** Two entries whose findings disagree with no `contradicts` link
  or supersession between them. Report the pair and the apparent conflict.

- **Stale / superseded claims.** An entry whose finding a newer entry supersedes,
  with no `<!-- superseded-by: <stem> -->` banner. Report the older/newer pair.

## Step 3 — Present (read-only)

Present findings in `minerva:review`'s **finding presentation** format — numbered
items, a severity tag, a one-line description, and the entry reference. Reuse only
the *presentation*; do **not** run review's FIX / SUGGEST / IGNORE disposition
machinery (that path writes files and assumes a work-unit scratchpad — out of scope
here). Two grouped sections:

```
## Mechanical findings (deterministic — these fail the CI drift gate)
1. [error] index — <message>  (entry stem)
2. [warning] index — <message>  (entry stem)
...

## Advisory findings (LLM-judged — spot-checked, not exhaustive; never CI-gated)
1. [orphan] <stem> — no inbound/outbound `## Related`; candidate for cross-linking
2. [contradiction] <stem> ↔ <stem> — <apparent conflict>
3. [stale] <stem> superseded by <stem> — no supersession banner
...
```

Then **stop**. For each finding, state how it would be *remediated* — but do not
apply it:

- **Mechanical** findings (index drift, broken links, missing reciprocals) are
  repaired within the `## Related` / banner spans per
  `.minerva/knowledge/016-constraint-promote-narrowed-never-overwrite.md`. Findings in the
  deterministic subset are repaired by invoking `minerva:lint-fix` via the `Skill`
  tool; the remainder by hand (or re-run `minerva:promote`, which maintains the
  index + reciprocals when it ingests).
- **Advisory** findings are suggestions for the user to act on; never auto-apply
  them.

If both passes are clean, report: `knowledge-lint: <N> entries, no mechanical
findings; advisory pass surfaced nothing (spot-checked).`

## Out of scope

- **Any file mutation.** The gated, span-confined fix-applier is `minerva:lint-fix` — it
  imports the span constants from `scripts/knowledge_spans.py`
  (`.minerva/knowledge/019-constraint-knowledge-span-model-single-sourced.md`) and
  apply repairs behind a confirmation gate.
- **Editing the detector.** `scripts/knowledge_lint.py` is frozen; consume its API.
- **Linting `.minerva/reference/`** (present-tense operational docs, different shape).
- **CI-gating the advisory dimensions.** They are provisional and advisory only.
