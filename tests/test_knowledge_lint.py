"""Fixture tests for the deterministic knowledge linter (`scripts/knowledge_lint.py`).

Each defect family is exercised on a synthetic temp corpus, plus false-positive
guards for the cases the live corpus 015/016/017 would otherwise trip
(builds-on↔see-also reciprocity, banner-borne back-links, a fenced `## Related`
example, inline-prose links). `test_live_knowledge_clean` runs the same function the
CLI uses against the real `.minerva/knowledge/`.
"""
from pathlib import Path

from knowledge_lint import lint_knowledge, main, parse_entry

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


def index(watermark, decisions=(), bugs=(), patterns=(), constraints=(), references=()):
    s = f"# Knowledge index\n<!-- index-watermark: {watermark} -->\n"
    for header, items in [("## Decisions", decisions), ("## Bugs", bugs),
                          ("## Patterns", patterns), ("## Constraints", constraints),
                          ("## References", references)]:
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
def test_watermark_below_max_is_not_drift(tmp_path):
    """The invariant is `watermark <= max NNN`, not equality.

    This is what lets an add-only `minerva:promote` leave the index untouched on a
    work-unit branch: the new entry is *pending*, so the branch's CI drift gate stays
    green until reconciliation catalogues it.
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


def test_out_of_order_merge_stays_green(tmp_path):
    """The regression that killed the scalar-floor design.

    Unit A allocates 050, unit B allocates 051. B merges and reconciles first, so the
    watermark reaches 051. A then merges — its entry is *below* the watermark. A floor
    comparison would call that drift: A's branch goes red, and (worse) no pending
    warning is emitted, which is the signal `minerva:cleanup` gates reconciliation on,
    so 050 would never be catalogued at all. Entries do not merge in NNN order.
    """
    d = make_dir(
        tmp_path,
        {"051-decision-b.md": entry("decision", "b"),
         "050-decision-a.md": entry("decision", "a",
                                    related=[("051-decision-b", "builds on")])},
        index("051", decisions=["051-decision-b"]),
    )
    f = lint_knowledge(d)
    assert errors(f) == []
    assert any("050 has no catalog line" in x.message for x in f)
    assert any(x.family == "reciprocal" for x in f)


def test_four_digit_entries_are_visible(tmp_path):
    r"""Allocator widens past 999 rather than wrapping. A fixed `\d{3}` would make
    the 1000th entry invisible to the catalog checks AND to duplicate detection at the
    same moment — both backstops failing together."""
    d = make_dir(
        tmp_path,
        {"0999-decision-foo.md": entry("decision", "foo"),
         "1000-decision-bar.md": entry("decision", "bar")},
        index("1000", decisions=["0999-decision-foo", "1000-decision-bar"]),
    )
    assert lint_knowledge(d) == []


def test_duplicate_nnn_does_not_indict_the_wrong_file(tmp_path):
    """`entries[nnn]` is an arbitrary group member, so type/slug findings derived from
    it name the wrong file. Quarantine them; the duplicate error is the real signal."""
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "001-bug-bar.md": entry("bug", "bar")},
        index("001", decisions=["001-decision-foo"]),
    )
    f = lint_knowledge(d)
    assert [x.family for x in errors(f)] == ["duplicate"]
    assert not any("catalogued under" in x.message for x in f)


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
    """Pending, not drift. Promote no longer writes catalog lines at all, so an
    uncatalogued entry only ever means "reconciliation hasn't run yet"."""
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "002-constraint-bar.md": entry("constraint", "bar")},
        index("002", decisions=["001-decision-foo"]),  # 002 omitted
    )
    f = lint_knowledge(d)
    assert errors(f) == []
    assert any("002 has no catalog line" in x.message and x.severity == "warning"
               for x in f)


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
    f = lint_knowledge(d)
    assert errors(f) == []
    assert any(x.family == "reciprocal" and "002 has no back-link to 001" in x.message
               and x.severity == "warning" for x in f)


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


def test_corruption_below_the_watermark_is_self_healed_not_errored(tmp_path):
    """Pins a DELIBERATE trade-off, not an oversight — do not "fix" this back.

    Entry 001 is already reconciled (watermark 002), then its catalog line is dropped
    by a hand-edit or a bad merge. The scalar-floor design reported that as a hard
    error; this design reports a pending warning and lets the next reconciliation
    regenerate the line from the entry's `**Summary**`.

    Restoring the loud error means restoring the floor, which misclassifies
    out-of-order merges — see `test_out_of_order_merge_stays_green`. That failure is
    both more frequent and more damaging: it reddens an innocent branch AND suppresses
    the pending signal cleanup gates reconciliation on, so the entry is never
    catalogued at all. Losing loud detection of corruption in a machine-generated file
    is the cheaper side of that trade.
    """
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "002-constraint-bar.md": entry("constraint", "bar")},
        index("002", constraints=["002-constraint-bar"]),  # 001's line dropped
    )
    f = lint_knowledge(d)
    assert errors(f) == []
    assert any("001 has no catalog line" in x.message and x.severity == "warning"
               for x in f)


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
