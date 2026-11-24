# status — the three tables

Read this before rendering. It carries the table shapes, the column semantics, and the
**Next step** mapping that is the whole point of the skill. A status dump that reports state
without naming the action buries decided-to-wait work among decided-and-done; the **Next
step** column is what makes this a status *check* rather than a data dump.

## Table 1 — Active units

**Only units that are not finished.** A unit is finished when its gate is `released` or
`abandoned` **and** it has no worktree on disk. Everything else belongs here. Finished units
are counted in table 2, never listed.

| Unit | Stage | Gate | Phase | Branch | PR | Next step |
|---|---|---|---|---|---|---|
| `2026-08-27-deferral-cost-model` | in-progress | open | 1 of 2 | `…-phase-2` | #101 merged | `lorestrom:work` — phase 2 |
| `2026-08-28-status-skill` | promoted | open | — | `2026-08-28-status-skill` | — | `lorestrom:ship` |

- **Unit** — the `<date-slug>`. It is also the worktree directory name and the phase-1
  branch name, which is why one column serves all three.
- **Stage** — `in-progress` (gate open, not promoted), `promoted` (`unit-state`'s `promoted`),
  `released` or `abandoned` (the gate's state).
- **Gate** — the gate's own state from `get_gate`. When the unit doc's `minerva:state`
  disagrees, append `(doc says <value>)`: cleanup refreshes it, status does not.
- **Phase** — `merged + 1` of `total` from `phases` for a phased unit, `—` otherwise. Show the
  phase's `name` when the table has room.
- **Branch** — for a phased unit, `next_branch`, because that is the one a reader is about to
  check out. Never rebuild the name.
- **PR** — number and state from the step-3 join, or `—` when `gh` was unavailable.

## Table 2 — Rollup

| | |
|---|---|
| Units | 65 total · 2 open · 61 released · 2 abandoned (3 ids refused) |
| Worktrees on disk | 2 |
| Phased units incomplete | 1 |
| Checkout | `main` at `<sha>` (origin/main `<sha>` — **2 behind**) |
| Open followups | 2 (`priority: critical` 1, `priority: high` 1) |

- **open** counts gates in state `open` (and `releasing`, named when present).
- **ids refused** is `unit-ids`' count; omit the clause at zero.
- **Checkout** exists because phase merges are read from local refs: a not-yet-fetched
  checkout reports a merged phase as unmerged. Omit the "behind" clause when the two match.
- **Open followups** come from `gh issue list --label "minerva:followup" --state open
  --json number,title,labels`. Omit the row entirely when no tracker is reachable.

## Table 3 — Knowledge

When the project has no entries, render one line — *"no knowledge entries in Lorestrom for
this project"* — and no table.

| | |
|---|---|
| Entries | 82 (decision 27 · constraint 25 · pattern 24 · bug 5 · reference 1) |
| Themes | 14 · 2 entries unthemed |
| Pending | 3 entries, held by 2 open units |
| Incomplete imports | 1 — re-run `lorestrom:init` |
| Reference docs | 6 |

Omit any row at zero except Entries. Name the skill that closes each gap; do not run it.

## The Next step mapping

Evaluate **in order** and take the first match. The ordering is what keeps a phased unit
from falling into the cleanup arm.

| Condition | Next step |
|---|---|
| phased and not `complete` | `lorestrom:work` — phase `next_position` of `total` |
| gate `open`, every phase's PR `MERGED` | `lorestrom:cleanup` (releases the gate) |
| gate `released` or `abandoned`, worktree present | `lorestrom:cleanup` |
| `promoted`, no open PR | `lorestrom:ship` |
| `promoted`, PR open | wait for CI / merge — no action |
| a PR `CLOSED` unmerged, gate open | `lorestrom:cleanup <unit>` (it will propose abandoning) |
| gate `open`, not promoted | `lorestrom:review`, then `lorestrom:promote` |

**Why the phase arm comes first.** A phase-1-merged unit has a merged PR *and* a worktree on
disk, so the naive reading is "cleanup is overdue". It is not: teardown and the gate's release
both wait for the final phase. Recommending cleanup there would at best do nothing and at
worst invite a forced teardown — the one way this read-only skill can still cause damage,
through the action it names.

**When `gh` was unavailable**, the PR-dependent arms cannot fire. Fall back to the stage-only
arms and mark the PR column `—`. The result is coarser and never wrong.
