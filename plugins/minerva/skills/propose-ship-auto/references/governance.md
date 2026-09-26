# Governance — failure modes, observability, out of scope

## Failure modes, escalation, budget caps

**Per-decision budget.** Each tier has its own hard cap, from `references/decision-protocol.md`:

- **Solo** dispatches nothing.
- **Reviewer, Skeptic gate:** at most two dispatches — the review, plus one fold-audit re-check when and only when the main model folded the critique. Never a third reviewer.
- **Reviewer, Verifier gate (completion):** one dispatch. A `revise` loops through Phase 2.5 rather than re-dispatching.
- **Panel:** one initial vote + one revision vote. 6 subagent dispatches max per panel.

A decision that moves up from reviewer to panel spends both budgets, so the worst case for one decision is 8 dispatches.

**Propose-wave restart.** When the gate wave's restart check (`references/phases.md` Phase 1) finds whole-proposal's first-wave review stale, that review is discarded. The re-dispatched whole-proposal is a new review of a new artifact, with a fresh per-tier budget of its own. A restarted whole-proposal can therefore spend up to 4 reviewer dispatches in total (2 stale, 2 restarted), or one panel budget on top of the stale wave's dispatches. There is at most **one** restart per run, because the check is made once, after scope and approach are final.

**Provisional review findings.** Code review sent out alongside completion verification (`references/phases.md` Phase 2 step 4) is Phase 3's code-review pass, run early, not an extra reviewer. It is re-run only when a failed completion led to a changed diff.

**Per-phase abort triggers.**
- Propose phase: if 2 of the 3 propose-phase decisions (scope, approach, whole-proposal) reach the user, abort the run. The strategic intent is too ambiguous for autonomous adjudication. Recommend: "switch to manual `minerva:propose`." Most escalations now pass through a panel before reaching the user, so this fires less often than it used to; `references/decision-protocol.md`'s *Re-measure* section checks whether it has gone inert.

**Global escalation counter.** Maintain across the run; per-run state owned by the main orchestration loop (it survives the inline skill-loader delegations of Phases 6 / 7). Increment on every user escalation — a panel that failed quorum twice, an upward move from a capped row, or a hardcoded trigger. If it reaches **3**, halt before the next decision point and report status. Recovery: run the individual minerva skills manually from the current state.

**Hard escalation triggers (skip tier selection entirely).**
- In-flight work collision (pre-flight) — the check in `skills/propose/references/in-flight-check.md`.
- An open issue matching the seed at intake — the ask in `skills/propose/references/issue-match.md`; it counts toward the counter like any other.
- Worktree creation failure (git error, gitignore missing, slug collision).
- Ship-phase failures classified as `other`, push rejection, `gh` auth failure.
- Global escalation counter reaching 3.

**Final report on bail.**
- Phase reached.
- Reason for bail (escalation count / hard trigger / CI failure).
- Current state of `.minerva/work/<date-slug>/` (proposal status, scratchpad summary, committed state).
- Exact next manual command (e.g., `minerva:work <date-slug>`, `minerva:ship <date-slug>`).

## Durable counters

Once a unit exists, checkpoint run counters at every phase transition and before
yielding, per the runtime contract. Carry intake escalations into the first
checkpoint; restore them on resume. A new session never grants a new budget.

## Observability

- Every decision logs one line to `scratchpad.md` under a `## Decisions YYYY-MM-DD` header per the Per-decision logging format in `references/decision-protocol.md`, naming its tier and why that tier was chosen.
- Every `[reviewed — folded]` line at a Skeptic gate is immediately followed by its `[rechecked — …]` line, so `scripts/decision_telemetry.py` can pair them.
- Escalations log under the same header with `[escalated to user]` and a one-line summary of what was asked.
- The final report (success or bail) lists decisions per tier (solo / reviewer / panel), total reviewer and panel dispatches, and total escalations for the run.

## Out of scope

- **Modifying any existing minerva skill at run time.** This skill orchestrates by *invocation only*. `minerva:propose`, `minerva:work`, `minerva:review`, `minerva:promote`, `minerva:replan`, `minerva:round-table`, `minerva:synthesize`, `minerva:ship`, and `minerva:cleanup` are never altered by a run; Phases 6 and 7 only *invoke* `minerva:ship` and `minerva:cleanup`, leading with an auto-mode instruction to auto-accept their gates, and the panel mechanics are likewise *invoked* from `minerva:round-table` in caller mode.
- **Sizing the whole run up front, or switching orchestrators mid-run.** Tier is chosen per decision; a change that grows simply makes its later decisions route higher (`2026-05-31-decision-per-decision-skip-over-sizing-gate`). There is no mode flag and no recommendation to hand the run to another skill.
- **Auto-cascading into new work units.** If Phase 4 surfaces TODOs marked "seed new proposal", they are reported as suggestions — the skill does not invoke `minerva:propose-ship-auto` recursively in the same run.
- **Capping implementation time.** Phase 2's implementation loop has no time or token bound. If the user wants to cap, they interrupt manually.
- **Strict ordering of review and promote.** Same as the canonical lifecycle — review runs before promote so review-derived scratchpad notes flow through the promote partition. If review triggers a replan, Phase 3 cycles back to Phase 2; promote runs after the next review pass.
- **A configurable quorum.** The 3/3 vs. 2/3 quorums per decision type are fixed (see the Decision taxonomy in `references/decision-protocol.md`); `minerva:round-table`'s standalone 2/3 default never applies inside this skill. If a user wants different thresholds, they fork the skill.
