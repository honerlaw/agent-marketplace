"""Fixture tests for the deterministic knowledge linter (`scripts/knowledge_lint.py`).

The wiki stores entries and nothing else — the catalog, backlinks and supersession are
derived on read by `knowledge_catalog.py` — so the linter checks only what an entry can
get wrong on its own: its id, its `## Related` links, and the `**Theme**`/`**Summary**`
lines the catalog reads. `test_live_knowledge_clean` runs the same function the CLI uses
against the real `.minerva/knowledge/`.
"""
from pathlib import Path

from knowledge_lint import METADATA_REQUIRED_FROM, lint_knowledge, main, parse_entry

REPO_ROOT = Path(__file__).resolve().parent.parent
LIVE_KNOWLEDGE = REPO_ROOT / ".minerva" / "knowledge"


# --- fixture builders --------------------------------------------------------
def entry(typ, slug, related=None, banner=None, extra_body="", theme="wiki",
          summary="a summary"):
    s = f"# {slug} title\n\n**Date**: 2026-06-02\n**Type**: {typ}\n"
    if theme:
        s += f"**Theme**: {theme}\n"
    if summary:
        s += f"**Summary**: {summary}\n"
    s += "**Context**: .minerva/work/x\n"
    if banner:  # (stem, stem)
        s += f"\n<!-- superseded-by: {banner[0]} -->\n> **Superseded by [[{banner[1]}]]** (2026-06-02)\n"
    s += "\n## Context\nc\n\n## Finding\nf\n" + extra_body + "\n## Implications\ni\n"
    if related:  # list of (stem, relationship)
        s += "\n## Related\n" + "".join(f"- [[{stem}]] — {rel}\n" for stem, rel in related)
    return s


def make_dir(tmp_path, files: dict):
    for name, content in files.items():
        (tmp_path / name).write_text(content)
    return tmp_path


def errors(findings):
    return [f for f in findings if f.severity == "error"]


# A clean two-entry baseline: two entries sharing a theme, one linking the other.
def clean(tmp_path):
    return make_dir(tmp_path, {
        "2026-10-02-decision-foo.md": entry("decision", "foo",
                                            related=[("2026-10-02-constraint-bar", "see also")]),
        "2026-10-02-constraint-bar.md": entry("constraint", "bar"),
    })


# --- clean corpus ------------------------------------------------------------
def test_clean_corpus_has_no_findings(tmp_path):
    assert lint_knowledge(clean(tmp_path)) == []


def test_a_one_way_link_needs_no_reciprocal(tmp_path):
    """Backlinks are derived, so a forward link alone is complete. The retired reciprocal
    check is what made every promote leave work for a post-merge reconciliation pass."""
    assert not any(f.family.startswith("reciprocal") for f in lint_knowledge(clean(tmp_path)))


def test_no_index_md_is_not_a_finding(tmp_path):
    """A corpus without `index.md` is the migrated, desired state — not a missing file."""
    assert not any("index.md" in f.message for f in lint_knowledge(clean(tmp_path)))


# --- ids -----------------------------------------------------------------------
def test_four_digit_entries_are_visible(tmp_path):
    r"""Legacy ids widened past 999 rather than wrapping; a fixed `\d{3}` would make the
    1000th entry invisible to every check at once."""
    d = make_dir(tmp_path, {
        "0999-decision-foo.md": entry("decision", "foo"),
        "1000-decision-bar.md": entry("decision", "bar", related=[("0999-decision-foo", "x")]),
    })
    assert lint_knowledge(d) == []
    (d / "1000-decision-bar.md").write_text(
        entry("decision", "bar", related=[("0998-decision-gone", "x")]))
    assert any("0998" in f.message for f in errors(lint_knowledge(d)))


def test_same_day_entries_are_not_duplicates(tmp_path):
    """Two entries sharing a DATE are ordinary and first-class: identity is the stem."""
    d = make_dir(tmp_path, {
        "2026-10-09-decision-foo.md": entry("decision", "foo"),
        "2026-10-09-bug-bar.md": entry("bug", "bar"),
    })
    assert lint_knowledge(d) == []


def test_impossible_date_is_reported(tmp_path):
    """`ENTRY_RE` is shape-only, so `2026-13-45` matches it. Conformance must check
    the calendar, or a typo passes as a valid entry forever."""
    d = make_dir(tmp_path, {"2026-13-45-decision-foo.md": entry("decision", "foo")})
    f = errors(lint_knowledge(d))
    assert any(x.family == "id" and "2026-13-45" in x.message for x in f)


# --- broken links ------------------------------------------------------------
def test_broken_related_link(tmp_path):
    d = make_dir(tmp_path, {"2026-10-02-decision-foo.md": entry(
        "decision", "foo", related=[("2026-10-02-bug-gone", "see also")])})
    f = errors(lint_knowledge(d))
    assert len(f) == 1 and f[0].family == "broken-link" and "2026-10-02-bug-gone" in f[0].message


def test_lint_reports_a_broken_link_on_a_multi_target_line(tmp_path):
    """The second target of a shared line is a real edge, so a dangling one is a real
    broken link."""
    (tmp_path / "001-decision-foo.md").write_text(
        entry("decision", "foo") + "\n## Related\n- [[001-decision-foo]] / [[999-bug-gone]] — x\n")
    msgs = [f.message for f in lint_knowledge(tmp_path)]
    assert any("999-bug-gone" in m for m in msgs)


# --- metadata --------------------------------------------------------------------
def test_a_new_entry_without_theme_or_summary_is_an_error(tmp_path):
    d = make_dir(tmp_path, {f"{METADATA_REQUIRED_FROM}-decision-foo.md":
                            entry("decision", "foo", theme=None, summary=None)})
    f = errors(lint_knowledge(d))
    assert {x.family for x in f} == {"metadata"} and len(f) == 2


def test_an_older_entry_without_theme_or_summary_is_only_a_warning(tmp_path):
    """A consumer corpus that has not run `minerva:migrate-fix` stays green."""
    d = make_dir(tmp_path, {
        "2026-09-30-decision-foo.md": entry("decision", "foo", theme=None, summary=None),
        "042-bug-bar.md": entry("bug", "bar", theme=None, summary=None),
    })
    f = lint_knowledge(d)
    assert errors(f) == [] and sum(x.family == "metadata" for x in f) == 4


def test_the_metadata_rule_does_not_flip_when_a_legacy_index_reappears(tmp_path):
    """Keyed on the entry's own date, never on `index.md`: a 2.x cleanup or a stale CI job
    can recreate that file, and enforcement must not silently relax with it."""
    d = make_dir(tmp_path, {f"{METADATA_REQUIRED_FROM}-decision-foo.md":
                            entry("decision", "foo", summary=None)})
    (d / "index.md").write_text("# Knowledge index\n")
    f = lint_knowledge(d)
    assert [x.family for x in errors(f)] == ["metadata"]
    assert any(x.family == "legacy" for x in f)


def test_a_fenced_theme_line_is_not_the_field(tmp_path):
    p = make_dir(tmp_path, {"2026-10-02-pattern-foo.md": entry(
        "pattern", "foo", theme=None, extra_body="\n```\n**Theme**: wiki\n```\n")})
    assert parse_entry(p / "2026-10-02-pattern-foo.md")["theme"] is None


# --- legacy aggregates and theme drift -------------------------------------------
def test_legacy_aggregates_are_warnings_naming_migrate_fix(tmp_path):
    d = clean(tmp_path)
    (d / "index.md").write_text("# Knowledge index\n")
    (d / "overview.md").write_text("# Knowledge overview\n")
    f = lint_knowledge(d)
    legacy = [x for x in f if x.family == "legacy"]
    assert errors(f) == [] and len(legacy) == 2
    assert all("minerva:migrate-fix" in x.message for x in legacy)


def test_a_singleton_theme_is_an_advisory_warning(tmp_path):
    d = make_dir(tmp_path, {
        "2026-10-02-decision-foo.md": entry("decision", "foo", theme="wiki"),
        "2026-10-02-bug-bar.md": entry("bug", "bar", theme="wikki"),
        "2026-10-02-bug-baz.md": entry("bug", "baz", theme="wiki"),
    })
    f = lint_knowledge(d)
    assert errors(f) == []
    assert [x.message.split("'")[1] for x in f if x.family == "theme"] == ["wikki"]


# --- false-positive guards (must NOT flag) -----------------------------------
def test_fenced_related_example_is_ignored(tmp_path):
    """A ## Related example inside a code fence must not be parsed as the block.

    Discriminating: the fenced example is placed AFTER the real ## Related block, so
    a non-fence-aware "last ## Related header wins" parser would select the fenced
    one and flag its bogus link. Only genuine fence-tracking keeps this clean.
    """
    real = entry("decision", "foo", related=[("2026-10-02-constraint-bar", "see also")])
    fenced_after = (
        "\nFor reference, the convention is:\n\n```markdown\n## Related\n"
        "- [[2026-10-02-decision-bogus]] — see also\n```\n"
    )
    d = make_dir(tmp_path, {
        "2026-10-02-decision-foo.md": real + fenced_after,
        "2026-10-02-constraint-bar.md": entry("constraint", "bar"),
    })
    assert lint_knowledge(d) == []


def test_inline_prose_link_is_not_an_edge(tmp_path):
    """An inline [[stem]] in prose (outside ## Related) is neither a link nor an edge."""
    d = make_dir(tmp_path, {
        "2026-10-02-decision-foo.md": entry(
            "decision", "foo", extra_body="\nSee [[2026-10-02-decision-bogus]] for context.\n"),
        "2026-10-02-constraint-bar.md": entry("constraint", "bar"),
    })
    assert lint_knowledge(d) == []


# --- CLI exit code -----------------------------------------------------------
def test_main_exits_nonzero_on_error(tmp_path):
    d = make_dir(tmp_path, {"2026-10-02-decision-foo.md": entry(
        "decision", "foo", related=[("2026-10-02-bug-gone", "x")])})
    assert main([str(d)]) == 1


def test_main_exits_zero_on_clean(tmp_path):
    assert main([str(clean(tmp_path))]) == 0


# --- live corpus -------------------------------------------------------------
def test_live_knowledge_clean():
    """The real .minerva/knowledge/ wiki must pass the deterministic linter."""
    findings = lint_knowledge(LIVE_KNOWLEDGE)
    assert errors(findings) == [], "\n".join(f.message for f in errors(findings))


# --- type resolution (unit 051) ----------------------------------------------
# `declared_type` used to come from one spelling of one body line. Real corpora carry
# it in four places, and an entry the parser could not read was reported as a mismatch
# it did not have and could never be relocated. Each case below is a shape that exists
# in a live corpus.
def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text)
    return p


def test_type_field_canonical_spelling(tmp_path):
    p = _write(tmp_path, "001-pattern-foo.md", "# t\n\n**Type**: pattern\n\n## Context\nc\n")
    assert parse_entry(p)["declared_type"] == "pattern"


def test_type_field_colon_inside_the_bold_markers(tmp_path):
    p = _write(tmp_path, "001-constraint-foo.md", "# t\n\n**Type:** constraint\n\n## Context\nc\n")
    assert parse_entry(p)["declared_type"] == "constraint"


def test_type_field_plain_no_bold(tmp_path):
    p = _write(tmp_path, "001-pattern-foo.md", "# t\n\nType: pattern\n\n## Context\nc\n")
    assert parse_entry(p)["declared_type"] == "pattern"


def test_type_falls_back_to_frontmatter(tmp_path):
    p = _write(tmp_path, "001-bug-foo.md",
               "---\nname: foo\nmetadata:\n  type: bug\n---\n\n# t\n\n## Context\nc\n")
    assert parse_entry(p)["declared_type"] == "bug"


def test_type_falls_back_to_the_filename(tmp_path):
    """The last resort, and the only source that always exists. Entries whose type
    lives solely in a prose H1 (`# 426 — bug: …`) land here."""
    p = _write(tmp_path, "426-bug-foo.md", "# 426 — bug: something broke\n\nprose\n")
    assert parse_entry(p)["declared_type"] == "bug"


def test_body_field_beats_frontmatter_and_filename(tmp_path):
    """Ordering is the safety property: a fallback may only ever fill a gap. An entry
    misnamed against its own stated type keeps the type it states."""
    p = _write(tmp_path, "001-pattern-foo.md",
               "---\nmetadata:\n  type: bug\n---\n\n# t\n\n**Type**: constraint\n\n## Context\nc\n")
    assert parse_entry(p)["declared_type"] == "constraint"


def test_frontmatter_beats_the_filename(tmp_path):
    p = _write(tmp_path, "001-pattern-foo.md",
               "---\nmetadata:\n  type: decision\n---\n\n# t\n\n## Context\nc\n")
    assert parse_entry(p)["declared_type"] == "decision"


def test_a_fenced_type_line_is_not_read_as_the_field(tmp_path):
    """`parse_entry` scans non-fenced lines; a documentation example inside a fence
    must not become the entry's own type."""
    p = _write(tmp_path, "001-pattern-foo.md",
               "# t\n\n```\n**Type**: bug\n```\n\n## Context\nc\n")
    assert parse_entry(p)["declared_type"] == "pattern"  # from the filename, not the fence


def test_a_body_type_line_is_not_mistaken_for_frontmatter(tmp_path):
    """The frontmatter scan must stop at the closing `---`. A single span-both pattern
    reaches past it and reads the body."""
    p = _write(tmp_path, "001-pattern-foo.md",
               "---\nname: foo\n---\n\n# t\n\n```yaml\ntype: bug\n```\n\n## Context\nc\n")
    assert parse_entry(p)["declared_type"] == "pattern"  # filename, not the fenced body line


# --- the shared edge model (lint and the derived catalog read edges the same way) ---
def test_every_wikilink_in_the_related_block_is_an_edge():
    """`- [[a]] / [[b]] — label` states two edges, and the editor already treats the
    second as a real back-link. The detector read only the first, because it derived
    edges from the start-anchored CATALOG_LINE_RE."""
    from knowledge_lint import related_edges
    text = "# t\n\n## Related\n- [[2026-01-01-decision-a]] / [[2026-01-02-pattern-b]] — both\n"
    assert {t for t, _ in related_edges(text)} == {
        "2026-01-01-decision-a", "2026-01-02-pattern-b"}


def test_a_multi_target_line_carries_no_label():
    """There is no single label for a two-target line, so the label is None rather than
    one invented from the line's tail."""
    from knowledge_lint import related_edges
    text = "# t\n\n## Related\n- [[2026-01-01-decision-a]] / [[2026-01-02-pattern-b]] — both\n"
    assert {lab for _, lab in related_edges(text)} == {None}


def test_a_single_target_line_still_carries_its_label():
    from knowledge_lint import related_edges
    text = "# t\n\n## Related\n- [[2026-01-01-decision-a]] — supersedes\n"
    assert related_edges(text) == [("2026-01-01-decision-a", "supersedes")]


def test_a_labelled_edge_upgrades_an_earlier_unlabelled_mention():
    """A stray mention must not suppress the properly-labelled line further down, or the
    catalog would miss a supersession the entry does state correctly."""
    from knowledge_lint import related_edges
    text = ("# t\n\n## Related\n"
            "- [[2026-01-01-decision-a]] / [[2026-01-02-pattern-b]] — both\n"
            "- [[2026-01-01-decision-a]] — supersedes\n")
    assert dict(related_edges(text))["2026-01-01-decision-a"] == "supersedes"


def test_a_fenced_related_block_states_no_edges():
    from knowledge_lint import related_edges
    text = "# t\n\n## Related\n```\n- [[2026-01-01-decision-a]] — supersedes\n```\n"
    assert related_edges(text) == []




def test_an_inverted_supersedes_edge_is_a_warning(tmp_path):
    d = make_dir(tmp_path, {
        "2026-10-02-decision-old.md": entry(
            "decision", "old", related=[("2026-10-05-decision-new", "supersedes: oops")]),
        "2026-10-05-decision-new.md": entry("decision", "new"),
    })
    f = lint_knowledge(d)
    assert errors(f) == []
    assert [x.family for x in f] == ["supersession"]
    assert "superseded by" in f[0].message
