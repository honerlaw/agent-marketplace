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

    [ -n "$PLUGIN_SCRIPTS" ] && { python3 "$PLUGIN_SCRIPTS/plugin_guard.py" || exit 1; }

**It compares the whole scripts directory, not one named module.** A per-module check was the
first design and it had two holes, both found by review: a site can invoke more than one script
(`cleanup/references/reconciliation.md` runs `knowledge_lint` *and* `synthesis_status`), and every
module imports siblings — `workstream_status` imports `work_status`, and most modules import
`knowledge_lint`/`knowledge_spans` — so naming one module leaves its transitive dependencies
unchecked. Comparing the directory makes both unrepresentable rather than patched, and removes the
argument that could name the wrong module.

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


def divergence(resolved_dir: Path, tree_root):
    """`(resolved_dir, local_dir)` when the two scripts directories differ; None when they agree.

    None — meaning "proceed" — is returned for every case that is not a genuine divergence:

    - **No working tree** (not a git repo): nothing to compare against.
    - **The tree has no `plugins/minerva/scripts/`**: this is every ordinary consumer project,
      where minerva is an installed copy and the cache-only resolution cannot skew against a
      worktree at all. The guard ships in shared skill prose to every install, so a false positive
      here would emit warnings about worktrees and symlinks at users who have neither.
    - **The two paths are the same directory**: running from the primary checkout itself.

    The comparison is over **every `*.py` in the directory**, by content. Scoping it to one named
    module left two holes: a site may invoke several scripts, and every module imports siblings,
    so a stale transitive dependency passed unnoticed. Directory scope closes both by construction.

    Content, never realpaths — inside a worktree the realpaths always differ, so a path comparison
    would hard-fail every self-development session even when the code is byte-identical.
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
    # `errors` are files present on one side only — a module added or removed on the branch, which
    # is a divergence exactly as much as an edited one.
    if mismatch or errors:
        return resolved_dir, local_dir
    return None


def main(argv):
    if len(argv) != 1:
        print("usage: plugin_guard.py   (no arguments; compares the whole scripts directory)",
              file=sys.stderr)
        return 2

    # An explicit choice is always honoured — the escape hatch at the call site. Someone who has
    # deliberately pointed at a scripts directory does not need to be told it is not the one the
    # working tree holds.
    if os.environ.get("MINERVA_SCRIPTS"):
        return 0

    found = divergence(Path(__file__).resolve().parent, working_tree_root())
    if found is None:
        return 0

    resolved, local = found
    print(
        f"minerva: refusing to run against a stale scripts directory.\n"
        f"  would import from: {resolved}\n"
        f"  you are editing  : {local}\n"
        f"These differ. Skill snippets resolve through ~/.claude/plugins/minerva, which on a\n"
        f"self-hosting checkout symlinks to the PRIMARY checkout — so this would execute that\n"
        f"checkout's branch, not your worktree's. Merge your change, or set MINERVA_SCRIPTS to\n"
        f"choose a directory deliberately (see issue #104).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
