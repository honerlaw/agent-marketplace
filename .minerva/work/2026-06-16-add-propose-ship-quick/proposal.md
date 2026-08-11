# Proposal: add-propose-ship-quick

**Date**: 2026-06-16
**Status**: Shipped (2026-06-16)

## Goal
Add a new minerva orchestrator skill, `minerva:propose-ship-quick` — a lightweight fast-path sibling of `minerva:propose-ship-auto`. It runs the same end-to-end lifecycle (propose → work → review → promote → synthesize → ship → cleanup) with **no scheduled human gates**, but the **main model adjudicates every strategic/tactical decision directly** instead of convening a 3-agent `minerva:round-table` panel. The same user-escalation fallback is preserved as an **exceptional** path: when the main model genuinely cannot decide, it escalates to the user — the role panel-escalation plays in `propose-ship-auto`. Optimized for small, low-risk changes (small UI fixes, bug fixes) the user wants done quickly, without multi-agent deliberation or long runs.

The three orchestrators form a ladder by adjudication cost: `propose-ship` (human gates) · `propose-ship-quick` (main model decides) · `propose-ship-auto` (consensus panels).

## Why
`propose-ship-auto` dispatches fresh-context subagent panels at every decision point — thorough, but slow and token-heavy, and overkill for a one-line UI tweak or a small bug fix. Users want to run the full minerva lifecycle quickly for small changes where the main model's own judgment is sufficient, reserving the panel machinery (`propose-ship-auto`) for genuinely ambiguous / high-stakes work and the human-gated path (`propose-ship`) for staying in the loop. This fills the gap between "fully manual lifecycle" and "panel-governed lifecycle".

## Approach
What shipped (see [[2026-06-16-decision-propose-ship-quick-main-model-adjudication]] for the adjudication-cost-ladder decision, the fail-closed-escalation-predicate framing, and the rejected alternatives). **Option A — standalone, self-contained skill** (selected; B/C rejected — see Open Questions). Created `plugins/minerva/skills/propose-ship-quick/` mirroring `propose-ship-auto`'s structure with the decision mechanism swapped:

1. **`SKILL.md`** — thin core (≤9 KB; `tests/test_skill_budget.py` enforces). Same phase map and hardcoded escalation triggers as auto; auto's "Panel protocol" section becomes a "Solo-decision protocol" section that points (with a *read* directive) at the reference files.
2. **`references/solo-decision-protocol.md`** — the differentiator:
   - **Default**: the main model decides each strategic/tactical decision directly, fast, context-grounded.
   - **Escalation predicate** — structurally parallel to auto's skip predicate but fail-closed in the *opposite* direction. Auto's predicate is fail-open toward deciding-without-panel (skip the panel only if every clause holds). Quick's governs decide-vs-escalate: the main model decides directly **unless** any of these holds, in which case it escalates — (a) genuine ambiguity (no dominant option after honest analysis), (b) high blast-radius / irreversible, (c) introduces a public interface or cross-cutting contract the model isn't confident about, (d) conflicts with a documented `.minerva/knowledge/` constraint. On any doubt, escalate (fail-closed toward escalation).
   - **Scope-fit escape** — if mid-run the change proves *not* small (scope explosion / deep complexity), escalate recommending a switch to `propose-ship-auto` or `propose-ship`, leaving the work unit recoverable (same final-report-on-bail shape).
   - **Never-bypassed self-checks** — completion verification, mid-work divergence confirmation, and replan acceptance are always performed as rigorous main-model self-checks (never elided because the change "looks small"), escalating on genuine uncertainty. These map to the same phase boundaries auto uses.
   - **Hardcoded escalation triggers** (unchanged from auto): in-flight collision, worktree-creation failure, ship-phase `other`/push-rejection/`gh`-auth failure, global escalation counter at 3.
   - **Escalation counter** — per-run state owned by the orchestrating main loop, maintained in-context for the single `propose-ship-quick` invocation (Skill-tool delegations run inline in that loop, so it survives across phases 4.5/6/7); incremented on every user escalation. Halt-at-3 = stop before the next decision and emit the final-report-on-bail.
   - **Logging** — one line per decision to `scratchpad.md` under `## Quick decisions YYYY-MM-DD` (distinct heading, no collision with `minerva:work`'s sections), prefixed `[decided]` / `[escalated to user]` / `[synthesis]`.
3. **`references/phases.md`** — mirrors auto's phase map 1-to-1 (1 Propose, 2 Work, 2.5 Replan, 3 Review, 4 Promote, 4.5 Synthesis, 5 Ship gate, 6 Ship, 7 Cleanup). No phase is removed. The only per-phase change: every panel-dispatch + skip-predicate + revision-round step is replaced by "the main model decides per the solo-decision protocol; escalate on genuine uncertainty." Delegated phases (4.5 synthesize, 6 ship, 7 cleanup) carry the same auto-mode instructions as auto.
4. **`references/governance.md`** — failure modes / escalation budget / out of scope, parallel to auto's. Drops only the panel-specific budget (the per-decision vote cap is meaningless without panels); retains the global escalation counter halt-at-3, the propose-phase abort, and the hard triggers. Out-of-scope keeps "never modify an existing minerva skill at run time" and "no auto-cascade into new work units".
5. **Delegations**: Phase 4.5 → `minerva:synthesize`, Phase 6 → `minerva:ship`, Phase 7 → `minerva:cleanup`, each with auto's auto-mode instruction. Does **not** delegate to `minerva:round-table`.
6. **`evals/propose-ship-quick/contract.json`** — frontmatter `{name: propose-ship-quick, non_empty: description}`; body/reference anchors covering the solo mechanism, the escalation path, and the three delegations (using the documented `file:` object-anchor retarget for prose that lives in a reference rather than the ≤9 KB body); `cross_surface` `{root_readme, plugin_readme, using_minerva_body}` all true.
7. **Catalog surfaces** (all four test-enforced): root `README.md`, `plugins/minerva/README.md`, `using-minerva/SKILL.md` body (these three by `cross_surface`), and `pages/index.md` between the skills-catalog markers (`tests/test_site_catalog.py`). Editing an existing skill's catalog body is ordinary authoring, not the runtime self-modification auto's out-of-scope rule forbids.

## Success criteria
- `plugins/minerva/skills/propose-ship-quick/SKILL.md` exists; frontmatter `name: propose-ship-quick`, non-empty description; body ≤9 KB.
- Each `references/*.md` is mentioned with a *read* directive in SKILL.md; no dangling/malformed pointers (`tests/test_skill_budget.py` passes).
- `evals/propose-ship-quick/contract.json` exists; every anchor appears in its declared location (body or retargeted reference file); `cross_surface` satisfied (`tests/test_skill_contracts.py` passes).
- `minerva:propose-ship-quick` appears in root `README.md`, `plugins/minerva/README.md`, `using-minerva/SKILL.md`, and the `pages/index.md` catalog section (`tests/test_site_catalog.py` + `cross_surface` pass).
- `solo-decision-protocol.md` documents: main-model-decides-by-default; the fail-closed escalation predicate (4 conditions); the scope-fit escape; the never-bypassed completion/divergence/replan self-checks; the hardcoded escalation triggers; and the per-run escalation counter with halt-at-3 semantics.
- The CI-scoped pytest suite is green with the new contract present.

## Open Questions
- **Name** — `propose-ship-quick` (confirmed by the user; matches the "quick variation, done quickly" framing). Rejected alternatives: `propose-ship-solo`, `propose-ship-fast`.
- **Rejected approaches** — **B**: a thin skill reusing `propose-ship-auto`'s reference files via cross-skill paths — rejected; breaks the self-contained-skill convention and the pointer-integrity infra in `tests/test_skill_budget.py` (each `references/<name>.md` pointer must resolve inside this skill's own dir with a *read* directive), and adds reader indirection. **C**: parameterize `propose-ship-auto` with a mode flag — rejected; forbidden by the "never modify an existing minerva skill at run time" out-of-scope rule and would couple two protocols in one file.
- **behavioral.json eval** — out of scope (behavioral evals are on-demand, not a CI gate; `contract.json` is the regression floor).
