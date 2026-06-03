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
def entry(typ, slug, related=None, banner=None, body_extra=""):
    s = f"# {slug} title\n\n**Date**: {DATE}\n**Type**: {typ}\n**Context**: x\n"
    if banner:  # (nnn, stem)
        s += f"\n<!-- superseded-by: {banner[0]} -->\n> **Superseded by [[{banner[1]}]]** ({DATE})\n"
    s += "\n## Context\nc\n\n## Finding\nf\n" + body_extra + "\n## Implications\ni\n"
    if related:  # [(stem, label)]
        s += "\n## Related\n" + "".join(f"- [[{st}]] — {lab}\n" for st, lab in related)
    return s


def index_md(watermark, sections):  # sections: {"Decisions":[(stem,summary)], ...}
    blocks = []
    for name in ["Decisions", "Bugs", "Patterns", "Constraints"]:
        rows = sections.get(name, [])
        block = [f"## {name}"]
        if rows:
            block.append("")
            block += [f"- [[{st}]] — {summ}" for st, summ in rows]
        blocks.append("\n".join(block))
    return f"# Knowledge index\n<!-- index-watermark: {watermark} -->\n\n" + "\n\n".join(blocks) + "\n"


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
        index_md("002", {"Decisions": [("001-decision-foo", "d")], "Constraints": [("002-constraint-bar", "c")]}),
    )


def test_clean_corpus_is_noop(tmp_path):
    kd = clean(tmp_path)
    before = {p.name: p.read_text() for p in kd.glob("*.md")}
    batch = fix.apply(kd, DATE)
    assert batch["index"] is None and batch["entries"] == {} and batch["refusals"] == []
    assert {p.name: p.read_text() for p in kd.glob("*.md")} == before  # byte-identical


def test_watermark_fixed(tmp_path):
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo"),
         "002-constraint-bar.md": entry("constraint", "bar")},
        index_md("001", {"Decisions": [("001-decision-foo", "d")],  # watermark 001, max is 002
                         "Constraints": [("002-constraint-bar", "c")]}),
    )
    assert any("watermark" in f.message for f in errors(kd))
    fix.apply(kd, DATE)
    assert errors(kd) == []
    assert "<!-- index-watermark: 002 -->" in (kd / "index.md").read_text()


def test_stale_catalog_line_removed(tmp_path):
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo")},
        index_md("001", {"Decisions": [("001-decision-foo", "d"), ("009-decision-ghost", "gone")]}),
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
        index_md("002", {"Decisions": [("001-decision-foo", "d"),
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
        index_md("002", {"Decisions": [("001-decision-foo", "d")], "Constraints": [("002-constraint-bar", "c")]}),
    )
    assert any(f.family == "reciprocal" for f in errors(kd))
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
        index_md("002", {"Decisions": [("001-decision-foo", "d")], "Constraints": [("002-constraint-bar", "c")]}),
    )
    fix.apply(kd, DATE)
    assert errors(kd) == []
    a = (kd / "001-decision-foo.md").read_text()
    assert "<!-- superseded-by: 002 -->" in a       # banner
    assert "[[002-constraint-bar]] — superseded by" in a  # AND the Related line


def test_invalid_label_refused_atomically(tmp_path):
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo", related=[("002-constraint-bar", "frobnicates")]),
         "002-constraint-bar.md": entry("constraint", "bar")},
        index_md("002", {"Decisions": [("001-decision-foo", "d")], "Constraints": [("002-constraint-bar", "c")]}),
    )
    before = (kd / "002-constraint-bar.md").read_text()
    batch = fix.apply(kd, DATE)
    assert any("not in closed vocab" in r[2] for r in batch["refusals"])
    assert (kd / "002-constraint-bar.md").read_text() == before  # no partial write


def test_idempotent(tmp_path):
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo", related=[("002-constraint-bar", "builds on")]),
         "002-constraint-bar.md": entry("constraint", "bar")},
        index_md("009", {"Decisions": [("001-decision-foo", "d")],  # watermark wrong too
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
        index_md("001", {"Decisions": [("003-decision-c", "c"), ("001-decision-a", "a")],
                         "Bugs": [("002-bug-b", "b")]}),
    )
    fix.apply(kd, DATE)
    assert errors(kd) == []
    text = (kd / "index.md").read_text()
    for h in ["## Decisions", "## Bugs", "## Patterns", "## Constraints"]:
        assert h in text  # all four headers incl. empty Patterns + Constraints
    # ascending NNN order within Decisions
    assert text.index("001-decision-a") < text.index("003-decision-c")
    assert parse_index(kd / "index.md")["watermark"] == "003"


def test_dry_run_writes_nothing(tmp_path):
    kd = make_dir(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo")},
        index_md("000", {"Decisions": [("001-decision-foo", "d")]}),  # watermark wrong
    )
    before = {p.name: p.read_text() for p in kd.glob("*.md")}
    fix.main(["--dry-run", "--date", DATE, str(kd)])
    assert {p.name: p.read_text() for p in kd.glob("*.md")} == before  # untouched
