"""Fixture tests for the deterministic synthesis-status signal
(`scripts/synthesis_status.py`).

Exercises the three load-bearing cases: the no-overview bootstrap (REQUIRED — the
first run with no `overview.md` must not crash and must report everything
un-synthesized), a populated overview that lags the corpus (some un-synthesized scope),
and link-rot detection — including the fence-aware guard that a fenced example
`[[NNN-...]]` link is NOT flagged (knowledge entry 023). `test_live_overview_clean`
runs the same function the skill consumes against the real `.minerva/knowledge/`:
either no overview yet (bootstrap) or, once dogfooded, zero link-rot.

Imports only `knowledge_lint` + `synthesis_status` — deliberately nothing that drags
in the unrelated `lib`-dependent browser/storage modules (which abort collection).
"""
from pathlib import Path

from synthesis_status import synthesis_status

REPO_ROOT = Path(__file__).resolve().parent.parent
LIVE_KNOWLEDGE = REPO_ROOT / ".minerva" / "knowledge"


# --- fixture builders --------------------------------------------------------
def entry(typ, slug):
    return (f"# {slug} title\n\n**Date**: 2026-06-03\n**Type**: {typ}\n"
            "**Context**: .minerva/work/x\n\n## Context\nc\n\n## Finding\nf\n")


def overview(watermark, body=""):
    return (f"# Knowledge overview\n<!-- synthesis-watermark: {watermark} -->\n\n"
            f"{body}")


def make_corpus(tmp_path, entries: dict, overview_text=None):
    for name, content in entries.items():
        (tmp_path / name).write_text(content)
    if overview_text is not None:
        (tmp_path / "overview.md").write_text(overview_text)
    return tmp_path


# --- 1. no-overview bootstrap (REQUIRED) -------------------------------------
def test_no_overview_bootstrap(tmp_path):
    make_corpus(tmp_path, {
        "001-decision-foo.md": entry("decision", "foo"),
        "002-pattern-bar.md": entry("pattern", "bar"),
    })  # no overview.md
    st = synthesis_status(tmp_path)
    assert st["overview_exists"] is False
    assert st["synthesis_watermark"] == -1
    assert st["corpus_max_nnn"] == 2
    assert st["unsynthesized"] == ["001", "002"]  # everything is un-synthesized
    assert st["link_rot"] == []  # no overview → nothing to rot


def test_empty_corpus_no_crash(tmp_path):
    st = synthesis_status(tmp_path)
    assert st["corpus_max_nnn"] == -1
    assert st["unsynthesized"] == []
    assert st["overview_exists"] is False


# --- 2. populated overview that lags the corpus ------------------------------
def test_populated_lagging_overview(tmp_path):
    make_corpus(
        tmp_path,
        {
            "001-decision-foo.md": entry("decision", "foo"),
            "002-pattern-bar.md": entry("pattern", "bar"),
            "003-constraint-baz.md": entry("constraint", "baz"),
        },
        overview_text=overview("001", "A theme referencing [[001-decision-foo]].\n"),
    )
    st = synthesis_status(tmp_path)
    assert st["overview_exists"] is True
    assert st["synthesis_watermark"] == 1
    assert st["corpus_max_nnn"] == 3
    assert st["unsynthesized"] == ["002", "003"]  # NNN > watermark
    assert st["link_rot"] == []  # [[001-...]] resolves


def test_fully_synthesized_no_unsynthesized(tmp_path):
    make_corpus(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo")},
        overview_text=overview("001", "All caught up: [[001-decision-foo]].\n"),
    )
    st = synthesis_status(tmp_path)
    assert st["unsynthesized"] == []


# --- 3. link-rot detection + fence-awareness ---------------------------------
def test_link_rot_unresolved_link(tmp_path):
    make_corpus(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo")},
        overview_text=overview(
            "001",
            "Live: [[001-decision-foo]]. Dead: [[099-decision-ghost]].\n",
        ),
    )
    st = synthesis_status(tmp_path)
    assert st["link_rot"] == ["099-decision-ghost"]  # 099 has no entry file


def test_fenced_example_link_not_flagged(tmp_path):
    body = (
        "Real link: [[001-decision-foo]].\n\n"
        "```\n"
        "An example inside a fence: [[099-decision-ghost]] must be ignored.\n"
        "```\n"
    )
    make_corpus(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo")},
        overview_text=overview("001", body),
    )
    st = synthesis_status(tmp_path)
    assert st["link_rot"] == []  # the fenced [[099-...]] is NOT link-rot (entry 023)


def test_overview_without_watermark_comment(tmp_path):
    make_corpus(
        tmp_path,
        {"001-decision-foo.md": entry("decision", "foo")},
        overview_text="# Knowledge overview\n\nNo watermark comment here.\n",
    )
    st = synthesis_status(tmp_path)
    assert st["overview_exists"] is True
    assert st["synthesis_watermark"] == -1  # missing comment → -1
    assert st["unsynthesized"] == ["001"]


# --- live corpus -------------------------------------------------------------
def test_live_overview_clean():
    """The real corpus: either no overview yet (bootstrap), or zero link-rot."""
    st = synthesis_status(LIVE_KNOWLEDGE)
    assert st["link_rot"] == [], f"live overview has link-rot: {st['link_rot']}"
