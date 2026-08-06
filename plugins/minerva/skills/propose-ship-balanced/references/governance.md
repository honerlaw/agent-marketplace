# Governance — failure modes, observability, out of scope

## Failure modes, escalation, budget caps

**Reviewer budget.** Each reviewer gate dispatches **one** subagent and the main model arbitrates inline — there is **no** revision-round re-dispatch and no panel vote. A reviewer gate's critique is either folded, proceeded past, or escalated to the user per the [escalation predicate](verify-protocol.md). The solo gates dispatch nothing.

**Per-phase abort triggers.**
- Propose phase: if the propose-phase decisions (scope, approach, whole-proposal) escalate to the point the strategic intent is too ambiguous for the main model to resolve even with the user's answers, abort the balanced run. Recommend: "switch to manual `minerva:propose`," or `minerva:propose-ship-auto` if independent panel review is wanted across the board.

**Global escalation counter.** Maintain across the run; per-run, owned by the main orchestration loop (it survives the inline `Skill`-tool delegations of Phases 6 / 7). Increment on every user escalation. If it reaches **3**, halt before the next decision point and report status. A run that escalates this often is not a good fit for this rung — recommend `minerva:propose-ship-auto` or `minerva:propose-ship`. Recovery: run the individual minerva skills manually from the current state.

**Hard escalation triggers (skip the main model's judgment entirely).**
- In-flight work collision (pre-flight).
- Worktree creation failure (git error, gitignore missing, slug collision).
- Ship-phase failures classified as `other`, push rejection, `gh` auth failure.
- Global escalation counter reaching 3.

**Scope-fit escape.** If the change proves not small-or-medium (scope explosion / deep complexity), escalate recommending `minerva:propose-ship-auto` or `minerva:propose-ship`, and emit the final-report-on-bail so the work is recoverable under the heavier orchestrator.

**Final report on bail.**
- Phase reached.
- Reason for bail (escalation count / hard trigger / scope-fit / CI failure).
- Current state of `.minerva/work/<NNN-slug>/` (proposal status, scratchpad summary, committed state).
- Exact next manual command (e.g., `minerva:work <NNN-slug>`, `minerva:ship <NNN-slug>`).

## Observability

- Every decision logs one line to `scratchpad.md` under a `## Balanced decisions YYYY-MM-DD` header per `references/verify-protocol.md`, with the `[decided]` / `[reviewed — folded]` / `[reviewed — clean]` / `[escalated to user]` prefixes.
- Reviewer gates record what the reviewer flagged and whether it was folded, so a later `minerva:review` / `minerva:promote` pass can audit the call.
- The final report (success or bail) lists total decisions, total reviewer gates, and total escalations for the run.

## Out of scope

- **Modifying any existing minerva skill at run time.** This skill orchestrates by *invocation only*. `minerva:propose`, `minerva:work`, `minerva:review`, `minerva:promote`, `minerva:replan`, `minerva:synthesize`, `minerva:ship`, and `minerva:cleanup` are never altered by a run; Phases 6 and 7 only *invoke* `minerva:ship` and `minerva:cleanup`, leading with an auto-mode instruction to auto-accept their gates.
- **Convening a `minerva:round-table` panel.** That is `minerva:propose-ship-auto`'s mechanism. This skill's independent review is a **single advisory reviewer** arbitrated by the main model — never a 3-agent consensus panel. If full panel review is wanted at every gate, the user should run `minerva:propose-ship-auto`.
- **Auto-cascading into new work units.** Phase 4 TODOs marked "seed new proposal" are reported as suggestions — this skill does not invoke itself recursively in the same run.
- **Capping implementation time.** Phase 2's loop has no time or token bound; the scope-fit escape is the relief valve, not a hard cap.
- **Strict ordering of review and promote.** Same as the canonical lifecycle — review runs before promote so review-derived scratchpad notes flow through the promote partition. If review triggers a replan, Phase 3 cycles back to Phase 2; promote runs after the next review pass.
- **Large or high-stakes changes.** This skill is for small-to-medium, low-to-moderate-risk work. When the change is ambiguous or high-stakes enough to want independent agents arguing it out at every gate, use `minerva:propose-ship-auto`; when the user wants to stay in the loop, use `minerva:propose-ship`; when the change is a trivial one-file tweak, use `minerva:propose-ship-quick`.
