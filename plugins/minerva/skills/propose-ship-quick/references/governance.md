# Governance — failure modes, observability, out of scope

## Failure modes, escalation, budget caps

**No panel budget.** Unlike `minerva:propose-ship-auto`, this skill convenes no panels, so there is no per-decision vote cap. A decision is either decided directly by the main model or escalated to the user per the [escalation predicate](solo-decision-protocol.md).

**Per-phase abort triggers.**
- Propose phase: if the propose-phase decisions (scope, approach, whole-proposal) escalate to the point the strategic intent is too ambiguous for the main model to resolve even with the user's answers, abort the quick run. Recommend: "switch to manual `minerva:propose`," or `minerva:propose-ship-auto` if independent panel review is wanted.

**Global escalation counter.** Maintain across the run; per-run, owned by the main orchestration loop (it survives the inline `Skill`-tool delegations of Phases 6 / 7). Increment on every user escalation. If it reaches **3**, halt before the next decision point and report status. A run that escalates this often is not a good fit for the fast path — recommend `minerva:propose-ship-auto` or `minerva:propose-ship`. Recovery: run the individual minerva skills manually from the current state.

**Hard escalation triggers (skip the main model's judgment entirely).**
- In-flight work collision (pre-flight) — the check in `plugins/minerva/skills/propose/references/in-flight-check.md`.
- An open issue matching the seed at intake — the ask in `plugins/minerva/skills/propose/references/issue-match.md`; it counts toward the counter like any other.
- Worktree creation failure (git error, gitignore missing, slug collision).
- Ship-phase failures classified as `other`, push rejection, `gh` auth failure.
- Global escalation counter reaching 3.

**Scope-fit escape.** If the change proves not small (scope explosion / deep complexity), escalate recommending `minerva:propose-ship-auto` or `minerva:propose-ship`, and emit the final-report-on-bail so the work is recoverable under the heavier orchestrator.

**Final report on bail.**
- Phase reached.
- Reason for bail (escalation count / hard trigger / scope-fit / CI failure).
- Current state of `.minerva/work/<date-slug>/` (proposal status, scratchpad summary, committed state).
- Exact next manual command (e.g., `minerva:work <date-slug>`, `minerva:ship <date-slug>`).

## Observability

- Every decision logs one line to `scratchpad.md` under a `## Quick decisions YYYY-MM-DD` header per `references/solo-decision-protocol.md`.
- Escalations log under the same header with `[escalated to user]` and a one-line summary of what was asked.
- The final report (success or bail) lists total decisions and total escalations for the run.

## Out of scope

- **Modifying any existing minerva skill at run time.** This skill orchestrates by *invocation only*. `minerva:propose`, `minerva:work`, `minerva:review`, `minerva:promote`, `minerva:replan`, `minerva:synthesize`, `minerva:ship`, and `minerva:cleanup` are never altered by a run; Phases 6 and 7 only *invoke* `minerva:ship` and `minerva:cleanup`, leading with an auto-mode instruction to auto-accept their gates.
- **Convening a `minerva:round-table` panel.** That is `minerva:propose-ship-auto`'s mechanism; this skill's entire identity is that the main model decides instead. If panel review is wanted, the user should run `minerva:propose-ship-auto`.
- **Auto-cascading into new work units.** Phase 4 TODOs marked "seed new proposal" are reported as suggestions — this skill does not invoke itself recursively in the same run.
- **Capping implementation time.** Phase 2's loop has no time or token bound; the scope-fit escape is the relief valve, not a hard cap.
- **Strict ordering of review and promote.** Same as the canonical lifecycle — review runs before promote so review-derived scratchpad notes flow through the promote partition. If review triggers a replan, Phase 3 cycles back to Phase 2; promote runs after the next review pass.
- **Large or high-stakes changes.** This skill is for small, low-risk work. When the change is ambiguous or high-stakes enough to want independent agents arguing it out, use `minerva:propose-ship-auto`; when the user wants to stay in the loop, use `minerva:propose-ship`.
