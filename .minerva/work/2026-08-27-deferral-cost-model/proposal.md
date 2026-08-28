# Proposal: deferral-cost-model

**Date**: 2026-08-27
**Status**: Draft

## Goal

Replace minerva's cost-free deferral with an explicit cost model, delivered in two phases:
**plan-level phasing**, so oversized work stops fragmenting into N separate work units, and a
**correctness-only bar on the issue tracker**, with below-bar observations routed to the knowledge
corpus instead of a backlog.

## Why

Four independent places manufacture deferred work, and every one of them treats *recording* as free
and *dropping* as lossy:

| Source | Mechanism |
|---|---|
| `minerva:review` triage | `SUGGEST` writes a scratchpad note — the low-friction middle option between FIX and IGNORE |
| `minerva:promote` step 5 | Any forward-looking scratchpad line becomes a TODO; **Keep** files a GitHub issue |
| Scope check (all four orchestrators) | "decompose" → *abort the run, re-run with one sub-unit at a time* |
| Work-phase scope-fit escape | change proves large → escalate |

`references/github-issues.md` states the bias outright — "**Never lose a kept item**" — and no skill
anywhere states a budget, a bar, or a cost for filing. The judgment is one-sided by construction.

The evidence in this repo:

- ~150 bullets across 24 `followups.md` files.
- 18 `minerva:followup` issues, of which **15 were filed in a single backfill batch** on 2026-08-22.
- An entire skill, `minerva:backfill-followups`, written for no purpose but to excavate that backlog
  after it rotted.
- The `low` priority tier is self-refuting: it is defined as "*It does not matter whether we do it*",
  and an item at that level still gets a labelled GitHub issue with a back-link.

Decomposition is judged the same one-sided way. `propose/SKILL.md:32` states a cost of **not**
splitting ("do not produce a 500-line proposal") and states no cost of splitting at all; a second
trigger at `propose/references/on-approval.md:110` can re-decompose a unit that already passed the
gate. When either fires, all four orchestrators abort the run and hand back N sub-units, each
requiring its own propose / work / review / promote / ship / cleanup cycle.

The four costs this imposes — a backlog nobody reads, triage attention spent mid-run, calendar time
lost to fan-out, and work that never reaches a clean "done" — were all confirmed as real by the user
during exploration.

## Approach

### Phase 1 — plan-level phasing

The thing that splits when work is too big is the **plan**, not the **unit**. One work unit, one
proposal, one worktree, one scratchpad, one promote, one knowledge pass — shipping as an ordered
series of PRs.

- **`## Phases` in the proposal template** (`propose/references/on-approval.md`): an ordered list of
  shippable increments, each with its own success criteria. **Soft ceiling of ~3**, matching
  `propose/SKILL.md`'s own existing calibration; more than three must be argued in the proposal, and
  more than ~5 is treated as evidence the scope is wrong rather than evidence of five phases.
- **Branch topology — sequential off the default branch.** Phase 1 keeps the bare `<date-slug>`
  branch exactly as today; phases N≥2 use `<date-slug>-phase-N`, cut from the default branch only
  after phase N−1 merges. Every phase PR is therefore an ordinary PR against the default branch, so
  `minerva:ship`'s PR logic runs unchanged — it just runs N times.
- **A unit with no `## Phases` section is unphased and behaves exactly as today.** The mechanism is
  inert for every existing unit and every existing consumer of the branch-name convention — the same
  safety property that made `## References` safe to add to every corpus at once
  (`2026-08-09-decision-reference-is-a-fifth-entry-type`).
- **The single record propagates by ordinary merge.** `proposal.md` and `scratchpad.md` ride each
  phase's PR onto the default branch, so phase N+1 — cut from that branch — inherits them. No
  carrying machinery is needed.
- **Phase progress is derived, never written.** `scripts/work_status.py` gains a phase predicate that
  reads completion from merged `<date-slug>-phase-N` branches. No checkbox, no marker: the promote
  marker acquired eight spellings across this corpus and misread 16 of 51 units
  (`2026-08-11-pattern-the-enumeration-is-what-fails`,
  `2026-08-10-pattern-presence-assertions-rot-into-green-lies`).
- **`minerva:ship`** loops its existing one-branch-one-PR logic per phase, and each phase's report
  **names the phases still outstanding** — a report that omits deferred work lies by omission
  (`2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption`).
- **`minerva:cleanup` becomes phase-aware.** It does two unrelated jobs, and phasing splits them:
  knowledge reconciliation runs on every invocation as it does now, while worktree teardown is
  deferred until the final phase merges, at which point the unit's merged phase branches are pruned
  too. Without this, phase branches accumulate forever — cleanup's exact-match merge detection
  (`gh pr list --head <date-slug>`, `git branch --merged | grep "^[* ] <date-slug>$"`) can never see
  them.
- **The duplicate-slug glob widens.** `on-approval.md` refuses on `git branch --list "*-<slug>"`,
  which cannot match `<date-slug>-phase-N`; a future propose for the same slug would miss in-flight
  phase work.
- **Both decomposition triggers and all four orchestrator scope-check steps state the cost of
  splitting**, and name plan-level phasing as the default response to "too big". Decomposition into
  separate work units survives only for genuinely independent subsystems.

### Phase 2 — the deferral bar

Ships *through* the phase-1 mechanism, which is what proves that mechanism works end-to-end.

- **A single-sourced policy file**, `promote/references/deferral-bar.md`, is the only statement of the
  bar and its outlets. Every consumer — `review`'s triage, `promote`'s step 5 and `github-issues.md`,
  and the four orchestrator `phases.md` files — **points at it** by qualified cross-skill path rather
  than restating it. This is only representable because of
  `2026-08-22-decision-qualified-cross-skill-reference-pointers`; the alternative reproduces the
  six-copy `## Target resolution` hazard knowing both halves of that lesson
  (`2026-08-22-pattern-repeated-blocks-may-be-deliberate-divergence-not-duplication`).
- **The bar is a mechanical test, not a severity judgment.** An item may become an issue only if a
  **concrete failure scenario** can be written for it — specific inputs or state producing a wrong
  output or a crash. If one cannot be written, it is not a defect. This mirrors the `ReportFindings`
  tool's own required `failure_scenario` field, and it refuses the entire "this could be cleaner"
  class by construction. Stating what *qualifies* rather than what is *excluded* is the same
  inversion as `2026-08-22-pattern-a-denylist-safety-guard-fails-open`: an allowlist's refusals are
  complete, a denylist's gaps are invisible.
- **Three outlets, and only three:**
  - **Qualifies** → a GitHub issue whose body carries a required `**Failure scenario**:` line.
  - **Below the bar** → a `.minerva/knowledge/` entry of type `reference` — a standing fact about the
    system — or discard. `minerva:review` already reads the corpus on every future unit, so the
    observation re-surfaces by locality when relevant code is next touched, and it carries no
    burn-down obligation to rot. The `reference` type already has precedent for exactly this: one of
    the four entries that justified adding the type was "a curated followups backlog"
    (`2026-08-09-decision-reference-is-a-fifth-entry-type`).
  - **Documentation for behavior this diff touched** → neither outlet. It is not deferred work, it is
    *unfinished* work: a definition-of-done condition on the unit, alongside tests passing. Scoped by
    the diff — every doc describing behavior the change added, altered, or removed must be correct at
    merge; docs the diff did not invalidate stay out of scope.
- **`minerva:promote`'s Mode B carries the load mid-unit.** Durable knowledge found during phase 1 is
  promoted as it is found, landing in phase 1's PR, so an abandoned unit never strands unwritten
  knowledge. Only the full Mode A wrap-up waits for the final phase.
- **The `low` tier retires.** Once every filed item is a defect, "it does not matter whether we do it"
  is incoherent; the remaining levels denote a defect's urgency, not its worthiness.
- **`minerva:backfill-followups` is retired.** Its entire purpose was bulk-filing items the bar now
  refuses.
- **Existing history is left alone.** The ~150 `followups.md` bullets stay exactly as they are, still
  greppable, never re-triaged — re-triaging them is precisely the attention cost this unit exists to
  eliminate. Open issues below the bar are closed (#94), and #98, which passes the bar but predates
  the field, has `**Failure scenario**:` backfilled.

## Success criteria

- `plugins/minerva/skills/promote/references/deferral-bar.md` exists, and a test asserts that every
  consumer contains a qualified pointer to it that resolves, and that no consumer restates the bar's
  predicate in its own prose.
- The priority table in `github-issues.md` has exactly **three** rows, asserted by counting the
  table's rows — not by searching prose for `low`, which is a substring of "follow", "below" and
  "allow" (`2026-08-11-pattern-the-enumeration-is-what-fails`).
- The `gh issue create` body template in `github-issues.md` contains a `**Failure scenario**:` line,
  asserted by a hermetic test that makes no network call.
- A fail-soft check inside `promote`'s **existing** `gh issue list` duplicate-check query reports any
  open `minerva:followup` issue missing that field. It adds no new network call and never fails a run.
- `scripts/work_status.py` exposes a phase predicate, with tests covering an unphased unit, a unit
  with some phases merged, and a fully merged unit — plus an **inertness test** proving an unphased
  unit's derived state is unchanged from today's.
- `minerva:ship` targets `<date-slug>-phase-N` for phases N≥2 and its report names every outstanding
  phase; `minerva:cleanup` skips teardown while any declared phase is unmerged, and prunes the unit's
  merged phase branches once the final phase lands.
- `on-approval.md`'s duplicate-slug check matches a `<date-slug>-phase-N` branch.
- Both decomposition triggers and all four orchestrator scope-check steps state the cost of splitting
  and name phasing as the default response; the ~3-phase soft ceiling is documented.
- `minerva:backfill-followups` is removed from every catalog surface, not just its own directory
  (`2026-07-21-pattern-catalog-semantic-drift-recurs`: catalog surfaces drift semantically even
  during active scrubbing — sweep all four).
- `deferral-bar.md` states the documentation rule — docs for behavior the diff touched are a
  definition-of-done condition, never a triage outlet — and states its diff-bounded scope. Stated
  only, not audited, by explicit decision.
- The phasing documentation states that `promote`'s Mode B is the mechanism for durable knowledge
  found mid-unit, and that each phase's ship report names outstanding phases so a stalled unit is
  never silent.
- Every `SKILL.md` remains at or under 9216 bytes (`tests/test_skill_budget.py`).
- Issue #94 is closed; issue #98 carries a `**Failure scenario**:` line.
- **This unit itself ships as exactly two phases** — the dogfood proof that phase 1's mechanism works.

## Phases

1. **Plan-level phasing** — `## Phases` in the proposal template, the `<date-slug>-phase-N` topology,
   the `work_status.py` phase predicate, the `ship` loop, phase-aware `cleanup`, the widened
   duplicate-slug glob, and the cost-of-splitting text at both decomposition triggers and all four
   scope-check steps. Ships as an ordinary single PR on branch `2026-08-27-deferral-cost-model`.
2. **The deferral bar** — `deferral-bar.md` and its consumer pointers, the `**Failure scenario**:`
   requirement and its two checks, the retirement of the `low` tier and of
   `minerva:backfill-followups`, and the tracker cleanup (#94, #98). Ships through the phase-1
   mechanism on branch `2026-08-27-deferral-cost-model-phase-2`.

## Open Questions

None material. Both were resolved during grilling: knowledge stranded by an abandoned unit is handled
by `promote`'s existing Mode B, and worktree handling across phases needs no new machinery because
the record propagates by ordinary merge.
