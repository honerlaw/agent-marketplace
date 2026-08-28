# status — the three tables

Read this before rendering. It carries the table shapes, the column semantics, and the
**Next step** mapping that is the whole point of the skill.

A status dump that reports state without naming the action is the shape
`2026-08-22-pattern-a-ledger-line-is-not-a-resolution` warns about — a record marking work
as handled without separating decided-and-done from decided-to-wait buries it. The
**Next step** column is what makes this a status *check* rather than a data dump.

## Table 1 — Active units

**Only units that are not finished.** A unit is finished when `stage` is `shipped` **and**
`worktree_present` is false **and** (unphased, or `progress.complete`). Everything else
belongs here. Finished units are counted in table 2, never listed: this project's own
corpus is 65 units, and a 65-row table is not a status check.

| Unit | Stage | Phase | Branch | PR | Next step |
|---|---|---|---|---|---|
| `2026-08-27-deferral-cost-model` | in-progress | 1 of 2 | `…-phase-2` | #101 merged | `minerva:work` — phase 2 |
| `2026-08-28-status-skill` | draft | — | `2026-08-28-status-skill` | — | `minerva:work` |

- **Unit** — the `<date-slug>`. It is also the worktree directory name and the phase-1
  branch name, which is why one column serves all three.
- **Phase** — `progress.merged + 1` of `progress.total` for a phased unit, `—` otherwise.
  Show the phase *name* (`phase_name()` on the title) when the table has room.
- **Branch** — for a phased unit, the branch of the *next* phase (`progress.next_branch`),
  because that is the one a reader is about to check out. Never rebuild the name.
- **PR** — number and state from the step-4 join, or `—` when `gh` was unavailable. An
  absent tracker renders as `—`; it never blocks the row.

## Table 2 — Rollup

One line per fact, so it stays readable in a terminal.

| | |
|---|---|
| Units | 65 total · 2 in flight · 63 shipped |
| Worktrees on disk | 2 |
| Phased units incomplete | 1 |
| Checkout | `main` at `b4c8b65` (origin/main `c58e319` — **2 behind**) |
| Open followups | 2 (`priority: medium` 1, `priority: low` 1) |

- **in flight** is `counts.in_flight` — the imported `work_status` predicate (`Status is
  Draft` **or** not promoted), deliberately wider than any single stage. Do not recompute
  it from `by_stage`.
- **Checkout** exists because the walk reads *files*, not refs: a not-yet-pulled primary
  checkout reports a merged unit as unshipped. Printing HEAD beside `origin/<default>`
  makes a stale tree visible instead of silently wrong. Omit the "behind" clause when the
  two match.
- **Open followups** come from `gh issue list --label "minerva:followup" --state open
  --json number,title,labels`. Omit the row entirely when no tracker is reachable.

## Table 3 — Knowledge health

Straight from `knowledge`. When `knowledge.exists` is false, render one line — *"no
`.minerva/knowledge/` in this checkout"* — and no table: an absent corpus and a clean one
are different states, and only one is good news.

| | |
|---|---|
| Entries | 82 (decision 27 · constraint 25 · pattern 24 · bug 5 · reference 1) |
| Lint | 0 errors · 0 warnings — `minerva:lint` |
| Overview | present · 2 entries unsynthesized — `minerva:synthesize` |
| Link rot | 0 |

Name the skill that closes each gap; do not run it, and do not reproduce its findings.

## The Next step mapping

Evaluate **in order** and take the first match. The ordering is what keeps a phased unit
from falling into the cleanup arm.

| Condition | Next step |
|---|---|
| `progress.phased` and not `progress.complete` | `minerva:work` — phase `next_position` of `total` |
| PR `MERGED` and `worktree_present` | `minerva:cleanup` |
| `stage` is `promoted`, no open PR | `minerva:ship` |
| `stage` is `promoted`, PR open | wait for CI / merge — no action |
| `stage` is `in-progress` | `minerva:review`, then `minerva:promote` |
| `stage` is `draft` | `minerva:work` |
| `stage` is `shipped`, `worktree_present` | `minerva:cleanup` |

**Why the phase arm comes first.** A phase-1-merged unit has a merged PR *and* a worktree
on disk, so the naive reading is "cleanup is overdue". It is not: `minerva:cleanup`'s
"Teardown waits" defers teardown until the final phase, because removing the worktree
between phases destroys the workspace the remaining phases are cut in. `worktree_present`
on an incomplete phased unit is **expected state**, not a backlog item. Recommending
cleanup there would destroy live work — the one way this read-only skill can still cause
damage, through the action it names.

**When `gh` was unavailable**, the two PR-dependent arms cannot fire. Fall back to the
stage-only arms and mark the PR column `—`. The result is coarser and never wrong: a
`promoted` unit reads as "needs shipping", which is true whether or not a PR is already
open — and `minerva:ship` is idempotent about an existing one.
