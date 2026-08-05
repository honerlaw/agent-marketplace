"""Git-fixture tests for the cross-branch entry allocator (`scripts/knowledge_next_nnn.py`).

The allocator exists because a knowledge entry is a **new file**: when two work units
independently pick the same NNN, git merges both cleanly and ships a duplicate id with
no conflict to catch it. Once `minerva:promote` became add-only there is no longer even
an incidental `index.md` conflict to notice, so these tests cover the sources a plain
directory scan cannot see — an unmerged local branch, a remote branch, and a number
used by a commit that was later rebased away.

Each test builds a real throwaway repo; `conftest.py` puts `scripts/` on `sys.path`.
"""
import subprocess

import pytest

from knowledge_next_nnn import allocated_nnns, next_nnn


# --- fixture builders --------------------------------------------------------
def git(repo, *args):
    subprocess.run(["git", *args], cwd=str(repo), capture_output=True, check=True)


def init_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "t@example.com")
    git(path, "config", "user.name", "Test")
    return path


def add_entry(repo, nnn, typ="decision", slug="x"):
    kd = repo / ".minerva" / "knowledge"
    kd.mkdir(parents=True, exist_ok=True)
    (kd / f"{nnn}-{typ}-{slug}.md").write_text(
        f"# {slug}\n\n**Date**: 2026-01-01\n**Type**: {typ}\n"
        f"**Summary**: s\n**Context**: x\n\n## Finding\nf\n"
    )


def commit(repo, message="wip"):
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", message)


def kd(repo):
    return repo / ".minerva" / "knowledge"


# --- baseline ----------------------------------------------------------------
def test_empty_corpus_starts_at_001(tmp_path):
    repo = init_repo(tmp_path / "r")
    (repo / ".minerva" / "knowledge").mkdir(parents=True)
    assert next_nnn(kd(repo)) == "001"


def test_absent_directory_starts_at_001(tmp_path):
    repo = init_repo(tmp_path / "r")
    assert next_nnn(kd(repo)) == "001"


def test_non_git_directory_uses_the_working_tree_only(tmp_path):
    """A minerva project need not be a git repo; the scan degrades, never crashes."""
    plain = tmp_path / "plain"
    add_entry(plain, "003")
    assert next_nnn(kd(plain)) == "004"


def test_uncommitted_working_tree_entry_counts(tmp_path):
    """The entry promote just wrote isn't committed yet — allocating a sibling in the
    same run must still step past it."""
    repo = init_repo(tmp_path / "r")
    add_entry(repo, "001")
    commit(repo)
    add_entry(repo, "002")  # written, not committed
    assert next_nnn(kd(repo)) == "003"


# --- the sources a directory scan cannot see ---------------------------------
def test_sees_entry_on_an_unmerged_local_branch(tmp_path):
    """The exact near-miss this unit exists to prevent: another work unit's entry is
    sitting on its own branch, invisible to `ls .minerva/knowledge`."""
    repo = init_repo(tmp_path / "r")
    add_entry(repo, "001")
    commit(repo)
    git(repo, "checkout", "-q", "-b", "feature")
    add_entry(repo, "005")
    commit(repo, "other unit's entry")
    git(repo, "checkout", "-q", "main")

    assert sorted(kd(repo).glob("*.md")) == [kd(repo) / "001-decision-x.md"]  # tree shows 001
    assert "005" in allocated_nnns(kd(repo))
    assert next_nnn(kd(repo)) == "006"


def test_sees_entry_on_a_fetched_remote_branch(tmp_path):
    upstream = init_repo(tmp_path / "upstream")
    add_entry(upstream, "001")
    commit(upstream)
    git(upstream, "checkout", "-q", "-b", "feature")
    add_entry(upstream, "007")
    commit(upstream, "remote unit")
    git(upstream, "checkout", "-q", "main")

    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", str(upstream), str(clone)],
                   check=True, capture_output=True)
    # `feature` arrived as a remote-tracking ref at clone time — no fetch needed.
    assert next_nnn(kd(clone)) == "008"


def test_fetch_picks_up_a_branch_pushed_after_the_clone(tmp_path):
    upstream = init_repo(tmp_path / "upstream")
    add_entry(upstream, "001")
    commit(upstream)

    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", str(upstream), str(clone)],
                   check=True, capture_output=True)

    git(upstream, "checkout", "-q", "-b", "later")
    add_entry(upstream, "009")
    commit(upstream, "pushed from elsewhere")
    git(upstream, "checkout", "-q", "main")

    assert next_nnn(kd(clone)) == "002"                 # genuinely not yet visible
    assert next_nnn(kd(clone), fetch=True) == "010"     # visible after refreshing refs


def test_sees_a_number_whose_file_was_later_deleted(tmp_path):
    """"Ever added on a reachable ref", not "present on some tip". A renamed or deleted
    entry still holds its number — reissuing it would collide with the shipped history."""
    repo = init_repo(tmp_path / "r")
    add_entry(repo, "001")
    add_entry(repo, "004")
    commit(repo)
    (kd(repo) / "004-decision-x.md").unlink()
    commit(repo, "remove 004")

    assert sorted(p.name for p in kd(repo).glob("*.md")) == ["001-decision-x.md"]
    assert next_nnn(kd(repo)) == "005"


def test_number_from_a_force_deleted_branch_is_reusable(tmp_path):
    """Deliberate boundary. `git log --all` walks refs, not the reflog, so an
    abandoned force-deleted branch's number comes back into circulation. That entry
    never shipped, so reuse is correct — and reflogs are local-only and expiring, so
    honoring them would make allocation differ between machines."""
    repo = init_repo(tmp_path / "r")
    add_entry(repo, "001")
    commit(repo)
    git(repo, "checkout", "-q", "-b", "scratch")
    add_entry(repo, "004")
    commit(repo, "abandoned")
    git(repo, "checkout", "-q", "main")
    git(repo, "branch", "-qD", "scratch")

    assert next_nnn(kd(repo)) == "002"


def test_absent_corpus_does_not_scan_the_ambient_repo(tmp_path, monkeypatch):
    """Regression: resolving the repo from the process CWD instead of the knowledge
    path scanned whichever project the caller happened to be standing in."""
    repo = init_repo(tmp_path / "r")
    add_entry(repo, "001")
    commit(repo)
    elsewhere = init_repo(tmp_path / "elsewhere")
    add_entry(elsewhere, "777")
    commit(elsewhere)

    monkeypatch.chdir(elsewhere)
    assert next_nnn(kd(repo)) == "002"  # not 778


# --- robustness --------------------------------------------------------------
def test_offline_fetch_failure_is_not_fatal(tmp_path):
    """`--fetch` is best-effort: an unreachable remote narrows the scan, never fails."""
    repo = init_repo(tmp_path / "r")
    add_entry(repo, "001")
    commit(repo)
    git(repo, "remote", "add", "origin", str(tmp_path / "does-not-exist"))
    assert next_nnn(kd(repo), fetch=True) == "002"


def test_ignores_files_that_are_not_entries(tmp_path):
    repo = init_repo(tmp_path / "r")
    add_entry(repo, "001")
    (kd(repo) / "index.md").write_text("# Knowledge index\n<!-- index-watermark: 001 -->\n")
    (kd(repo) / "overview.md").write_text("# Knowledge overview\n")
    (kd(repo) / "notes.md").write_text("scratch\n")
    commit(repo)
    assert allocated_nnns(kd(repo)) == {"001"}


@pytest.mark.parametrize("nnn,expected", [("009", "010"), ("099", "100"), ("999", "1000")])
def test_padding_and_rollover(tmp_path, nnn, expected):
    """Above 999 the width grows rather than wrapping to 000 and colliding."""
    plain = tmp_path / f"p{nnn}"
    add_entry(plain, nnn)
    assert next_nnn(kd(plain)) == expected
