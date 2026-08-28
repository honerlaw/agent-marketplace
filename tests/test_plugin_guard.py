"""The guard that refuses to run a snippet against a stale copy of its module.

`~/.claude/plugins/minerva` symlinks to the primary checkout, so a skill snippet run while working
in a linked worktree imports the primary checkout's code. Adding a function fails loudly; MODIFYING
one runs the old behavior silently. `scripts/plugin_guard.py` turns the silent case into a non-zero
exit.

These tests are hermetic — no git repo of their own, no network. `divergence()` takes the working
tree root as an argument precisely so it can be tested without one.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from plugin_guard import divergence, main, working_tree_root

REPO = Path(__file__).resolve().parent.parent
GUARD = REPO / "plugins" / "minerva" / "scripts" / "plugin_guard.py"
TREE_SCRIPTS = Path("plugins") / "minerva" / "scripts"


def _tree(root: Path, module: str, body: str) -> Path:
    """A fake checkout whose `plugins/minerva/scripts/<module>.py` holds `body`."""
    d = root / TREE_SCRIPTS
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{module}.py").write_text(body)
    return d


def test_identical_copies_do_not_diverge(tmp_path):
    """The common self-development case: working in a worktree whose scripts match. Must stay
    silent, or every such session hard-fails for no reason."""
    resolved = _tree(tmp_path / "primary", "work_status", "x = 1\n")
    _tree(tmp_path / "wt", "work_status", "x = 1\n")
    assert divergence("work_status", resolved, tmp_path / "wt") is None


def test_differing_copies_diverge(tmp_path):
    """The silent failure this exists to catch: you edited the module, the snippet would run the
    other copy."""
    resolved = _tree(tmp_path / "primary", "work_status", "x = 1\n")
    _tree(tmp_path / "wt", "work_status", "x = 2\n")
    found = divergence("work_status", resolved, tmp_path / "wt")
    assert found is not None
    assert found[0].name == "work_status.py" and found[1].name == "work_status.py"


def test_a_consumer_project_is_a_silent_no_op(tmp_path):
    """A project that installs minerva normally has no `plugins/minerva/scripts/` of its own and
    cannot skew. The guard ships in shared skill prose to every install, so a false positive here
    would warn about worktrees and symlinks at users who have neither."""
    resolved = _tree(tmp_path / "primary", "work_status", "x = 1\n")
    consumer = tmp_path / "someones-app"
    (consumer / "src").mkdir(parents=True)
    assert divergence("work_status", resolved, consumer) is None


def test_no_git_repo_is_a_silent_no_op(tmp_path):
    resolved = _tree(tmp_path / "primary", "work_status", "x = 1\n")
    assert divergence("work_status", resolved, None) is None


def test_the_same_file_does_not_diverge(tmp_path):
    """Running from the primary checkout itself: resolved and local are one file."""
    resolved = _tree(tmp_path / "primary", "work_status", "x = 1\n")
    assert divergence("work_status", resolved, tmp_path / "primary") is None


def test_a_module_absent_from_the_tree_does_not_diverge(tmp_path):
    resolved = _tree(tmp_path / "primary", "work_status", "x = 1\n")
    _tree(tmp_path / "wt", "something_else", "y = 1\n")
    assert divergence("work_status", resolved, tmp_path / "wt") is None


def test_comparison_is_on_contents_not_paths(tmp_path):
    """Realpaths always differ inside a worktree. Comparing them would hard-fail every
    self-development session even when the code is byte-identical."""
    resolved = _tree(tmp_path / "primary", "work_status", "same\n")
    local_dir = _tree(tmp_path / "wt", "work_status", "same\n")
    assert local_dir.resolve() != resolved.resolve()      # genuinely different paths
    assert divergence("work_status", resolved, tmp_path / "wt") is None


def test_the_override_short_circuits_the_check(tmp_path, monkeypatch):
    """`MINERVA_SCRIPTS` is the escape hatch at the call site: an explicit choice is honoured
    without being second-guessed."""
    monkeypatch.setenv("MINERVA_SCRIPTS", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    assert main(["plugin_guard.py", "work_status"]) == 0


def test_bad_usage_exits_two():
    assert main(["plugin_guard.py"]) == 2


def test_the_guard_exits_non_zero_and_explains_itself(tmp_path):
    """End-to-end through the real CLI, because the contract the snippets rely on is the EXIT
    CODE, not the return value of a function. A guard that printed and exited 0 would be the
    unenforced warning this design rejected."""
    primary = _tree(tmp_path / "primary", "work_status", "x = 1\n")
    (primary / "plugin_guard.py").write_text(GUARD.read_text())
    wt = tmp_path / "wt"
    _tree(wt, "work_status", "x = 2\n")
    subprocess.run(["git", "init", "-q"], cwd=wt, check=True)

    proc = subprocess.run([sys.executable, str(primary / "plugin_guard.py"), "work_status"],
                          cwd=wt, capture_output=True, text=True)
    assert proc.returncode == 1, proc.stderr
    assert "stale" in proc.stderr and "work_status" in proc.stderr
    assert "MINERVA_SCRIPTS" in proc.stderr, "the message must name its own escape hatch"


def test_working_tree_root_outside_a_repo_is_none(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert working_tree_root() is None
