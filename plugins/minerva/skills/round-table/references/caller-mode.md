# round-table — caller mode + out of scope (verbatim from SKILL.md, work unit 035)

## Caller mode (orchestrators)

Another skill can delegate its decision points here. Caller mode rides an observable intake: the caller invokes `minerva:round-table` via the `Skill` tool **once**, when its first panel-worthy decision arrives, leading with a standing instruction that names (a) where each decision's quorum comes from (e.g., the caller's decision taxonomy), (b) where log lines go, and (c) any standing auto-mode behavior. Once the protocol is loaded, apply it at each subsequent decision point **without re-invoking the Skill tool** — re-injection adds nothing; each application supplies that decision's artifact, context, and quorum.

The caller owns — and this skill never does — the decision *taxonomy* (which decisions get a panel and at what quorum), any skip predicate (whether to convene at all), escalation budgets and abort triggers, and all other run-level state.

## Out of scope

- **Deciding whether to convene.** Invoking round-table always convenes a panel. Skip predicates ("is this decision too small to panel?") are caller policy — `minerva:propose-ship-auto` keeps its fail-closed skip predicate on its side of the boundary, and an ad-hoc user invocation is itself the decision to convene.
- **Quorum policy.** Which decisions warrant 3/3 vs. 2/3 is the caller's taxonomy. This skill counts votes against whatever quorum it is given, and supplies the 2/3 default only when no caller specifies one.
- **Run-level state.** Escalation counters, per-run budgets, and abort triggers belong to the orchestrating caller.
- **Interviewing the user.** `minerva:grill-plan` stress-tests a drafted plan by questioning *you*, one question at a time; round-table convenes *agents* to argue it out and only reaches you on escalation. They compose — grill a draft to convergence, then round-table it for an independent verdict — but they do not overlap.
