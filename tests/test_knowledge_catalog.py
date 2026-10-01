"""Tests for the derive-on-read knowledge catalog (`scripts/knowledge_catalog.py`).

The catalog replaced three committed aggregates — `index.md`, stored reciprocal links and
supersession banners, and `overview.md` — with views computed from the entries. These
tests pin that each view is complete from the entries alone, and that the portable
routing one-liner agents actually run reads the same thing the script does.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from knowledge_catalog import (UNTHEMED, backlinks, inverted_supersedes, load_entries, main,
                               render_catalog, superseded_by, theme_counts)

REPO_ROOT = Path(__file__).resolve().parent.parent
LIVE_KNOWLEDGE = REPO_ROOT / ".minerva" / "knowledge"
INIT_STEPS = REPO_ROOT / "plugins" / "minerva" / "skills" / "init" / "references" / "steps.md"


def entry(slug, typ="decision", theme="wiki", summary="does a thing", related=(),
          banner=None, body=""):
    s = f"# {slug} title\n\n**Date**: 2026-10-02\n**Type**: {typ}\n"
    if theme:
        s += f"**Theme**: {theme}\n"
    if summary:
        s += f"**Summary**: {summary}\n"
    s += "**Context**: .minerva/work/x\n"
    if banner:
        s += f"\n<!-- superseded-by: {banner} -->\n> **Superseded by [[{banner}]]** (2026-10-02)\n"
    s += f"\n## Finding\nf\n{body}"
    if related:
        s += "\n## Related\n" + "".join(f"- [[{t}]] — {lab}\n" for t, lab in related)
    return s


def corpus(tmp_path, files):
    for name, text in files.items():
        (tmp_path / f"{name}.md").write_text(text)
    return tmp_path


A, B, C = "2026-10-02-decision-a", "2026-10-02-decision-b", "2026-10-03-pattern-c"


def test_every_entry_appears_exactly_once_grouped_by_theme(tmp_path):
    d = corpus(tmp_path, {A: entry("a", theme="wiki"), B: entry("b", theme="lifecycle"),
                          C: entry("c", typ="pattern", theme="wiki")})
    out = render_catalog(load_entries(d))
    for stem in (A, B, C):
        assert out.count(f"[[{stem}]]") == 1
    assert out.index("## lifecycle (1)") < out.index(f"[[{B}]]") < out.index("## wiki (2)")
    assert f"- [[{C}]] (pattern) — does a thing" in out


def test_unthemed_entries_group_last_and_fall_back_to_the_title(tmp_path):
    d = corpus(tmp_path, {A: entry("a", theme=None, summary=None), B: entry("b", theme="wiki")})
    out = render_catalog(load_entries(d))
    assert out.index("## wiki") < out.index(f"## {UNTHEMED}")
    assert f"- [[{A}]] (decision) — a title" in out


def test_legacy_aggregates_are_ignored(tmp_path):
    d = corpus(tmp_path, {A: entry("a")})
    (d / "index.md").write_text(f"# Knowledge index\n\n## Decisions\n- [[{B}]] — ghost\n")
    (d / "overview.md").write_text(f"# Knowledge overview\n\n## Ghosts\n[[{B}]]\n")
    entries = load_entries(d)
    assert list(entries) == [A]
    assert B not in render_catalog(entries)


def test_backlinks_are_the_reversed_forward_links(tmp_path):
    d = corpus(tmp_path, {A: entry("a"), B: entry("b", related=[(A, "builds on")]),
                          C: entry("c", related=[(A, "see also"), (B, "see also")])})
    assert backlinks(load_entries(d), A) == [(B, "builds on"), (C, "see also")]


def test_a_fenced_related_example_is_not_a_backlink(tmp_path):
    d = corpus(tmp_path, {A: entry("a"), B: entry(
        "b", related=[(C, "see also")], body=f"\n```\n## Related\n- [[{A}]] — x\n```\n")})
    assert backlinks(load_entries(d), A) == []


def test_supersession_is_derived_from_a_forward_supersedes_edge(tmp_path):
    """The successor declares it; the superseded entry's file is never edited."""
    d = corpus(tmp_path, {A: entry("a"), B: entry("b", related=[(A, "supersedes")])})
    entries = load_entries(d)
    assert superseded_by(entries) == {A: [B]}
    assert f"(superseded by [[{B}]])" in render_catalog(entries)
    assert "superseded" not in (d / f"{A}.md").read_text()


def test_a_supersedes_label_may_carry_an_explanation(tmp_path):
    d = corpus(tmp_path, {A: entry("a"),
                          B: entry("b", related=[(A, "supersedes: the surface moved")])})
    assert superseded_by(load_entries(d)) == {A: [B]}


def test_a_label_that_only_mentions_superseding_is_not_the_claim(tmp_path):
    d = corpus(tmp_path, {A: entry("a"),
                          B: entry("b", related=[(A, "see also — nearly supersedes it")])})
    assert superseded_by(load_entries(d)) == {}


def test_supersession_is_the_union_of_edges_and_legacy_banners(tmp_path):
    """A legacy entry may state its own retirement (`superseded by` edge and banner) and
    the successor may also state it (`supersedes`). Union, not precedence: each successor
    is listed once, and a second successor named only by the banner still appears."""
    d = corpus(tmp_path, {
        A: entry("a", banner=C, related=[(B, "superseded by")]),
        B: entry("b", related=[(A, "supersedes")]),
        C: entry("c", typ="pattern"),
    })
    entries = load_entries(d)
    assert superseded_by(entries) == {A: [B, C]}
    line = next(ln for ln in render_catalog(entries).splitlines() if f"[[{A}]]" in ln)
    assert line.count(f"[[{B}]]") == 1 and line.count(f"[[{C}]]") == 1


def test_theme_counts(tmp_path):
    d = corpus(tmp_path, {A: entry("a", theme="wiki"), B: entry("b", theme="wiki"),
                          C: entry("c", theme=None)})
    assert theme_counts(load_entries(d)) == {"wiki": 2, UNTHEMED: 1}


def test_cli_modes(tmp_path, capsys):
    d = corpus(tmp_path, {A: entry("a"), B: entry("b", related=[(A, "builds on")])})
    assert main([str(d), "--themes"]) == 0
    assert capsys.readouterr().out == "wiki\t2\n"
    assert main([str(d), "--links-to", A]) == 0
    assert capsys.readouterr().out == f"- [[{B}]] — builds on\n"
    assert main([str(d), "--by-type"]) == 0
    assert "## decision (2)" in capsys.readouterr().out
    assert main([str(tmp_path / "missing")]) == 2


def test_live_corpus_is_fully_themed_and_summarised():
    entries = load_entries(LIVE_KNOWLEDGE)
    assert entries and UNTHEMED not in theme_counts(entries)
    assert all(e["summary"] for e in entries.values())


# --- the routing one-liner ---------------------------------------------------------
def routing_oneliner() -> str:
    """The `find … awk` catalog command exactly as the init Routing template writes it."""
    text = INIT_STEPS.read_text()
    template = re.search(r"~~~markdown\n(## minerva\n.*?)\n~~~", text, re.S).group(1)
    return next(ln.strip() for ln in template.splitlines()
                if ln.strip().startswith("find .minerva/knowledge"))


def run_oneliner(root, shell="sh"):
    return subprocess.run([shell, "-c", routing_oneliner()], cwd=root, capture_output=True,
                          text=True, check=True).stdout


def test_the_repo_routing_carries_the_template_oneliner():
    assert routing_oneliner() in (REPO_ROOT / "CLAUDE.md").read_text()


@pytest.mark.skipif(shutil.which("awk") is None, reason="awk not installed")
@pytest.mark.parametrize("use_live", [False, True])
def test_routing_oneliner_matches_the_catalog(tmp_path, use_live):
    """The one-liner is a second reader of the entries. It must see the same (theme, entry,
    summary, superseded) set as the script — ignoring a fenced example, reading a whole
    multi-word theme, tolerating CRLF, and deriving supersession from all three sources
    while ignoring an inverted `supersedes` edge."""
    if use_live:
        root = REPO_ROOT
    else:
        root = tmp_path
        kd = root / ".minerva" / "knowledge"
        kd.mkdir(parents=True)
        D, E, F = "2026-10-04-bug-d", "2026-10-05-bug-e", "041-pattern-f"
        corpus(kd, {
            A: entry("a", theme="wiki", summary="first"),
            B: entry("b", theme=None, summary="second",
                     body="\n```\n**Theme**: fenced\n**Summary**: fenced\n```\n"),
            C: entry("c", typ="pattern", theme="lifecycle", summary="third: with | pipes",
                     related=[(A, "supersedes: replaced it"), (D, "supersedes")]),
            D: entry("d", typ="bug", theme="knowledge wiki", summary="newer than C"),
            E: entry("e", typ="bug", related=[(B, "superseded by"), (A, "see also")]),
            F: entry("f", typ="pattern", banner=A),
        })
        crlf = kd / f"{D}.md"
        crlf.write_bytes(crlf.read_bytes().replace(b"\n", b"\r\n"))
        (kd / "index.md").write_text("# Knowledge index\n")
    got = set()
    for line in run_oneliner(root).splitlines():
        theme, stem, summary = line.split(" | ", 2)
        marked = summary.endswith(" (superseded)")
        got.add((theme, stem, summary[:-len(" (superseded)")] if marked else summary, marked))
    entries = load_entries(root / ".minerva" / "knowledge")
    sup = superseded_by(entries)
    want = {(e["theme"] or UNTHEMED, stem, e["summary"] or "", stem in sup)
            for stem, e in entries.items()}
    assert got == want
    if not use_live:
        # Pin the fixture so the parity above is not vacuous: A is retired by C's
        # `supersedes`, E by its own `superseded by`, F by its legacy banner — and D is
        # NOT, because C is older than D (an inverted edge the catalog must ignore).
        assert sup == {A: [C], E: [B], F: [A]}


@pytest.mark.skipif(shutil.which("awk") is None, reason="awk not installed")
@pytest.mark.parametrize("shell", ["sh", "zsh"])
def test_routing_oneliner_on_an_empty_corpus_prints_nothing_and_succeeds(tmp_path, shell):
    """An unmatched glob aborts the whole command in zsh; `find` makes an empty corpus a
    clean, empty listing in every shell."""
    if shutil.which(shell) is None:
        pytest.skip(f"{shell} not installed")
    (tmp_path / ".minerva" / "knowledge").mkdir(parents=True)
    assert run_oneliner(tmp_path, shell) == ""


def test_an_older_entry_cannot_supersede_a_newer_one(tmp_path):
    """A `supersedes` edge pointing forward in time is a mislabelled `superseded by`. Taken
    literally it marks the live entry retired in favour of the rule it replaced — the live
    corpus had one (2026-06-10 → 2026-06-13). Ignored here, and reported by lint."""
    d = corpus(tmp_path, {A: entry("a", related=[(C, "supersedes: the newer one")]),
                          C: entry("c", typ="pattern")})
    entries = load_entries(d)
    assert superseded_by(entries) == {}
    assert inverted_supersedes(entries) == [(A, C)]


def test_a_same_day_supersedes_is_honoured(tmp_path):
    d = corpus(tmp_path, {A: entry("a"), B: entry("b", related=[(A, "supersedes")])})
    assert superseded_by(load_entries(d)) == {A: [B]}
