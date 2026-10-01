"""Fixture tests for the deterministic migration-shape signal
(`scripts/migration_status.py`).

Exercises the migration-unique signal (`non_conforming_files` — files invisible to the
ENTRY_RE-globbing wiki tooling), the legacy-aggregate signal (whose polarity inverted in
3.0: a present `index.md`/`overview.md` is now the migration need), missing Theme/Summary,
stale agent-file routing, and `entries_without_related` — including the load-bearing
case that a malformed conforming-named entry (no `**Type**` / no `## Related`) is COUNTED,
not crashed on (the exact legacy shape this tool targets). `test_live_corpus_migrated`
asserts the real, already-migrated `.minerva/knowledge/` reports a clean shape.

Imports only `migration_status` (which transitively reuses `knowledge_lint`) — nothing
that drags in the unrelated `lib`-dependent modules that abort bare collection.
"""
from pathlib import Path

from migration_status import RESERVED_NONENTRY, migration_status, stale_routing_files

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


def test_legacy_aggregates_are_the_migration_need_not_invisible_files(tmp_path):
    # index.md and overview.md don't match ENTRY_RE; they are reported as the migration
    # need, never as non-conforming files.
    make_corpus(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo", [("001-decision-foo", "see also")])},
        index=True,
        overview=True,
    )
    st = migration_status(tmp_path)
    assert st["non_conforming_files"] == []
    assert st["legacy_aggregates"] == ["index.md", "overview.md"]
    assert RESERVED_NONENTRY == {"index.md", "overview.md"}


def test_absent_aggregates_are_the_migrated_state(tmp_path):
    make_corpus(tmp_path, {"001-decision-foo.md": entry("decision", "foo")})
    assert migration_status(tmp_path)["legacy_aggregates"] == []


def test_entries_missing_metadata(tmp_path):
    themed = entry("decision", "bar").replace(
        "**Context**", "**Theme**: wiki\n**Summary**: s\n**Context**")
    make_corpus(tmp_path, {"001-decision-foo.md": entry("decision", "foo"),
                           "002-decision-bar.md": themed})
    assert migration_status(tmp_path)["entries_missing_metadata"] == ["001-decision-foo.md"]


def test_stale_routing_is_a_section_naming_a_legacy_aggregate(tmp_path):
    (tmp_path / "CLAUDE.md").write_text(
        "# Project\n\n## minerva\n\n- `.minerva/knowledge/overview.md` — read first\n")
    (tmp_path / "AGENTS.md").write_text(
        "## minerva\n\n- `.minerva/knowledge/` — entries\n\n## Other\n"
        "`.minerva/knowledge/index.md` outside the section does not count\n")
    assert stale_routing_files(tmp_path) == ["CLAUDE.md"]
    kd = tmp_path / ".minerva" / "knowledge"
    kd.mkdir(parents=True)
    assert migration_status(kd)["stale_routing_files"] == ["CLAUDE.md"]


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
    assert st["legacy_aggregates"] == []


# --- return shape ------------------------------------------------------------
def test_returns_plain_primitives_only(tmp_path):
    import json
    make_corpus(tmp_path, {"001-decision-foo.md": entry("decision", "foo")}, index=True)
    st = migration_status(tmp_path)
    # JSON-serializable end to end (no Finding namedtuples or other objects)
    json.dumps(st)
    assert set(st) == {
        "non_conforming_files", "legacy_aggregates", "entries_missing_metadata",
        "entries_without_related", "stale_routing_files", "conforming_entry_count",
    }


# --- live corpus -------------------------------------------------------------
def test_live_corpus_migrated():
    """The real corpus is fully migrated to the 3.0 shape."""
    st = migration_status(LIVE_KNOWLEDGE)
    assert st["non_conforming_files"] == [], st["non_conforming_files"]
    assert st["legacy_aggregates"] == []
    assert st["entries_missing_metadata"] == []
    assert st["stale_routing_files"] == []
