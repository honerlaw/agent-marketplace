#!/usr/bin/env python3
"""Deterministic, read-only **migration-shape** signal for the `.minerva/knowledge/` wiki.

Answers the one question no other wiki tool can: *which files in the knowledge dir are
INVISIBLE to the wiki tooling, and is the corpus in the conforming shape the tooling
requires?*

The detector (`knowledge_lint`), the fixer (`knowledge_fix`), and `synthesis_status` all
enumerate the corpus via the `ENTRY_RE` glob ONLY. So a legacy corpus of non-conforming
files (entries predating the `NNN-type-slug` convention) reads as a *false clean* across
all of them — the files are simply never seen. This module globs the COMPLEMENT of
`ENTRY_RE` to inventory exactly those invisible files, plus a few cheap structural
presence/shape signals, so `minerva:migrate` can turn a false-clean legacy corpus into an
actionable conformance checklist.

It reuses the frozen detector's primitives (`ENTRY_RE`, and `parse_entry` — itself
fence-aware via `_strip_fences`) rather than re-deriving the grammar (knowledge entries
019 / 021 / 023), and returns only
plain JSON-serializable primitives (the same style as `synthesis_status`) — never lint's
`Finding` namedtuples, so this tool is not coupled to the frozen detector's internal
schema.

This is a SHAPE check, not a HEALTH check: a clean inventory (all files conforming,
index + overview present) can still coexist with `minerva:lint` index-drift errors. A
passing migration inventory still requires a green `minerva:lint` + `minerva:synthesize`
pass. Read-only; never writes.
"""
import json
import sys
from pathlib import Path

from knowledge_lint import ENTRY_RE, is_conforming_id, parse_entry

# Reserved non-entry files that legitimately live in the knowledge dir and must NOT be
# flagged as non-conforming. Extensible: the planned Phase-C `log.md` increment would be
# added here.
RESERVED_NONENTRY = {"index.md", "overview.md"}


def migration_status(knowledge_dir) -> dict:
    """Return the deterministic migration-shape signal for `knowledge_dir`.

    Keys (all JSON-serializable primitives — no lint Finding namedtuples):
      non_conforming_files   sorted list[str] of *.md filenames that do NOT match
                             ENTRY_RE and are not in RESERVED_NONENTRY — the
                             migration-unique signal (files invisible to all wiki tooling)
      index_present          bool
      overview_present       bool
      entries_without_related sorted list[str] of conforming entry filenames whose
                             `## Related` block is absent or empty (no cross-ref edges)
      conforming_entry_count int
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

    return {
        "non_conforming_files": non_conforming,
        "index_present": (kd / "index.md").exists(),
        "overview_present": (kd / "overview.md").exists(),
        "entries_without_related": without_related,
        "conforming_entry_count": len(entry_paths),
    }


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    knowledge_dir = argv[0] if argv else ".minerva/knowledge"
    print(json.dumps(migration_status(knowledge_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
