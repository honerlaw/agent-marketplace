"""Fixture tests for the deterministic knowledge linter (`scripts/knowledge_lint.py`).

Each defect family is exercised on a synthetic temp corpus, plus false-positive
guards for the cases the live corpus 015/016/017 would otherwise trip
(builds-on↔see-also reciprocity, banner-borne back-links, a fenced `## Related`
example, inline-prose links). `test_live_knowledge_clean` runs the same function the
CLI uses against the real `.minerva/knowledge/`.
"""
from pathlib import Path

from knowledge_lint import lint_knowledge, main

REPO_ROOT = Path(__file__).resolve().parent.parent
LIVE_KNOWLEDGE = REPO_ROOT / ".minerva" / "knowledge"


# --- fixture builders --------------------------------------------------------
def entry(typ, slug, related=None, banner=None, extra_body=""):
    s = f"# {slug} title\n\n**Date**: 2026-06-02\n**Type**: {typ}\n**Context**: .minerva/work/x\n"
    if banner:  # (nnn, stem)
        s += f"\n<!-- superseded-by: {banner[0]} -->\n> **Superseded by [[{banner[1]}]]** (2026-06-02)\n"
    s += "\n## Context\nc\n\n## Finding\nf\n" + extra_body + "\n## Implications\ni\n"
    if related:  # list of (stem, relationship)
        s += "\n## Related\n" + "".join(f"- [[{stem}]] — {rel}\n" for stem, rel in related)
    return s


def index(watermark, decisions=(), bugs=(), patterns=(), constraints=()):
    s = f"# Knowledge index\n<!-- index-watermark: {watermark} -->\n"
    for header, items in [("## Decisions", decisions), ("## Bugs", bugs),
                          ("## Patterns", patterns), ("## Constraints", constraints)]:
        s += f"\n{header}\n" + "".join(f"- [[{stem}]] — summary\n" for stem in items)
    return s


def make_dir(tmp_path, files: dict, index_text: str):
    for name, content in files.items():
        (tmp_path / name).write_text(content)
    (tmp_path / "index.md").write_text(index_text)
    return tmp_path


def errors(findings):
    return [f for f in findings if f.severity == "error"]


def families(findings):
    return {f.family for f in findings}


# A clean two-entry baseline.
def clean(tmp_path):
    return make_dir(
        tmp_path,
        {
            "001-decision-foo.md": entry("decision", "foo"),
            "002-constraint-bar.md": entry("constraint", "bar"),
        },
        index("002", decisions=["001-decision-foo"], constraints=["002-constraint-bar"]),
    )


# --- clean corpus ------------------------------------------------------------
def test_clean_corpus_has_no_findings(tmp_path):
    assert lint_knowledge(clean(tmp_path)) == []


# --- index drift -------------------------------------------------------------
def test_watermark_below_max_is_a_lagging_floor_not_drift(tmp_path):
    """The invariant is `watermark <= max NNN`, not equality.

    This is what lets an add-only `minerva:promote` leave the index untouched on a
    work-unit branch: the new entry sits above the floor and is *pending*, so the
    branch's CI drift gate stays green until reconciliation catalogues it.
    """
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "002-constraint-bar.md": entry("constraint", "bar")},
        index("001", decisions=["001-decision-foo"]),  # 002 not yet catalogued
    )
    findings = lint_knowledge(d)
    assert errors(findings) == []
    assert any(x.severity == "warning" and "pending reconciliation" in x.message
               for x in findings)


def test_watermark_above_max_is_an_error(tmp_path):
    """The floor may lag the corpus; it may never claim entries that don't exist."""
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo")},
        index("009", decisions=["001-decision-foo"]),
    )
    f = errors(lint_knowledge(d))
    assert any("watermark" in x.message for x in f)


def test_pending_entry_forward_link_needs_no_reciprocal_yet(tmp_path):
    """An add-only promote writes forward links only; reciprocals come later.

    Without this, every work-unit branch would trip the reciprocal check as an error
    for each cross-link its new entry declares.
    """
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "002-constraint-bar.md": entry("constraint", "bar",
                                        related=[("001-decision-foo", "builds on")])},
        index("001", decisions=["001-decision-foo"]),
    )
    findings = lint_knowledge(d)
    assert errors(findings) == []
    assert any(x.family == "reciprocal" and x.severity == "warning" for x in findings)


def test_missing_reciprocal_below_the_floor_is_still_an_error(tmp_path):
    """Reconciled entries get no leniency — the pending carve-out is keyed on NNN."""
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "002-constraint-bar.md": entry("constraint", "bar",
                                        related=[("001-decision-foo", "builds on")])},
        index("002", decisions=["001-decision-foo"],
              constraints=["002-constraint-bar"]),
    )
    f = errors(lint_knowledge(d))
    assert any(x.family == "reciprocal" for x in f)


def test_duplicate_nnn_is_detected(tmp_path):
    """Two entries sharing an id — invisible before, because every lookup was
    NNN-keyed and the second file silently overwrote the first."""
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "001-bug-bar.md": entry("bug", "bar")},
        index("001", decisions=["001-decision-foo"]),
    )
    f = errors(lint_knowledge(d))
    assert any(x.family == "duplicate" for x in f)
    assert any("001-bug-bar.md" in x.message and "001-decision-foo.md" in x.message
               for x in f)


def test_entry_missing_catalog_line(tmp_path):
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "002-constraint-bar.md": entry("constraint", "bar")},
        index("002", decisions=["001-decision-foo"]),  # 002 omitted
    )
    f = errors(lint_knowledge(d))
    assert any("002 has no catalog line" in x.message for x in f)


def test_catalog_line_with_no_file(tmp_path):
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo")},
        index("001", decisions=["001-decision-foo", "003-decision-ghost"]),
    )
    f = errors(lint_knowledge(d))
    assert any("003 has no entry file" in x.message for x in f)


def test_wrong_type_section(tmp_path):
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "002-constraint-bar.md": entry("constraint", "bar")},
        # 002 (a constraint) listed under Decisions
        index("002", decisions=["001-decision-foo", "002-constraint-bar"]),
    )
    f = errors(lint_knowledge(d))
    assert any("002" in x.message and "section" in x.message for x in f)


def test_slug_mismatch_is_warning_not_error(tmp_path):
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo")},
        index("001", decisions=["001-decision-renamed"]),  # same NNN, different slug
    )
    findings = lint_knowledge(d)
    assert errors(findings) == []  # not an error
    assert any(f.severity == "warning" and "slug" in f.message for f in findings)


# --- broken links ------------------------------------------------------------
def test_broken_related_link(tmp_path):
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo",
                                      related=[("099-decision-missing", "see also")]),
         "002-constraint-bar.md": entry("constraint", "bar")},
        index("002", decisions=["001-decision-foo"], constraints=["002-constraint-bar"]),
    )
    f = errors(lint_knowledge(d))
    assert any("broken-link" == x.family and "099" in x.message for x in f)


# --- missing reciprocals -----------------------------------------------------
def test_one_way_reciprocal_missing_back_nnn(tmp_path):
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo",
                                      related=[("002-constraint-bar", "see also")]),
         "002-constraint-bar.md": entry("constraint", "bar")},  # no back-link
        index("002", decisions=["001-decision-foo"], constraints=["002-constraint-bar"]),
    )
    f = errors(lint_knowledge(d))
    assert any(x.family == "reciprocal" and "002 has no back-link to 001" in x.message
               for x in f)


# --- false-positive guards (must NOT flag) -----------------------------------
def test_builds_on_see_also_pair_passes(tmp_path):
    """builds on ↔ see also is a valid reciprocal pair (labels differ)."""
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo",
                                      related=[("002-constraint-bar", "builds on")]),
         "002-constraint-bar.md": entry("constraint", "bar",
                                        related=[("001-decision-foo", "see also")])},
        index("002", decisions=["001-decision-foo"], constraints=["002-constraint-bar"]),
    )
    assert lint_knowledge(d) == []


def test_banner_backlink_satisfies_reciprocity(tmp_path):
    """A back-link living in the supersession banner counts as reciprocity."""
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo",
                                      related=[("002-constraint-bar", "supersedes")]),
         # 002's only back-reference to 001 is its banner, not a ## Related line
         "002-constraint-bar.md": entry("constraint", "bar",
                                        banner=("001", "001-decision-foo"))},
        index("002", decisions=["001-decision-foo"], constraints=["002-constraint-bar"]),
    )
    recip = [f for f in lint_knowledge(d) if f.family == "reciprocal"]
    assert recip == []


def test_fenced_related_example_is_ignored(tmp_path):
    """A ## Related example inside a code fence must not be parsed as the block.

    Discriminating: the fenced example is placed AFTER the real ## Related block, so
    a non-fence-aware "last ## Related header wins" parser would select the fenced
    one and flag its bogus [[099]] link. Only genuine fence-tracking keeps this clean.
    """
    real_001 = entry("decision", "foo", related=[("002-constraint-bar", "see also")])
    fenced_after = (
        "\nFor reference, the convention is:\n\n```markdown\n## Related\n"
        "- [[099-decision-bogus]] — see also\n```\n"
    )
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": real_001 + fenced_after,
         "002-constraint-bar.md": entry("constraint", "bar",
                                        related=[("001-decision-foo", "see also")])},
        index("002", decisions=["001-decision-foo"], constraints=["002-constraint-bar"]),
    )
    findings = lint_knowledge(d)
    assert not any("099" in f.message for f in findings)  # fenced bogus link ignored
    assert findings == []  # the real reciprocal 001<->002 is clean


def test_inline_prose_link_is_not_an_edge(tmp_path):
    """An inline [[NNN]] in prose (outside ## Related) is neither a link nor an edge."""
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo",
                                      extra_body="\nSee [[099-decision-bogus]] for context.\n"),
         "002-constraint-bar.md": entry("constraint", "bar")},
        index("002", decisions=["001-decision-foo"], constraints=["002-constraint-bar"]),
    )
    assert lint_knowledge(d) == []  # prose mention is invisible to the linter


def test_prose_mention_of_banner_string_is_not_a_banner(tmp_path):
    """The literal `<!-- superseded-by: NNN -->` in body prose is not a banner."""
    # 001 links 002; 002 mentions the banner SYNTAX in prose but is not superseded,
    # and carries a real ## Related back-link. Reciprocity must hold via ## Related,
    # and the prose mention must not be parsed as a banner edge.
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo",
                                      related=[("002-constraint-bar", "see also")]),
         "002-constraint-bar.md": entry(
             "constraint", "bar",
             extra_body="\nA banner looks like `<!-- superseded-by: NNN -->` in prose.\n",
             related=[("001-decision-foo", "see also")])},
        index("002", decisions=["001-decision-foo"], constraints=["002-constraint-bar"]),
    )
    assert lint_knowledge(d) == []


# --- CLI exit code -----------------------------------------------------------
def test_main_exits_nonzero_on_error(tmp_path):
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo")},
        index("001", decisions=["001-decision-foo", "003-decision-ghost"]),
    )
    assert main([str(d)]) == 1


def test_main_exits_zero_on_clean(tmp_path):
    assert main([str(clean(tmp_path))]) == 0


# --- live corpus -------------------------------------------------------------
def test_live_knowledge_clean():
    """The real .minerva/knowledge/ wiki must pass the deterministic linter."""
    findings = lint_knowledge(LIVE_KNOWLEDGE)
    assert errors(findings) == [], "\n".join(f.message for f in errors(findings))
