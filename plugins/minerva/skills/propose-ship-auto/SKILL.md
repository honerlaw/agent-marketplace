---
name: propose-ship-auto
description: Use when the user invokes `minerva:propose-ship-auto`, wants to run the full minerva lifecycle end-to-end with no human gates, or says things like "auto propose and ship", "fully automated", "do the whole thing without asking". Same lifecycle as `minerva:propose-ship` (propose → work → review → promote → ship → cleanup), but replaces each human-facing decision with a 3-agent Proponent/Skeptic/Arbiter consensus panel. Human input is only a fallback when the panel can't agree after one revision round. Small, low-risk decisions skip the panel via a fail-closed skip predicate, so a genuinely small task runs effectively panel-free.
---

Run the full minerva lifecycle end-to-end with consensus-panel decisions in place of human gates. This skill is a **hybrid orchestrator** — it delegates to `minerva:ship` and `minerva:cleanup` directly (those phases have no strategic gates) but inlines the propose / work / review / promote / replan phases so it can substitute panel calls for hard user gates.

The mechanism: at each strategic or tactical decision point, dispatch a 3-agent Proponent/Skeptic/Arbiter panel of fresh-context subagents. Operational decisions (commit messages, PR bodies, file paths) bypass the panel entirely — the main LLM executes them. For **small, low-risk decisions**, a [Skip predicate](#skip-predicate-small-decisions) lets the main LLM decide directly without convening a panel — so a genuinely small task runs effectively panel-free — while it fails closed to the full panel on any uncertainty and never skips the post-divergence or completion-verification panels.

## Usage

- `minerva:propose-ship-auto "add rate limiting"` — start a new auto run with the inline description as the strategic seed.
- `minerva:propose-ship-auto` — start with current-session chat context as the strategic seed (only sensible if the chat already discussed what to build).
- `minerva:propose-ship-auto --cleanup-only <NNN-slug> --retry=N` — internal re-entry from the cleanup-gate wake-up loop. Skips phases 1–6 and re-runs Phase 7.

## Pre-flight: in-flight work collision

Identical to `minerva:propose-ship`'s pre-flight section. This check is **not** panel-decided — wrong call here destroys real work, so escalation to the user is hardcoded:

1. List `.minerva/work/NNN-*/` plus `.minerva/worktrees/NNN-*/.minerva/work/NNN-*/`.
2. If any unit has a `proposal.md` whose `## Status` is `Draft` or whose scratchpad is **not** the post-promote marker, treat it as in-flight.
3. If the user's inline description overlaps a slug or goal, **stop and ask**:
   > "Found in-flight work unit `005-add-payments` — looks related. Resume that one (`minerva:work 005-add-payments`) or genuinely start fresh?"

Only proceed after the user confirms. This is the single mandatory pre-run user interaction.

## Panel protocol

Used at every strategic/tactical decision point (see [Decision taxonomy](#decision-taxonomy)).

### Skip predicate (small decisions)

Before dispatching a panel for any **skippable** strategic/tactical decision (see the `Skippable?` column in the [Decision taxonomy](#decision-taxonomy)), the main LLM first applies an explicit **conjunctive** test to *that specific decision*. Skip the panel — the main LLM decides directly — **only if every** clause holds:

- **additive / low-blast-radius** — the artifact adds rather than rewrites, with a bounded surface;
- **objectively verifiable without a judgment call** — the supporting evidence is mechanical (a named passing test, a file that exists, a count), not an opinion;
- **single-surface** — one file / one concern;
- **no new public interface or cross-cutting contract**;
- **violates no identifiable `.minerva/knowledge/` constraint**;
- **(approach-bearing decisions only)** the main LLM actually **enumerated ≥2 viable approaches and one is strictly dominant** on the stated criteria. This is an *action* check (did you do the enumeration), not a self-judgment that "no alternative exists" — the latter is gameable by an LLM that never looked.

**Fails closed.** If any single clause fails — or you are unsure whether it holds — convene the panel exactly as specified below, at the decision's existing quorum. The predicate only ever decides *whether to convene*; it never changes a quorum. Because every clause must pass, the worst case of a wrong skip is bounded to an additive, single-surface, low-risk change; the worst case of a wrong *non*-skip is a panel you didn't strictly need.

**Never-skippable — one rule.** Any panel whose trigger precondition is "a load-bearing divergence/finding has already surfaced," plus the completion self-check, is **never** skippable regardless of how small the change looks — its whole value is an independent second pair of eyes on the main LLM's own assessment, and its precondition is the negation of the low-blast-radius clause. Concretely: **completion verification**, **mid-work divergence confirmation**, **new-plan acceptance (replan)**, and **Replan-vs-FIX**. All hard user-escalation triggers and hardcoded gates (see [Failure modes](#failure-modes-escalation-budget-caps)) are likewise never skipped. Late-emerging risk needs no separate escape hatch: a decision that looks small but proves load-bearing simply fails the predicate and convenes its panel.

**Log every skip** under the same `## Panel decisions YYYY-MM-DD` header used for panel calls (see [Per-decision logging](#per-decision-logging)).

### Dispatch

Spawn 3 subagents via the `Agent` tool with fresh context. The Proponent and Skeptic run **in parallel** (single message with two `Agent` invocations); the Arbiter runs sequentially after both complete, since it needs their outputs.

Each agent receives the **artifact under review** (the draft proposal, the proposed approach, the triage assignment, etc.) plus the **decision context** (relevant `.minerva/knowledge/` entries, `proposal.md` for downstream decisions, repo conventions from `CLAUDE.md`/`AGENTS.md`). Use `subagent_type: general-purpose` unless a more specialized agent fits the decision.

### Agent briefs

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

### Vote semantics

Each agent ends with a verdict of `accept` / `revise` / `reject`. Count `accept` votes against the decision's **required quorum** from the [Decision taxonomy](#decision-taxonomy):

- **At or above quorum** → consensus, proceed.
  - 3/3 accepts at a 3/3-quorum decision → strong consensus, proceed silently.
  - 3/3 accepts at a 2/3-quorum decision → strong consensus, proceed silently.
  - 2/3 accepts at a 2/3-quorum decision → sufficient consensus, proceed. If the Skeptic dissented, log their high/medium concerns to `scratchpad.md` under a `## Panel concerns YYYY-MM-DD` header so the next phase picks them up.
- **Below quorum** → consensus failure. Trigger the **revision round** (below).
  - 2/3 accepts at a **3/3-quorum** decision → consensus failure (strategic decisions require unanimity; one Skeptic dissent at this tier is load-bearing).
  - ≤1/3 accepts at any quorum → consensus failure.

### Revision round

On consensus failure, the main LLM (not a new panel) synthesizes a revised draft using:
- The Skeptic's load-bearing critiques as the primary input.
- The Arbiter's reasoning to disambiguate which critiques mattered.
- The original artifact, modified to address those critiques without overcorrecting.

Re-dispatch the panel against the revised artifact. **Two votes maximum per decision point.** If the second vote also produces ≤1/3 accept, escalate to the user.

### Escalation

When a decision escalates:

1. Compose a focused, batched question for the user — pull the load-bearing concerns from both vote rounds, phrase them as decisions the user can make (not as "we couldn't decide"). Use the `AskUserQuestion` tool with multiple-choice options when possible.
2. Apply the user's answer as if the panel had voted to accept that path. Resume the flow from the next decision point.
3. Increment the **global escalation counter** (see [Failure modes](#failure-modes-escalation-budget-caps)).

### Per-decision logging

After every panel call (regardless of outcome), append a one-line entry to `scratchpad.md` under a `## Panel decisions YYYY-MM-DD` header:

```
## Panel decisions 2026-05-21
- [3/3 accept] scope check: single unit
- [2/3 accept, skeptic dissented] approach selection: option B (concerns logged: race risk in step 4)
- [escalated to user] success criteria verification: panel split 1/3 on whether criterion #2 is met
```

Decisions resolved by the [Skip predicate](#skip-predicate-small-decisions) instead of a panel **are logged** under the **same** header, prefixed `[skipped — small]`, and **must record the concrete evidence** that satisfied the predicate (so a later `minerva:review` / `minerva:promote` pass can audit that the skip was honest, not rubber-stamped). Approach-decision skips additionally record the rejected alternatives:

```
- [skipped — small] scope check: single additive unit (evidence: only SKILL.md touched)
- [skipped — small] approach selection: option B dominant (rejected: A — duplicates orchestration; C — coarse)
```

These entries are scratchpad data — `minerva:promote` treats them as routine noise unless a Skeptic concern reveals a durable pattern, in which case it goes through the standard PROMOTE/MERGE/DISCARD partition. A `[skipped — small]` line is **promote-invisible by construction** — a skip has no Skeptic, so it can never surface a durable pattern. This is intended: a decision trivial enough to skip yields no durable knowledge.

## Decision taxonomy

The `Skippable?` column applies the [Skip predicate](#skip-predicate-small-decisions): it gives the per-row bar a decision must clear for the main LLM to skip its panel. `No` = always run the panel (never-skippable). Operational rows are already main-LLM (no panel to skip).

| Phase | Decision | Tier | Quorum | Skippable? |
|---|---|---|---|---|
| Pre-flight | In-flight work collision | n/a | Hardcoded user escalation | **No** — hardcoded user escalation |
| Propose | Scope check (single unit vs. decompose) | Strategic | 3/3 | Only if obviously a single additive unit |
| Propose | Approach selection (from 2-3 candidates) | Strategic | 3/3 | Only if ≥2 approaches enumerated & one strictly dominant; skip log records the rejected alternatives |
| Propose | Whole-proposal acceptance | Strategic | 3/3 | Only if every section is trivially sound & single-surface |
| Work | Mid-work load-bearing divergence (panel confirms main LLM's detection) | Strategic | 2/3 | **No** — precondition is a surfaced divergence |
| Replan (if triggered) | New-plan acceptance | Strategic | 3/3 | **No** — convened only after a confirmed divergence |
| Work | Completion verification (success criteria honestly met) | Strategic | 3/3 | **No** — independent check on the main LLM's self-assessment |
| Review | Per-finding triage (single panel call for all findings) | Tactical | 2/3 | Only if all findings are low-severity (any medium+ → panel) |
| Review | Replan-vs-FIX (only if load-bearing finding surfaces) | Strategic | 2/3 | **No** — precondition is a surfaced load-bearing finding |
| Promote | Three-way partition (PROMOTE/MERGE/DISCARD/TODO) | Tactical | 2/3 | Only if every entry is unambiguous (e.g., all DISCARD-noise) |
| Promote | TODO disposition | Tactical | 2/3 | Only if a single unambiguous disposition |
| Ship | Commit message | Operational | No panel (main LLM accepts draft) | n/a — already main-LLM |
| Ship | PR title + body | Operational | No panel (main LLM accepts draft) | n/a — already main-LLM |
| Ship | CI auto-fix classification | Tactical | No panel (`ship`'s classifier handles it) | n/a — `ship`'s classifier |
| Cleanup gate | PR state polling + cleanup | n/a | No panel | n/a |

## Phase 1 — Propose (inline)

This phase replaces the user-interactive intake in `minerva:propose`.

1. **Assemble context.** Read: inline description, current chat history, `CLAUDE.md`/`AGENTS.md`, `.minerva/knowledge/` entries (at minimum `Type: pattern` and `Type: constraint`), the 2-3 most recent `.minerva/work/NNN-*/proposal.md` files for tone and conventions, and any `followups.md` whose entries could be adjacent.

2. **Design synthesis.** The main LLM drafts a complete proposal (Goal / Why / Approach / Success criteria / Open Questions) along with 2-3 candidate approaches it considered. This is the strategic intake — context-grounded inference rather than user Q&A. Keep it in conversation; do not write any file yet.

3. **Scope-check panel.** Dispatch panel with artifact = "is this a single work unit, or should it decompose into multiple?". On `≤1/3 accept` after revision, escalate with the sub-units the Skeptic identified as options. If user picks "decompose", abort the auto run cleanly: "scope check escalated to decomposition — re-run with one sub-unit at a time."

4. **Approach-selection panel.** Dispatch panel with artifact = the 2-3 candidate approaches + the recommended one. On consensus, the picked approach replaces the draft's `## Approach` section. On escalation, ask the user to pick.

5. **Whole-proposal-acceptance panel.** Dispatch panel with artifact = the full Goal/Why/Approach/Success-criteria/Open-Questions draft (post step 4). On `accept`, the draft is final. On revision-round failure, escalate with the Skeptic's top 1-3 concerns as a batched question.

6. **Worktree + branch creation.** Identical to `minerva:propose`'s "On approval — worktree setup + file writes" section, steps 1–7:
   - Derive slug, check duplicates, compute NNN across local work / local branches / remote branches.
   - Resolve default branch.
   - Pre-flight gitignore check on `.minerva/worktrees/` — abort to user if missing.
   - `git worktree add -b <NNN-slug> .minerva/worktrees/<NNN-slug> <default-branch>`.
   - `EnterWorktree` with `path: ".minerva/worktrees/<NNN-slug>"`.

7. **File writes (inside the worktree).** Identical to `minerva:propose` steps 8–9, 11:
   - Create `.minerva/work/<NNN-slug>/`.
   - Write `proposal.md` with the approved content per the template in `minerva:propose` step 9.
   - Write `scratchpad.md` with the header-only template from `minerva:propose` step 9.
   - Append the initial `## Panel decisions YYYY-MM-DD` block to `scratchpad.md` with the votes from steps 3–5.
   - `git add` the work-unit directory; commit `chore: initialize <NNN-slug> work unit`.

8. **Self-review.** Re-read `proposal.md` with fresh eyes per `minerva:propose` step 10 (placeholders, internal consistency, ambiguity, scope). Fix inline. **No post-write user gate** — the whole-proposal-acceptance panel already covered that role.

9. Continue to Phase 2.

## Phase 2 — Work (inline)

This phase replaces the user-interactive setup and completion signal in `minerva:work`. Implementation work itself is unchanged — the main LLM writes code as normal, maintains `scratchpad.md` per `minerva:work`'s implementation protocol.

1. **Setup.** Already inside the worktree from Phase 1. Read `proposal.md` and any `replan.md` entries (none on first pass). Skip the user-facing "resolve open questions" step — the proposal-acceptance panel already addressed open questions during whole-proposal review; any that remain are deferred deliberately and surface in the final report.

2. **Implementation loop.** Main LLM implements per `minerva:work`'s "Implementation protocol" section: scratchpad maintenance, divergence detection. **No upper bound on implementation time** — the auto skill doesn't cap coding work.

3. **Divergence detection.** When the main LLM notices what looks like a load-bearing divergence (a core assumption broke, the approach is shifting, scope is shifting), trigger the **divergence panel**: artifact = "is this divergence load-bearing enough to warrant a replan?". On `2/3 accept`, proceed to replan ([Phase 2.5](#phase-25--replan-inline-if-triggered)). On `≤1/3 accept`, continue implementing without replan — the panel determined the divergence was a routine choice. On escalation, ask the user.

4. **Completion verification.** When the main LLM judges that every `## Success criteria` item appears met:
   - Compose a checklist: each criterion, the evidence (test name, file path, behavior observed), and a yes/no.
   - Dispatch the **completion-verification panel**: artifact = the checklist + the latest diff (`git diff <default>...HEAD`). The panel votes on whether each criterion is honestly checkable.
   - On `3/3 accept`, advance to Phase 3.
   - On `≤1/3 accept`, this is treated as a **success-criteria divergence**, not a regular consensus failure — auto-trigger Phase 2.5 (replan) to clarify the criteria, then resume implementation. Skip the standard revise-and-revote.
   - On `2/3 accept`, proceed but log dissent concerns to scratchpad for the review phase to scrutinize.

## Phase 2.5 — Replan (inline, if triggered)

Mirrors `minerva:replan`'s protocol with panel-based acceptance.

1. Already inside the worktree. Read `proposal.md`, prior `replan.md` entries, current `scratchpad.md`.

2. **Frame the replan** around the three pieces: Original plan / What changed / New plan. The main LLM drafts all three.

3. **New-plan-acceptance panel.** Artifact = the full replan entry draft + the proposal's current `## Approach` for comparison. On `3/3 accept`, write. On revision-round failure, escalate.

4. **Write.** Append the entry to `replan.md` per `minerva:replan`'s "On approval — file write" section. If the new plan changes success criteria, also edit `proposal.md`'s `## Success criteria` section.

5. Return control to Phase 2 (or Phase 3 if replan was triggered from review).

## Phase 3 — Review (inline)

Replaces the user-interactive triage in `minerva:review`. Diff resolution and finding generation can still delegate to `code-review:code-review` for PR-mode, but the triage is panel-driven.

1. **Read context.** `proposal.md`, all `replan.md` entries, current `scratchpad.md` (including prior `## Review triage YYYY-MM-DD` blocks), `followups.md`, and relevant `.minerva/knowledge/` entries.

2. **Diff resolution.** Same as `minerva:review`'s "Diff resolution" section.

3. **Generate findings.** Two passes:
   - **Minerva audit** (inline): spec fidelity (does the diff achieve `## Goal`, `## Approach`, `## Success criteria`?) + knowledge compliance (does the diff violate any documented pattern/constraint/decision?).
   - **Code review**: if a PR exists for this branch, invoke `code-review:code-review` via the `Skill` tool. Otherwise, perform the inline structured code review per `minerva:review`'s "Code review invocation" section.

4. **Triage panel.** Single panel call for the full set of numbered findings. Artifact = the findings list + proposed dispositions (default: high → FIX, medium → SUGGEST, low → IGNORE). Each panel agent reviews the disposition for every finding and votes on the set as a whole. On `2/3 accept`, apply dispositions. On `≤1/3 accept`, revise (the main LLM adjusts dispositions per Skeptic critique) and re-vote. On revision-round failure, escalate with the contested findings.

5. **Replan-vs-FIX check.** If any FIX finding reveals a load-bearing divergence (per `minerva:review`'s "Load-bearing divergence" heuristic), dispatch a **replan-vs-FIX panel** with that finding's context. On `2/3 accept for replan`, persist current triage state to scratchpad per `minerva:review`'s "Triage persistence" section, then trigger [Phase 2.5](#phase-25--replan-inline-if-triggered). After replan completes, return to step 4 (re-run triage).

6. **Apply dispositions.** Per `minerva:review`'s "On approval — file writes" section. FIX items get edited directly; SUGGEST items append to scratchpad under `## Review finding YYYY-MM-DD`; IGNORE items optional.

7. Continue to Phase 4.

## Phase 4 — Promote (inline)

Replaces the user-interactive partition in `minerva:promote` Mode A.

1. **Already inside the worktree.** Read `proposal.md`, `scratchpad.md`, `replan.md` if present.

2. **Idempotency check.** If `scratchpad.md` is the one-line promote marker, report "already promoted" and continue to Phase 5.

3. **Partition draft.** The main LLM proposes a four-way partition per `minerva:promote` Mode A step 3: PROMOTE / MERGE INTO PROPOSAL / DISCARD / TODO. Skip entries already marked `→ promoted to ...`.

4. **Partition panel.** Artifact = the full partition with one-line justifications per entry. On `2/3 accept`, apply. On revision-round failure, escalate with the contested entries.

5. **TODO disposition panel.** Only if any entries landed in the TODO bucket. Artifact = each TODO with a proposed disposition (followups.md / seed new proposal / discard). On `2/3 accept`, apply. On revision-round failure, escalate.

6. **Apply writes.** Per `minerva:promote` Mode A step 7: write PROMOTE items as `.minerva/knowledge/NNN-<type>-<slug>.md` using the knowledge entry template; rewrite `proposal.md`'s `## Approach` (and Status to `Shipped (YYYY-MM-DD)`); apply TODO dispositions; archive the scratchpad and write the one-line promote marker.

7. **TODO seed gate (if any).** If any TODO was marked "seed new proposal", do **not** auto-invoke `minerva:propose` in the same run — surface the list in the final report as suggested follow-up work units. Auto mode does not cascade into new auto runs without explicit user direction.

8. Continue to Phase 5.

## Phase 5 — Ship gate

There is no gate. The `promote → ship` confirmation that `minerva:propose-ship` requires is replaced by silent advancement. If the completion-verification panel in Phase 2 voted with full consensus and the review + promote panels also accepted, the auto skill trusts those signals and proceeds.

If the global escalation counter has reached 3 by this point, halt instead of shipping (see [Failure modes](#failure-modes-escalation-budget-caps)).

## Phase 6 — Ship (delegated)

Invoke `minerva:ship` via the `Skill` tool. Before invoking, lead with this auto-mode instruction:

> "You are running inside `minerva:propose-ship-auto`. When `minerva:ship` reaches Hard gate #1 (commit message) and Hard gate #2 (PR title + body), accept the drafted content without prompting the user. All other `minerva:ship` behavior — pre-flight, branch creation, push, PR creation, CI watch loop, auto-merge — is unchanged."

These two gates are operational tier and don't warrant panel calls — the main LLM's draft from `proposal.md` is good enough by definition.

If `minerva:ship`'s CI auto-fix classifier marks a failure as `other` or bails on a non-trivial test/build, **do not panel-vote on the bail** — escalate to the user with the failing job log. This is a hard escalation trigger.

## Phase 7 — Cleanup gate

Identical to `minerva:propose-ship`'s Phase 7. After `minerva:ship` returns:

1. `gh pr view <branch> --json state,mergedAt 2>/dev/null`.
2. **`MERGED`** → invoke `minerva:cleanup <NNN-slug> --yes` via the `Skill` tool. Report and exit.
3. **`OPEN`, auto-merge enabled** → `ScheduleWakeup` with `delaySeconds: 300`, `prompt: minerva:propose-ship-auto --cleanup-only <NNN-slug> --retry=N`. Cap retries at 12. On exhaustion, surface manual instructions.
4. **`OPEN`, auto-merge declined** → surface manual cleanup instructions; do not schedule wake-up.
5. **`CLOSED` (not merged)** → leave worktree in place; surface manual cleanup instructions.
6. **No PR found** → exit silently (ship must have bailed before opening one — already reported above).

When re-entered via `--cleanup-only`, skip phases 1–6 and re-run this phase directly.

## Failure modes, escalation, budget caps

**Per-decision budget.** Hard cap: one initial vote + one revision vote per decision. 6 subagent dispatches max per decision point.

**Per-phase abort triggers.**
- Propose phase: if 2 of the 3 propose-phase panels (scope, approach, whole-proposal) escalate, abort the auto run. The strategic intent is too ambiguous for panel-driven decisions. Recommend: "switch to manual `minerva:propose`."

**Global escalation counter.** Maintain across the run. Increment on every user escalation. If it reaches **3**, halt before the next panel call and report status. Recovery: run individual minerva skills manually from the current state.

**Hard escalation triggers (skip the panel entirely).**
- In-flight work collision (pre-flight).
- Worktree creation failure (git error, gitignore missing, slug collision).
- Ship-phase failures classified as `other`, push rejection, `gh` auth failure.
- Global escalation counter reaching 3.

**Final report on bail.**
- Phase reached.
- Reason for bail (escalation count / hard trigger / CI failure).
- Current state of `.minerva/work/<NNN-slug>/` (proposal status, scratchpad summary, committed state).
- Exact next manual command (e.g., `minerva:work <NNN-slug>`, `minerva:ship <NNN-slug>`).

## Observability

- Every panel call logs one line to `scratchpad.md` under a `## Panel decisions YYYY-MM-DD` header per the [Per-decision logging](#per-decision-logging) section.
- Escalations log under the same header with `[escalated to user]` and a one-line summary of what was asked.
- The final report (success or bail) lists total panel calls and total escalations for the run.

## Out of scope

- **Modifying any existing minerva skill.** The auto skill is purely additive. `minerva:propose`, `minerva:work`, `minerva:review`, `minerva:promote`, `minerva:replan`, `minerva:ship`, and `minerva:cleanup` are unchanged.
- **Auto-cascading into new work units.** If Phase 4 surfaces TODOs marked "seed new proposal", they are reported as suggestions — the auto skill does not invoke `minerva:propose-ship-auto` recursively in the same run.
- **Capping implementation time.** Phase 2's implementation loop has no time or token bound. If the user wants to cap, they interrupt manually.
- **Strict ordering of review and promote.** Same as the canonical lifecycle — review runs before promote so review-derived scratchpad notes flow through the promote partition. If review triggers a replan, Phase 3 cycles back to Phase 2; promote runs after the next review pass.
- **A configurable quorum.** The 3/3 vs. 2/3 quorums per decision type are fixed (see [Decision taxonomy](#decision-taxonomy)). If a user wants different thresholds, they fork the skill.
