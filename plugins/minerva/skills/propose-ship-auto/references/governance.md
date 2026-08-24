# Governance — failure modes, observability, out of scope

## Failure modes, escalation, budget caps

**Per-decision budget.** Hard cap: one initial vote + one revision vote per decision. 6 subagent dispatches max per decision point.

**Per-phase abort triggers.**
- Propose phase: if 2 of the 3 propose-phase panels (scope, approach, whole-proposal) escalate, abort the auto run. The strategic intent is too ambiguous for panel-driven decisions. Recommend: "switch to manual `minerva:propose`."

**Global escalation counter.** Maintain across the run. Increment on every user escalation. If it reaches **3**, halt before the next panel call and report status. Recovery: run individual minerva skills manually from the current state.

**Hard escalation triggers (skip the panel entirely).**
- In-flight work collision (pre-flight) — the check in `plugins/minerva/skills/propose/references/in-flight-check.md`.
- An open issue matching the seed at intake — the ask in `plugins/minerva/skills/propose/references/issue-match.md`; it counts toward the counter like any other.
- Worktree creation failure (git error, gitignore missing, slug collision).
- Ship-phase failures classified as `other`, push rejection, `gh` auth failure.
- Global escalation counter reaching 3.

**Final report on bail.**
- Phase reached.
- Reason for bail (escalation count / hard trigger / CI failure).
- Current state of `.minerva/work/<date-slug>/` (proposal status, scratchpad summary, committed state).
- Exact next manual command (e.g., `minerva:work <date-slug>`, `minerva:ship <date-slug>`).

## Observability

- Every panel call logs one line to `scratchpad.md` under a `## Panel decisions YYYY-MM-DD` header per the Per-decision logging format in `references/panel-protocol.md`.
- Escalations log under the same header with `[escalated to user]` and a one-line summary of what was asked.
- The final report (success or bail) lists total panel calls and total escalations for the run.

## Out of scope

- **Modifying any existing minerva skill at run time.** This skill orchestrates by *invocation only*. `minerva:propose`, `minerva:work`, `minerva:review`, `minerva:promote`, `minerva:replan`, `minerva:round-table`, `minerva:synthesize`, `minerva:ship`, and `minerva:cleanup` are never altered by a run; Phases 6 and 7 only *invoke* `minerva:ship` and `minerva:cleanup`, leading with an auto-mode instruction to auto-accept their gates, and the panel mechanics are likewise *invoked* from `minerva:round-table` in caller mode.
- **Auto-cascading into new work units.** If Phase 4 surfaces TODOs marked "seed new proposal", they are reported as suggestions — the auto skill does not invoke `minerva:propose-ship-auto` recursively in the same run.
- **Capping implementation time.** Phase 2's implementation loop has no time or token bound. If the user wants to cap, they interrupt manually.
- **Strict ordering of review and promote.** Same as the canonical lifecycle — review runs before promote so review-derived scratchpad notes flow through the promote partition. If review triggers a replan, Phase 3 cycles back to Phase 2; promote runs after the next review pass.
- **A configurable quorum.** The 3/3 vs. 2/3 quorums per decision type are fixed (see the Decision taxonomy in `references/panel-protocol.md`); `minerva:round-table`'s standalone 2/3 default never applies inside this skill. If a user wants different thresholds, they fork the skill.
