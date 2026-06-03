"""Fixture tests for the deterministic migration-shape signal
(`scripts/migration_status.py`).

Exercises the migration-unique signal (`non_conforming_files` — files invisible to the
ENTRY_RE-globbing wiki tooling), the `RESERVED_NONENTRY` allowlist exemption, the
index/overview presence bools, and `entries_without_related` — including the load-bearing
case that a malformed conforming-named entry (no `**Type**` / no `## Related`) is COUNTED,
not crashed on (the exact legacy shape this tool targets). `test_live_corpus_migrated`
asserts the real, already-migrated `.minerva/knowledge/` reports a clean shape.

Imports only `migration_status` (which transitively reuses `knowledge_lint`) — nothing
that drags in the unrelated `lib`-dependent modules that abort bare collection.
"""
from pathlib import Path

from migration_status import RESERVED_NONENTRY, migration_status

REPO_ROOT = Path(__file__).resolve().parent.parent
LIVE_KNOWLEDGE = REPO_ROOT / ".minerva" / "knowledge"


# --- fixture builders --------------------------------------------------------
def entry(typ, slug, related=None):
    s = (f"# {slug} title\n\n**Date**: 2026-06-03\n**Type**: {typ}\n"
         "**Context**: .minerva/work/x\n\n## Context\nc\n\n## Finding\nf\n")
    if related:  # list of (stem, relationship)
        s += "\n## Related\n" + "".join(f"- [[{stem}]] — {rel}\n" for stem, rel in related)
    return s


def make_corpus(tmp_path, entries: dict, index=False, overview=False, extra=None):
    for name, content in entries.items():
        (tmp_path / name).write_text(content)
    if index:
        (tmp_path / "index.md").write_text("# Knowledge index\n<!-- index-watermark: 000 -->\n")
    if overview:
        (tmp_path / "overview.md").write_text("# Knowledge overview\n<!-- synthesis-watermark: 000 -->\n")
    for name, content in (extra or {}).items():
        (tmp_path / name).write_text(content)
    return tmp_path


# --- non_conforming_files (the migration-unique signal) ----------------------
def test_non_conforming_files_flagged(tmp_path):
    make_corpus(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo", [("001-decision-foo", "see also")])},
        extra={
            "legacy-note.md": "# an old note, no NNN prefix\n",
            "2024-payment.md": "# pre-convention name\n",
        },
    )
    st = migration_status(tmp_path)
    assert st["non_conforming_files"] == ["2024-payment.md", "legacy-note.md"]
    assert st["conforming_entry_count"] == 1


def test_reserved_nonentry_exempt(tmp_path):
    # index.md and overview.md don't match ENTRY_RE but must NOT be flagged.
    make_corpus(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo", [("001-decision-foo", "see also")])},
        index=True,
        overview=True,
    )
    st = migration_status(tmp_path)
    assert st["non_conforming_files"] == []  # reserved files exempt
    assert st["index_present"] is True
    assert st["overview_present"] is True
    assert RESERVED_NONENTRY == {"index.md", "overview.md"}


def test_presence_bools_false_when_absent(tmp_path):
    make_corpus(tmp_path, {"001-decision-foo.md": entry("decision", "foo")})
    st = migration_status(tmp_path)
    assert st["index_present"] is False
    assert st["overview_present"] is False


# --- entries_without_related -------------------------------------------------
def test_entries_without_related_absent_and_empty_block(tmp_path):
    no_related = entry("decision", "foo")  # no ## Related header at all
    empty_related = entry("pattern", "bar") + "\n## Related\n"  # header, no links
    has_related = entry("constraint", "baz", [("001-decision-foo", "see also")])
    make_corpus(tmp_path, {
        "001-decision-foo.md": no_related,
        "002-pattern-bar.md": empty_related,
        "003-constraint-baz.md": has_related,
    })
    st = migration_status(tmp_path)
    # both the absent-header and the present-but-empty entries count
    assert st["entries_without_related"] == ["001-decision-foo.md", "002-pattern-bar.md"]


def test_fenced_related_example_does_not_count_as_real(tmp_path):
    # A fenced ## Related example is not a real edge (knowledge 023) — the entry still
    # counts as without-related.
    fenced = (entry("decision", "foo")
              + "\nSee the convention:\n```\n## Related\n- [[001-decision-foo]] — see also\n```\n")
    make_corpus(tmp_path, {"001-decision-foo.md": fenced})
    st = migration_status(tmp_path)
    assert st["entries_without_related"] == ["001-decision-foo.md"]


def test_malformed_conforming_entry_counted_not_crashed(tmp_path):
    # The legacy shape this tool targets: a conforming FILENAME but garbage body —
    # no **Type**, no sections, no ## Related. Must be COUNTED, never raise.
    make_corpus(tmp_path, {
        "099-decision-malformed.md": "just some legacy prose, no minerva structure at all\n",
    })
    st = migration_status(tmp_path)  # must not raise
    assert st["entries_without_related"] == ["099-decision-malformed.md"]
    assert st["conforming_entry_count"] == 1
    assert st["non_conforming_files"] == []  # the NAME conforms; only the body is legacy


def test_empty_dir_no_crash(tmp_path):
    st = migration_status(tmp_path)
    assert st["non_conforming_files"] == []
    assert st["entries_without_related"] == []
    assert st["conforming_entry_count"] == 0
    assert st["index_present"] is False


# --- return shape ------------------------------------------------------------
def test_returns_plain_primitives_only(tmp_path):
    import json
    make_corpus(tmp_path, {"001-decision-foo.md": entry("decision", "foo")}, index=True)
    st = migration_status(tmp_path)
    # JSON-serializable end to end (no Finding namedtuples or other objects)
    json.dumps(st)
    assert set(st) == {
        "non_conforming_files", "index_present", "overview_present",
        "entries_without_related", "conforming_entry_count",
    }


# --- live corpus -------------------------------------------------------------
def test_live_corpus_migrated():
    """The real corpus is already migrated: no non-conforming files, index+overview present."""
    st = migration_status(LIVE_KNOWLEDGE)
    assert st["non_conforming_files"] == [], st["non_conforming_files"]
    assert st["index_present"] is True
    assert st["overview_present"] is True
