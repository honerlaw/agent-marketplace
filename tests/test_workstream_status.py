"""Tests for the workstream aggregator (`scripts/workstream_status.py`).

The failure this exists to prevent is a **falsely-clean status table**. Every other way
this skill can be wrong is visible — a missing column, an ugly cell. Under-reporting is
not: a workstream that renders as "nothing in flight" looks exactly like a tidy project,
and the reader's next action is to start work that already exists.

Two of these tests pin defects the live corpus produced on the first smoke run, before any
of them existed. `test_worktree_present_is_a_directory_test_not_a_glob_sighting` is the
important one: the first implementation set the flag from the worktree glob, and because
every linked worktree carries the whole COMMITTED `.minerva/work/` history, it read true
for all 65 units in the project. Asserting `worktree_present` is set somewhere would have
passed against that bug — `2026-08-10-pattern-presence-assertions-rot-into-green-lies` —
so the assertions here are the negative ones.
"""
from pathlib import Path

import pytest

from workstream_status import _has_scratchpad_body, _stage, workstream_status

HEADER_ONLY = """# Scratchpad: a-unit

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion.
"""

PROMOTE_MARKER = "Summarized at minerva:promote on 2026-08-09 — see archive/.\n"


def write_unit(root: Path, slug: str, *, status="Draft", scratchpad=HEADER_ONLY,
               phases=None, under_worktree=None):
    """Materialise one work unit. `under_worktree` puts it inside that worktree's tree."""
    base = root / ".minerva"
    if under_worktree:
        base = base / "worktrees" / under_worktree / ".minerva"
    d = base / "work" / slug
    d.mkdir(parents=True, exist_ok=True)

    proposal = f"# Proposal: {slug}\n\n**Status**: {status}\n\n## Goal\nx\n"
    if phases:
        proposal += "\n## Phases\n\n" + "".join(
            f"{i}. **{name}** — does a thing\n" for i, name in enumerate(phases, start=1))
    (d / "proposal.md").write_text(proposal)
    if scratchpad is not None:
        (d / "scratchpad.md").write_text(scratchpad)
    return d


def make_worktree_dir(root: Path, slug: str):
    """The on-disk worktree directory — what `worktree_present` actually asks about."""
    (root / ".minerva" / "worktrees" / slug).mkdir(parents=True, exist_ok=True)


# --- stage ladder -------------------------------------------------------------


def test_each_stage_value_is_reachable(tmp_path):
    write_unit(tmp_path, "2026-01-01-drafted")
    write_unit(tmp_path, "2026-01-02-started", scratchpad=HEADER_ONLY + "\n## Notes\nbegan\n")
    write_unit(tmp_path, "2026-01-03-promoted", scratchpad=PROMOTE_MARKER)
    write_unit(tmp_path, "2026-01-04-done", status="Shipped (2026-01-04)",
               scratchpad=PROMOTE_MARKER)

    stages = {u["slug"]: u["stage"] for u in workstream_status(tmp_path)["units"]}
    assert stages == {
        "2026-01-01-drafted": "draft",
        "2026-01-02-started": "in-progress",
        "2026-01-03-promoted": "promoted",
        "2026-01-04-done": "shipped",
    }


def test_a_promoted_unit_is_never_read_as_in_progress():
    """The rung order is the whole point: a post-promote scratchpad IS a body.

    Ordering the ladder scratchpad-first would classify every finished unit in the corpus
    as live work — the exact falsely-*dirty* mirror of the failure this module guards.
    """
    assert _has_scratchpad_body(PROMOTE_MARKER)
    assert _stage({"status": "Draft", "promoted": True}, has_scratchpad_body=True) == "promoted"


def test_header_only_scratchpad_has_no_body():
    assert not _has_scratchpad_body(HEADER_ONLY)
    assert not _has_scratchpad_body("")


def test_a_fenced_header_example_does_not_hide_the_body_under_it():
    """Fence-aware, per `2026-06-11-constraint-fence-scans-import-fence-re`."""
    text = HEADER_ONLY + "\n```\n# Scratchpad: x\n> **Ephemeral working memory.**\n```\n"
    assert _has_scratchpad_body(text)


def test_a_blockquote_styled_log_is_a_body_not_more_header(tmp_path):
    """Regression: header is a PREFIX, not a set of line shapes.

    Skipping every `>` line wherever it appeared read a scratchpad whose notes are
    written as blockquotes — a natural way to log an error, and the style the
    propose-written header itself models — as an untouched draft. Under-reporting
    arriving through the check meant to prevent it.
    """
    body = HEADER_ONLY + "\n> Investigated the failing test; root cause is a race.\n> Fix in progress.\n"
    assert _has_scratchpad_body(body)

    write_unit(tmp_path, "2026-06-01-quoted", scratchpad=body)
    (unit,) = workstream_status(tmp_path)["units"]
    assert unit["stage"] == "in-progress"


def test_an_h1_after_the_header_block_is_a_body(tmp_path):
    """The H1 exemption is spent on the FIRST one; a later `# ` heading is content."""
    assert _has_scratchpad_body(HEADER_ONLY + "\n# Findings\n")


def test_an_interrupted_promote_is_not_reported_as_shipped(tmp_path):
    """`minerva:promote` writes Status and archives the scratchpad in two non-atomic
    steps. A run interrupted between them leaves `Shipped` with no marker; reading
    Status alone renders that unit as done while `in_flight` still counts it live —
    one row of the table contradicting another, with "done" as the visible half."""
    assert _stage({"status": "Shipped (2026-06-02)", "promoted": False},
                  has_scratchpad_body=True) == "in-progress"

    write_unit(tmp_path, "2026-06-02-half", status="Shipped (2026-06-02)",
               scratchpad=HEADER_ONLY + "\n## Notes\nwork\n")
    (unit,) = workstream_status(tmp_path)["units"]
    assert unit["stage"] != "shipped"
    assert unit["in_flight"], "the two signals must agree that this unit is not done"


# --- the two roots, and the dedupe --------------------------------------------


def test_a_unit_living_only_in_a_worktree_is_still_found(tmp_path):
    """The case the second glob exists for: unmerged work has no main-tree copy."""
    write_unit(tmp_path, "2026-02-01-only-in-wt", under_worktree="2026-02-01-only-in-wt")
    slugs = [u["slug"] for u in workstream_status(tmp_path)["units"]]
    assert slugs == ["2026-02-01-only-in-wt"]


def test_a_slug_in_both_roots_is_one_unit_and_the_main_tree_record_wins(tmp_path):
    write_unit(tmp_path, "2026-02-02-both", status="Shipped (2026-02-02)",
               scratchpad=PROMOTE_MARKER)
    write_unit(tmp_path, "2026-02-02-both", status="Draft",
               under_worktree="2026-02-02-both")

    units = workstream_status(tmp_path)["units"]
    assert len(units) == 1, "the same slug under both roots is one unit, not two"
    assert units[0]["stage"] == "shipped", "the main-tree record must win the dedupe"


def test_a_directory_without_a_proposal_is_not_a_unit(tmp_path):
    (tmp_path / ".minerva" / "work" / "not-a-unit").mkdir(parents=True)
    (tmp_path / ".minerva" / "work" / "not-a-unit" / "notes.md").write_text("hi")
    write_unit(tmp_path, "2026-02-03-real")

    assert [u["slug"] for u in workstream_status(tmp_path)["units"]] == ["2026-02-03-real"]


def test_a_unit_with_no_scratchpad_and_no_status_does_not_crash(tmp_path):
    d = tmp_path / ".minerva" / "work" / "2026-02-04-bare"
    d.mkdir(parents=True)
    (d / "proposal.md").write_text("# Proposal: bare\n")

    (unit,) = workstream_status(tmp_path)["units"]
    assert unit["stage"] == "draft"
    assert unit["status"] is None


def test_an_empty_project_reports_zero_units_not_an_error(tmp_path):
    result = workstream_status(tmp_path)
    assert result["units"] == []
    assert result["counts"]["total"] == 0


# --- worktree_present ---------------------------------------------------------


def test_worktree_present_is_a_directory_test_not_a_glob_sighting(tmp_path):
    """Regression: the flag once read true for every unit in the project.

    A linked worktree contains the whole committed `.minerva/work/` history, so `sibling`
    below is reachable through `other`'s worktree tree while having no worktree of its
    own. Sighting-through-a-glob and has-a-worktree-directory are different questions.
    """
    write_unit(tmp_path, "2026-03-01-sibling", status="Shipped (2026-03-01)",
               scratchpad=PROMOTE_MARKER)
    write_unit(tmp_path, "2026-03-02-live")
    # `live`'s worktree carries a copy of `sibling`'s record, exactly as a real one does.
    write_unit(tmp_path, "2026-03-01-sibling", under_worktree="2026-03-02-live")
    write_unit(tmp_path, "2026-03-02-live", under_worktree="2026-03-02-live")
    make_worktree_dir(tmp_path, "2026-03-02-live")

    flags = {u["slug"]: u["worktree_present"] for u in workstream_status(tmp_path)["units"]}
    assert flags == {"2026-03-01-sibling": False, "2026-03-02-live": True}


def test_counts_worktrees_present(tmp_path):
    write_unit(tmp_path, "2026-03-03-a")
    write_unit(tmp_path, "2026-03-04-b")
    make_worktree_dir(tmp_path, "2026-03-04-b")

    assert workstream_status(tmp_path)["counts"]["worktrees_present"] == 1


# --- phases -------------------------------------------------------------------


def test_a_phased_unit_mid_progress_reports_the_next_phase(tmp_path):
    write_unit(tmp_path, "2026-04-01-phased", phases=["Groundwork", "The rest"],
               scratchpad=HEADER_ONLY + "\n## Notes\nstarted\n")

    (unit,) = workstream_status(tmp_path, ["2026-04-01-phased"])["units"]
    assert unit["progress"] == {
        "phased": True, "total": 2, "merged": 1,
        "next_position": 2, "next_branch": "2026-04-01-phased-phase-2", "complete": False,
    }
    assert unit["phases"][1]["branch"] == "2026-04-01-phased-phase-2"
    assert not unit["progress"]["complete"]


def test_phase_branch_names_come_from_the_owner_module(tmp_path):
    """Phase 1 keeps the BARE slug; only phases 2+ get a suffix.

    Rebuilding these names in a second place is the shape
    `2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant` is about, so this
    asserts the topology the module owns rather than a string this test builds.
    """
    write_unit(tmp_path, "2026-04-02-phased", phases=["One", "Two", "Three"])
    (unit,) = workstream_status(tmp_path)["units"]
    assert [p["branch"] for p in unit["phases"]] == [
        "2026-04-02-phased",
        "2026-04-02-phased-phase-2",
        "2026-04-02-phased-phase-3",
    ]


def test_an_incomplete_phased_unit_is_counted_separately(tmp_path):
    """It is the count that stops a mid-phase worktree reading as cleanup-overdue."""
    write_unit(tmp_path, "2026-04-03-phased", phases=["One", "Two"])
    make_worktree_dir(tmp_path, "2026-04-03-phased")

    counts = workstream_status(tmp_path, ["2026-04-03-phased"])["counts"]
    assert counts["phased_incomplete"] == 1
    assert counts["worktrees_present"] == 1


def test_an_unphased_unit_reports_phased_false(tmp_path):
    write_unit(tmp_path, "2026-04-04-plain")
    (unit,) = workstream_status(tmp_path)["units"]
    assert unit["phases"] == []
    assert unit["progress"]["phased"] is False


def test_a_fenced_phases_example_does_not_phase_the_unit(tmp_path):
    """Delegated to `read_phases`, which is fence-aware; pinned because this skill's own
    prose shows a fenced `## Phases` example."""
    d = write_unit(tmp_path, "2026-04-05-fenced")
    (d / "proposal.md").write_text(
        "# Proposal: x\n\n**Status**: Draft\n\n```\n## Phases\n\n1. **Nope** — example\n```\n")
    (unit,) = workstream_status(tmp_path)["units"]
    assert unit["progress"]["phased"] is False


# --- counts and knowledge -----------------------------------------------------


def test_in_flight_count_uses_the_imported_predicate_not_the_stage(tmp_path):
    """`in_flight` is `Status is Draft OR not promoted` — deliberately wider than any one
    stage, and owned by `work_status`. A shipped-and-promoted unit is the only thing it
    excludes."""
    write_unit(tmp_path, "2026-05-01-draft")
    write_unit(tmp_path, "2026-05-02-promoted", scratchpad=PROMOTE_MARKER)
    write_unit(tmp_path, "2026-05-03-done", status="Shipped (2026-05-03)",
               scratchpad=PROMOTE_MARKER)

    counts = workstream_status(tmp_path)["counts"]
    assert counts["total"] == 3
    assert counts["in_flight"] == 2
    assert counts["by_stage"] == {"draft": 1, "promoted": 1, "shipped": 1}


def test_a_missing_knowledge_dir_reports_absent_not_a_clean_corpus(tmp_path):
    """An empty result and a missing target look identical downstream, and only one of
    them is good news (`2026-08-22-pattern-a-distinguished-state-inferred-from-outputs-is-the-steady-state`)."""
    write_unit(tmp_path, "2026-05-04-x")
    assert workstream_status(tmp_path)["knowledge"] == {"exists": False}


def test_knowledge_health_is_reported_for_a_real_corpus(tmp_path):
    kd = tmp_path / ".minerva" / "knowledge"
    kd.mkdir(parents=True)
    (kd / "2026-01-01-pattern-a-thing.md").write_text(
        "# A thing\n\n**Type**: pattern\n\nBody.\n\n## Related\n")
    (kd / "index.md").write_text("# Knowledge index\n\n## Patterns\n\n- [[2026-01-01-pattern-a-thing]] — a thing\n")

    k = workstream_status(tmp_path)["knowledge"]
    assert k["exists"] is True
    assert k["entries"] == 1
    assert k["by_type"] == {"pattern": 1}
    assert k["overview_exists"] is False
    assert k["unsynthesized"] == 1
    assert k["link_rot"] == 0


def test_lint_and_link_rot_counts_are_wired_to_real_findings(tmp_path):
    """Asserts the VALUES, not their types.

    `assert isinstance(lint_errors, int)` passes against an implementation that always
    returns 0, or one that files every error under `warnings` —
    `2026-08-10-pattern-presence-assertions-rot-into-green-lies`. This corpus is built to
    produce a real finding and a real broken overview link, so a swapped severity filter
    or a dropped `link_rot` goes red.
    """
    kd = tmp_path / ".minerva" / "knowledge"
    kd.mkdir(parents=True)
    (kd / "2026-01-01-pattern-a-thing.md").write_text(
        "# A thing\n\n**Type**: pattern\n\nBody.\n\n"
        "## Related\n\n- [[2026-01-02-pattern-does-not-exist]] — dangling\n")
    (kd / "index.md").write_text("# Knowledge index\n\n## Patterns\n")
    (kd / "overview.md").write_text(
        "# Overview\n\nSee [[2026-09-09-pattern-also-missing]].\n")

    k = workstream_status(tmp_path)["knowledge"]
    assert k["link_rot"] == 1, "overview links a stem with no entry"
    assert k["lint_errors"] + k["lint_warnings"] > 0, (
        "a dangling ## Related link and an uncatalogued entry must surface as findings")
    assert k["overview_exists"] is True


# --- the live corpus ----------------------------------------------------------

REPO = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(not (REPO / ".minerva" / "work").is_dir(),
                    reason="no .minerva/work in this checkout")
def test_the_live_corpus_does_not_report_every_unit_as_having_a_worktree():
    """Asks the corpus rather than a fixture — the shape
    `2026-08-11-pattern-the-enumeration-is-what-fails` recommends.

    This is the assertion that actually caught the glob bug: against it, every one of the
    project's units claimed a worktree. Worktrees are transient, so the bar is only that
    the flag DISCRIMINATES.
    """
    result = workstream_status(REPO)
    assert result["counts"]["total"] > 1
    assert result["counts"]["worktrees_present"] < result["counts"]["total"]
