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


def index(decisions=(), bugs=(), patterns=(), constraints=(), references=()):
    """No watermark line: reconciliation state is per-record now."""
    s = "# Knowledge index\n"
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
        index(decisions=["001-decision-foo"], constraints=["002-constraint-bar"]),
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
        index(decisions=["001-decision-foo"]),  # 002 not yet catalogued
    )
    findings = lint_knowledge(d)
    assert errors(findings) == []
    assert any(x.severity == "warning" and "pending reconciliation" in x.message
               for x in findings)


def test_stale_watermark_comment_is_ignored_not_read(tmp_path):
    """A consumer corpus still carries `<!-- index-watermark: NNN -->` until it
    migrates. The linter must ignore it silently — never read it, never trip on it."""
    idx = ("# Knowledge index\n<!-- index-watermark: 009 -->\n\n"
           "## Decisions\n- [[001-decision-foo]] — summary\n")
    d = make_dir(tmp_path, {"001-decision-foo.md": entry("decision", "foo")}, idx)
    f = lint_knowledge(d)
    assert errors(f) == []
    assert not any("watermark" in x.message for x in f)


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
        index(decisions=["001-decision-foo"]),
    )
    findings = lint_knowledge(d)
    assert errors(findings) == []
    assert any(x.family == "reciprocal" and x.severity == "warning" for x in findings)


def test_out_of_order_merge_stays_green(tmp_path):
    """The regression that killed the scalar-floor design, now structurally impossible.

    Unit A takes 050, unit B takes 051; B merges and reconciles first. Under a floor
    the watermark would reach 051, and A's later merge would sit *below* it — read as
    drift, with no pending warning, which is the signal `minerva:cleanup` gates
    reconciliation on, so 050 would never be catalogued at all.

    There is no floor to be below any more: an entry is pending iff it has no catalog
    line. Kept as a regression guard so the scalar cannot come back.
    """
    d = make_dir(
        tmp_path,
        {"051-decision-b.md": entry("decision", "b"),
         "050-decision-a.md": entry("decision", "a",
                                    related=[("051-decision-b", "builds on")])},
        index(decisions=["051-decision-b"]),
    )
    f = lint_knowledge(d)
    assert errors(f) == []
    assert any("050-decision-a has no catalog line" in x.message for x in f)
    assert any(x.family == "reciprocal" for x in f)


def test_four_digit_entries_are_visible(tmp_path):
    r"""Allocator widens past 999 rather than wrapping. A fixed `\d{3}` would make
    the 1000th entry invisible to the catalog checks AND to duplicate detection at the
    same moment — both backstops failing together."""
    d = make_dir(
        tmp_path,
        {"0999-decision-foo.md": entry("decision", "foo"),
         "1000-decision-bar.md": entry("decision", "bar")},
        index(decisions=["0999-decision-foo", "1000-decision-bar"]),
    )
    assert lint_knowledge(d) == []


def test_same_day_entries_are_not_duplicates(tmp_path):
    """Two entries sharing a DATE are ordinary and must be fully first-class.

    This is the inverse of the retired duplicate-id check. Ids are no longer scarce,
    so a shared leading token carries no meaning; identity is the whole stem. Reporting
    these as duplicates would have been wrong on its own, but the real damage was the
    quarantine that came with it — a flagged group was skipped by every per-entry
    check, so on a corpus where same-day entries are normal most of the corpus would
    go unchecked while the linter reported errors about it.
    """
    d = make_dir(
        tmp_path,
        {"2026-08-09-decision-foo.md": entry("decision", "foo"),
         "2026-08-09-bug-bar.md": entry("bug", "bar")},
        index(decisions=["2026-08-09-decision-foo"], bugs=["2026-08-09-bug-bar"]),
    )
    f = lint_knowledge(d)
    assert errors(f) == []
    assert not any(x.family == "duplicate" for x in f)


def test_same_day_entries_are_still_type_checked(tmp_path):
    """The quarantine is gone: a same-day sibling is checked, not skipped."""
    d = make_dir(
        tmp_path,
        {"2026-08-09-decision-foo.md": entry("decision", "foo"),
         "2026-08-09-bug-bar.md": entry("bug", "bar")},
        # the bug is miscatalogued under Decisions
        index(decisions=["2026-08-09-decision-foo", "2026-08-09-bug-bar"]),
    )
    f = errors(lint_knowledge(d))
    assert any("2026-08-09-bug-bar" in x.message and "section" in x.message for x in f)


def test_impossible_date_is_reported(tmp_path):
    """`ENTRY_RE` is shape-only, so `2026-13-45` matches it. Conformance must check
    the calendar, or a typo passes as a valid entry forever."""
    d = make_dir(
        tmp_path,
        {"2026-13-45-decision-foo.md": entry("decision", "foo")},
        index(decisions=["2026-13-45-decision-foo"]),
    )
    f = errors(lint_knowledge(d))
    assert any(x.family == "id" and "2026-13-45" in x.message for x in f)


def test_entry_missing_catalog_line(tmp_path):
    """Pending, not drift. Promote no longer writes catalog lines at all, so an
    uncatalogued entry only ever means "reconciliation hasn't run yet"."""
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "002-constraint-bar.md": entry("constraint", "bar")},
        index(decisions=["001-decision-foo"]),  # 002 omitted
    )
    f = lint_knowledge(d)
    assert errors(f) == []
    assert any("002-constraint-bar has no catalog line" in x.message
               and x.severity == "warning" for x in f)


def test_catalog_line_with_no_file(tmp_path):
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo")},
        index(decisions=["001-decision-foo", "003-decision-ghost"]),
    )
    f = errors(lint_knowledge(d))
    assert any("003-decision-ghost has no entry file" in x.message for x in f)


def test_wrong_type_section(tmp_path):
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "002-constraint-bar.md": entry("constraint", "bar")},
        # 002 (a constraint) listed under Decisions
        index(decisions=["001-decision-foo", "002-constraint-bar"]),
    )
    f = errors(lint_knowledge(d))
    assert any("002" in x.message and "section" in x.message for x in f)


def test_catalog_slug_mismatch_is_a_stale_line_plus_a_pending_entry(tmp_path):
    """A DELIBERATE behaviour change, recorded so it is not mistaken for a regression.

    Under id keying, a catalog line whose slug disagreed with the file was one cosmetic
    warning: the id still matched, so the line was assumed to be the same entry, renamed.
    Under stem keying there is no such assumption available — the catalogued stem simply
    names nothing, and the real file is uncatalogued. That is reported honestly as two
    findings, and reconciliation repairs both by rewriting the line.
    """
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo")},
        index(decisions=["001-decision-renamed"]),
    )
    findings = lint_knowledge(d)
    assert any(x.severity == "error" and "001-decision-renamed has no entry file"
               in x.message for x in findings)
    assert any(x.severity == "warning" and "001-decision-foo has no catalog line"
               in x.message for x in findings)


# --- broken links ------------------------------------------------------------
def test_broken_related_link(tmp_path):
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo",
                                      related=[("099-decision-missing", "see also")]),
         "002-constraint-bar.md": entry("constraint", "bar")},
        index(decisions=["001-decision-foo"], constraints=["002-constraint-bar"]),
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
        index(decisions=["001-decision-foo"], constraints=["002-constraint-bar"]),
    )
    f = lint_knowledge(d)
    assert errors(f) == []
    assert any(x.family == "reciprocal"
               and "002-constraint-bar has no back-link to 001-decision-foo" in x.message
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
        index(decisions=["001-decision-foo"], constraints=["002-constraint-bar"]),
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
        index(decisions=["001-decision-foo"], constraints=["002-constraint-bar"]),
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
        index(decisions=["001-decision-foo"], constraints=["002-constraint-bar"]),
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
        index(decisions=["001-decision-foo"], constraints=["002-constraint-bar"]),
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
        index(decisions=["001-decision-foo"], constraints=["002-constraint-bar"]),
    )
    assert lint_knowledge(d) == []


# --- CLI exit code -----------------------------------------------------------
def test_main_exits_nonzero_on_error(tmp_path):
    d = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo")},
        index(decisions=["001-decision-foo", "003-decision-ghost"]),
    )
    assert main([str(d)]) == 1


def test_main_exits_zero_on_clean(tmp_path):
    assert main([str(clean(tmp_path))]) == 0


# --- live corpus -------------------------------------------------------------
def test_live_knowledge_clean():
    """The real .minerva/knowledge/ wiki must pass the deterministic linter."""
    findings = lint_knowledge(LIVE_KNOWLEDGE)
    assert errors(findings) == [], "\n".join(f.message for f in errors(findings))


def test_dropped_catalog_line_is_self_healed_not_errored(tmp_path):
    """Pins a DELIBERATE trade-off, not an oversight — do not "fix" this back.

    Entry 001 is already reconciled (watermark 002), then its catalog line is dropped
    by a hand-edit or a bad merge. The scalar-floor design reported that as a hard
    error; this design reports a pending warning and lets the next reconciliation
    regenerate the line from the entry's `**Summary**`.

    Restoring the loud error means restoring a floor, which misclassifies
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
        index(constraints=["002-constraint-bar"]),  # 001's line dropped
    )
    f = lint_knowledge(d)
    assert errors(f) == []
    assert any("001-decision-foo has no catalog line" in x.message
               and x.severity == "warning" for x in f)


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


# --- the shared edge model (defect: lint and fix disagreed on what an edge is) ---
def test_every_wikilink_in_the_related_block_is_an_edge():
    """`- [[a]] / [[b]] — label` states two edges, and the editor already treats the
    second as a real back-link. The detector read only the first, because it derived
    edges from the start-anchored CATALOG_LINE_RE."""
    from knowledge_lint import related_edges
    text = "# t\n\n## Related\n- [[2026-01-01-decision-a]] / [[2026-01-02-pattern-b]] — both\n"
    assert {t for t, _ in related_edges(text)} == {
        "2026-01-01-decision-a", "2026-01-02-pattern-b"}


def test_a_multi_target_line_carries_no_label():
    """There is no single label to reciprocate from a two-target line, so the label is
    None and `knowledge_fix` refuses it rather than inventing one from the line's tail."""
    from knowledge_lint import related_edges
    text = "# t\n\n## Related\n- [[2026-01-01-decision-a]] / [[2026-01-02-pattern-b]] — both\n"
    assert {lab for _, lab in related_edges(text)} == {None}


def test_a_single_target_line_still_carries_its_label():
    from knowledge_lint import related_edges
    text = "# t\n\n## Related\n- [[2026-01-01-decision-a]] — supersedes\n"
    assert related_edges(text) == [("2026-01-01-decision-a", "supersedes")]


def test_a_labelled_edge_upgrades_an_earlier_unlabelled_mention():
    """A stray mention must not suppress the properly-labelled line further down, or the
    fixer would refuse a reciprocal the entry does state correctly."""
    from knowledge_lint import related_edges
    text = ("# t\n\n## Related\n"
            "- [[2026-01-01-decision-a]] / [[2026-01-02-pattern-b]] — both\n"
            "- [[2026-01-01-decision-a]] — supersedes\n")
    assert dict(related_edges(text))["2026-01-01-decision-a"] == "supersedes"


def test_a_fenced_related_block_states_no_edges():
    from knowledge_lint import related_edges
    text = "# t\n\n## Related\n```\n- [[2026-01-01-decision-a]] — supersedes\n```\n"
    assert related_edges(text) == []


def test_lint_reports_a_broken_link_on_a_multi_target_line(tmp_path):
    """The end-to-end consequence: the second target of a shared line is a real edge,
    so a dangling one is a real broken link."""
    (tmp_path / "001-decision-foo.md").write_text(
        entry("decision", "foo") + "\n## Related\n- [[001-decision-foo]] / [[999-bug-gone]] — x\n")
    (tmp_path / "index.md").write_text(
        "# Knowledge index\n\n## Decisions\n\n- [[001-decision-foo]] — d\n")
    msgs = [f.message for f in lint_knowledge(tmp_path)]
    assert any("999-bug-gone" in m for m in msgs)
