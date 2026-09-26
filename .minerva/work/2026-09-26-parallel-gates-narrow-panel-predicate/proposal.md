# Proposal: parallel-gates-narrow-panel-predicate

**Date**: 2026-09-26
**Status**: Shipped (2026-09-26)

## Goal
Cut `minerva:propose-ship-auto` wall time without dropping any gate, in three ways:
1. Run the three propose-phase gates concurrently.
2. Narrow when a decision earns a full 3-agent panel, so the reviewer tier really is the default.
3. Run the independent code review (and the inline minerva audit) concurrently with completion verification.

## Why
`scripts/run_trace.py --all` over the 6 propose-ship-auto runs (2026-09-23..26) shows:
- **Propose waits on serial gates.** The propose phase takes 12–39 min per run, median about 19. Only about 7 min of that is main-model activity. The rest is waiting on the scope, approach and whole-proposal gates, which are dispatched one after another; each Skeptic takes 2.5–5.5 min.
- **Panels fire far more than "reviewer is the default" suggests.** Approach went to a panel in 5 of 6 runs, whole-proposal in 5 of 6, and completion in 5 of 6 (its floor is a Verifier). The decision logs show why:
  - 9 of the 11 panels convened by the predicate cite the **public-interface clause**, mostly for a *new* tool surface in a new MCP server nobody consumes yet.
  - 3 of those 9 also cite "fail closed" (doubt).
  - Completion then re-fires the same clause on the same interface that the approach and whole-proposal gates already approved.
- **Completion verification and code review run sequentially.** The verify phase shows about 48s of activity against 19 min of waiting across runs, because code review only starts after completion returns.
- **Earlier propose gates almost never change what later gates review.**
  - In these 6 runs, scope resolved "one unit, one PR" every time, and approach always kept the recommended pick. This is pick stability in this sample. It is a different population from 2026-09-05's "approach 17/25 revision rate", which counts panels that revised the *write-up*, mostly with accept-with-fixes.
  - Whole-proposal is where folds and escalations happen.
  - The last run (2026-09-26-trace-orchestrator-run-time) already dispatched gates in parallel ad hoc with no rework (knowledge 2026-09-26-decision-trace-orchestrator-time-from-transcripts).
- **Expected saving.** Serial chain: scope reviewer (~2.5 min) + approach panel (~3–4 min: Skeptic, then Arbiter) + whole-proposal (~4–7 min) ≈ 10–13 min. Concurrent: the slowest gate, ≈ 4–7 min. That saves about 5–8 min per run in propose, plus about 3–5 min at verify/review. Candidate C would parallelize only the first two gates and save about 2.5–3 min.

## Approach
Recommended and approved: A — protocol changes in the orchestrator's references, pinned by contract tests.

### Scope and files in play
One work unit, one PR, no phases. The three changes edit the same orchestrator protocol files and are not independent subsystems, so decomposing them would be wrong. Phasing (`skills/propose/references/phasing.md`) is for "one coherent intent whose diff is too large to review in one PR". This diff is roughly 300–500 lines of prose plus roughly 200–350 lines of tests, which is reviewable in one PR; a recent unit shipped about 2,500 lines in one. Phasing would add a second review, PR, CI and merge-wait cycle (18–42 min of merge wait per PR in the trace) for no reviewability gain.

Files in play:
- `plugins/minerva/skills/propose-ship-auto/`: SKILL.md (8,450 of 9,216 budget bytes, so edits must stay small), references/phases.md, references/decision-protocol.md, references/governance.md.
- `plugins/minerva/skills/using-minerva/references/`: runtime.md, claude.md, codex.md.
- Summary lines that restate the panel predicate: plugins/minerva/skills/using-minerva/SKILL.md (routing table) and plugins/minerva/skills/propose-ship/SKILL.md (sibling description). These get a consistency check and are edited only if they turn stale.
- Tests:
  - tests/test_skill_contracts.py.
  - tests/test_skill_dispatch.py: `REGISTERED_SITES` pins the dispatch-instruction line count per file, so a new dispatch line in phases.md or runtime.md must be registered.
  - tests/test_decision_telemetry.py: the fenced logging example in decision-protocol.md must keep demonstrating all three tiers and all three `rechecked` outcomes.
  - tests/test_skill_budget.py.
- A new `.minerva/knowledge` decision entry.
- A minerva version bump in plugins/minerva/.claude-plugin/plugin.json and .codex-plugin/plugin.json.

### 1. Propose gate wave (phases.md Phase 1, steps 4–6)

**Draft, then route in gate order.**
- After design synthesis, the main model drafts all three decisions: scope, approach pick, and a whole-proposal verdict over the draft *with the recommended approach applied*.
- It routes them **in gate order**: scope, then approach (seeing scope's routing and the clause/surface pairs it claimed), then whole-proposal (seeing both). The once-per-surface rule (§2) therefore applies within the wave.
- Solo gates just decide.

**Dispatch in one message.** Every first-wave agent (a lone Skeptic, or a panel's Proponent + Skeptic pair) goes out in one message.

**Wait for the whole wave.** The parked-dispatch rule generalizes: while any first-wave result is outstanding, end the turn and resume on each notification. Reconcile only once the wave's results are all back. A panel's Arbiter is dispatched as soon as its own Proponent and Skeptic are back, without waiting for the rest of the wave.

**Reconcile in gate order:**
1. **Decompose aborts.** If scope resolves "decompose", abort as today and discard the other results. This wasted work is a known, accepted cost of the wave.
2. **Merge folds.** The scope and approach decisions stand (after any fold or panel accept), and their folds are merged into the draft **first**.
3. **Whole-proposal is held until scope and approach are final**, including any upward move to a panel. Only then is the restart check made, once, against the draft from step 2. If its first-wave review is materially stale, it is discarded and whole-proposal's tier is **selected again** against that draft before it is re-dispatched. Stale means any of:
   - the approach pick changed;
   - the scope decision changed the draft's structure (phases added or removed);
   - whole-proposal was routed on an earlier gate's **pending** clause that the earlier gate did not approve as drafted (as shipped: inside the wave, clauses are pending when later gates are routed);
   - a scope or approach fold rewrote `## Goal` or `## Success criteria`.

   Otherwise the first-wave result stands and its fixes merge in. Because the check waits for scope and approach to be final, a late upward move cannot slip past it, and at most one restart can happen.
4. **Fold-audits.** Every folded gate gets its fold-audit re-check, and these are dispatched concurrently. Each carries its own gate's original decision, its critique verbatim, and the revised decision.

**Budget.** A restart is a new review of a new artifact: the stale first-wave dispatch is discarded, and the restarted gate gets the normal two-dispatch Skeptic cap (or a fresh panel budget). The stale first wave is held unarbitrated, so it spent at most 1 reviewer or 3 panel dispatches. A restarted whole-proposal can therefore spend up to 3 reviewer dispatches (1 stale + 2), and at worst 11. governance.md states this explicitly. The "2 of 3 propose decisions reach the user → abort" rule is unchanged.

**Logging.** Each decision line keeps its tier tag, and its `(tier: …)` reason adds `parallel wave`. A restart logs its own line naming the staleness condition.

### 2. Narrower panel predicate (decision-protocol.md tier selection)

**The interface clause is narrowed.** It now covers only decisions that change an **existing** public interface or cross-cutting contract that consumers outside this work unit already rely on (rename, removal, behavior change).
- **Introducing** a new interface, package or tool surface is not by itself a panel clause. It fails the solo predicate's unchanged "no new public interface" clause, so it lands at the reviewer tier.
- A consumer added within the same work unit does not make an interface "existing".
- The blast-radius, ambiguity and knowledge-tension clauses are unchanged.

**A clause fires once per surface per run, and only for an already-approved change.**
- A *surface* is the named thing consumers bind to: a server's tool set, a CLI's flags and output, an env-var contract, a skill's protocol file.
- Once a gate has adjudicated a clause for a surface **and approved that change** (at any tier), later gates don't re-fire that clause for that same approved change. The record is the decision-log line, whose `(tier: …)` reason names the clause and the surface.
- A surface that had no concern when an earlier gate ran is not exempted from a later one.
- Completion goes to a panel on the interface clause only when the diff changes an interface or contract **beyond what the proposal approved**.

**Doubt about the interface clause goes to the reviewer (never solo), not a panel.** This applies to the narrowed interface clause only, and only at the Skeptic gates (scope, approach, whole-proposal). At completion the reviewer is a Verifier, which cannot move up, so interface doubt there still convenes the completion panel; doubt about the ambiguity, blast-radius or knowledge-tension clauses still convenes a panel, as today.
- In that case the main model passes its specific doubt to the Skeptic in CONTEXT.
- The Skeptic brief gains a `## Panel warranted?` section, where the Skeptic names any panel clause it believes holds, with evidence.
- A named, evidenced clause the main model cannot rule out is a third upward-move event (reviewer → panel). As shipped, it applies only on rows whose ceiling is panel and only for a clause that was not already the reason the decision reached the reviewer; capped rows (triage, partition, TODO) ignore it. It goes up **before** folding the critique, with no fold-audit, and is logged `[reviewed — escalated]`.
- The "Both predicates fail closed, in opposite directions" paragraph is rewritten to state this one exception and its trade-off. For the interface clause, the second check is now an independent Skeptic seeded with the main model's doubt, rather than an automatic panel.
- Doubt about a solo clause still denies solo.

**Rationale and examples.** The "Why these floors" rationale and the logging examples are updated to match. The floors and ceilings in the taxonomy table are unchanged.

### 3. Verify ∥ review (phases.md Phase 2 step 4 + Phase 3 step 3)

**Dispatch together.** When the completion checklist is composed, dispatch the completion Verifier (or the completion panel's first wave) **and** the independent code reviewer in the same message. Run the inline minerva audit while they run.

**When completion passes** (Verifier `accept`, or a completion panel at 3/3 or 2/3 — the latter proceeds with dissent logged as today): Phase 3 triages the already-generated code-review findings and the audit findings. There is no second code-review dispatch.

**When completion fails** (Verifier `revise`/`reject`, or a completion panel at ≤1/3): replan (Phase 2.5) as today. A replan always re-runs the inline audit, because it can rewrite `## Success criteria`. If the resumed implementation also changes the diff outside `.minerva/work/`, **both** the early code-review and the audit findings are discarded and Phase 3 re-generates them against the final diff. Otherwise the code-review findings stand.

Review → promote ordering is unchanged.

### 4. Runtime/adapters

- **runtime.md** "Independent reviewer operation": independent decisions with no data dependency may be dispatched concurrently. Each decision still waits for its own result before it is arbitrated. A wave is reconciled only once all of its results are back, and a parked handle is resumed on its notification.
- **claude.md**: several `Agent` calls in one message. Per 2026-07-27, synchronous dispatches issued in one message already run concurrently, so this needs no new capability.
- **codex.md**: several spawn_agent calls, then wait on all of them.

### Candidates considered
- **A (recommended):** the above.
- **B:** add a lighter 2-agent "mini-panel" tier (Proponent + Skeptic, no Arbiter). Rejected: it adds a fourth tier with new quorum semantics and telemetry tags, while the measured problem is routing (panels convened on uncontested decisions), not panel size.
- **C:** parallelize only scope and approach, and keep whole-proposal strictly after approach. Safer, with no hold/restart logic, but it leaves the long pole serial (whole-proposal, 3–7 min, the gate that actually folds and escalates) and saves about 2.5–3 min instead of about 5–8. Dominated by A, given the restart rule and the observed zero approach-pick changes.

## Success criteria
1. **Propose wave (phases.md Phase 1).** It describes routing in gate order with one-message dispatch; waiting for the full wave (Arbiters as their pairs complete); reconciliation in gate order (decompose aborts, then scope and approach folds merge first); holding whole-proposal until scope and approach are final; the single restart check with its three staleness conditions; and concurrent fold-audits.
2. **Budget (governance.md).** It states that a restart discards the stale dispatch, that the restarted gate gets a fresh per-gate budget, and the resulting totals: 3 reviewer dispatches, or at worst 11 (as shipped; the draft said 4 before review corrected the arithmetic).
3. **Tier selection (decision-protocol.md):**
   - the interface clause is narrowed to changes to an existing interface with consumers outside the unit, and introduce-then-consume within one unit is not "existing";
   - the once-per-surface rule has a defined "surface", suppresses re-firing only on an already-approved change, and is recorded in the decision-log reason;
   - doubt about the interface clause goes to the reviewer, the main model's doubt is passed in CONTEXT, and the Skeptic brief carries `## Panel warranted?`, which is listed as an upward-move event;
   - doubt about the other panel clauses still convenes a panel;
   - the "Both predicates fail closed" paragraph names the exception and its trade-off;
   - completion goes to a panel only on an interface change beyond what the proposal approved;
   - Parked dispatches covers several outstanding handles in a wave;
   - the logging examples still demonstrate every tier and every `rechecked` outcome;
   - "Why these floors" is consistent with all of the above.
4. **Verify ∥ review (phases.md Phase 2 step 4 + Phase 3 step 3).** Concurrent Verifier (or completion panel) plus code review; the inline audit runs during the wait; the outcome mapping for all Verifier and completion-panel outcomes; and discard-and-regenerate of **both** code-review and audit findings when the diff changes after a failed completion.
5. **SKILL.md** phase map and binding-floor lines are consistent with 1–4, with no stale "doubt about a panel clause convenes the panel" wording left unqualified, and the file stays within the 9,216-byte budget. using-minerva/SKILL.md and propose-ship/SKILL.md summaries are checked and fixed if stale.
6. **runtime.md, claude.md and codex.md** permit concurrent dispatch of independent decisions, with the wave-reconciliation and parked-handle rule.
7. **Tests.** Contract tests pin the new text: the wave, the hold/restart rule, the narrowed clause, the interface-only doubt→reviewer rule, and the concurrent verify/review with its discard rule. `REGISTERED_SITES` in tests/test_skill_dispatch.py is updated for any new dispatch-instruction lines. The full `python3 -m pytest -q tests` run passes.
8. **Knowledge and version.** A knowledge decision entry records the change with the trace evidence. The minerva version gets a minor bump to 2.1.0 in both plugin.json files: this refines protocol behavior and removes no skill or caller, unlike the 2.0.0 deletion of quick and balanced.

## Open Questions
- None blocking.
- `scripts/run_trace.py` already reports designed verify/review overlap as "out-of-order signal ignored"; per 2026-09-26 that is honest, not a bug. It is left as is here; the knowledge entry notes that the overlap is now by design.
- Skipping the Arbiter when quorum is already settled (a round-table change) is out of scope.
