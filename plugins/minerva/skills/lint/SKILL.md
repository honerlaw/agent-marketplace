---
name: lint
description: Health-checks the `.minerva/knowledge/` wiki — runs the deterministic detector for mechanical defects (invalid ids, broken `## Related` links, missing `**Theme**` / `**Summary**` metadata, legacy `index.md` / `overview.md` still present, single-entry themes) and adds LLM-judged advisory findings (orphans by computed backlinks, contradictions, stale/superseded claims), presenting everything in `minerva:review`'s finding format. Read-only — it reports; repairs are made by hand, or by `minerva:migrate-fix` for a legacy corpus's metadata. Use when the knowledge-lint CI gate is failing, the user asks to health-check / audit the wiki, or wants to surface orphaned / contradictory / stale knowledge entries, or when they invoke `minerva:lint`.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

## Runtime

Read `skills/using-minerva/references/runtime.md` before executing; follow its host adapter.

Health-check the `.minerva/knowledge/` wiki and report its coherence problems.
`minerva:lint` is **read-only**: it surfaces findings and stops. It is the
interactive, human-facing companion to the deterministic drift gate
(`scripts/knowledge_lint.py`, shipped in work unit 021) — it makes that gate's
mechanical failures *actionable* and adds the LLM-judged dimensions the gate
deliberately can't compute.

> **Read-only contract.** This skill must not modify any file. Its `allowed-tools`
> is host metadata; the read-only protocol applies regardless of available tools. It proposes no FIX disposition and
> offers no "apply"/"write" affordance. Repairs are made by hand, except a legacy
> corpus's missing metadata, which `minerva:migrate-fix` backfills. New knowledge
> entries are written by `minerva:promote`, never through this skill.

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
ROOT="$(git rev-parse --show-toplevel)"; PLUGIN_SCRIPTS="$(python3 "$MINERVA_PLUGIN_ROOT/scripts/minerva_runtime.py" resolve --skill-file "$MINERVA_SKILL_FILE")" || exit 1; [ -n "$PLUGIN_SCRIPTS" ] && { python3 "$PLUGIN_SCRIPTS/plugin_guard.py" || exit 1; }; python3 -c "import sys, json; sys.path.insert(0, sys.argv[1]); \
from knowledge_lint import lint_knowledge; \
print(json.dumps([f._asdict() for f in lint_knowledge(sys.argv[2])]))" "$PLUGIN_SCRIPTS" "$ROOT/.minerva/knowledge"
```

Each `Finding` has `family`, `severity` (`error` / `warning`), and `message`. Treat all
of them as **high-confidence mechanical** findings. The families:

- **`id`** (error) — a date-shaped id that is not a real calendar date.
- **`broken-link`** (error) — a `## Related` wikilink to an entry that does not exist.
- **`metadata`** — an entry missing its `**Theme**` or `**Summary**` line, which the
  derived catalog reads. An **error** for an entry whose filename id is a date on or after
  2026-10-01; a **warning** for an older or legacy `NNN` entry. The rule keys on the
  entry's own date, not on whether legacy files exist, so it cannot flip when a stale tool
  recreates `index.md`: every new entry is enforced and an un-backfilled legacy corpus
  stays green.
- **`legacy`** (warning) — a pre-3.0 `index.md` / `overview.md` is still present. Nothing
  maintains it any more (the catalog is derived on read —
  `2026-10-01-decision-knowledge-aggregates-are-derived-on-read`), so it can only go stale;
  `minerva:migrate-fix` folds it into the entries and deletes it. A collaborator still on
  minerva 2.x can recreate it; the warning is how that shows up.
- **`theme`** (warning, advisory) — a theme used by exactly one entry. A drift signal (two
  near-duplicate names for one theme), never an error: a freshly coined theme
  legitimately starts at one.

There are no catalog-drift, watermark or missing-reciprocal checks: none of those is
stored any more, so none can drift. The detector and its span module (`scripts/knowledge_lint.py`,
`scripts/knowledge_spans.py`) are **frozen** — invoke them, never edit them.

## Step 2 — Judged pass (LLM, advisory)

Read the corpus once (`Read`/`Grep` over `.minerva/knowledge/*.md`) and surface
three **advisory** dimensions. These are LLM judgment — they are **never CI-gated**
(see `.minerva/knowledge/013-decision-behavioral-evals-provisional.md`) and must be
framed **"spot-checked, not exhaustive"** (a single-context read; reliable up to
roughly low-hundreds of entries — contradiction detection is inherently O(n²) in
attention, so a clean result is not a guarantee).

> **After upgrading minerva, the count is not a baseline.** The 3.0 detector checks
> different things (no reciprocal/index findings; new metadata, legacy and theme
> findings), so re-baseline any pending finding-count comparison rather than reading the
> change as damage or repair. See `skills/migrate-fix/references/upgrading.md`.

- **Orphans.** Backlinks are computed, not stored, so derive the graph from the catalog
  script — the same edge model `knowledge_catalog.py --links-to <stem>` prints:

  ```bash
  ROOT="$(git rev-parse --show-toplevel)"
  PLUGIN_SCRIPTS="$(python3 "$MINERVA_PLUGIN_ROOT/scripts/minerva_runtime.py" resolve --skill-file "$MINERVA_SKILL_FILE")" || exit 1
  [ -n "$PLUGIN_SCRIPTS" ] && { python3 "$PLUGIN_SCRIPTS/plugin_guard.py" || exit 1; }
  python3 -c "import sys, json; sys.path.insert(0, sys.argv[1]); \
  from knowledge_catalog import load_entries, backlinks, superseded_by; \
  E=load_entries(sys.argv[2]); S=superseded_by(E); succ={x for v in S.values() for x in v}; \
  print(json.dumps([s for s,e in E.items() if not e['edges'] and not backlinks(E,s) and s not in S and s not in succ]))" "$PLUGIN_SCRIPTS" "$ROOT/.minerva/knowledge"
  ```

  Keyed on the entry's **stem**, never on the id alone. Under date ids the id is the DATE,
  so an id-keyed graph collapses every entry sharing a day into one bucket and almost
  nothing can look orphaned — 0 reported against 14 real ones, on the corpus where this
  was caught.

  An entry with no outbound `## Related` link, no computed backlink and no supersession
  relation (derived from `supersedes` / legacy `superseded by` edges and legacy banners)
  is an **orphan candidate for cross-linking**, *not* a defect. Whether an orphan should
  be linked (and to what) is the only LLM judgment here; many entries legitimately stand
  alone. Entries are write-once, so the fix is a forward link from the *newer* side —
  usually a new entry written by `minerva:promote` — never an edit to an old neighbour.

- **Contradictions.** Two entries whose findings disagree with no `contradicts` link
  or supersession between them. Report the pair and the apparent conflict.

- **Stale / superseded claims.** An entry whose finding a newer entry supersedes, with no
  supersession relation between them (no `supersedes` edge in the newer entry's
  `## Related`, and no legacy banner). The catalog derives supersession from that edge, so
  a missing edge leaves the older entry listed as current. Report the older/newer pair.

## Step 3 — Present (read-only)

Present both passes in `minerva:review`'s finding format — mechanical findings, then
advisory ones — with how each would be remediated, and then **stop**: nothing is applied.
The exact layout, the remediation wording per family, and the clean-run line live in
`references/presentation.md`. **Read it before presenting.**

## Out of scope

- **Any file mutation.** Repairs are made by hand, or by `minerva:migrate-fix` (gated) for
  a legacy corpus's metadata.
- **Editing the detector.** `scripts/knowledge_lint.py` is frozen; consume its API.
- **Linting `.minerva/reference/`** (present-tense operational docs, different shape).
- **CI-gating the advisory dimensions.** They are provisional and advisory only.
