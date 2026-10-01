#!/usr/bin/env python3
"""Deterministic, read-only **migration-shape** signal for the `.minerva/knowledge/` wiki.

Answers the question no other wiki tool can: *is this corpus in the shape the current
tooling reads, and if not, what moves it there?* Three gaps are reported:

- **invisible files** — the wiki tools (`knowledge_lint`, `knowledge_catalog`) enumerate the
  corpus via the `ENTRY_RE` glob ONLY, so a legacy file that does not conform to
  `<id>-<type>-<slug>.md` is never seen: a *false clean*. This module globs the complement.
- **legacy aggregates** — a pre-3.0 corpus keeps `index.md` / `overview.md` beside its
  entries. 3.0 derives both on read, so their PRESENCE is now the migration need and their
  absence is the migrated state (`minerva:migrate-fix` folds them into the entries via
  `knowledge_backfill.py`).
- **stale routing** — an agent file whose `## minerva` section still routes readers to
  `overview.md` / `index.md`, which a migrated corpus no longer has (`minerva:init` refreshes it).

Plus two per-entry signals: entries missing the `**Theme**` / `**Summary**` lines the catalog
reads, and entries with no `## Related` edges (advisory — forward links are still the wiki's
cross-reference surface).

It reuses the detector's primitives (`ENTRY_RE`, `parse_entry` — fence-aware) rather than
re-deriving the grammar, and returns only plain JSON-serializable primitives, never lint's
`Finding` namedtuples. This is a SHAPE check, not a HEALTH check: a clean inventory can still
coexist with `knowledge_lint` errors. Read-only; never writes.
"""
import json
import sys
from pathlib import Path

from knowledge_lint import ENTRY_RE, is_conforming_id, parse_entry
from knowledge_spans import unfenced

# Pre-3.0 aggregates. Not flagged as non-conforming files — they are reported as the
# migration need under `legacy_aggregates` instead.
LEGACY_AGGREGATES = ("index.md", "overview.md")
RESERVED_NONENTRY = set(LEGACY_AGGREGATES)
AGENT_FILES = ("CLAUDE.md", "AGENTS.md", "GEMINI.md")
# What a pre-3.0 Routing section names. Either one means the section sends readers to a
# file a migrated corpus no longer has.
STALE_ROUTING_MARKERS = (".minerva/knowledge/overview.md", ".minerva/knowledge/index.md")


def _routing_section(text: str):
    """The `## minerva` section of an agent file (to the next `## ` or EOF), or None."""
    # Fence-aware: a `## minerva` or `## ` line inside a code block (the section's own
    # catalog one-liner sits in one) is content, not a section boundary.
    lines = list(unfenced(text.splitlines()))
    start = next((k for k, (_, ln) in enumerate(lines) if ln.strip() == "## minerva"), None)
    if start is None:
        return None
    end = next((k for k in range(start + 1, len(lines)) if lines[k][1].startswith("## ")),
               len(lines))
    return "\n".join(ln for _, ln in lines[start:end])


def stale_routing_files(project_root) -> list:
    """Agent files at `project_root` whose `## minerva` section routes to a legacy aggregate."""
    out = []
    for name in AGENT_FILES:
        path = Path(project_root) / name
        if not path.is_file():
            continue
        section = _routing_section(path.read_text())
        if section and any(marker in section for marker in STALE_ROUTING_MARKERS):
            out.append(name)
    return out


def migration_status(knowledge_dir) -> dict:
    """Return the deterministic migration-shape signal for `knowledge_dir`.

    Keys (all JSON-serializable primitives — no lint Finding namedtuples):
      non_conforming_files     sorted list[str] of *.md filenames that do NOT match ENTRY_RE
                               and are not a legacy aggregate — files invisible to all tools
      legacy_aggregates        sorted list[str] of `index.md` / `overview.md` still present —
                               the migration need (empty = migrated)
      entries_missing_metadata sorted list[str] of conforming entry filenames with no
                               `**Theme**` or no `**Summary**` line
      entries_without_related  sorted list[str] of conforming entry filenames whose
                               `## Related` block is absent or empty (advisory)
      stale_routing_files      agent files at the project root (two levels above
                               `knowledge_dir`) whose `## minerva` section names a legacy
                               aggregate
      conforming_entry_count   int
    """
    kd = Path(knowledge_dir)

    # Conformance is BOTH conditions: the stem shape AND a real id. `ENTRY_RE` is
    # shape-only, so `2026-13-45-pattern-x.md` matches it — and a file that matches the
    # glob is treated as a live entry by every wiki tool, which would let an impossible
    # date pass as conforming forever. Checking the calendar here is what keeps this a
    # genuine shape audit rather than a regex that agrees with itself.
    def _conforms(path) -> bool:
        m = ENTRY_RE.match(path.name)
        return bool(m) and is_conforming_id(m.group(1))

    md_files = sorted(p for p in kd.glob("*.md"))
    entry_paths = [p for p in md_files if _conforms(p)]

    non_conforming = sorted(
        p.name for p in md_files
        if not _conforms(p) and p.name not in RESERVED_NONENTRY
    )

    # entries_without_related: reuse the frozen, fence-aware parser. `related_out` is the
    # empty set both when the `## Related` header is absent AND when it is present but
    # carries no catalog links — both mean "this entry contributes no cross-ref edges".
    # parse_entry is robust to malformed entries (missing **Type** / sections) — it
    # returns a dict with empty `related_out` rather than raising — which is exactly the
    # legacy shape this tool is meant to inventory.
    without_related = sorted(
        p.name for p in entry_paths if not parse_entry(p)["related_out"]
    )

    missing_metadata = []
    for p in entry_paths:
        parsed = parse_entry(p)
        if not (parsed["theme"] and parsed["summary"]):
            missing_metadata.append(p.name)

    return {
        "non_conforming_files": non_conforming,
        "legacy_aggregates": [name for name in LEGACY_AGGREGATES if (kd / name).exists()],
        "entries_missing_metadata": sorted(missing_metadata),
        "entries_without_related": without_related,
        "stale_routing_files": stale_routing_files(kd.resolve().parent.parent),
        "conforming_entry_count": len(entry_paths),
    }


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    knowledge_dir = argv[0] if argv else ".minerva/knowledge"
    print(json.dumps(migration_status(knowledge_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
