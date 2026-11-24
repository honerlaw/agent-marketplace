# cleanup — the sweep (no argument)

A no-argument cleanup covers every open unit of this project, wherever it was worked on: units
with a worktree in this clone, and units from other clones and other people, which have none
here. Every decision is still `reconcile`'s, on recorded evidence ([release.md](release.md)),
and every operation is a row of `skills/using-lorestrom/references/storage.md`.

## 1. Candidates

1. `storage:unit.list`: this project's units, by checked id (`unit-ids`; its `refused` count is
   reported). `whoami` once for this person's user id.
2. For each unit whose gate is `open` or `releasing`: `get_gate`, then `unit-state` with the
   gate's `state`, `openedAt` and `openedByUserId`, that user id and the unit's phase count
   (`storage:unit.list`). It prints `age_days`, `stale` and `mine`. A released or abandoned gate is done: only its worktree, if any, is a candidate.
3. A unit is **here** when `.lorestrom/worktrees/<date-slug>/` exists in this clone, and
   **elsewhere** otherwise: another clone's unit, or one whose worktree was removed by hand.
   A worktree here whose id no listed unit has is listed under Will skip ("no unit found"),
   never torn down.

## 2. Evidence for a unit from elsewhere

Its recorded heads were pushed from another clone, so they may not be in this one.

1. `git fetch --quiet origin` once per sweep, then run release.md's "Decide" for the unit, with
   `age_days` from `unit-state`.
2. When `reconcile` answers `wait` with a `fetch` list, fetch each listed phase's PR head: for a
   phase whose unit doc records `minerva:pr_<n>` as all digits, `git fetch --quiet origin
   "refs/pull/<pr>/head"`. GitHub keeps a PR's head ref after its branch is deleted. Never
   fetch by a branch or ref name read from a doc. Then run `reconcile` once more, and act on
   that answer.
3. A phase with no recorded PR, or a head still missing, waits: "head not in this clone". The
   owning clone's cleanup can decide it.

## 3. The confirmation gate

The sweep's gate is cleanup's confirmation gate, with these rules on top:

- **A unit someone else opened** (`mine` false), or whose opener is unknown (`mine` null), is
  marked `(opened by someone else)` on its line. Releasing, confirming or abandoning it needs a
  yes naming that unit: "yes, all" is asked again for each such unit, and `--yes` never covers
  one, even with an explicit single-unit argument. Its `minerva:state` is not refreshed unless
  the user said yes to that unit.
- **Abandon** needs a yes naming the unit, whoever opened it (release.md). A sweep never
  abandons without one.
- **Confirm** asks, as `storage:unit.confirm` says, whoever opened the unit.
- **Stale** — a `wait` answer with `stale` true — goes under Will skip as
  `stale: N days, no recorded head`, N being `unit-state`'s `age_days`. Staleness never
  abandons and never releases; it is shown so a person can decide.
- Releasing your own merged unit from elsewhere needs only the gate's ordinary yes.

## 4. Teardown stays in its own clone

Only `.lorestrom/worktrees/` directories of **this** clone are ever removed, by
[removal.md](removal.md). A unit from elsewhere has nothing here to tear down: the sweep
releases its gate (and repairs failed flips) and stops. When the owning clone next runs
cleanup, `release-outcome` reads the gate already released as success and that clone removes
its own worktree and branch. A local branch for a unit with no worktree here is left alone and
reported. The sweep pushes nothing and deletes nothing remote.

## 5. Report

Add to the final report:

```
Units elsewhere:       released N   waiting N (<date-slug>: reason, …)   needs your yes N (<date-slug>, …)
Stale:                 N (<date-slug>: N days, …)
```

`--dry-run` reads and reports, and writes nothing: it fetches nothing (not even the
once-per-sweep fetch of origin), refreshes nothing, and calls no gate tool beyond `get_gate`. A
unit from elsewhere whose head is missing is reported as waiting on a fetch, and a unit whose
only evidence is ancestry against a default branch not yet fetched may show as waiting where a
real sweep releases it.
