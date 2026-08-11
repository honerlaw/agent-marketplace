"""Fixture tests for the NNN -> YYYY-MM-DD migration (`scripts/knowledge_rename.py`).

Covers the three properties that make the migration safe to run once, unattended:
fence-awareness (a fenced `[[...]]` example is documentation, not an edge), batch
collision refusal BEFORE anything moves, and the structural claim the whole scheme
rests on — that an identical stem produced on two branches is a real git conflict
rather than a silent duplicate.
"""
import subprocess

import pytest

import knowledge_rename as ren


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "t@t.t")
    git(tmp_path, "config", "user.name", "t")
    (tmp_path / ".minerva" / "knowledge").mkdir(parents=True)
    (tmp_path / ".minerva" / "work").mkdir(parents=True)
    return tmp_path


def entry(typ, slug, body=""):
    return (f"# {slug}\n\n**Date**: 2026-01-01\n**Type**: {typ}\n"
            f"**Context**: .minerva/work/001-thing\n\n## Context\nc\n\n## Finding\nf\n"
            f"{body}")


# --- fence-awareness ---------------------------------------------------------
def test_fenced_wikilink_is_byte_identical(repo):
    """The guarantee. Every skill that documents the convention contains a fenced
    example; rewriting one corrupts the doc (knowledge 023, and 028 — third violation)."""
    text = (
        "Live edge: [[001-decision-foo]].\n\n"
        "```\n"
        "- [[001-decision-foo]] — an EXAMPLE, must not move\n"
        "```\n\n"
        "Another live one: [[001-decision-foo]].\n"
    )
    out = ren.rewrite_links(text, {"001-decision-foo": "2026-05-19-decision-foo"})
    assert "- [[001-decision-foo]] — an EXAMPLE, must not move" in out  # untouched
    assert out.count("[[2026-05-19-decision-foo]]") == 2                # both live ones
    assert out.count("[[001-decision-foo]]") == 1                       # only the fenced


def test_unmapped_target_is_left_alone(repo):
    """No fuzzy matching: a link the migration cannot resolve is never guessed at."""
    out = ren.rewrite_links("[[099-decision-ghost]]", {"001-decision-foo": "x"})
    assert out == "[[099-decision-ghost]]"


def test_banner_marker_and_context_path_are_retargeted(repo):
    text = ("<!-- superseded-by: 001-decision-foo -->\n"
            "**Context**: .minerva/work/001-thing\n")
    out = ren.rewrite_links(
        text,
        {"001-decision-foo": "2026-05-19-decision-foo"},
        {"001-thing": "2026-05-19-thing"},
    )
    assert "<!-- superseded-by: 2026-05-19-decision-foo -->" in out
    assert "**Context**: .minerva/work/2026-05-19-thing" in out


# --- collision refusal -------------------------------------------------------
def test_batch_refused_before_any_move(repo):
    """Two entries landing on one target must abort the WHOLE batch untouched.

    Checking per-file as you go is too late — the first half would already have moved
    with no clean way back."""
    kd = repo / ".minerva" / "knowledge"
    (kd / "001-decision-foo.md").write_text(entry("decision", "foo"))
    (kd / "002-decision-foo.md").write_text(entry("decision", "foo"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "both on one day")

    plan = ren.plan(repo)
    assert plan["collisions"], "same date+type+slug must be detected as a collision"

    before = sorted(p.name for p in kd.glob("*.md"))
    with pytest.raises(ren.CollisionError):
        ren.apply(repo, plan)
    assert sorted(p.name for p in kd.glob("*.md")) == before  # nothing moved


def test_same_date_different_slug_is_not_a_collision(repo):
    """Sharing a date is ordinary — it is only a collision if the whole stem matches."""
    kd = repo / ".minerva" / "knowledge"
    (kd / "001-decision-foo.md").write_text(entry("decision", "foo"))
    (kd / "002-pattern-bar.md").write_text(entry("pattern", "bar"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "same day, different slugs")

    plan = ren.plan(repo)
    assert plan["collisions"] == []
    assert len(set(plan["entries"].values())) == 2


# --- the structural guarantee ------------------------------------------------
def test_identical_stem_on_two_branches_conflicts(repo):
    """The claim the whole scheme rests on.

    Under NNN, two branches picking the same id produced two DIFFERENT filenames, so
    git merged both cleanly and the duplicate shipped silently — knowledge 055, which
    is why a cross-branch allocator had to exist. Under stem identity the same event is
    the same PATH on both sides, so git raises an add/add conflict and a human resolves
    it. This test is the evidence for retiring the allocator.
    """
    kd = repo / ".minerva" / "knowledge"
    (kd / "seed.md").write_text("seed\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "seed")

    stem = "2026-08-09-pattern-same-finding.md"
    git(repo, "checkout", "-q", "-b", "unit-a")
    (kd / stem).write_text(entry("pattern", "a-version"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "unit A promotes")

    git(repo, "checkout", "-q", "main")
    git(repo, "checkout", "-q", "-b", "unit-b")
    (kd / stem).write_text(entry("pattern", "b-version"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "unit B promotes")

    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--no-edit", "unit-a")
    merged = git(repo, "merge", "--no-edit", "unit-b")

    assert merged.returncode != 0, "identical stems must NOT merge cleanly"
    assert "CONFLICT" in (merged.stdout + merged.stderr)


# --- date derivation ---------------------------------------------------------
def test_follow_without_diff_filter_dates_a_renamed_path(repo):
    """`--follow` and `--diff-filter=A` are incompatible: under --follow git reports a
    creation as a rename, so pairing them returns NOTHING and the path is skipped."""
    kd = repo / ".minerva" / "knowledge"
    old = repo / ".minerva" / "decisions"
    old.mkdir()
    (old / "001-decision-foo.md").write_text(entry("decision", "foo"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "create under the old directory")
    git(repo, "mv", ".minerva/decisions/001-decision-foo.md",
        ".minerva/knowledge/001-decision-foo.md")
    git(repo, "commit", "-q", "-m", "migrate directory")

    got = ren.landing_date(repo, ".minerva/knowledge/001-decision-foo.md")
    assert got is not None, "a renamed path must still resolve to a date"
    assert len(got) == 10 and got[4] == "-"


# --- reference forms the rewriter used to miss --------------------------------
MAP = {"015-decision-foo": "2026-05-19-decision-foo"}


def test_rewrites_a_knowledge_path_reference():
    """An entry referenced by PATH rather than by wikilink. The linter's edge model only
    knows `[[wikilinks]]`, so a corpus can lose every one of these and still lint clean
    both before and after — 182 of them broke in one real migration, undetected."""
    src = "See `.minerva/knowledge/015-decision-foo.md` for detail.\n"
    assert ren.rewrite_links(src, MAP) == \
        "See `.minerva/knowledge/2026-05-19-decision-foo.md` for detail.\n"


def test_rewrites_a_relative_markdown_link():
    assert ren.rewrite_links("[e](015-decision-foo.md)\n", MAP) == \
        "[e](2026-05-19-decision-foo.md)\n"
    assert ren.rewrite_links("[e](./015-decision-foo.md)\n", MAP) == \
        "[e](./2026-05-19-decision-foo.md)\n"


def test_leaves_an_unmapped_path_byte_identical():
    """Map-lookup-only is what bounds the blast radius: these patterns can only retarget
    a file the migration is already moving, never invent a target."""
    src = "See `.minerva/knowledge/099-bug-other.md` and [x](other.md).\n"
    assert ren.rewrite_links(src, MAP) == src


def test_leaves_a_fenced_path_reference_alone():
    src = "```\n`.minerva/knowledge/015-decision-foo.md`\n```\n"
    assert ren.rewrite_links(src, MAP) == src


def test_context_path_with_trailing_punctuation_resolves():
    """`,` used to be captured INTO the lookup key, so `111-terms,` missed the map and
    the path was left behind while its neighbour on the same line was rewritten."""
    dmap = {"111-terms": "2026-06-05-terms"}
    out = ren.rewrite_links(
        "**Context**: .minerva/work/111-terms, .minerva/work/111-terms\n", {}, dmap)
    assert "111-terms" not in out
    assert out.count("2026-06-05-terms") == 2


def test_plan_counts_bare_shorthand_without_rewriting_it(tmp_path):
    """`[[139]]` names an entry with no slug. Before a rename a reader can resolve it
    with `ls .minerva/knowledge/139-*`; after one the number is in no filename at all.
    Counted so the migration reports it — never resolved, because resolving by number
    alone is wrong often enough to refuse."""
    kd = tmp_path / ".minerva" / "knowledge"
    kd.mkdir(parents=True)
    git(tmp_path, "init", "-q")
    (kd / "015-decision-foo.md").write_text("body\n")
    (tmp_path / "notes.md").write_text("see [[139]] and [[139]] and [[204]]\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")

    result = ren.plan(tmp_path)
    assert result["shorthand_refs"] == {"139": 2, "204": 1}
    # and the rewriter leaves them exactly as they were
    assert ren.rewrite_links("see [[139]]\n", result["entries"]) == "see [[139]]\n"


def test_an_already_migrated_work_dir_is_not_re_migrated(tmp_path):
    """The migration must be idempotent for work dirs as it already was for entries.

    `WORK_DIR_RE` matched a bare `NNN` only, so `2026-08-07-foo/` read as id `2026` plus
    slug `08-07-foo` and was re-dated to `2026-<today>-08-07-foo/` — with every
    `**Context**` path retargeted to the corrupted name. On this repo a second run wanted
    to rename all 50-odd already-migrated work dirs. The entry branch never had the bug
    because `ENTRY_RE` embeds the shared id grammar, date arm first.
    """
    wd = tmp_path / ".minerva" / "work"
    (wd / "2026-08-07-already-migrated").mkdir(parents=True)
    (wd / "111-legacy-unit").mkdir()
    git(tmp_path, "init", "-q")
    for name in ("2026-08-07-already-migrated", "111-legacy-unit"):
        (wd / name / "proposal.md").write_text("# p\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")

    work = ren.plan(tmp_path)["work"]
    assert "2026-08-07-already-migrated" not in work
    assert "111-legacy-unit" in work  # the genuine legacy unit still migrates


def test_shorthand_count_ignores_fenced_examples(tmp_path):
    """A `[[139]]` inside a fence is documentation showing the old syntax, not a live
    reference. Counting it would report migration work that does not exist — the same
    fence-blindness the plugin has had to re-fix twice before."""
    kd = tmp_path / ".minerva" / "knowledge"
    kd.mkdir(parents=True)
    git(tmp_path, "init", "-q")
    (tmp_path / "doc.md").write_text(
        "live [[139]] here\n\n```\nexample: see [[204]] for the old style\n```\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")

    assert ren.plan(tmp_path)["shorthand_refs"] == {"139": 1}


def test_a_markdown_link_outside_the_knowledge_dir_is_still_map_bound():
    """`MD_LINK_RE` is not directory-anchored, unlike `KNOWLEDGE_PATH_RE` — deliberately,
    matching `WIKILINK_STEM_RE`'s existing whole-repo reach. What bounds it is the map:
    a stem the migration is not moving is left byte-identical wherever it appears."""
    assert ren.rewrite_links("[x](README.md) and [y](099-bug-other.md)\n", MAP) == \
        "[x](README.md) and [y](099-bug-other.md)\n"
    assert ren.rewrite_links("[x](015-decision-foo.md)\n", MAP) == \
        "[x](2026-05-19-decision-foo.md)\n"


# --- bare [[NNN]] resolution: refuses by default, resolves only the provable case ---
def _legacy_corpus(tmp_path, entries=(), work=(), text=""):
    """A corpus that is still ENTIRELY legacy — the only state resolution is sound in."""
    kd = tmp_path / ".minerva" / "knowledge"
    wd = tmp_path / ".minerva" / "work"
    kd.mkdir(parents=True)
    wd.mkdir(parents=True)
    for name in entries:
        (kd / f"{name}.md").write_text("body\n")
    for name in work:
        (wd / name).mkdir()
        (wd / name / "proposal.md").write_text("# p\n")
    if text:
        (tmp_path / "notes.md").write_text(text)
    git(tmp_path, "init", "-q")
    git(tmp_path, "add", "-A")
    git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
    return tmp_path


def test_shorthand_resolves_only_when_provably_unambiguous(tmp_path):
    root = _legacy_corpus(tmp_path, entries=["139-decision-foo"], text="see [[139]]\n")
    r = ren.plan(root, resolve_shorthand=True)
    assert r["shorthand_refusals"] == []
    assert r["shorthand_resolved"]["139"].endswith("-decision-foo")


def test_shorthand_refuses_when_a_work_unit_shares_the_id(tmp_path):
    """The dominant observed failure: of 23 bare numbers naming exactly one entry, ~6
    meant the same-numbered WORK UNIT instead. `entries` alone cannot see that."""
    root = _legacy_corpus(tmp_path, entries=["139-decision-foo"],
                          work=["139-some-unit"], text="see [[139]]\n")
    r = ren.plan(root, resolve_shorthand=True)
    assert r["shorthand_resolved"] == {}
    assert "work unit" in dict(r["shorthand_refusals"])["139"]


def test_shorthand_refuses_when_two_entries_share_the_id(tmp_path):
    """Not hypothetical: this repo's own history has `001-gitignore-before-worktree` and
    `001-review-lens-ownership`. `entries` keys on the full stem, so a naive lookup by
    bare id would never notice."""
    root = _legacy_corpus(tmp_path, entries=["001-decision-foo", "001-decision-bar"],
                          text="see [[001]]\n")
    r = ren.plan(root, resolve_shorthand=True)
    assert r["shorthand_resolved"] == {}
    assert "2 entries share id 001" in dict(r["shorthand_refusals"])["001"]


def test_shorthand_refuses_everything_on_a_partially_migrated_corpus(tmp_path):
    """The guard can only see work units that still carry a legacy id. Once one is
    renamed its number leaves the filesystem, so a reference meaning THAT unit stops
    colliding with anything and would resolve to whatever entry still holds the number —
    the exact failure the guard exists to prevent. So a mixed corpus refuses outright."""
    root = _legacy_corpus(tmp_path, entries=["139-decision-foo"],
                          work=["2026-01-01-already-migrated"], text="see [[139]]\n")
    r = ren.plan(root, resolve_shorthand=True)
    assert r["shorthand_resolved"] == {}
    assert "partially migrated" in dict(r["shorthand_refusals"])["139"]


def test_shorthand_is_never_rewritten_without_the_flag(tmp_path):
    """Upgrading minerva must not silently start rewriting anyone's corpus."""
    root = _legacy_corpus(tmp_path, entries=["139-decision-foo"], text="see [[139]]\n")
    r = ren.plan(root)
    assert r["shorthand_resolved"] == {} and r["shorthand_refusals"] == []
    assert ren.rewrite_links("see [[139]]\n", r["entries"]) == "see [[139]]\n"


def test_resolution_is_fence_aware_and_map_bound(tmp_path):
    root = _legacy_corpus(tmp_path, entries=["139-decision-foo"], text="see [[139]]\n")
    smap = ren.plan(root, resolve_shorthand=True)["shorthand_resolved"]
    assert ren.rewrite_links("```\nsee [[139]]\n```\n", {}, None, smap) == \
        "```\nsee [[139]]\n```\n"
    assert ren.rewrite_links("see [[999]]\n", {}, None, smap) == "see [[999]]\n"


def test_plan_reports_skipped_and_invalid_date_ids(tmp_path):
    """A plan is a control only when its anomalies are separable at the output's real
    size — three corrupted rows among 552 were missed on a real dry run."""
    root = _legacy_corpus(tmp_path, entries=["2026-01-01-decision-done"],
                          work=["2026-13-45-bad-date"])
    r = ren.plan(root)
    assert any("2026-01-01-decision-done" in p for p in r["already_migrated"])
    assert any("2026-13-45-bad-date" in p for p in r["invalid_date_ids"])


def test_shorthand_sites_carry_file_and_line(tmp_path):
    root = _legacy_corpus(tmp_path, entries=["139-decision-foo"],
                          text="line one\nsee [[139]]\n")
    sites = ren.plan(root)["shorthand_sites"]
    assert ("notes.md", 2, "139") in sites
