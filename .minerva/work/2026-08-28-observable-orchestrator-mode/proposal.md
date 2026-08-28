# Proposal: observable-orchestrator-mode

**Date**: 2026-08-28
**Status**: Shipped (2026-08-28)

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

*(Rewritten at promote to describe what shipped.)*

1. **One observable argument, declared machine-readably.** Each affected skill carries a
   `**Mode argument**:` line — `--auto` for `work`, `replan`, `review`, `promote`, `ship` and
   `synthesize`; `--yes` for `cleanup`, unchanged. Orchestrators pass `--auto=<orchestrator>`, whose
   value names the caller, because `ship` needs the caller's identity to hand back to the right
   Phase 7 and a boolean would have needed a second channel.

2. **The three prose carve-outs migrated** (`review/references/protocol.md`,
   `promote/references/modes.md`, `ship/references/protocol.md`), and `work` and `replan` — which
   had none — gained one. `work`'s divergence trigger now returns to the orchestrator's Phase 2.5
   instead of invoking `minerva:replan`, which reached `minerva:grill-plan`, a user interview.

3. **A seventh skill, beyond the original six.** `minerva:synthesize` kept the carve-out at two hops
   (orchestrator -> `cleanup --yes` -> synthesize) where a contract derived from orchestrator phase
   protocols cannot see it. `cleanup` now passes `--auto=cleanup` on the invocation line when it is
   itself orchestrated.

4. **Each orchestrator declares a `## Delegated skills` inventory** — skill, how it is run
   (`invoked` through the `Skill` tool / `inlined` from its own prose / `cited` for format only),
   and the argument passed. This draws the invocation-vs-citation boundary explicitly rather than by
   classifying prose, which could not separate a real delegation from
   "per `minerva:replan`'s 'On approval - file write'" without a brittle verb list.

5. **Two contract tests, positive and negative.** `tests/test_orchestrator_mode.py` derives the
   gated set from the orchestrators' own phase protocols and checks declaration, inventory coverage
   and use; `tests/test_phase_continuation.py` asserts every phase names its successor. The negative
   check — no skill anywhere gates on a judgment about its caller — is hop-independent, and is what
   would have caught `synthesize` on day one.

6. **The phase hand-offs.** `-quick` and `-balanced` Phase 2 gained the missing continuation to
   Phase 3; Phases 5 and 6 gained one in all three. `ship` carries its caller across its own
   `ScheduleWakeup` and, **only when resumed from that wake-up**, hands back via the `--cleanup-only`
   re-entry all four orchestrators already documented — the synchronous path is excluded on both
   sides so the cleanup gate cannot run twice.

7. **Budget accommodation.** `work` had no `references/` directory at all, which is why its gates
   stayed inline at 9147 of 9216 bytes; its worktree-addressing section moved out. `cleanup` shed
   its merge-detection section for the same reason.

8. **Shared test locators.** `tests/skills_corpus.py` states the orchestrator list and the
   phase-section parser once, replacing three copies across two new modules and `test_phasing.py`.

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

## Deferred work

- **#113** — reviewer-gate protocols mandate a synchronous `Agent` dispatch the tool schema may not
  expose. Observed twice during this run: both reviewer dispatches backgrounded and parked the run,
  while `tests/test_skill_dispatch.py` stayed green because it checks that the pin is *written*, not
  that it is *accepted*. Out of scope here; see
  `.minerva/knowledge/2026-08-28-constraint-reviewer-gates-assume-a-synchronous-dispatch.md`.

## Open Questions

- None outstanding. Flag spelling resolved to `--auto`; `cleanup`'s `--yes` is deliberately left
  unrenamed because it skips one destructive-action confirmation, not a set of strategic gates.
