#!/usr/bin/env python3
"""Refuse to run a skill snippet against a stale copy of the scripts it is about to import.

An adapted copy of minerva's guard. A loaded lorestrom package may be a symlink or cached
copy of a primary checkout, so while this plugin is developed in a linked worktree a snippet
can resolve scripts other than the ones being edited. Adding a function then fails loudly;
modifying one imports fine and silently runs the old code. This guard turns the silent case
into a non-zero exit.

Invoked as one line at each `PLUGIN_SCRIPTS=` site::

    [ -n "$PLUGIN_SCRIPTS" ] && { python3 "$PLUGIN_SCRIPTS/plugin_guard.py" || exit 1; }

It compares the whole scripts directory by content, because modules import siblings, and it
exits non-zero rather than warning, because a printed warning is not enforced. The escape
hatch is `LORESTROM_SCRIPTS`. It does not cover skill prose, which the host loads through the
same symlink.
"""
import filecmp
import os
import subprocess
import sys
from pathlib import Path

# Where a checkout keeps these scripts, relative to its own root.
_TREE_SCRIPTS = Path("plugins") / "lorestrom" / "scripts"


def working_tree_root():
    """The root of the tree the caller is standing in (the worktree when inside one).

    Returns None outside a git repo, which makes the guard a silent no-op there.
    """
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=False)
    except (OSError, ValueError):
        return None
    if out.returncode != 0:
        return None
    root = out.stdout.strip()
    return Path(root) if root else None


def divergence(resolved_dir: Path, tree_root):
    """`(resolved_dir, local_dir)` when the two scripts directories differ; None when they agree.

    None (proceed) for every case that is not a genuine divergence: no working tree, a tree
    with no `plugins/lorestrom/scripts/` (every consumer project), or the same directory.
    The comparison is over every `*.py`, by content, never by realpath.
    """
    if tree_root is None:
        return None
    local_dir = tree_root / _TREE_SCRIPTS
    if not local_dir.is_dir() or not resolved_dir.is_dir():
        return None
    if local_dir.resolve() == resolved_dir.resolve():
        return None

    names = {p.name for p in local_dir.glob("*.py")} | {p.name for p in resolved_dir.glob("*.py")}
    match, mismatch, errors = filecmp.cmpfiles(str(resolved_dir), str(local_dir),
                                               sorted(names), shallow=False)
    # `errors` are files present on one side only: a divergence as much as an edited one.
    if mismatch or errors:
        return resolved_dir, local_dir
    return None


def main(argv):
    if len(argv) != 1:
        print("usage: plugin_guard.py   (no arguments; compares the whole scripts directory)",
              file=sys.stderr)
        return 2
    # An explicit choice is always honoured: the escape hatch at the call site.
    if os.environ.get("LORESTROM_SCRIPTS"):
        return 0
    found = divergence(Path(__file__).resolve().parent, working_tree_root())
    if found is None:
        return 0
    resolved, local = found
    print(
        f"lorestrom: refusing to run against a stale scripts directory.\n"
        f"  would import from: {resolved}\n"
        f"  you are editing  : {local}\n"
        f"These differ. The loaded plugin resolves to a separate package, which may be the\n"
        f"primary checkout or a cached install. Update the lorestrom plugin, or set\n"
        f"LORESTROM_SCRIPTS to choose a directory deliberately.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
