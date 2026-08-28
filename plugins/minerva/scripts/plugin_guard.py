#!/usr/bin/env python3
"""Refuse to run a skill snippet against a stale copy of the module it is about to import.

`~/.claude/plugins/minerva` is a **symlink** to the primary checkout on a self-hosting install,
so every snippet's `PLUGIN_SCRIPTS` resolution lands in `<repo>/plugins/minerva/scripts`
regardless of which worktree the work is happening in. minerva develops itself in linked
worktrees under `.minerva/worktrees/<date-slug>/`, each holding its own copy of these scripts at
a realpath that resolution never reaches.

The consequence is that a snippet run against a work-unit branch executes whatever branch the
**primary checkout** happens to be on. Adding a function fails loudly with an `ImportError`;
**modifying** one imports fine and silently runs the old behavior, so a change gets "verified"
against code nobody wrote. The loud case was observed and initially misdiagnosed as
plugin-redeploy lag (issue #104); the silent case is what this guard exists for.

Invoked as one line at each `PLUGIN_SCRIPTS=` site::

    python3 "${SCRIPTS}/plugin_guard.py" work_status || exit 1

**It exits non-zero rather than printing a warning.** A printed warning from inside a snippet is
unenforced — the caller runs the stale code anyway — which is a constraint restated at runtime
rather than enforced at runtime, the failure
`2026-08-11-pattern-an-unenforced-constraint-is-aspirational` names. The escape hatch that entry
prescribes is `MINERVA_SCRIPTS`, below.

What this guard deliberately does **not** cover: skill *prose*. The harness loads `SKILL.md`
through the same symlink, so a skill-text edit in a worktree is equally inactive — and a stale
load would omit this guard too. That half is not reachable from here.
"""
import filecmp
import os
import subprocess
import sys
from pathlib import Path

# Where a checkout keeps these scripts, relative to its own root.
_TREE_SCRIPTS = Path("plugins") / "minerva" / "scripts"


def working_tree_root():
    """The root of the tree the caller is standing in — the *worktree* when inside one.

    Deliberately `--show-toplevel`, not the `--git-common-dir` form that
    `2026-08-28-constraint-worktree-reaching-paths-anchor-to-the-primary-checkout` requires
    elsewhere. That entry governs paths that reach **across** worktrees (into
    `.minerva/worktrees/…`), where the primary checkout is the right anchor. Here the question is
    the opposite one — *which code am I editing right now* — and the answer is the current tree.
    Using the primary-checkout form here would compare the resolved copy against itself and never
    fire.

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


def divergence(module: str, resolved_dir: Path, tree_root):
    """`(resolved, local)` when the two copies of `module` differ; None when they agree.

    None — meaning "proceed" — is returned for every case that is not a genuine divergence:

    - **No working tree** (not a git repo): nothing to compare against.
    - **The tree has no `plugins/minerva/scripts/`**: this is every ordinary consumer project,
      where minerva is an installed copy and the cache-only resolution cannot skew against a
      worktree at all. The guard ships in shared skill prose to every install, so a false positive
      here would emit warnings about worktrees and symlinks at users who have neither.
    - **The tree has no copy of this module**: nothing to be stale against.
    - **The two paths are the same file**: running from the primary checkout itself.

    The comparison is on **file contents**, never realpaths. Inside a worktree the realpaths
    always differ, so a path comparison would hard-fail every self-development session even when
    the code is byte-identical — which is the common case and must stay silent.
    """
    if tree_root is None:
        return None
    local_dir = tree_root / _TREE_SCRIPTS
    if not local_dir.is_dir():
        return None
    local = local_dir / f"{module}.py"
    resolved = resolved_dir / f"{module}.py"
    if not local.is_file() or not resolved.is_file():
        return None
    if local.resolve() == resolved.resolve():
        return None
    if filecmp.cmp(str(local), str(resolved), shallow=False):
        return None
    return resolved, local


def main(argv):
    if len(argv) != 2:
        print("usage: plugin_guard.py <module-name>", file=sys.stderr)
        return 2
    module = argv[1]

    # An explicit choice is always honoured — the escape hatch at the call site. Someone who has
    # deliberately pointed at a scripts directory does not need to be told it is not the one the
    # working tree holds.
    if os.environ.get("MINERVA_SCRIPTS"):
        return 0

    found = divergence(module, Path(__file__).resolve().parent, working_tree_root())
    if found is None:
        return 0

    resolved, local = found
    print(
        f"minerva: refusing to run against a stale '{module}'.\n"
        f"  would import : {resolved}\n"
        f"  you are editing: {local}\n"
        f"These differ. Skill snippets resolve through ~/.claude/plugins/minerva, which on a\n"
        f"self-hosting checkout symlinks to the PRIMARY checkout — so this would execute that\n"
        f"checkout's branch, not your worktree's. Merge your change, or set MINERVA_SCRIPTS to\n"
        f"choose a directory deliberately (see issue #104).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
