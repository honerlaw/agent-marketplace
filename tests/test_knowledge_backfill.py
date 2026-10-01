"""Tests for the one-time legacy-aggregate migration (`scripts/knowledge_backfill.py`).

The backfill moves a pre-3.0 corpus's `index.md` summaries and `overview.md` theme
grouping onto the entries, then deletes both files. Its safety property is that it only
ever INSERTS metadata lines: every other byte of every entry is unchanged.
"""
from knowledge_backfill import (backfill, index_summaries, insert_metadata, main,
                                overview_themes, theme_slug)
from knowledge_catalog import load_entries

A, B, C = "2026-08-01-decision-a", "2026-08-02-bug-b", "041-pattern-c"
D = "2026-08-04-constraint-d"  # linked only by the second section


def entry(slug, typ="decision", summary=None, theme=None):
    s = f"# {slug} title\n\n**Date**: 2026-08-01\n**Type**: {typ}\n"
    if theme:
        s += f"**Theme**: {theme}\n"
    if summary:
        s += f"**Summary**: {summary}\n"
    s += ("**Context**: .minerva/work/x\n\n## Finding\nf\n\n```\n**Type**: fenced\n```\n"
          "\n## Related\n- [[2026-08-02-bug-b]] — see also\n")
    return s


INDEX = f"""# Knowledge index
<!-- index-watermark: 041 -->

## Decisions
- [[{A}]] — decides a
```
- [[{B}]] — fenced, not a catalog line
```

## Bugs
- [[{B}]] — fixes b
"""

OVERVIEW = f"""# Knowledge overview

Intro prose that mentions [[{C}]] before any theme section.

## The knowledge wiki: a navigable corpus

Narrative linking [[{A}]] and wrapping onto
## a line that is not a header [[{B}]].

## Concurrency: what shared state costs

[[{D}]], then [[{B}]] and [[{A}]] again — the first section already won.
"""


def legacy_corpus(tmp_path, files=None):
    files = files or {A: entry("a"), B: entry("b", typ="bug", summary="kept as written"),
                      C: entry("c", typ="pattern")}
    for stem, text in files.items():
        (tmp_path / f"{stem}.md").write_text(text)
    (tmp_path / "index.md").write_text(INDEX)
    (tmp_path / "overview.md").write_text(OVERVIEW)
    return tmp_path


def removed_inserted(before: str, after: str) -> str:
    """`after` minus the lines the backfill is allowed to add."""
    kept = [ln for ln in after.splitlines(keepends=True)
            if not ln.startswith(("**Theme**: ", "**Summary**: ")) or ln in before]
    return "".join(kept)


def test_theme_slug():
    assert theme_slug("The knowledge wiki: a navigable corpus") == "knowledge-wiki"
    assert theme_slug("Git worktrees and promote/scratchpad mechanics") == \
        "git-worktrees-and-promote-scratchpad-mechanics"
    assert theme_slug("An MCP server: transport") == "mcp-server"


def test_index_summaries_are_fence_aware():
    assert index_summaries(INDEX) == {A: "decides a", B: "fixes b"}


def test_overview_themes_take_the_first_linking_section():
    # B's link sits on a wrapped `## ` prose line inside the first section: still that section.
    assert overview_themes(OVERVIEW) == {A: "knowledge-wiki", B: "knowledge-wiki",
                                         D: "concurrency"}


def test_backfill_fills_moves_and_deletes(tmp_path):
    d = legacy_corpus(tmp_path)
    result = backfill(d)
    assert result["legacy"] == ["index.md", "overview.md"]
    assert not (d / "index.md").exists() and not (d / "overview.md").exists()
    entries = load_entries(d)
    assert (entries[A]["theme"], entries[A]["summary"]) == ("knowledge-wiki", "decides a")
    # an authored Summary wins over the index line; the theme still comes from the overview
    assert (entries[B]["theme"], entries[B]["summary"]) == ("knowledge-wiki", "kept as written")
    # linked only before the first section, and absent from the index: reported, not invented
    assert entries[C]["theme"] is None and entries[C]["summary"] is None
    assert result["no_theme"] == [C] and result["no_summary"] == [C]


def test_backfill_changes_no_byte_outside_inserted_lines(tmp_path):
    d = legacy_corpus(tmp_path)
    before = {p.name: p.read_text() for p in d.glob("[0-9]*.md")}
    backfill(d)
    for name, text in before.items():
        assert removed_inserted(text, (d / name).read_text()) == text


def test_inserted_lines_follow_the_type_line_in_template_order(tmp_path):
    d = legacy_corpus(tmp_path)
    backfill(d)
    lines = (d / f"{A}.md").read_text().splitlines()
    i = lines.index("**Type**: decision")
    assert lines[i + 1:i + 3] == ["**Theme**: knowledge-wiki", "**Summary**: decides a"]


def test_insert_falls_back_to_the_h1_without_type_or_date():
    text = "# Title\nprose\n\n## Finding\nf\n"
    assert insert_metadata(text, "wiki", "s") == \
        "# Title\n\n**Theme**: wiki\n**Summary**: s\nprose\n\n## Finding\nf\n"


def test_insert_handles_a_type_line_without_trailing_newline():
    assert insert_metadata("**Type**: bug", "wiki") == "**Type**: bug\n**Theme**: wiki\n"


def test_dry_run_writes_nothing(tmp_path):
    d = legacy_corpus(tmp_path)
    before = {p.name: p.read_text() for p in d.glob("*.md")}
    result = backfill(d, dry_run=True)
    assert result["edits"]
    assert {p.name: p.read_text() for p in d.glob("*.md")} == before


def test_a_migrated_corpus_is_a_no_op(tmp_path, capsys):
    d = legacy_corpus(tmp_path)
    backfill(d)
    after = {p.name: p.read_text() for p in d.glob("*.md")}
    assert backfill(d)["edits"] == {}
    assert {p.name: p.read_text() for p in d.glob("*.md")} == after
    assert main([str(d)]) == 0
    assert "already migrated" in capsys.readouterr().out


def test_an_entry_that_already_has_both_lines_is_untouched(tmp_path):
    d = legacy_corpus(tmp_path, {A: entry("a", summary="mine", theme="mine")})
    text = (d / f"{A}.md").read_text()
    assert backfill(d)["edits"] == {}
    assert (d / f"{A}.md").read_text() == text
