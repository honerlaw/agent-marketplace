# Proposal: observable-orchestrator-mode

**Date**: 2026-08-28
**Status**: Draft

## Goal

Replace minerva's prose orchestrator carve-out with an **observable argument** across every
skill the `propose-ship-*` orchestrators inline, and enforce it with a corpus-derived contract
test. Close the paths by which an autonomous run yields control back to the user mid-phase, and
fix two hand-off gaps in the same family.

## Why

An autonomous run stops at unpredictable points and waits for the user to say "continue". The
stops are not at phase boundaries, which is what makes them look random.

**The orchestrators inline six skills**, counted from their own `references/phases.md`:
`review` (18 mentions), `ship` (15), `promote` (12), `work` (9), `replan` (6), `cleanup` (6).
Their gates were retrofitted for autonomous use **inconsistently**:

| Skill | Carve-out |
|---|---|
| `review` | prose — `references/protocol.md:125` |
| `promote` | prose — `references/modes.md:31` |
| `ship` | prose — `references/protocol.md:160` |
| `cleanup` | **observable argument** — `--yes`, `SKILL.md:68` |
| `work` | **none** |
| `replan` | **none** |

`work` governs Phase 2 — where a run spends most of its time — and carries three hand-back
instructions: `SKILL.md:65` ("Confirm before proceeding"), `:99` ("pause implementation. Tell
the user"), and `:116`, which states its operating model outright: *"After the initial
resumption summary it hands control back to normal conversation."* Because that posture is in
force across the bulk of the run rather than at a boundary, the resulting stops are scattered.

**A concrete path from an autonomous run into a human interview:**

    orchestrator Phase 2  ("implement per `minerva:work`'s Implementation protocol")
      -> work/SKILL.md:99  ("pause implementation. Tell the user ... then invoke the
                            `minerva:replan` skill and follow its protocol")
      -> replan/SKILL.md:49 ("invoke the `minerva:grill-plan` skill")
      -> grill-plan          a one-question-at-a-time user interview

No orchestrator mentions `grill-plan` anywhere (zero hits across all four). Each orchestrator
defines its own Phase 2.5 for replan, but nothing redirects `work:99` to it, so the trigger path
bypasses Phase 2.5 entirely.

**The prose form is the wrong mechanism, by minerva's own standing decision.** A clause reading
"when invoked by an orchestrator, its adjudication satisfies this gate" asks the model to
self-judge *am I orchestrated?*. `2026-06-07-decision-phase-handoff-rides-observable-intake`
rejects exactly that shape: *"'An inline argument was passed' is observable; 'the prior phase
converged' is an opinion,"* and directs future handoffs to prefer an observable signal. `cleanup`'s
`--yes` is that form. Fixing a prose-noticing failure by adding more prose is the weaker fix.

**Two hand-off gaps in the same family** — a step that must happen next with nothing causing it:

- `propose-ship-quick` and `-balanced` end Phase 2 with no continuation to Phase 3. Every other
  phase has one (`Continue to Phase 2/4/5`); `-auto` has it inside its step 4.
- `ship`'s CI watch ends the turn by design, and its `ScheduleWakeup` prompt is pinned to
  `minerva:ship <date-slug> --watch-iteration=<N>` — a re-entry into *ship*, carrying no
  knowledge of the orchestrator. The orchestrator's Phase 7 is therefore never triggered on any
  run where CI is still pending when the PR opens, and ship's final report closes with
  "Run `minerva:cleanup` afterward" — an instruction addressed to a human.

This is the third attested instance of the shape. `2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption`
named it; `2026-08-28-pattern-a-decider-and-an-executor-are-different-surfaces` (shipped in #101)
named it again and states that the durable fix is a test deriving the legal set from the
definition site. Neither enforces anything —
`2026-08-11-pattern-an-unenforced-constraint-is-aspirational` applies.

## Approach

1. **One observable argument.** Orchestrators invoke every inlined skill with an explicit
   `--auto` argument, following `cleanup --yes`'s precedent. Each inlined skill documents it and
   states which of its gates the argument satisfies.

2. **Migrate the three prose carve-outs** (`review/references/protocol.md:125`,
   `promote/references/modes.md:31`, `ship/references/protocol.md:160`) to the flag, so one
   mechanism covers the corpus. `cleanup`'s `--yes` stays as-is — it means something narrower
   (skip a destructive-action confirmation) and already satisfies the observability rule.

3. **Give `work` a `references/` directory.** It is the only one of the six with none, which is
   why its gates stayed inline: at 9147 bytes against the 9216-byte budget
   (`tests/test_skill_budget.py:32`) it has 69 bytes of headroom and no escape hatch. Move prose
   out to buy budget, and document the flag there.

4. **Redirect `work:99`.** Under `--auto`, a suspected load-bearing divergence returns to the
   orchestrator's Phase 2.5 instead of invoking `minerva:replan` (and thence `grill-plan`).

5. **Contract test**, modeled on `tests/test_deferral_bar.py` (single source + `CONSUMERS` +
   parametrized consumer check). Derive the consumer set by scanning
   `propose-ship-*/references/phases.md` for `minerva:<skill>` rather than hardcoding it, then
   assert both halves:
   - every named skill documents an observable mode argument;
   - every **invocation site** for that skill also carries the argument.

   The second half is what keeps this from going vacuous
   (`2026-08-10-pattern-presence-assertions-rot-into-green-lies`): pairing the argument to each
   invocation means a newly added site cannot pass unflagged.

   **Two boundaries have to be explicit, or the test is wrong in a way that reads clean.**

   - *Which mentions count.* An **invocation site** directs the model to run the skill — a
     `Skill`-tool call, or a "per `minerva:<skill>`'s <protocol>" delegation the orchestrator
     then executes. A **citation site** merely names a section as the source of a template or
     format (auto Phase 2.5 step 4 cites `minerva:replan`'s "On approval — file write"; several
     steps cite `minerva:propose`'s worktree-setup section). Citations must **not** require the
     argument. Requiring it everywhere would force nonsense edits, and the predictable response
     is to weaken the test until it passes — so the boundary is asserted too, not just applied
     (`2026-08-11-pattern-a-tolerant-reader-needs-a-boundary`).
   - *Which argument counts.* The invariant is "an observable argument the orchestrator passes",
     not the literal string `--auto`. `cleanup` satisfies it today with `--yes`, so the test
     reads each skill's own declared mode argument rather than assuming one spelling — otherwise
     it false-positives on the one skill that already got this right, and a false positive on a
     correct skill is how a gate gets weakened.

6. **Phase-continuation test.** Assert every `## Phase N` section in each orchestrator's
   `phases.md` names its successor, and add the missing continuation to `-quick` and
   `-balanced` Phase 2.

7. **Close the ship -> Phase 7 hand-off.** `ship` carries its caller across its own
   `ScheduleWakeup`, and at final report — when a caller is present — invokes
   `minerva:<caller> --cleanup-only <date-slug>` via the `Skill` tool instead of printing the
   human-facing recommendation. No new vocabulary is needed: all four orchestrators already
   document `--cleanup-only <date-slug>`, and it already skips phases 1-6 and runs Phase 7.

## Success criteria

- Each of the six skills named in the orchestrators' `phases.md` declares an observable mode
  argument (`--auto` for the five being migrated; `--yes` for `cleanup`, unchanged).
- Removing the argument from any single **invocation site** turns the contract test red —
  verified by deleting one occurrence and observing the failure, not by assertion alone.
- Adding a **citation site** that names a skill without the argument leaves the suite green —
  verified the same way, so the invocation/citation boundary is demonstrated in both directions.
- Removing a `Continue to Phase N` line turns the phase-continuation test red, verified by
  deleting one and observing the failure.
- `propose-ship-quick` and `-balanced` Phase 2 each end with a numbered continuation to Phase 3.
- `work/SKILL.md` is at or under 9216 bytes with the argument documented, and `work/references/`
  exists with every file reachable by a `read`-verb pointer from `SKILL.md`.
- No `minerva:ship` path prints the "Run `minerva:cleanup` afterward" recommendation when a
  caller is present; the caller survives a `ScheduleWakeup` round trip.
- `pytest` passes in full.

## Open Questions

- None outstanding. Flag spelling resolved to `--auto`; `cleanup`'s `--yes` is deliberately left
  unrenamed.
