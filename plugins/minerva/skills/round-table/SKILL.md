---
name: round-table
description: Use when the user invokes `minerva:round-table`, asks to convene a round table / decision panel / multi-agent consensus on a decision or drafted artifact, or when another skill delegates a decision to the consensus-panel protocol. Dispatches a 3-agent Proponent/Skeptic/Arbiter panel of fresh-context subagents over the artifact, counts accept votes against a caller-specified quorum (default 2/3), runs at most one revision round, and escalates to the user when consensus fails twice. A pure extraction of the panel protocol formerly inlined in `minerva:propose-ship-auto`, which now delegates its panel calls here; usable standalone for any decision.
---

Convene a 3-agent consensus panel — **Proponent**, **Skeptic**, **Arbiter** — of fresh-context subagents over a decision or drafted artifact, and convert their verdicts into a single accept / revise / reject outcome against a quorum.

Three uses:

1. **Ad-hoc judgment calls** — a decision framed mid-conversation ("refactor X or wrap it?") gets an independent multi-agent verdict.
2. **Drafted-artifact review** — a concrete draft (plan, doc, design, diff) gets the Proponent/Skeptic/Arbiter treatment before you commit to it.
3. **A building block for other skills** — orchestrators delegate their decision points here (this is how `minerva:propose-ship-auto` runs every strategic/tactical decision; see [Caller mode](#caller-mode-orchestrators)).

This skill is a pure, behavior-preserving extraction of the panel protocol formerly inlined in `minerva:propose-ship-auto` — the mechanics are unchanged; only their home moved.

## Usage

- `minerva:round-table "<framed decision or artifact>"` — the inline argument carries the decision (an observable intake — no session-scanning to guess what's under review). A "choose among options" decision is framed as an artifact: the candidate options plus the recommended pick, which the panel accepts, revises, or rejects.
- `minerva:round-table "<decision> — quorum 3/3"` — the caller may state a quorum inline. Absent one, the default is **2/3**.
- With the artifact already in conversation (a draft you just wrote), the argument can simply point at it: `minerva:round-table "review the draft plan above"`.

## Dispatch

Spawn 3 subagents via the `Agent` tool with fresh context. The Proponent and Skeptic run **in parallel** (single message with two `Agent` invocations); the Arbiter runs sequentially after both complete, since it needs their outputs.

Each agent receives the **artifact under review** (the draft, the proposed approach, the framed decision, etc.) plus the **decision context** (relevant `.minerva/knowledge/` entries, the work unit's `proposal.md` when one is in context, repo conventions from `CLAUDE.md`/`AGENTS.md`). Use `subagent_type: general-purpose` unless a more specialized agent fits the decision.

## Agent briefs

**Proponent prompt template:**
```
You are the Proponent in a 3-agent consensus panel reviewing this artifact.

ARTIFACT:
<the draft / proposal / decision under review>

CONTEXT:
<relevant knowledge entries, proposal, repo conventions>

YOUR ROLE: Argue for why this artifact is sound given the stated goal,
project constraints, and conventions. Cite specific evidence from the
context where you can.

After you've made your strongest honest case, render a final verdict
of one of: accept, revise, reject. Your role is to defend, but the
verdict must be truthful — if the artifact has fundamental problems
you couldn't argue around, say so.

Output format:
## Defense
<your argument>

## Verdict
<accept | revise | reject>: <one-sentence reason>
```

**Skeptic prompt template:**
```
You are the Skeptic in a 3-agent consensus panel reviewing this artifact.

ARTIFACT:
<the draft / proposal / decision under review>

CONTEXT:
<relevant knowledge entries, proposal, repo conventions>

YOUR ROLE: Surface every load-bearing risk, ambiguity, divergence from
convention, missing piece, or unstated assumption in this artifact. Be
specific — cite the part of the artifact you're critiquing.

After your critique, render a final verdict of one of: accept, revise,
reject. Your role is to find problems, but the verdict must reflect
whether the problems you found are actually load-bearing — a list of
nitpicks that don't block soundness should result in 'accept' with
concerns logged.

Output format:
## Critique
<your concerns, each as a numbered item with severity high/medium/low>

## Verdict
<accept | revise | reject>: <one-sentence reason>
```

**Arbiter prompt template:**
```
You are the Arbiter in a 3-agent consensus panel. You have already
received the Proponent's defense and the Skeptic's critique of this
artifact.

ARTIFACT:
<the draft / proposal / decision under review>

CONTEXT:
<same as above>

PROPONENT'S DEFENSE:
<full Proponent output>

SKEPTIC'S CRITIQUE:
<full Skeptic output>

YOUR ROLE: Weigh both sides. Decide which arguments are load-bearing
and which are not. Render a final verdict.

Output format:
## Reasoning
<which arguments mattered and why>

## Verdict
<accept | revise | reject>: <one-sentence reason>
```

## Vote semantics

Each agent ends with a verdict of `accept` / `revise` / `reject`. Count `accept` votes against the **required quorum** — specified by the caller, defaulting to **2/3** when none is given:

- **At or above quorum** → consensus, proceed.
  - 3/3 accepts at a 3/3-quorum decision → strong consensus, proceed silently.
  - 3/3 accepts at a 2/3-quorum decision → strong consensus, proceed silently.
  - 2/3 accepts at a 2/3-quorum decision → sufficient consensus, proceed. If the Skeptic dissented, log their high/medium concerns under a `## Panel concerns YYYY-MM-DD` header (see [Logging](#logging)) so the caller's next phase — or the user — picks them up.
- **Below quorum** → consensus failure. Trigger the **revision round** (below).
  - 2/3 accepts at a **3/3-quorum** decision → consensus failure (a 3/3 quorum demands unanimity; one Skeptic dissent at this tier is load-bearing).
  - ≤1/3 accepts at any quorum → consensus failure.

## Revision round

On consensus failure, the main LLM (not a new panel) synthesizes a revised draft using:
- The Skeptic's load-bearing critiques as the primary input.
- The Arbiter's reasoning to disambiguate which critiques mattered.
- The original artifact, modified to address those critiques without overcorrecting.

Re-dispatch the panel against the revised artifact. **Two votes maximum per decision point.** If the second vote also produces ≤1/3 accept, escalate to the user.

## Escalation

When a decision escalates:

1. Compose a focused, batched question for the user — pull the load-bearing concerns from both vote rounds, phrase them as decisions the user can make (not as "we couldn't decide"). Use the `AskUserQuestion` tool with multiple-choice options when possible.
2. Apply the user's answer as if the panel had voted to accept that path.
3. Run-level escalation state is the **caller's**, never this skill's: if the orchestrating skill maintains an escalation counter or abort budget (e.g., `minerva:propose-ship-auto`'s global escalation counter), the caller updates it after the escalation.

## Logging

After every panel call (regardless of outcome), record a one-line entry under a `## Panel decisions YYYY-MM-DD` header:

```
## Panel decisions 2026-05-21
- [3/3 accept] scope check: single unit
- [2/3 accept, skeptic dissented] approach selection: option B (concerns logged: race risk in step 4)
- [escalated to user] success criteria verification: panel split 1/3 on whether criterion #2 is met
```

**Where the line goes rides an observable signal, not a judgment call.** If an in-flight work unit is in context — the working tree contains a `.minerva/work/NNN-*/scratchpad.md` that is not the post-promote marker, or the session has already named the unit — append the entry (and any `## Panel concerns` block) to that unit's `scratchpad.md`. If no work unit is in context, the verdict and its log line live in the conversation only — there is nothing durable to write, which matches ad-hoc use being commitment-free. If multiple in-flight units exist and none is named in session context, ask which one (if any) should carry the log.

Callers may add their own policy lines under the same header (e.g., `minerva:propose-ship-auto`'s `[skipped — small]`, `[user-directed]`, and `[synthesis]` prefixes) — those are caller policy, not part of this protocol.

## Caller mode (orchestrators)

Another skill can delegate its decision points here. Caller mode rides an observable intake: the caller invokes `minerva:round-table` via the `Skill` tool **once**, when its first panel-worthy decision arrives, leading with a standing instruction that names (a) where each decision's quorum comes from (e.g., the caller's decision taxonomy), (b) where log lines go, and (c) any standing auto-mode behavior. Once the protocol is loaded, apply it at each subsequent decision point **without re-invoking the Skill tool** — re-injection adds nothing; each application supplies that decision's artifact, context, and quorum.

The caller owns — and this skill never does — the decision *taxonomy* (which decisions get a panel and at what quorum), any skip predicate (whether to convene at all), escalation budgets and abort triggers, and all other run-level state.

## Out of scope

- **Deciding whether to convene.** Invoking round-table always convenes a panel. Skip predicates ("is this decision too small to panel?") are caller policy — `minerva:propose-ship-auto` keeps its fail-closed skip predicate on its side of the boundary, and an ad-hoc user invocation is itself the decision to convene.
- **Quorum policy.** Which decisions warrant 3/3 vs. 2/3 is the caller's taxonomy. This skill counts votes against whatever quorum it is given, and supplies the 2/3 default only when no caller specifies one.
- **Run-level state.** Escalation counters, per-run budgets, and abort triggers belong to the orchestrating caller.
- **Interviewing the user.** `minerva:grill-plan` stress-tests a drafted plan by questioning *you*, one question at a time; round-table convenes *agents* to argue it out and only reaches you on escalation. They compose — grill a draft to convergence, then round-table it for an independent verdict — but they do not overlap.
