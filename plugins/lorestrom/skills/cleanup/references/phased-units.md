# cleanup — phased work units

A unit whose proposal declares a `## Phases` section ships **one PR per phase** while
keeping a single record and a single Lorestrom gate. A merged phase therefore does not mean the unit is finished, and
cleanup's one job — worktree and branch teardown — must wait for the final phase.

**Read this before tearing down any worktree.** A unit with no `## Phases` section is unphased —
the normal case — and nothing here applies to it.

Background, branch topology and the soft ceiling live in
`skills/propose/references/phasing.md`.

Knowledge waits for the final phase: an entry `lorestrom:promote`'s Mode B writes is pending lore
until the unit's gate is released, and `reconcile` releases only when every phase has merged.
Between phases cleanup reports the gate as waiting and changes nothing.

## Teardown waits

Removing the worktree between phases destroys the workspace the remaining phases are cut in.

## Deciding whether a phased unit is finished

A merged phase-1 branch means *that phase* shipped, not that the unit is done. Ask the helper —
never infer it from the branch name: fetch the default branch, then run `phases --unit
<date-slug>` on `{"proposal": <the proposal record>, "mergedPrs": [...], "heads": {...},
"base": <sha>}` (`storage:unit.read`), with the head names `gh pr list --state merged --json
headRefName` returns for the unit's phase branches and the unit doc's recorded heads and base.

- **`complete: False`** → skip teardown. Report the unit as `phase N of M — teardown deferred`.
- **`complete: True`** → tear down, and prune the unit's merged phase branches too (below).

Fetch the default branch first. A stale local ref reports a merged phase as unmerged, which
defers teardown forever on a unit that is actually finished.

## Pruning phase branches

The main Removal step deletes `<date-slug>`. For a completed phased unit, delete each
`<date-slug>-phase-N` the same way: `git branch -d`, with the identical `-D` fallback and the
identical precondition — that phase's merged-PR check passed.

Take every name from the `branch` of each phase `phases` printed. Do not rebuild the string: two
derivations plus a comment asking them to agree drift apart.

## Why this step has to exist at all

Merge detection is exact-match on `<date-slug>` — both the `gh pr list --head` query and the
`git branch --merged | grep -Fqx -- "<date-slug>"` fallback. Neither can ever match a
`-phase-N` branch.

That makes the existing logic **safe by accident**: it will not tear down a live phased unit,
because it cannot see the branch that would tell it to. But the same blindness means nothing
would ever prune those branches, and they would accumulate in every repo that uses phasing.
Accidental safety with a permanent leak attached is not a design — this file is what makes both
halves deliberate.
