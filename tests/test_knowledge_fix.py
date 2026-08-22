"""Tests for the deterministic knowledge-wiki fixer (`scripts/knowledge_fix.py`).

Each mechanical fix family is exercised on a drifted temp corpus; after `apply` the
corpus must be clean per `knowledge_lint.lint_knowledge`. Plus the two safety models
(entry `body_complement` byte-identity; index skeleton/NNN-order preservation),
idempotency, reciprocal-label derivation + atomic refusal, and dry-run-writes-nothing.
"""
from pathlib import Path

import knowledge_fix as fix
from knowledge_lint import lint_knowledge, parse_index
from knowledge_edits import body_complement

DATE = "2026-01-01"


# --- fixture builders (canonical skeleton) -----------------------------------
def entry(typ, slug, related=None, banner=None, body_extra="", summary=None):
    s = f"# {slug} title\n\n**Date**: {DATE}\n**Type**: {typ}\n"
    if summary:
        s += f"**Summary**: {summary}\n"
    s += "**Context**: x\n"
    if banner:  # (nnn, stem)
        s += f"\n<!-- superseded-by: {banner[1]} -->\n> **Superseded by [[{banner[1]}]]** ({DATE})\n"
    s += "\n## Context\nc\n\n## Finding\nf\n" + body_extra + "\n## Implications\ni\n"
    if related:  # [(stem, label)]
        s += "\n## Related\n" + "".join(f"- [[{st}]] — {lab}\n" for st, lab in related)
    return s


def index_md(sections):  # sections: {"Decisions":[(stem,summary)], ...}
    blocks = []
    for name in ["Decisions", "Bugs", "Patterns", "Constraints", "References"]:
        rows = sections.get(name, [])
        block = [f"## {name}"]
        if rows:
            block.append("")
            block += [f"- [[{st}]] — {summ}" for st, summ in rows]
        blocks.append("\n".join(block))
    return "# Knowledge index\n\n" + "\n\n".join(blocks) + "\n"


def make_dir(tmp_path, files, index_text):
    for name, content in files.items():
        (tmp_path / name).write_text(content)
    (tmp_path / "index.md").write_text(index_text)
    return tmp_path


def errors(kd):
    return [f for f in lint_knowledge(kd) if f.severity == "error"]


# A clean two-entry baseline (catalogued, watermark correct, reciprocal).
def clean(tmp_path):
    return make_dir(
        tmp_path,
        {
            "001-decision-foo.md": entry("decision", "foo", related=[("002-constraint-bar", "see also")]),
            "002-constraint-bar.md": entry("constraint", "bar", related=[("001-decision-foo", "see also")]),
        },
        index_md({"Decisions": [("001-decision-foo", "d")], "Constraints": [("002-constraint-bar", "c")]}),
    )


def test_clean_corpus_is_noop(tmp_path):
    kd = clean(tmp_path)
    before = {p.name: p.read_text() for p in kd.glob("*.md")}
    batch = fix.apply(kd, DATE)
    assert batch["index"] is None and batch["entries"] == {} and batch["refusals"] == []
    assert {p.name: p.read_text() for p in kd.glob("*.md")} == before  # byte-identical


def test_stale_watermark_comment_is_stripped(tmp_path):
    """A consumer index still carries the comment until it migrates. The fixer must
    drop it when it rewrites, and never write a new one — there is no scalar state."""
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "002-constraint-bar.md": entry("constraint", "bar")},
        "# Knowledge index\n<!-- index-watermark: 001 -->\n\n"
        "## Decisions\n\n- [[001-decision-foo]] — d\n\n"
        "## Constraints\n\n- [[002-constraint-bar]] — c\n",
    )
    fix.apply(kd, DATE)
    assert errors(kd) == []
    text = (kd / "index.md").read_text()
    assert "index-watermark" not in text          # stripped on rewrite
    assert "- [[001-decision-foo]]" in text        # catalog itself preserved
    assert "- [[002-constraint-bar]]" in text


def test_index_sorts_a_date_id_corpus(tmp_path):
    """Regression: `plan_index` sorted catalog rows with `int(t[0])`, which raises on a
    date id. It survived the whole migration because every other fixture in this file
    uses legacy ids, so nothing here ever fed `plan_index` a date — the first thing to
    do so was a live reconciliation, after the ids had already shipped.

    Mixed on purpose: legacy ids must still sort ahead of dates, and `"1000" < "999"`
    must not resurface.
    """
    kd = make_dir(
        tmp_path,
        {"999-decision-legacy-late.md": entry("decision", "legacy-late", summary="a"),
         "1000-decision-legacy-wide.md": entry("decision", "legacy-wide", summary="b"),
         "2026-05-19-decision-early.md": entry("decision", "early", summary="c"),
         "2026-08-10-decision-later.md": entry("decision", "later", summary="d")},
        index_md({"Decisions": [("999-decision-legacy-late", "a")]}),
    )
    fix.apply(kd, DATE)
    assert errors(kd) == []
    text = (kd / "index.md").read_text()
    order = [text.index(s) for s in
             ["999-decision-legacy-late", "1000-decision-legacy-wide",
              "2026-05-19-decision-early", "2026-08-10-decision-later"]]
    assert order == sorted(order), "legacy ids sort first and numerically; dates follow"


def test_stale_catalog_line_removed(tmp_path):
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo")},
        index_md({"Decisions": [("001-decision-foo", "d"), ("009-decision-ghost", "gone")]}),
    )
    assert any("009" in f.message for f in errors(kd))
    fix.apply(kd, DATE)
    assert errors(kd) == []
    assert "009-decision-ghost" not in (kd / "index.md").read_text()


def test_wrong_type_section_relocated_preserving_summary(tmp_path):
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "002-constraint-bar.md": entry("constraint", "bar")},
        # 002 (constraint) wrongly listed under Decisions, with a distinctive summary
        index_md({"Decisions": [("001-decision-foo", "d"),
                                       ("002-constraint-bar", "DISTINCTIVE SUMMARY")]}),
    )
    assert any("002" in f.message and "section" in f.message for f in errors(kd))
    fix.apply(kd, DATE)
    assert errors(kd) == []
    text = (kd / "index.md").read_text()
    # summary preserved verbatim, now under Constraints
    assert "- [[002-constraint-bar]] — DISTINCTIVE SUMMARY" in text
    cons = text.index("## Constraints")
    assert text.index("002-constraint-bar", cons) > cons  # appears after the Constraints header


def test_missing_reciprocal_added(tmp_path):
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo", related=[("002-constraint-bar", "builds on")]),
         "002-constraint-bar.md": entry("constraint", "bar")},  # no back-link
        index_md({"Decisions": [("001-decision-foo", "d")], "Constraints": [("002-constraint-bar", "c")]}),
    )
    assert any(f.family == "reciprocal" for f in lint_knowledge(kd))  # pending, a warning
    before_body = body_complement((kd / "002-constraint-bar.md").read_text())
    fix.apply(kd, DATE)
    assert errors(kd) == []
    b = (kd / "002-constraint-bar.md").read_text()
    assert "[[001-decision-foo]] — see also" in b  # builds on -> see also reciprocal
    assert body_complement(b) == before_body  # ENTRY safety: body untouched


def test_supersession_writes_banner_and_related_line(tmp_path):
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),  # will be superseded by 002
         "002-constraint-bar.md": entry("constraint", "bar", related=[("001-decision-foo", "supersedes")])},
        index_md({"Decisions": [("001-decision-foo", "d")], "Constraints": [("002-constraint-bar", "c")]}),
    )
    fix.apply(kd, DATE)
    assert errors(kd) == []
    a = (kd / "001-decision-foo.md").read_text()
    assert "<!-- superseded-by: 002-constraint-bar -->" in a       # banner
    assert "[[002-constraint-bar]] — superseded by" in a  # AND the Related line


def test_prose_label_reciprocates_as_see_also(tmp_path):
    """The practiced convention is a descriptive sentence, not a five-term vocabulary.
    A prose label cannot be inverted mechanically, so the BACK-link gets the neutral
    term — strictly better than the missing link it replaces."""
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry(
            "decision", "foo",
            related=[("002-constraint-bar", "the sibling failure on the other write path")]),
         "002-constraint-bar.md": entry("constraint", "bar")},
        index_md({"Decisions": [("001-decision-foo", "d")], "Constraints": [("002-constraint-bar", "c")]}),
    )
    batch = fix.apply(kd, DATE)
    assert batch["refusals"] == []
    assert "- [[001-decision-foo]] — see also" in (kd / "002-constraint-bar.md").read_text()
    # The forward line keeps its prose — only the reciprocal is neutral.
    assert "the sibling failure on the other write path" in (kd / "001-decision-foo.md").read_text()


def test_directional_prose_label_refused_atomically(tmp_path):
    """A label that READS like a retirement claim is refused, not softened: guessing
    the direction of a supersession from prose is the edit a human must make."""
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry(
            "decision", "foo",
            related=[("002-constraint-bar", "supersedes the old approach entirely")]),
         "002-constraint-bar.md": entry("constraint", "bar")},
        index_md({"Decisions": [("001-decision-foo", "d")], "Constraints": [("002-constraint-bar", "c")]}),
    )
    before = (kd / "002-constraint-bar.md").read_text()
    batch = fix.apply(kd, DATE)
    assert any("write the reciprocal by hand" in r[2] for r in batch["refusals"])
    assert (kd / "002-constraint-bar.md").read_text() == before  # no partial write


def test_idempotent(tmp_path):
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo", related=[("002-constraint-bar", "builds on")]),
         "002-constraint-bar.md": entry("constraint", "bar")},
        index_md({"Decisions": [("001-decision-foo", "d")],  # watermark wrong too
                         "Constraints": [("002-constraint-bar", "c")]}),
    )
    fix.apply(kd, DATE)
    assert errors(kd) == []
    snapshot = {p.name: p.read_text() for p in kd.glob("*.md")}
    batch2 = fix.apply(kd, DATE)  # second run
    assert batch2["index"] is None and batch2["entries"] == {}
    assert {p.name: p.read_text() for p in kd.glob("*.md")} == snapshot  # byte-identical


def test_index_skeleton_and_order_preserved(tmp_path):
    kd = make_dir(
        tmp_path,
        {"003-decision-c.md": entry("decision", "c"),
         "001-decision-a.md": entry("decision", "a"),
         "002-bug-b.md": entry("bug", "b")},
        # watermark wrong + Decisions out of NNN order
        index_md({"Decisions": [("003-decision-c", "c"), ("001-decision-a", "a")],
                         "Bugs": [("002-bug-b", "b")]}),
    )
    fix.apply(kd, DATE)
    assert errors(kd) == []
    text = (kd / "index.md").read_text()
    for h in ["## Decisions", "## Bugs", "## Patterns", "## Constraints"]:
        assert h in text  # all four headers incl. empty Patterns + Constraints
    # ascending NNN order within Decisions
    assert text.index("001-decision-a") < text.index("003-decision-c")
    assert "watermark" not in parse_index(kd / "index.md")


def test_fenced_related_example_not_treated_as_edge(tmp_path):
    """A fenced `## Related` example in an entry body must NOT be read as a real
    forward edge (fence-aware, matching the detector) — so the fixer invents no edit.
    """
    fenced = "\nExample:\n\n```markdown\n## Related\n- [[002-constraint-bar]] — supersedes\n```\n"
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo", body_extra=fenced),  # no REAL ## Related
         "002-constraint-bar.md": entry("constraint", "bar")},
        index_md({"Decisions": [("001-decision-foo", "d")], "Constraints": [("002-constraint-bar", "c")]}),
    )
    assert errors(kd) == []  # detector (fence-aware) sees a clean corpus
    before = {p.name: p.read_text() for p in kd.glob("*.md")}
    batch = fix.apply(kd, DATE)
    assert batch["entries"] == {}  # no spurious banner/Related edit from the fenced example
    assert {p.name: p.read_text() for p in kd.glob("*.md")} == before  # byte-identical


def test_unknown_type_line_refused_not_dropped(tmp_path):
    kd = make_dir(
        tmp_path,
        {"001-weird-x.md": entry("weird", "x")},  # declared type not one of the 4
        index_md({"Decisions": [("001-weird-x", "keep me")]}),
    )
    batch = fix.apply(kd, DATE)
    assert any("001" in r[0] or "001" in r[2] for r in batch["refusals"])
    text = (kd / "index.md").read_text()
    assert "001-weird-x" in text and "keep me" in text  # line NOT dropped, summary intact


def test_missing_index_refused_not_fabricated(tmp_path):
    (tmp_path / "001-decision-foo.md").write_text(entry("decision", "foo"))
    # no index.md written
    batch = fix.apply(tmp_path, DATE)
    assert batch["index"] is None
    assert any("missing" in r[2] for r in batch["refusals"])
    assert not (tmp_path / "index.md").exists()  # no hollow skeleton fabricated


def test_dry_run_writes_nothing(tmp_path):
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo")},
        index_md({"Decisions": [("001-decision-foo", "d")]}),  # watermark wrong
    )
    before = {p.name: p.read_text() for p in kd.glob("*.md")}
    fix.main(["--dry-run", "--date", DATE, str(kd)])
    assert {p.name: p.read_text() for p in kd.glob("*.md")} == before  # untouched


# --- catalog-line insertion (what makes an add-only promote possible) --------
def test_missing_catalog_line_added_from_entry_summary(tmp_path):
    """The entry states its own summary, so reconciliation can catalogue it with no
    LLM in the loop — this is the operation promote stops doing in-branch."""
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "002-constraint-bar.md": entry("constraint", "bar", summary="bar is bounded")},
        index_md({"Decisions": [("001-decision-foo", "d")]}),  # 002 uncatalogued
    )
    fix.apply(kd, DATE)
    text = (kd / "index.md").read_text()
    assert "- [[002-constraint-bar]] — bar is bounded" in text
    assert "index-watermark" not in text
    assert errors(kd) == []


def test_added_catalog_line_lands_in_the_declared_type_section(tmp_path):
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "002-pattern-baz.md": entry("pattern", "baz", summary="baz recurs")},
        index_md({"Decisions": [("001-decision-foo", "d")]}),
    )
    fix.apply(kd, DATE)
    body = (kd / "index.md").read_text()
    patterns = body.split("## Patterns")[1].split("## Constraints")[0]
    assert "002-pattern-baz" in patterns


def test_missing_catalog_line_without_summary_is_still_refused(tmp_path):
    """The fixer relocates a summary the entry states; it never invents one."""
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "002-constraint-bar.md": entry("constraint", "bar")},  # no **Summary**
        index_md({"Decisions": [("001-decision-foo", "d")]}),
    )
    batch = fix.apply(kd, DATE)
    assert any("Summary" in r[2] for r in batch["refusals"])
    assert "002-constraint-bar" not in (kd / "index.md").read_text()


def test_mixed_corpus_needs_no_backfill(tmp_path):
    """An old entry with no Summary keeps its existing verbatim line while a new one
    is catalogued from its own — the state a consumer repo lands in on day one."""
    kd = make_dir(
        tmp_path,
        {"001-decision-old.md": entry("decision", "old"),           # legacy, no Summary
         "002-constraint-new.md": entry("constraint", "new", summary="new is add-only")},
        index_md({"Decisions": [("001-decision-old", "hand-written summary")]}),
    )
    fix.apply(kd, DATE)
    text = (kd / "index.md").read_text()
    assert "- [[001-decision-old]] — hand-written summary" in text  # preserved verbatim
    assert "- [[002-constraint-new]] — new is add-only" in text
    assert errors(kd) == []


# --- shared NNNs are addressed by STEM ---------------------------------------
def test_shared_nnn_lines_are_relocated_by_stem(tmp_path):
    """Two entries share an NNN but not a stem, so each catalog line is placed under
    its OWN declared type. Under NNN keying both collapsed onto an arbitrary winner
    and neither could be moved."""
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "001-bug-bar.md": entry("bug", "bar")},
        index_md({"Bugs": [("001-decision-foo", "d")],       # both misfiled,
                         "Decisions": [("001-bug-bar", "b")]}),      # each under the other's
    )
    batch = fix.apply(kd, DATE)
    text = (kd / "index.md").read_text()
    assert "- [[001-decision-foo]] — d" in text.split("## Bugs")[0]   # now under Decisions
    assert "- [[001-bug-bar]] — b" in text.split("## Bugs")[1]        # now under Bugs
    assert not any("shared by multiple entries" in r[2] for r in batch["refusals"])


def test_shared_nnn_both_get_catalog_lines(tmp_path):
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo", summary="s1"),
         "001-bug-bar.md": entry("bug", "bar", summary="s2")},
        index_md({}),
    )
    fix.apply(kd, DATE)
    text = (kd / "index.md").read_text()
    assert "- [[001-decision-foo]] — s1" in text
    assert "- [[001-bug-bar]] — s2" in text


def test_shared_nnn_reciprocal_lands_on_the_named_stem(tmp_path):
    """The back-link goes to the entry the wikilink NAMES, not to whichever member of
    the group a bare-NNN lookup happened to win."""
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "001-bug-bar.md": entry("bug", "bar"),
         "002-pattern-baz.md": entry("pattern", "baz", summary="s",
                                     related=[("001-bug-bar", "see also")])},
        index_md({"Decisions": [("001-decision-foo", "d")],
                         "Bugs": [("001-bug-bar", "b")],
                         "Patterns": [("002-pattern-baz", "p")]}),
    )
    untouched = (kd / "001-decision-foo.md").read_text()
    batch = fix.apply(kd, DATE)
    assert "- [[002-pattern-baz]] — see also" in (kd / "001-bug-bar.md").read_text()
    assert (kd / "001-decision-foo.md").read_text() == untouched  # the twin is not written to
    assert batch["refusals"] == []


def test_second_link_on_a_related_line_counts_as_a_back_link(tmp_path):
    """A back-link already present as the SECOND target on a shared line must be
    detected. The editor scans the whole span, so a line-anchored detector disagreed
    with it: it re-planned the entry as changed on every run while the editor kept
    no-opping, so `apply` never converged."""
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo",
                                      related=[("002-constraint-bar", "see also")]),
         "002-constraint-bar.md": entry("constraint", "bar")},
        index_md({"Decisions": [("001-decision-foo", "d")],
                         "Constraints": [("002-constraint-bar", "c")]}),
    )
    # 002 links back to 001, but as the second target of a two-link line.
    bar = kd / "002-constraint-bar.md"
    bar.write_text(bar.read_text().rstrip("\n") +
                   "\n\n## Related\n- [[003-pattern-other]] / [[001-decision-foo]] — both unchanged\n")
    batch = fix.plan(kd, DATE)
    assert "002-constraint-bar" not in batch["entries"]  # nothing to add


def test_related_before_another_section_is_refused_not_fatal(tmp_path):
    """One malformed entry must not abort the batch: its own back-link is refused and
    every unrelated edit still lands."""
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo",
                                      related=[("002-constraint-bar", "see also"),
                                               ("003-pattern-baz", "see also")]),
         "002-constraint-bar.md": entry("constraint", "bar").replace(
             "## Implications\ni\n", "## Related\n- [[009-pattern-nope]] — x\n\n## Implications\ni\n"),
         "003-pattern-baz.md": entry("pattern", "baz")},
        index_md({"Decisions": [("001-decision-foo", "d")],
                         "Constraints": [("002-constraint-bar", "c")],
                         "Patterns": [("003-pattern-baz", "p")]}),
    )
    batch = fix.apply(kd, DATE)
    assert any("cannot be located" in r[2] for r in batch["refusals"])
    # the healthy sibling still got its back-link
    assert "- [[001-decision-foo]] — see also" in (kd / "003-pattern-baz.md").read_text()


def test_shared_id_no_longer_blocks_the_supersession_banner(tmp_path):
    """The last place a shared id genuinely degraded output, now closed.

    The marker used to hold a bare id, so it could not say WHICH sharer retired the
    entry and the banner was withheld. It carries the full stem now, so the banner is
    always stamped — which matters because under date ids a shared id is ordinary.
    """
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo",
                                      related=[("003-pattern-old", "supersedes")]),
         "001-bug-bar.md": entry("bug", "bar"),
         "003-pattern-old.md": entry("pattern", "old")},
        index_md({"Decisions": [("001-decision-foo", "d")],
                         "Bugs": [("001-bug-bar", "b")],
                         "Patterns": [("003-pattern-old", "o")]}),
    )
    batch = fix.apply(kd, DATE)
    old_text = (kd / "003-pattern-old.md").read_text()
    assert "- [[001-decision-foo]] — superseded by" in old_text   # link written
    assert "<!-- superseded-by: 001-decision-foo -->" in old_text  # banner STAMPED
    assert not any("supersession banner not stamped" in r[2] for r in batch["refusals"])


# --- the fifth type (unit 052) -----------------------------------------------
def test_reference_entry_is_catalogued_under_references(tmp_path):
    kd = make_dir(
        tmp_path,
        {"001-reference-how-the-thing-runs.md": entry("reference", "how-the-thing-runs",
                                                      summary="how it is operated")},
        index_md({}),
    )
    batch = fix.apply(kd, DATE)
    text = (kd / "index.md").read_text()
    assert "- [[001-reference-how-the-thing-runs]] — how it is operated" in text.split("## References")[1]
    assert batch["refusals"] == []


def test_reference_line_filed_elsewhere_is_relocated(tmp_path):
    kd = make_dir(
        tmp_path,
        {"001-reference-how-the-thing-runs.md": entry("reference", "how-the-thing-runs")},
        index_md({"Constraints": [("001-reference-how-the-thing-runs", "r")]}),
    )
    fix.apply(kd, DATE)
    text = (kd / "index.md").read_text()
    assert "- [[001-reference-how-the-thing-runs]] — r" in text.split("## References")[1]
    assert "001-reference" not in text.split("## References")[0]


def test_a_corpus_with_no_reference_entries_gains_only_the_header(tmp_path):
    """The fifth section must be inert for every corpus that does not use it: one empty
    header, and not a single existing line moved."""
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "002-pattern-bar.md": entry("pattern", "bar")},
        index_md({"Decisions": [("001-decision-foo", "d")],
                         "Patterns": [("002-pattern-bar", "p")]}),
    )
    fix.apply(kd, DATE)
    text = (kd / "index.md").read_text()
    assert text.rstrip().endswith("## References")
    assert "- [[001-decision-foo]] — d" in text.split("## Bugs")[0]
    assert "- [[002-pattern-bar]] — p" in text.split("## Patterns")[1].split("## Constraints")[0]


def test_the_four_original_types_keep_their_order(tmp_path):
    kd = make_dir(
        tmp_path,
        {"001-decision-a.md": entry("decision", "a"), "002-bug-b.md": entry("bug", "b"),
         "003-pattern-c.md": entry("pattern", "c"), "004-constraint-d.md": entry("constraint", "d"),
         "005-reference-e.md": entry("reference", "e")},
        index_md({"Decisions": [("001-decision-a", "a")], "Bugs": [("002-bug-b", "b")],
                         "Patterns": [("003-pattern-c", "c")],
                         "Constraints": [("004-constraint-d", "d")],
                         "References": [("005-reference-e", "e")]}),
    )
    batch = fix.apply(kd, DATE)
    headers = [ln for ln in (kd / "index.md").read_text().splitlines() if ln.startswith("## ")]
    assert headers == ["## Decisions", "## Bugs", "## Patterns", "## Constraints", "## References"]
    assert batch["index"] is None  # already canonical -> byte-level no-op


# --- the fixer and the linter share ONE edge model ----------------------------
def test_fixer_and_linter_derive_the_same_edges():
    """The invariant `RELATED_LINE_RE`'s comment asserted and the code did not hold: the
    linter derived edges from the start-anchored CATALOG_LINE_RE, the fixer from the
    also-end-anchored RELATED_LINE_RE. Any line with trailing content that is not
    `— label` diverged, and an edge the linter counts but the fixer skips is a finding
    nothing repairs and nothing refuses — a convergence loop that never terminates while
    the fixer prints "corpus clean". Asserted over the shapes that used to diverge."""
    from knowledge_lint import related_edges
    for tail in ["— supersedes", "/ [[2026-01-02-pattern-b]] — both", "/", "",
                 "— refines  ", "/ [[2026-01-02-pattern-b]]"]:
        text = f"# t\n\n## Related\n- [[2026-01-01-decision-a]] {tail}\n"
        assert {t for t, _ in fix._forward_related(text)} == \
               {t for t, _ in related_edges(text)}, tail


def test_multi_target_line_produces_a_refusal_not_silence(tmp_path):
    """The reported failure mode: 18 of 41 findings were neither planned nor refused.
    A two-target line has no single label to reciprocate, so the edge must surface as a
    REFUSAL — visible, and never a fabricated label written into a neighbour."""
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "002-constraint-bar.md": entry("constraint", "bar"),
         "003-pattern-other.md": entry("pattern", "other")},
        index_md({"Decisions": [("001-decision-foo", "d")],
                  "Constraints": [("002-constraint-bar", "c")],
                  "Patterns": [("003-pattern-other", "p")]}),
    )
    foo = kd / "001-decision-foo.md"
    foo.write_text(foo.read_text().rstrip("\n") +
                   "\n\n## Related\n- [[002-constraint-bar]] / [[003-pattern-other]] — both\n")
    batch = fix.plan(kd, DATE)
    reasons = " ".join(r[2] for r in batch["refusals"])
    assert batch["refusals"], "the edge must not vanish silently"
    assert "relationship label" in reasons
    # and nothing was auto-written from a label the line does not carry
    assert "002-constraint-bar" not in batch["entries"]
    assert "003-pattern-other" not in batch["entries"]


def test_a_fenced_catalog_line_does_not_become_a_live_entry(tmp_path):
    """`plan_index` REWRITES index.md from what it parses, so a fence-blind scan promoted
    a documented example into the catalog. The detector never saw it — `parse_index` is
    fence-aware — so the entry came out catalogued twice, once carrying the example's fake
    summary, with no refusal and a clean lint run."""
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo", summary="the real one")},
        "# Knowledge index\n\n## Decisions\n\n"
        "```\n- [[001-decision-foo]] — QUOTED IN A FENCE, not the real summary\n```\n\n"
        "- [[001-decision-foo]] — the real one\n\n"
        "## Bugs\n\n## Patterns\n\n## Constraints\n\n## References\n",
    )
    new, _old, refusals, _hard = fix.plan_index(kd)
    assert new.count("001-decision-foo") == 1, "the fenced example must not be catalogued"
    assert "QUOTED IN A FENCE" not in new
    assert refusals == []


def test_the_fixer_and_the_linter_read_index_md_the_same_way(tmp_path):
    """The invariant behind the fix: one file, one parse."""
    from knowledge_lint import parse_index
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo", summary="the real one")},
        "# Knowledge index\n\n## Decisions\n\n"
        "```\n- [[002-bug-fenced]] — an example line\n```\n\n"
        "- [[001-decision-foo]] — the real one\n\n"
        "## Bugs\n\n## Patterns\n\n## Constraints\n\n## References\n",
    )
    new, _old, _r, _hard = fix.plan_index(kd)
    assert "002-bug-fenced" not in new
    assert "002-bug-fenced" not in parse_index(kd / "index.md")["catalog"]


# --- Hard index refusal suppresses entry edits (issue #81) ------------------------

def _entry(kd, stem, typ="decision", related=(), summary="s"):
    body = f"# {stem}\n\n**Type**: {typ}\n\n**Summary**: {summary}\n\n## Related\n"
    body += "".join(f"- [[{t}]] — refines\n" for t in related)
    (kd / f"{stem}.md").write_text(body)


def test_hard_refusal_suppresses_entry_edits(tmp_path):
    """A refused index rewrite must not leave reciprocal links behind.

    The defect: `plan()` called `plan_index` and `plan_reciprocals` independently, so a
    wholesale index refusal still returned entry edits and `apply()` wrote them —
    neighbour entries gained back-links the catalog does not know about.
    """
    kd = tmp_path
    # A links to B, so plan_reciprocals WOULD want to write B's back-link...
    _entry(kd, "2026-01-01-decision-a", related=["2026-01-02-decision-b"])
    _entry(kd, "2026-01-02-decision-b")
    # ...but index.md is missing, which is a hard refusal.
    batch = fix.plan(kd, "2026-01-03")
    assert batch["index"] is None
    assert batch["entries"] == {}, (
        "a hard index refusal must suppress entry edits — writing them leaves the "
        "corpus half-reconciled"
    )
    assert batch["refusals"], "the refusal itself must still be reported"


def test_hard_refusal_flag_is_set_on_the_missing_index_path(tmp_path):
    _entry(tmp_path, "2026-01-01-decision-a")
    _new, _old, refusals, hard = fix.plan_index(tmp_path)
    assert hard is True
    assert refusals


def test_per_entry_refusal_on_a_canonical_index_still_yields_entry_edits(tmp_path):
    """NEGATIVE CASE — the steady state that breaks the obvious (inferred) gate.

    Gating on "index unchanged AND refusals present" looks equivalent to gating on a
    hard refusal, and is not. An entry of unrecognized type sitting in a known section
    produces a per-entry refusal on EVERY run; once the index is canonical, that run
    also has `new == old`. The inferred gate would fire here and silently discard the
    reciprocal edits below, forever after.
    """
    kd = tmp_path
    _entry(kd, "2026-01-01-weird-thing", typ="weird")
    _entry(kd, "2026-01-01-decision-a", related=["2026-01-02-decision-b"])
    _entry(kd, "2026-01-02-decision-b")
    # Seed a catalog that already lists the weird entry under a KNOWN section: that is
    # what makes its refusal per-entry ("left under ## Decisions, not relocated")
    # rather than the unplaceable hard refusal.
    (kd / "index.md").write_text(
        "# Knowledge index\n\n## Decisions\n\n"
        "- [[2026-01-01-weird-thing]] — s\n"
        "- [[2026-01-01-decision-a]] — s\n"
        "- [[2026-01-02-decision-b]] — s\n\n"
        "## Patterns\n\n## Constraints\n\n## Bugs\n")
    # Canonicalise, so a later run leaves the index untouched.
    new, _old, _refusals, hard = fix.plan_index(kd)
    assert hard is False
    (kd / "index.md").write_text(new)

    new2, old2, refusals2, hard2 = fix.plan_index(kd)
    # The precise conditions that make the inferred gate wrong:
    assert new2 == old2, "index is canonical, so the rewrite is a no-op"
    assert refusals2, "and a benign per-entry refusal is present"
    assert hard2 is False, "yet this is NOT a hard refusal"

    batch = fix.plan(kd, "2026-01-03")
    assert batch["entries"], (
        "a per-entry refusal must NOT suppress entry edits — this is the ordinary "
        "steady state, not a failure"
    )
