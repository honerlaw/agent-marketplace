# cleanup — phased work units

A unit whose `proposal.md` declares a `## Phases` section ships **one PR per phase** while
keeping a single record. That splits cleanup's two jobs apart, because they no longer happen at
the same moment.

**Read this before tearing down any worktree.** A unit with no `## Phases` section is unphased —
the normal case — and nothing here applies to it.

Background, branch topology and the soft ceiling live in
`plugins/minerva/skills/propose/references/phasing.md`.

## The split

| Job | When it runs on a phased unit |
|---|---|
| Knowledge reconciliation | **Every invocation**, exactly as today — ungated |
| Worktree + branch teardown | **Only once the final phase has merged** |

### Reconciliation is never gated on phase completion

`minerva:promote`'s Mode B lands knowledge entries in the PR of whichever phase discovered them.
An entry that merged with phase 1 must be catalogued when phase 1 merges — not held until the
last phase, which may be days away or may never come.

Deferring it re-creates the exact failure
`2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption` documents: entries sitting
on the default branch, present but uncatalogued and therefore invisible to a reader, while the
run that skipped them reports itself successful. That happened six times in two days on this
project, and every one was found by accident.

### Teardown waits

Removing the worktree between phases destroys the workspace the remaining phases are cut in.

## Deciding whether a phased unit is finished

A merged phase-1 branch means *that phase* shipped, not that the unit is done. Ask the module
that owns the topology — never infer it from the branch name:

```bash
# The PRIMARY checkout, resolvable from any CWD. `--show-toplevel` returns the LINKED
# worktree when invoked inside one, and these paths reach *into* .minerva/worktrees/.
ROOT="$(cd "$(dirname "$(git rev-parse --git-common-dir)")" && pwd)"
PLUGIN_SCRIPTS=$(find -L "${HOME}/.claude/plugins/minerva" "${HOME}/.claude/plugins/cache/agent-marketplace/minerva" -maxdepth 2 -type d -name "scripts" 2>/dev/null | head -1)
[ -n "$PLUGIN_SCRIPTS" ] && { python3 "$PLUGIN_SCRIPTS/plugin_guard.py" work_status || exit 1; }
python3 -c "
import subprocess, sys; sys.path.insert(0, '${PLUGIN_SCRIPTS:-$ROOT/scripts}')
from work_status import read_phases, phase_progress
merged = subprocess.run(['git','branch','--merged','<default>','--format=%(refname:short)'],
                        capture_output=True, text=True).stdout.split()
proposal = '$ROOT/.minerva/worktrees/<date-slug>/.minerva/work/<date-slug>/proposal.md'
print(phase_progress(read_phases(open(proposal).read()), merged, '<date-slug>'))
"
```

**If this raises `ImportError: cannot import name 'read_phases'`,** the resolved scripts directory is a *deployed plugin copy* that predates these functions — plugin-cache-first resolution is the documented rule, so the fix is to update the installed minerva plugin, not to edit the path. Re-running against `$ROOT/scripts` confirms the diagnosis.

The scripts path resolves plugin-cache-first and falls back to `$ROOT/scripts`, per
`2026-06-03-constraint-skill-wraps-script-via-importable-api` — a bare
`sys.path.insert(0, 'scripts')` raises `ModuleNotFoundError` from any subdirectory. Cleanup
always runs from the parent repo (it removes worktrees, so it must never be inside one), which
is why the proposal path is anchored at `$ROOT` and reaches *into* the worktree.

- **`complete: False`** → skip teardown. Report the unit as `phase N of M — teardown deferred`.
- **`complete: True`** → tear down, and prune the unit's merged phase branches too (below).

Fetch the default branch first. A stale local ref reports a merged phase as unmerged, which
defers teardown forever on a unit that is actually finished.

## Pruning phase branches

The main Removal step deletes `<date-slug>`. For a completed phased unit, delete each
`<date-slug>-phase-N` the same way: `git branch -d`, with the identical `-D` fallback and the
identical precondition — that phase's merged-PR check passed.

Resolve every name through `phase_branch()` in `scripts/work_status.py`. Do not rebuild the
string: two derivations plus a comment asking them to agree is the shape
`2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant` is about.

## Why this step has to exist at all

Merge detection is exact-match on `<date-slug>` — both the `gh pr list --head` query and the
`git branch --merged | grep "^[* ] <date-slug>$"` fallback. Neither can ever match a
`-phase-N` branch.

That makes the existing logic **safe by accident**: it will not tear down a live phased unit,
because it cannot see the branch that would tell it to. But the same blindness means nothing
would ever prune those branches, and they would accumulate in every repo that uses phasing.
Accidental safety with a permanent leak attached is not a design — this file is what makes both
halves deliberate.
