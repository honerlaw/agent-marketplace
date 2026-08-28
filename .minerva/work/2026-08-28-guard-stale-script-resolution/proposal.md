# Proposal: guard-stale-script-resolution

**Date**: 2026-08-28
**Status**: Draft
**Closes**: #104

## Goal

Stop a minerva skill snippet from silently executing the primary checkout's code when the work
being verified lives in a linked worktree. Make the divergence a hard, non-ignorable stop with a
deliberate override, single-sourced so twelve call sites cannot drift.

## Why

`~/.claude/plugins/minerva` is a **symlink** to `<repo>/plugins/minerva` — the primary checkout.
Every snippet resolves its Python through it:

```bash
PLUGIN_SCRIPTS=$(find -L "${HOME}/.claude/plugins/minerva" "${HOME}/.claude/plugins/cache/agent-marketplace/minerva" -maxdepth 2 -type d -name "scripts" 2>/dev/null | head -1)
```

minerva develops itself in linked worktrees under `.minerva/worktrees/<date-slug>/`, each holding
its own `plugins/minerva/scripts/` at a realpath that resolution never reaches. So a snippet run
against a work-unit branch executes **whatever branch the primary checkout is on**.

- **Loud:** adding a function gives `ImportError: cannot import name 'read_phases'`. Observed in
  `2026-08-27-deferral-cost-model` — and *misdiagnosed there* as plugin-redeploy lag, which is why
  #104 needed correcting before this unit could be scoped.
- **Silent, and the real target:** *modifying* a function imports fine and runs the old behavior.
  You verify a change against code you did not write. Nothing surfaces it.

The skill-text half of the same symlink is out of reach — the harness picks what prose to load, and
a stale load would omit any detection we add. Demonstrated live on 2026-08-28: a concurrent
session's worktree differed from the primary checkout in seven skill files, none active in that
session. This unit does not pretend to fix that half.

## Approach

**A single-sourced guard, invoked in one line at each site.**

1. **`scripts/plugin_guard.py`** — given a module name, compares the resolved scripts directory's
   copy against the current working tree's `plugins/minerva/scripts/<module>.py`, and exits
   non-zero when they differ.
   - **Compares file bytes, not realpaths.** Realpaths always differ inside a worktree, so a
     realpath check would hard-fail every self-development session even when the code is identical.
   - **Silent no-op when the working tree has no `plugins/minerva/scripts/`** — which is every
     consumer project, where the cache-only resolution cannot skew. The guard ships in shared skill
     prose to every install, so a false positive there would emit warnings about worktrees and
     symlinks to users who have neither.
   - **`MINERVA_SCRIPTS` override** forces a directory explicitly and skips the comparison — the
     escape hatch at the call site that
     `2026-08-11-pattern-an-unenforced-constraint-is-aspirational` prescribes.
2. **One line at each of the 12 sites**, immediately after the `PLUGIN_SCRIPTS=$(find …)`
   assignment: `python3 "${SCRIPTS}/plugin_guard.py" <module> || exit 1`.
   - **Bash level, never inside the `python3 -c` payload.** `tests/test_skill_snippets.py:163-165`
     byte-substitutes `'${PLUGIN_SCRIPTS:-$ROOT/scripts}'` inside that payload and then asserts
     `"$ROOT" not in prog`; adding `$ROOT`-bearing text there trips it.
   - The 12 sites are not uniform — seven feed `sys.path.insert` inside `python3 -c`, two invoke
     `python3 "$SCRIPTS/x.py"` directly, one binds `SCRIPTS=` once and reuses it. A bash-level line
     after the assignment is the one shape that fits all three.
3. **A structural contract test** pinning the guard at every registered site, in the
   registered-sites style `tests/test_skill_dispatch.py` already uses, so a *new* site is a
   deliberate registration rather than a silent omission.

**Rejected — worktree-first resolution.** Preferring the working tree's copy would silently change
which code runs, and because prose still comes from the primary checkout it would run new code
under old instructions.

**Rejected — a printed warning.** A `print` from a snippet is unenforced; the caller runs the stale
code anyway. That is a constraint restated at runtime rather than enforced at runtime — the exact
failure `2026-08-11-pattern-an-unenforced-constraint-is-aspirational` names, and the reason a
warning-only design was revised out of this proposal.

**Rejected — repointing the symlink at the active worktree.** This would close both halves, so it
is rejected on cost, not impossibility: the symlink is global per-user while minerva supports
concurrent worktrees, so repointing for one session corrupts a sibling's. Two such sessions were
live when this was diagnosed.

## Success criteria

- `scripts/plugin_guard.py` exists and exits non-zero when the resolved copy of a named module
  differs from the current working tree's copy; zero when they match.
- It is a **silent no-op** when the working tree has no `plugins/minerva/scripts/` — asserted by a
  test that simulates a consumer project.
- `MINERVA_SCRIPTS` skips the comparison and is honoured as the resolved directory.
- All **12** `PLUGIN_SCRIPTS=$(find …)` sites across 10 files carry the guard line, at bash level;
  a structural test enumerates the sites and fails if one lacks it.
- The guard line appears **outside** every `python3 -c` payload, and `tests/test_skill_snippets.py`
  still passes unchanged.
- A new knowledge entry states the hazard and **explicitly delimits**
  `2026-08-28-constraint-worktree-reaching-paths-anchor-to-the-primary-checkout`: anchoring to the
  primary checkout is right for paths that reach *across* worktrees, and wrong for *the code you
  are editing*. Without that boundary the two entries read as contradictory.
- Every `SKILL.md` stays at or under 9216 bytes (`tests/test_skill_budget.py`) — `using-minerva`
  has 18 bytes of headroom per #107, and four of the twelve sites are in `SKILL.md` files.
- The full suite passes.

## Open Questions

None. Both reviewer gates (scope, approach) returned `revise`; every load-bearing point is folded
into the Approach and Success criteria above.
