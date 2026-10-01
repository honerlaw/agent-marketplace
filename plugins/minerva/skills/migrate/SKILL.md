---
name: migrate
description: Checks an existing `.minerva/knowledge/` folder against the current (3.0) wiki shape — read-only; runs the deterministic `migration_status` shape signal (files that don't conform to the naming convention and are therefore invisible to the wiki tooling — a false clean — legacy `index.md` / `overview.md` aggregates still present, entries missing the `**Theme**` / `**Summary**` lines the derived catalog reads, agent-file routing that still names the legacy aggregates, and entries with no `## Related` cross-refs) and emits a migration checklist naming the skill that closes each gap. It never edits files. Use when old notes don't appear in the catalog or lint reports clean on a corpus that predates the wiki conventions, when upgrading a corpus written by minerva 2.x, when the user asks to migrate / restructure / refactor a legacy knowledge folder or wants a migration check, or when they invoke `minerva:migrate`.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

## Runtime

Read `skills/using-minerva/references/runtime.md` before executing; follow its host adapter.

Assess an existing `.minerva/knowledge/` corpus against the current wiki shape and report
a **migration checklist**. `minerva:migrate` is **read-only**: it inventories what needs
migrating and names the skill that closes each gap, then stops.

> **Read-only contract.** This skill must not modify any file. Its `allowed-tools` is
> host metadata; the read-only protocol applies regardless of available tools. It performs no renames, writes no
> metadata, and runs no remediation skill — it only *reports* and *recommends*.

> **This is a SHAPE check, NOT a HEALTH check.** `migration_status` tells you whether the
> corpus is in the *shape* the wiki tooling reads (conforming filenames, no legacy
> aggregates, every entry carrying `**Theme**` and `**Summary**`, routing that points at
> the derived catalog). A clean inventory can still coexist with `minerva:lint` errors
> (e.g. a broken `## Related` link), so a passing migration check **still requires** a
> green `minerva:lint` pass — that is the ongoing health check; this is the one-time shape
> audit.

## Why this exists

The detector (`scripts/knowledge_lint.py`) and the derived catalog
(`scripts/knowledge_catalog.py`) enumerate the corpus through the `ENTRY_RE` glob
**only**. A file that doesn't match — a legacy note named before the
`YYYY-MM-DD-type-slug` convention — is **invisible** to both, so a pre-conventions corpus
reads as a *false clean* across the whole toolchain. `minerva:migrate` is the one surface
that globs the **complement** of `ENTRY_RE` and inventories those invisible files.

It also reports the minerva 3.0 upgrade. Before 3.0 the wiki stored a catalog
(`index.md`) and a theme-grouped overview (`overview.md`) beside the entries, kept current
by a post-merge pass. 3.0 derives both on read from each entry's `**Theme**` and
`**Summary**` lines (`2026-10-01-decision-knowledge-aggregates-are-derived-on-read`), so a
corpus that still holds the legacy files has its catalog data in the wrong place: the
entries lack the metadata the catalog reads, and the routing section still sends readers
to files that will be deleted.

## Target

The `.minerva/knowledge/` corpus of the **current working tree**, resolved from
`git rev-parse --show-toplevel` — the same per-branch semantics `minerva:lint` uses —
plus the agent files (`CLAUDE.md` / `AGENTS.md` / `GEMINI.md`) at that root for the
routing check. Takes no work-unit argument; it audits the whole knowledge base.

## Step 1 — Run the shape signal (deterministic, read-only)

Run `migration_status` through its **importable Python API**, anchoring both the
`scripts/` import path and the corpus path to the working-tree root so it works from any
subdirectory (`scripts/migration_status.py` is read-only — it never writes):

```bash
ROOT="$(git rev-parse --show-toplevel)"; PLUGIN_SCRIPTS="$(python3 "$MINERVA_PLUGIN_ROOT/scripts/minerva_runtime.py" resolve --skill-file "$MINERVA_SKILL_FILE")" || exit 1; [ -n "$PLUGIN_SCRIPTS" ] && { python3 "$PLUGIN_SCRIPTS/plugin_guard.py" || exit 1; }; python3 -c "import sys, json; sys.path.insert(0, sys.argv[1]); \
from migration_status import migration_status; \
print(json.dumps(migration_status(sys.argv[2]), indent=2))" "$PLUGIN_SCRIPTS" "$ROOT/.minerva/knowledge"
```

The returned dict carries plain-primitive signals:

- `non_conforming_files` — `*.md` files in the knowledge dir that match neither id form
  (`YYYY-MM-DD-type-slug` or legacy `NNN-type-slug`), excluding the legacy aggregates.
  **The migration-unique signal** — these files are invisible to all other wiki tooling.
- `legacy_aggregates` — `index.md` / `overview.md` still present. **Presence is the
  migration need; an empty list is the migrated state.** 3.0 never writes either file.
- `entries_missing_metadata` — conforming entries with no `**Theme**` or no `**Summary**`
  line. The derived catalog lists them under `(unthemed)` / by H1 title, and lint flags
  them (an error for an entry dated 2026-10-01 or later, a warning for an older one).
- `stale_routing_files` — agent files whose `## minerva` section still names
  `.minerva/knowledge/overview.md` or `.minerva/knowledge/index.md`.
- `entries_without_related` — conforming entries whose `## Related` block is absent or
  empty (no forward cross-ref edges). Advisory: derived fence-aware from the detector's
  `parse_entry`, and robust to malformed legacy entries (a conforming-named file with no
  `**Type**` / no sections is counted, never crashed on).
- `conforming_entry_count` — how many entries already match the convention.

## Step 2 — Emit the migration checklist (read-only)

Translate the signal into a checklist. For each gap, **name** the skill that closes it and
a one-line effect — do **not** run it, and do not reproduce its findings. List the gaps in
this order, because it is the order they must be closed in:

1. **`non_conforming_files` non-empty** → rename each file by hand to
   `<YYYY-MM-DD>-<type>-<slug>.md` (type is `decision` / `bug` / `pattern` / `constraint` /
   `reference`) so the tooling can see it; a free-form note has no id to derive, so the
   name is a judgment call. **Legacy `NNN-` entries** (conforming, but pre-date-id) are
   renamed automatically by **`minerva:migrate-fix`**, which derives each date from git
   and retargets every wikilink. Do renames first: the backfill below matches entries to
   their legacy catalog lines by stem.
2. **`legacy_aggregates` non-empty, or `entries_missing_metadata` non-empty** → run
   **`minerva:migrate-fix`**. Its backfill fills each missing `**Summary**` from the
   legacy `index.md` line and each missing `**Theme**` from the `overview.md` section that
   links the entry, then deletes both legacy files. Entries it cannot fill are reported
   for hand-writing — with no legacy files present, every listed entry needs its
   metadata written by hand.
3. **`stale_routing_files` non-empty** → re-run **`minerva:init`**; it detects the stale
   `## minerva` section and offers a gated refresh to the catalog one-liner.
4. **`entries_without_related` non-empty** → advisory. Authoring which entries relate (and
   the relationship label) is LLM judgment; add forward `## Related` links by hand where
   a real relationship exists. Nothing automates it.
5. **Always, after the corpus conforms** → run `minerva:lint` to confirm health.

Present it as a numbered checklist with the counts from the signal, then **stop**. If
`non_conforming_files`, `legacy_aggregates`, `entries_missing_metadata` and
`stale_routing_files` are all empty, report: `migration: corpus is in conforming shape
(<N> entries) — run minerva:lint to confirm health.` (mention `entries_without_related`
as an advisory count if non-zero).

## Out of scope

- **Any file mutation** — no renames, no metadata writes, no routing edits. This skill
  reports; the gated remediation lives in `minerva:migrate-fix` and `minerva:init` (run
  by the user), and the judged work is done by hand.
- **Editing the detector** (`scripts/knowledge_lint.py`) — `migration_status` consumes
  its `ENTRY_RE` / `parse_entry` API, never re-derives it.
- **Being a health check** — broken links and contradictions are owned by `minerva:lint`;
  this skill checks *shape*, not *health*.
- **Scanning subdirectories** — like the detector and the catalog, `migration_status`
  globs `*.md` non-recursively (top-level of `.minerva/knowledge/` only); entries nested in
  a subdirectory are not inventoried.
