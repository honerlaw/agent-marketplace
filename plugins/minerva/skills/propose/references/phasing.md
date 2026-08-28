# Plan-level phasing — one unit, N PRs

Work that is too big for one pull request splits its **plan**, not its **work unit**.

One unit. One `proposal.md`, one `scratchpad.md`, one worktree, one `minerva:promote`, one
knowledge pass — shipping as an ordered series of pull requests, one per phase.

**Read this file before declaring `## Phases` on a proposal, and before shipping or cleaning
up a unit that declares them.**

## Why this exists

minerva's previous answer to "too big" was to decompose into N separate work units and abort
the run: *"scope check resolved to decomposition — re-run with one sub-unit at a time."* That
multiplies every per-unit cost by N — propose, worktree, review, promote, knowledge
reconciliation, ship, cleanup, and a human gate at each transition — and each new unit
re-derives the project context the previous one just built.

The judgment was also one-sided by construction: the prose stated a cost of **not** splitting
("do not produce a 500-line proposal") and stated no cost of splitting at all. A model asked to
weigh a stated cost against an unstated one splits every time. In one corpus this turned single
intents into as many as twenty pieces of work.

Phasing keeps the reviewable-increment benefit and pays the ceremony once.

## When to phase, and how much

- **Phase** when the work is one coherent intent whose diff is too large to review in one PR.
- **Decompose into separate units** only for **genuinely independent subsystems** — work that
  would not share a proposal, a reviewer, or a record.
- **Do neither** when the work fits one PR. Most work fits one PR. An unphased unit is the
  normal case and nothing in this file applies to it.

**Soft ceiling: about three phases.** This matches `minerva:propose`'s own long-standing
calibration for decomposition ("work that should be three separate units"). More than three is
allowed but must be **argued in the proposal** — name why the work does not fit in three.
More than about five is evidence the scope itself is wrong, not evidence of five phases; go
back and ask what the smallest thing actually worth shipping is.

Phasing makes fragmentation cheap, and cheap fragmentation is the failure this whole mechanism
exists to prevent. A unit that declares eight phases has reproduced the disease under a new
name.

## Declaring phases

An ordered `## Phases` section in `proposal.md`, after `## Success criteria`:

```markdown
## Phases

1. **<name>** — what ships in this PR, and its own success criteria.
2. **<name>** — what ships in this PR, and its own success criteria.
```

Each phase must be **independently shippable**: its PR merges to the default branch on its own,
leaving the repository working. A phase that only makes sense once a later phase lands is not a
phase — it is the first half of one.

**A unit with no `## Phases` section is unphased**, and every consumer behaves exactly as it did
before this mechanism existed. That inertness is what made phasing safe to add to `ship`,
`cleanup`, `work_status` and four orchestrators at once — the same argument
`2026-08-09-decision-reference-is-a-fifth-entry-type` made for appending an empty index section.

## Branch topology — sequential off the default branch

| Phase | Branch |
|---|---|
| 1 | `<date-slug>` — the bare slug, exactly as an unphased unit |
| 2 | `<date-slug>-phase-2` |
| N | `<date-slug>-phase-N` |

Phase N's branch is cut from the **default branch**, and only **after phase N−1 has merged**.
Every phase PR is therefore an ordinary PR against the default branch: `minerva:ship`'s
one-branch-one-PR logic and its idempotency guarantee run unchanged, N times.

**Phase 1 keeps the bare slug deliberately.** It leaves the worktree directory and the phase-1
branch matched, so all six `Target resolution` blocks, `minerva:propose`'s duplicate-slug check,
and `minerva:cleanup`'s merge detection keep working untouched on a phased unit's first phase.
Only phases 2+ introduce a name those consumers have not seen.

Never rebuild these names by hand. Resolve them through `phase_branch()` in
`scripts/work_status.py` — two derivations plus a comment asking them to agree is exactly the
shape `2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant` is about.

## The record propagates by ordinary merge

`proposal.md` and `scratchpad.md` are committed into each phase's PR, so they land on the
default branch with phase 1. Phase N+1, cut from that branch, inherits them automatically.

Nothing carries the record forward; git does. To start phase N in the unit's existing worktree,
fetch and cut the new branch from the updated default branch — the docs arrive with it.

## Progress is derived, never written

Which phases are done is read off **which phase branches have merged**, via `phase_progress()`
in `scripts/work_status.py`. There is no checkbox in the proposal and no progress marker in the
scratchpad.

This is not a stylistic preference. The one hand-maintained lifecycle marker minerva already had
— promote's — acquired eight spellings across one corpus and misread 16 of 51 units. A second
hand-maintained progress marker would be the same bug with a new name
(`2026-08-10-pattern-presence-assertions-rot-into-green-lies`).

`phase_progress()` takes the merged-branch set as an **argument** rather than shelling out to
git, so `work_status.py` stays a pure reader of declarations and its tests need no repo. The
caller — `minerva:ship`, `minerva:cleanup` — already holds the `git branch --merged` /
`gh pr list` result.

## Promote: Mode B during, Mode A at the end

The full `minerva:promote` Mode A pass — knowledge entries, proposal rewrite, scratchpad archive,
the `**Closes**` field — runs **once**, after the final phase. That is the whole point: the
ceremony is paid once.

But **do not let durable knowledge wait for it.** Use `minerva:promote`'s existing **Mode B**
(single-item mid-work promotion) as findings arrive, so each phase's PR carries the knowledge
that phase produced. Without this, a unit abandoned after phase 1 strands everything it learned.

## Reporting: never let a pending phase be silent

Every phase's ship report **names the phases still outstanding**. A unit that stalls after phase
1 must be visible as a unit that stalled, not as a unit that finished.

This is the direct application of
`2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption`: deferred work with no
trigger, reported by a step that omits it, is undetectable. Both halves have to be closed — the
trigger is the next phase, and the report is what makes its absence noticeable.

## The orchestrator loop

`minerva:propose-ship`, `-quick`, `-balanced` and `-auto` all end with: ship → poll the PR → on
`MERGED`, run `minerva:cleanup` → report and exit. **On a phased unit that last step is wrong**,
and wrong in the silent direction: phase 1 merges, cleanup correctly defers teardown, the run
reports success, and phases 2..N never ship. The unit stalls at a report that says it finished.

So every orchestrator's cleanup gate gains one branch, before it reports:

> After `minerva:cleanup` returns on a `MERGED` phase, re-derive `phase_progress()`. If
> `complete` is false, **loop back to the ship phase** for `next_branch` — cut it from the
> freshly fetched default branch and ship it. Only when `complete` is true does the run report
> and exit.

Two rules ride with the loop:

- **Promote Mode A runs before the FINAL phase's ship**, not before phase 1's. Its output — the
  knowledge entries, the `## Approach` rewrite, the `**Closes**` field, the archived scratchpad —
  belongs in the last PR, because until then the unit is not finished. Use **Mode B** during the
  earlier phases so each phase's PR still carries what it learned.
- **The review phase re-runs per phase**, against that phase's own diff. A phase is its own
  reviewable increment; reviewing phase 1's diff tells you nothing about phase 3's.

**Every phase transition is a place a run can die**, so the report at each one names the
outstanding phases (see [Reporting](#reporting-never-let-a-pending-phase-be-silent) above). A
loop whose exit is silent is indistinguishable from a loop that completed.

## Cleanup: reconcile every phase, tear down once

`minerva:cleanup` does two unrelated jobs, and phasing separates them:

- **Knowledge reconciliation** runs on every invocation, exactly as it does now. A Mode B entry
  that landed in phase 1's PR must be catalogued then, not after the final phase — otherwise it
  sits on the default branch present but uncatalogued, which is the precise stranding failure
  `2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption` describes.
- **Worktree teardown is deferred** while any declared phase is unmerged, and the unit's merged
  phase branches are pruned only once the final phase lands.

Cleanup's merge detection is exact-match on `<date-slug>`, so without this it would never see a
`-phase-N` branch at all: safe by accident, but the branches would accumulate forever.
