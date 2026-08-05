#!/usr/bin/env python3
"""Allocate the next `.minerva/knowledge/` entry number, safely across branches.

`minerva:promote` used to allocate by scanning one directory in one worktree
(max+1). That is blind to entries sitting on other branches, so two work units in
flight independently picked the same number — and because a knowledge entry is a
NEW FILE, git merged both cleanly and shipped a duplicate id with no conflict to
catch it. `minerva:propose` already avoids this one layer up by scanning local work
dirs, local branches AND remote branches; this module is the same idea for entries.

It matters more here than there. Once promote is add-only, a work-unit branch's
`.minerva/` footprint is purely new files, so the textual `index.md` conflict that
used to catch collisions incidentally is gone by construction. This scan is the
only remaining backstop, which is also why it lives in a tested script rather than
as prose bash in a skill (knowledge 007, 021).

Sources, unioned:
  1. the working tree's knowledge directory (including entries not yet committed);
  2. every knowledge entry ever ADDED along the history of any ref — local branches
     and remote-tracking branches alike (`git log --all --diff-filter=A`).

(2) is deliberately "ever added on a reachable ref" rather than "present on some tip":
an entry whose file was later renamed or deleted still holds its number. It does NOT
cover commits reachable only from the reflog (an abandoned, force-deleted branch) —
those never shipped, so reusing their numbers is correct, and reflogs are local-only
and expiring, which would make allocation differ between machines.

Skipping a number costs nothing; reusing one is the bug this exists to prevent.

CLI: `python3 scripts/knowledge_next_nnn.py [<knowledge-dir>] [--fetch]`
Prints the next 3-digit NNN. `--fetch` refreshes remotes first (best-effort: a
network failure or a repo with no remote is not an error, it just narrows source 2).
"""
import re
import subprocess
import sys
from pathlib import Path

ENTRY_RE = re.compile(r"^(\d{3})-[a-z]+-.+\.md$")
# Same shape, but matched against a repo-relative path emitted by git.
PATH_ENTRY_RE = re.compile(r"(?:^|/)(\d{3})-[a-z]+-[^/]+\.md$")

DEFAULT_KNOWLEDGE_DIR = ".minerva/knowledge"


def _git(args, cwd, timeout=30):
    """Run a git command, returning stdout or None if git/the repo isn't usable."""
    try:
        proc = subprocess.run(
            ["git"] + args, cwd=str(cwd), capture_output=True, text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def _nearest_existing(path: Path) -> Path:
    """The first existing directory at or above `path`.

    The knowledge dir may not exist yet (a first-ever promote). Resolving the repo
    from the process CWD instead would scan whatever repo the caller happens to be
    standing in — a different project's numbers, silently.
    """
    p = path.resolve()
    while not p.is_dir() and p != p.parent:
        p = p.parent
    return p


def repo_root(start) -> Path:
    """The git top-level containing `start`, or None outside a repo."""
    out = _git(["rev-parse", "--show-toplevel"], _nearest_existing(Path(start)))
    return Path(out.strip()) if out and out.strip() else None


def _worktree_nnns(knowledge_dir: Path) -> set:
    if not knowledge_dir.is_dir():
        return set()
    return {m.group(1) for p in knowledge_dir.glob("*.md")
            if (m := ENTRY_RE.match(p.name))}


def _history_nnns(root: Path, rel_knowledge: str) -> set:
    """Every entry NNN ever added under `rel_knowledge`, across all refs.

    Path-limited traversal, so this stays cheap even on a large history.
    """
    out = _git(["log", "--all", "--diff-filter=A", "--name-only", "--format=",
                "--", rel_knowledge], root)
    if out is None:
        return set()
    return {m.group(1) for line in out.splitlines()
            if (m := PATH_ENTRY_RE.search(line.strip()))}


def allocated_nnns(knowledge_dir=DEFAULT_KNOWLEDGE_DIR, fetch=False) -> set:
    """The union of every NNN visible in the working tree and in history."""
    kd = Path(knowledge_dir)
    found = _worktree_nnns(kd)

    root = repo_root(kd)
    if root is None:
        return found  # non-git project: the directory is all there is

    if fetch:
        # Best-effort: offline, unauthenticated, or remote-less repos just proceed
        # with whatever refs are already local.
        _git(["fetch", "--quiet", "--all"], root, timeout=120)

    try:
        rel = str(kd.resolve().relative_to(root.resolve()))
    except ValueError:
        rel = DEFAULT_KNOWLEDGE_DIR
    return found | _history_nnns(root, rel)


def next_nnn(knowledge_dir=DEFAULT_KNOWLEDGE_DIR, fetch=False) -> str:
    """The next free 3-digit entry number. `001` on an empty/absent corpus."""
    found = allocated_nnns(knowledge_dir, fetch=fetch)
    return f"{(max(int(n) for n in found) + 1) if found else 1:03d}"


def main(argv=None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    fetch = "--fetch" in argv
    argv = [a for a in argv if a != "--fetch"]
    knowledge_dir = argv[0] if argv else DEFAULT_KNOWLEDGE_DIR
    print(next_nnn(knowledge_dir, fetch=fetch))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
