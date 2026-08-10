---
name: migrate
description: Checks an existing `.minerva/knowledge/` folder against the current LLM-wiki structure — read-only; runs the deterministic `migration_status` shape signal (files that don't conform to the naming convention and are therefore invisible to the wiki tooling — a false clean — plus missing index.md / overview.md and entries with no `## Related` cross-refs) and emits a migration checklist naming the existing skills that close each gap. It never edits files; renames and cross-ref authoring are judgment calls done by hand. Use when old notes don't appear in the index or lint reports clean on a corpus that predates the wiki conventions, when the user asks to migrate / restructure / refactor a legacy knowledge folder or wants a migration check, or when they invoke `minerva:migrate`.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

Assess an existing `.minerva/knowledge/` corpus against the current LLM-wiki structure
and report a **migration checklist**. `minerva:migrate` is **read-only**: it inventories
what needs migrating and names the skill that closes each gap, then stops.

> **Read-only contract.** This skill must not modify any file. Its `allowed-tools` omits
> `Edit` / `Write` / `MultiEdit` by design. It performs no renames, authors no
> cross-references, and runs no remediation skill — it only *reports* and *recommends*.

> **This is a SHAPE check, NOT a HEALTH check.** `migration_status` tells you whether the
> corpus is in the *shape* the wiki tooling requires (conforming filenames, index +
> overview present, entries carrying `## Related`). A clean migration inventory can still
> coexist with `minerva:lint` errors (e.g. a stale index watermark or catalog drift), so a
> passing migration check **still requires** a green `minerva:lint` pass and a
> `minerva:synthesize` pass — those are the ongoing health checks; this is the one-time
> shape audit.

## Why this exists

The detector (`scripts/knowledge_lint.py`), the fixer (`scripts/knowledge_fix.py`), and
`scripts/synthesis_status.py` all enumerate the corpus through the `ENTRY_RE` glob
(`^\d{3}-[a-z]+-.+\.md$`) **only**. A file that doesn't match — a legacy entry named
before the `YYYY-MM-DD-type-slug` convention — is **invisible** to every one of them, so a
pre-conventions corpus reads as a *false clean* across the whole toolchain.
`minerva:migrate` is the one surface that globs the **complement** of `ENTRY_RE` and
inventories those invisible files, turning a false-clean legacy corpus into an actionable
checklist.

## Target

The `.minerva/knowledge/` corpus of the **current working tree**, resolved from
`git rev-parse --show-toplevel` — the same per-branch semantics `minerva:lint` and the
unit-021 drift gate use. Takes no work-unit argument; it audits the whole knowledge base.

## Step 1 — Run the shape signal (deterministic, read-only)

Run `migration_status` through its **importable Python API**, anchoring both the
`scripts/` import path and the corpus path to the working-tree root so it works from any
subdirectory (`scripts/migration_status.py` is read-only — it never writes):

```bash
ROOT="$(git rev-parse --show-toplevel)"; PLUGIN_SCRIPTS=$(find -L "${HOME}/.claude/plugins/minerva" "${HOME}/.claude/plugins/cache/agent-marketplace/minerva" -maxdepth 2 -type d -name "scripts" 2>/dev/null | head -1); python3 -c "import sys, json; sys.path.insert(0, '${PLUGIN_SCRIPTS:-$ROOT/scripts}'); \
from migration_status import migration_status; \
print(json.dumps(migration_status('$ROOT/.minerva/knowledge'), indent=2))"
```

The returned dict carries plain-primitive signals:

- `non_conforming_files` — `*.md` files in the knowledge dir that do **not** match
  `ENTRY_RE` (excluding the reserved `index.md` / `overview.md`). **The migration-unique
  signal** — these are the files invisible to all other wiki tooling.
- `index_present` / `overview_present` — booleans for the index catalog and the synthesis
  overview.
- `entries_without_related` — conforming entries whose `## Related` block is absent or
  empty (no cross-ref edges). Derived fence-aware from the frozen detector's `parse_entry`
  (a fenced `## Related` example does not count), and robust to malformed legacy entries
  (a conforming-named file with no `**Type**` / no sections is counted, never crashed on).
- `conforming_entry_count` — how many entries already match the convention.

## Step 2 — Emit the migration checklist (read-only)

Translate the signal into a checklist. For each gap, **name** the existing skill that
closes it and a one-line effect — do **not** run it, and do not reproduce its findings:

- **`non_conforming_files` non-empty** → these files must be **renamed** to
  `<YYYY-MM-DD>-<type>-<slug>.md` (type is `decision` / `bug` / `pattern` / `constraint` / `reference`) so the tooling
  can see them. This rename is automated by **`minerva:migrate-fix`**, which derives each date from git
  and retargets every `[[…]]` wikilink and catalog line — deliberate mutation this
  read-only check never performs itself.
- **`index_present` false** → run `minerva:init` (it scaffolds / backfills `index.md` from
  the existing entries).
- **`overview_present` false** → run `minerva:synthesize` (it creates the theme-grouped
  `overview.md`).
- **`entries_without_related` non-empty** → these entries need `## Related` cross-refs
  **authored**. ⚠️ **Not automated** — authoring which entries relate (and the
  relationship label) is LLM judgment; do it by hand. `minerva:lint-fix` only repairs *reciprocals of links that already exist*, not the
  initial edges.
- **Always, after the corpus conforms** → run `minerva:lint` to surface mechanical drift
  (index watermark, broken links, missing reciprocals) and `minerva:lint-fix` to repair
  the deterministic subset. Then run `minerva:synthesize` to (re)build the overview.

Present it as a numbered checklist with the counts from the signal, then **stop**. If
`non_conforming_files` and `entries_without_related` are both empty and index + overview
are present, report: `migration: corpus is in conforming shape (<N> entries) — run
minerva:lint + minerva:synthesize to confirm health.`

## Out of scope

- **Any file mutation** — no renames, no cross-ref authoring, no index/overview writes.
  This skill reports; the gated/judged remediation lives in `minerva:init` /
  `minerva:lint-fix` / `minerva:synthesize` (run by the user) or in future
  migration-APPLY units.
- **Editing the frozen detector** (`scripts/knowledge_lint.py`) — `migration_status`
  consumes its `ENTRY_RE` / `parse_entry` API, never re-derives it.
- **Being a health check** — mechanical drift and synthesis staleness are owned by
  `minerva:lint` and `minerva:synthesize`; this skill checks *shape*, not *health*.
- **Scanning subdirectories** — like the detector / fixer / synthesis tooling,
  `migration_status` globs `*.md` non-recursively (top-level of `.minerva/knowledge/`
  only); entries nested in a subdirectory are not inventoried (consistent with the rest of
  the toolchain, which is equally non-recursive).
