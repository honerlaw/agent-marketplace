# propose-ship-auto — design

**Date**: 2026-05-21
**Status**: Approved (pending written-spec review)

## Goal

Add a new minerva skill, `minerva:propose-ship-auto`, that runs the same end-to-end lifecycle as `minerva:propose-ship` (propose → work → review → promote → ship → cleanup) but replaces the human-facing decision gates with a multi-agent consensus panel. Human input is **only** a fallback when consensus can't be reached after one revision round.

## Why

`minerva:propose-ship` already conducts the full lifecycle, but pauses at every gate for user input — that's correct for high-stakes work where the human is the authoritative decider. For lower-stakes work (the user has thought it through, the scope is clear, the success criteria are obvious from context), the gates are friction without much risk-reduction. An auto variant lets the user delegate the whole flow when they trust the consensus panel to catch the same ambiguities they would.

The mechanism — Proponent / Skeptic / Arbiter panels of fresh-context subagents voting on each load-bearing decision — uses adversarial structure to surface real concerns rather than chained agreement. When the panel can't agree, the skill falls back to user input rather than guessing; the failure mode is "ask a focused question," not "ship something wrong."

## Approach

### Skill shape

- New skill at `plugins/minerva/skills/propose-ship-auto/SKILL.md`.
- Registered in the minerva plugin (`plugin.json`); README updated to list it alongside `minerva:propose-ship`.
- Invocation: `minerva:propose-ship-auto "add rate limiting"` — same shape as `propose-ship`, including the optional inline description.
- Pre-flight in-flight collision check is identical to `propose-ship` and is **not** panel-decided — it hardcodes user escalation. Wrong call here destroys real work.
- Phase 7 (cleanup gate) is identical to `propose-ship`: `gh pr view` → `ScheduleWakeup` polling at 270s intervals, capped at 12 retries, invokes `minerva:cleanup` on `MERGED`.

### Orchestration model — Option C (hybrid)

The existing minerva skills have hard, explicit user gates baked into their instructions. A pure thin-conductor approach (delegating to them and trying to override gates from the parent skill) is too fragile — the LLM is reading two conflicting sets of instructions. A pure inline approach duplicates ~30% of lifecycle logic. The hybrid:

- **Delegate** to existing skills for phases with no strategic/tactical user gates:
  - `minerva:ship` — gates are operational-tier (commit message, PR body). Panel doesn't fire here. The auto skill leads with "auto mode: accept the drafted commit message and PR body without asking" — a soft override of an operational gate, low fragility risk.
  - `minerva:cleanup` — no user gates. Direct delegation.
- **Inline** the phases dominated by strategic/tactical gates, referencing the existing skills for shared templates (NNN derivation, worktree setup, file templates, idempotency rules) without invoking them:
  - Propose flow (intake → draft synthesis → panel acceptance → worktree + branch creation → file writes per `minerva:propose` step 9 template).
  - Work flow (implementation loop, replan-trigger detection, success-criteria verification — panel fires for the strategic decisions; main LLM does implementation).
  - Review flow (diff resolution + finding generation can still delegate to `code-review:code-review` for PR-mode; **triage** is inline and panel-driven).
  - Promote flow (read scratchpad + draft partition inline; panel approves; auto skill applies writes per `minerva:promote`'s Mode A template).
  - Replan (if triggered mid-work) — inline. Draft + panel + append per `minerva:replan` template.

SKILL.md size estimate: 250-350 lines.

### Panel mechanism (the P/S/A consensus protocol)

**Dispatch.** A panel call dispatches 3 subagents via the `Agent` tool, all fresh-context. Each gets the artifact + a structured prompt for its role:

- **Proponent** — defends the artifact. Brief: "Argue for why this draft is sound given the goal, constraints, and project conventions. After arguing, render an honest verdict of `accept` / `revise` / `reject` — your role is to defend, but your verdict must be truthful."
- **Skeptic** — attacks the artifact. Brief: "Surface every load-bearing risk, ambiguity, divergence from convention, and missing piece. After your critique, render an honest verdict — your role is to find problems, but your verdict must reflect whether the problems are actually load-bearing."
- **Arbiter** — judges. Receives the artifact + Proponent's defense + Skeptic's critique. Brief: "You have both sides. Render a verdict and explain which arguments were load-bearing."

Proponent + Skeptic run in parallel (single tool-call message with two `Agent` invocations). Arbiter runs after both complete, since it needs their outputs. Net: one "vote" is 2 parallel calls + 1 sequential call.

**Vote semantics** — each agent ends with a verdict of `accept` / `revise` / `reject`. The accept count is compared against the decision's **required quorum** (3/3 or 2/3 per the taxonomy below):

- **At or above quorum** → consensus, proceed. If a 2/3-quorum decision passes with 2/3 (Skeptic dissents), log the Skeptic's high/medium concerns to `scratchpad.md` under a `## Panel concerns YYYY-MM-DD` header so the next phase picks them up.
- **Below quorum** → consensus failure, revise once and re-vote. Specifically: 2/3 accepts on a 3/3-quorum decision fails (strategic decisions require unanimity); ≤1/3 accepts on any quorum fails.

**Revision round.** On failure, the main LLM (not a panel) synthesizes the Skeptic's load-bearing critiques + Arbiter's reasoning into a revised draft. Re-vote with the revised artifact. Two votes maximum per decision point.

**Escalation.** If the second vote also fails, the skill bails to the user with a focused, batched list of the load-bearing ambiguities the Skeptic flagged — phrased as questions, not as "we couldn't decide." The user's answer lands as if the panel had voted to accept that path. Resume the flow from the next decision point.

### Decision taxonomy (which decisions get the panel)

The S/T/O tiering determines panel involvement. Operational decisions never go to a panel.

| Phase | Decision | Tier | Quorum |
|---|---|---|---|
| Pre-flight | In-flight work collision | n/a | Hardcoded user escalation |
| Propose | Scope check (single unit vs. decompose) | Strategic | 3/3 |
| Propose | Approach selection (from 2-3 candidates) | Strategic | 3/3 |
| Propose | Whole-proposal acceptance (Goal / Why / Approach / Success criteria / Open Questions, single panel call) | Strategic | 3/3 |
| Work | Mid-work load-bearing divergence (panel confirms main LLM's detection) | Strategic | 2/3 |
| Replan (if triggered) | New-plan acceptance | Strategic | 3/3 |
| Work | Completion verification (success criteria honestly met against diff/tests) | Strategic | 3/3 |
| Review | Per-finding triage (single panel call assigning FIX/SUGGEST/IGNORE to all findings as a batch) | Tactical | 2/3 |
| Review | Replan-vs-FIX (only if a load-bearing finding surfaces) | Strategic | 2/3 |
| Promote | Three-way partition (PROMOTE/MERGE/DISCARD/TODO) | Tactical | 2/3 |
| Promote | TODO disposition (followups/seed/discard per TODO) | Tactical | 2/3 |
| Ship | Commit message | Operational | No panel |
| Ship | PR title + body | Operational | No panel |
| Ship | CI auto-fix classification + bail | Tactical | No panel (`ship`'s rule-based classifier handles it) |
| Cleanup gate | PR state polling + cleanup | n/a | No panel |

**Cumulative panel calls in a clean run:** ~6 (scope, approach, proposal, completion, review triage, promote partition). Each ~3-6 subagent dispatches. Net: 20-35 subagent calls per full run, plus the main LLM doing implementation.

**Cumulative panel calls in a realistic worst case:** add 2 for a replan cycle (divergence detection + new-plan acceptance) and 2 for a review re-cycle. Net: ~10 panel calls.

### Strategic intake (where Goal / Why / Approach / Success criteria come from)

The user invokes `minerva:propose-ship-auto "add rate limiting"`. The strategic content has to come from context — there's no Q&A loop to fill the gap.

1. The auto skill assembles **available context**: inline description, current chat history, repo state (`CLAUDE.md` / `AGENTS.md`, `.minerva/knowledge/`, recent `.minerva/work/NNN-*/proposal.md` files for tone and conventions, `.minerva/work/NNN-*/followups.md` for adjacent TODOs).
2. The main LLM drafts a complete proposal (Goal / Why / Approach / Success criteria / Open Questions) plus 2-3 candidate approaches it had to choose among. This is the **design synthesis** step.
3. The panel runs against the draft — first on scope decomposition, then approach selection, then whole-proposal acceptance.
4. If any of those panels fail after one revision, the skill escalates to the user with a focused, batched question (e.g., "panel could not agree on whether this is a single unit — here are the three sub-units it identified, pick one to proceed with, or keep as one"). Resume on answer.

The intake is "one shot, multi-vote" — the user is never asked to fill in fields, only to disambiguate when the panel can't agree on what context already implies.

### Failure modes, escalation, budget caps

**Per-decision budget.** One initial vote + one revision vote = at most 6 subagent dispatches per decision. Hard cap. After that, escalate.

**Per-phase budget.**
- Propose: up to 3 panel calls (scope, approach, whole-proposal). If 2 of those escalate to user, abort the auto run with a clear message — "panel could not agree on the strategic intent; switch to manual `minerva:propose`."
- Work: replan-detection panel calls are unbounded in count, but each is preceded by main LLM's own detection (panel confirms). Implementation time itself is uncapped.
- Review: 1-2 panel calls (triage + possible replan-vs-FIX). Re-cycle if replan fires.
- Promote: 2 panel calls (partition + TODO disposition).
- Ship: panel doesn't fire.

**Per-run global circuit breaker.** If the run accumulates ≥3 user escalations across the full lifecycle, stop and recommend manual mode. The signal value of "panels kept failing to agree" outweighs continuing to push.

**Replan as the recovery mechanism.** Three places trigger a replan:
1. Mid-work load-bearing divergence (auto-detected by main LLM, confirmed by 2/3 panel).
2. Review surfacing a load-bearing finding (panel decision Replan vs. FIX).
3. Completion-verification panel votes ≤1/3 that success criteria are met — a signal the criteria themselves may be wrong or the work isn't really done. Auto-trigger replan to clarify success criteria, then resume work.

**Hard escalation triggers (always go to user, never panel).**
- In-flight work collision (pre-flight).
- Worktree creation failure (git error, gitignore missing, slug collision).
- Ship phase hard-fails: CI failures classified as `other`, push rejected, `gh` auth failed.
- Global circuit breaker tripped.

**Failure-mode reporting.** When the skill bails, the final message includes:
- Phase reached.
- Reason for bail (escalation count, hard trigger, CI failure type).
- Current state of `.minerva/work/NNN-slug/` (proposal status, scratchpad contents, what was committed).
- The exact next manual command (e.g., "resume with `minerva:work NNN-slug`" or "fix CI, then `minerva:ship NNN-slug`").

### Observability

Every panel call appends a one-line entry to `scratchpad.md` under a `## Panel decisions YYYY-MM-DD` header so the run is auditable after the fact:

```
## Panel decisions 2026-05-21
- [3/3 accept] scope check: single unit
- [2/3 accept, skeptic dissented] approach selection: option B (concerns logged: race risk in step 4)
- [escalated to user] success criteria verification: panel split 1/3 on whether criterion #2 is honestly met
```

These entries are scratchpad data — `minerva:promote` treats them as routine noise unless a Skeptic concern reveals a durable pattern, in which case it goes through the standard PROMOTE/MERGE/DISCARD partition. The entries are not protected.

## Success criteria

- A new skill exists at `plugins/minerva/skills/propose-ship-auto/SKILL.md` and is listed in the minerva plugin's README.
- Invoking `minerva:propose-ship-auto "<description>"` from a minerva-tracked project runs the full propose → work → review → promote → ship → cleanup lifecycle with no scheduled user gates.
- Panel calls fire at the decision points enumerated in the taxonomy above, using the Proponent / Skeptic / Arbiter dispatch and vote semantics described.
- On consensus failure (≤1/3), the skill attempts one revision round before escalating to the user with a focused, batched question.
- All panel decisions are logged to `scratchpad.md` under a `## Panel decisions YYYY-MM-DD` header.
- The skill bails cleanly with a state report and a next-step command when any hard escalation trigger fires or the global circuit breaker trips.
- Phase 7 cleanup gate behaves identically to `minerva:propose-ship` (PR state polling via `ScheduleWakeup`).
- The skill does not modify any existing minerva skill's behavior.

## Open Questions

None at design time. Open questions discovered during implementation are appended here.
