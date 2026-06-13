# Proposal: fix-synthesize-worktree-root

**Date**: 2026-06-13
**Status**: Shipped (2026-06-13)

## Goal

Fix `minerva:synthesize` (SKILL.md Step 1) so it correctly locates `scripts/synthesis_status.py` when invoked from inside a git worktree, preventing Claude Sonnet from getting stuck in Phase 4.5 of `minerva:propose-ship-auto`.

## Why

The Step 1 bash command in `synthesize/SKILL.md` uses `git rev-parse --show-toplevel` to build the path to `scripts/`. In a git worktree, `--show-toplevel` returns the *worktree root* (e.g., `.minerva/worktrees/170-rename-ats-score-label-optimized`), not the main repo root. Since `scripts/` only exists in the main repo, the Python import fails with `ModuleNotFoundError: No module named 'synthesis_status'`. When this error surfaces in Phase 4.5 of `propose-ship-auto`, Claude Sonnet sometimes gets stuck retrying or spinning instead of gracefully no-oping.

## Approach

Two-part fix (Option C — fix root cause and add resilience):

1. **Fix the bash command** to use `git rev-parse --git-common-dir` instead of `--show-toplevel`. In any worktree, `--git-common-dir` returns the path to the shared `.git` directory (the main repo's `.git`), so `dirname` of that path is always the main repo root — works for both the main working tree and any worktree.

   New command:
   ```bash
   ROOT="$(dirname "$(git rev-parse --git-common-dir)")"; python3 -c "import sys, json; sys.path.insert(0, '$ROOT/scripts'); from synthesis_status import synthesis_status; print(json.dumps(synthesis_status('$ROOT/.minerva/knowledge'), indent=2))"
   ```

   Note: when run from the main working tree, `--git-common-dir` returns `.git` (relative), so `dirname ".git"` = `.` and `$(dirname ".")` evaluated in a subshell after `cd` still resolves to the current directory. To handle the relative case robustly, wrap it: `ROOT="$(cd "$(dirname "$(git rev-parse --git-common-dir)")" && pwd)"`.

2. **Add a graceful fallback paragraph** in Step 1 of the skill: if the Python command exits non-zero for any reason (e.g., the script is missing, Python is unavailable), the skill should proceed as if the signal returned `{"unsynthesized": [], "link_rot": []}` — a no-op signal — rather than retrying or stalling.

## Success criteria

- The bash command in `synthesize/SKILL.md` Step 1 uses `--git-common-dir` (or equivalent) to locate the main repo root.
- A resilience note in Step 1 instructs the model to no-op on bash failure.
- The command produces correct output when run from the main working tree (regression-free).
- The command produces correct output when run from a minerva worktree (the primary fix).

## Open Questions

None.
