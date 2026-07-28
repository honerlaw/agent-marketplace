---
name: round-table
description: Dispatches a 3-agent Proponent/Skeptic/Arbiter panel of fresh-context subagents over a decision or drafted artifact, counts accept votes against a caller-specified quorum (default 2/3), runs at most one revision round, and escalates to the user when consensus fails twice. Use when another skill delegates a decision to the consensus-panel protocol, when the user asks to convene a round table / decision panel / multi-agent consensus on a decision or drafted artifact, or when they invoke `minerva:round-table`. Usable standalone for any decision.
---

Convene a 3-agent consensus panel — **Proponent**, **Skeptic**, **Arbiter** — of fresh-context subagents over a decision or drafted artifact, and convert their verdicts into a single accept / revise / reject outcome against a quorum.

Three uses:

1. **Ad-hoc judgment calls** — a decision framed mid-conversation ("refactor X or wrap it?") gets an independent multi-agent verdict.
2. **Drafted-artifact review** — a concrete draft (plan, doc, design, diff) gets the Proponent/Skeptic/Arbiter treatment before you commit to it.
3. **A building block for other skills** — orchestrators delegate their decision points here (this is how `minerva:propose-ship-auto` runs every strategic/tactical decision; see [Caller mode](#caller-mode-orchestrators)).

## Usage

- `minerva:round-table "<framed decision or artifact>"` — the inline argument carries the decision (an observable intake — no session-scanning to guess what's under review). A "choose among options" decision is framed as an artifact: the candidate options plus the recommended pick, which the panel accepts, revises, or rejects.
- `minerva:round-table "<decision> — quorum 3/3"` — the caller may state a quorum inline. Absent one, the default is **2/3**.
- With the artifact already in conversation (a draft you just wrote), the argument can simply point at it: `minerva:round-table "review the draft plan above"`.

## Dispatch

Spawn 3 subagents via the `Agent` tool with fresh context. Pass `run_in_background: false` in **every** panel `Agent` call — the panel is blocking by construction (votes are counted in the same turn, and the Arbiter needs the Proponent's and Skeptic's outputs), while a backgrounded dispatch returns only a handle and strands the run mid-panel with no legal next step. The pin costs no parallelism: the Proponent and Skeptic still run **in parallel** (single message with two synchronous `Agent` invocations); the Arbiter runs sequentially after both complete, since it needs their outputs. Use `subagent_type: general-purpose` unless a more specialized agent fits the decision. Pass `model: "sonnet"` in each Agent tool call for Proponent, Skeptic, and Arbiter. (A cheaper tier than the orchestrator — the pin keeps panel cost deterministic; update the alias if the model lineup shifts.)

### The shared block — cache-aligned prompt prefix

Every panel prompt **begins** with the same shared block, **byte-identical across all three agents for a given dispatch**. Identical leading bytes are what let the three requests share the prompt cache — so all role-specific text comes after the block, never before it:

```
ARTIFACT:
<the draft / proposal / decision under review>

CONTEXT:
<the enumerated decision context — see the inclusion list below>
```

CONTEXT is an **enumerated inclusion list**, not an open-ended dump. It contains, when each exists, exactly:

- the framed decision or stated goal the artifact serves;
- the work unit's `proposal.md`, when one is in context;
- `.minerva/knowledge/` entries **already cited in this session** — never a fresh corpus scan;
- repo conventions from `CLAUDE.md` / `AGENTS.md` that bear on the decision.

There is no size cap: the list bounds *what kinds* of input the panel sees, not how much. When `proposal.md` exceeds roughly 2,000 tokens, include only the section most relevant to the decision under review (e.g. `## Approach` for approach-selection panels, `## Success criteria` for completion-verification panels) rather than the full document.

## Agent briefs

The three role briefs — Proponent, Skeptic, Arbiter — live in `references/briefs.md`. **Read it at this run's first dispatch**; each prompt is the shared block, then (Arbiter only) the Proponent's and Skeptic's outputs, then the role brief.

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

## Caller mode and scope boundaries

When another skill delegates its decision points here (orchestrator use), read `references/caller-mode.md` **before the first delegated decision** — it defines caller-mode intake (quorum source, log destination, standing auto-mode behavior, no re-invocation per decision) and this skill's scope boundaries (convening is the caller's call; quorum policy, skip predicates, run-level state, and user-interviewing all live elsewhere).
