---
name: propose-ship-auto
description: Runs the full minerva lifecycle end-to-end with no human gates — fully automated, for unattended runs ("do the whole thing without asking", "handle decisions yourself", "auto propose and ship"). Same lifecycle as `minerva:propose-ship` (propose - work - review - promote - synthesize - ship - cleanup, where the self-gating `minerva:synthesize` step refreshes the knowledge-wiki overview when promote added scope), but replaces each human-facing decision with a 3-agent Proponent/Skeptic/Arbiter consensus panel (mechanics delegated to `minerva:round-table`). Human input is only a fallback when a panel can't agree after one revision round, and a fail-closed skip predicate lets genuinely small decisions run panel-free. Use for non-trivial changes the user wants shipped autonomously, or when they invoke `minerva:propose-ship-auto`.
---

Run the full minerva lifecycle end-to-end with consensus-panel decisions in place of human gates. This skill is a **hybrid orchestrator** — it delegates to `minerva:synthesize` (Phase 4.5, self-gating), `minerva:ship`, and `minerva:cleanup` directly (those phases have no strategic gates) but inlines the propose / work / review / promote / replan phases so it can substitute panel calls for hard user gates.

The mechanism: at each strategic or tactical decision point, dispatch a 3-agent Proponent/Skeptic/Arbiter panel of fresh-context subagents — the panel mechanics live in `minerva:round-table`, to which this skill delegates (see the Delegation section of `references/panel-protocol.md`). Operational decisions (commit messages, PR bodies, file paths) bypass the panel entirely — the main LLM executes them. For **small, low-risk decisions**, a Skip predicate (`references/panel-protocol.md`) lets the main LLM decide directly without convening a panel — so a genuinely small task runs effectively panel-free — while it fails closed to the full panel on any uncertainty and never skips the post-divergence or completion-verification panels.

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

Only proceed after the user confirms. This is the single mandatory — and **only permitted** — pre-run user interaction (see No ceremony ratification in `references/panel-protocol.md`).

## Panel protocol

The full panel-protocol policy — the **Skip predicate (small decisions)**, **No ceremony ratification**, **Delegation to `minerva:round-table`**, and **Per-decision logging** (formats and worked examples) — lives in `references/panel-protocol.md`. **Read that file once, in full, before this run's first strategic/tactical decision point**; its rules then apply to every decision that follows.

Binding floor, even before the reference is read:

- The conjunctive skip predicate is applied silently per-decision, only where the **Decision taxonomy** row (in `references/panel-protocol.md`) is skippable, and **fails closed** to a panel on any uncertainty. It is the only de-ceremony mechanism — never ask the user to pre-ratify skips or pick a "ceremony level".
- **Never-skippable:** completion verification, mid-work divergence confirmation, new-plan acceptance (replan), Replan-vs-FIX, and every hardcoded escalation trigger.
- Panel mechanics (dispatch, Proponent/Skeptic/Arbiter briefs, votes, revision round, escalation composition) are delegated to `minerva:round-table` in caller mode; quorums always come from the Decision taxonomy (in `references/panel-protocol.md`), never round-table's standalone default.
- Every panel call, predicate skip (`[skipped — small]` + evidence), user-directed bypass (`[user-directed]`), and synthesis outcome (`[synthesis]`) logs one line to `scratchpad.md` under `## Panel decisions YYYY-MM-DD`.

## Phases

Execute the phases in order. The full inline protocols — panel artifacts, vote handling, escalation aftermath, and file-write steps — live in `references/phases.md`. **Before executing each phase, read that phase's section there**; the map below locates the work, it is not the protocol:

1. **Propose (inline)** — assemble context → design synthesis → scope-check panel (3/3) → approach-selection panel (3/3) → whole-proposal-acceptance panel (3/3) → worktree + branch + file writes per `minerva:propose` → self-review. No post-write user gate.
2. **Work (inline)** — implement per `minerva:work`'s protocol; divergence panel (2/3) when a load-bearing divergence is suspected; completion-verification panel (3/3) on the success-criteria checklist + diff.
   - **2.5 Replan (inline, if triggered)** — draft Original plan / What changed / New plan; new-plan-acceptance panel (3/3); append to `replan.md`.
3. **Review (inline)** — minerva audit + code review (PR mode delegates to `code-review:code-review`); single triage panel (2/3) over all findings; replan-vs-FIX panel (2/3) if a load-bearing finding surfaces.
4. **Promote (inline)** — partition panel (2/3); TODO-disposition panel (2/3); apply writes per `minerva:promote` Mode A; archive scratchpad.
   - **4.5 Synthesis (delegated, self-gating)** — invoke `minerva:synthesize` via the `Skill` tool with its auto-mode instruction (auto-accept the write gate only; the Step-2 self-gate is unchanged). Log the `[synthesis]` outcome line; if it wrote, ship must stage `.minerva/knowledge/overview.md` and note the refresh in the PR body.
5. **Ship gate** — no gate: silent advancement, except halt if the global escalation counter has reached 3.
6. **Ship (delegated)** — invoke `minerva:ship` via the `Skill` tool with its auto-mode instruction (auto-accept hard gates #1 commit message and #2 PR title/body; everything else unchanged). CI auto-fix bails classified `other` are escalated to the user — never panel-voted.
7. **Cleanup gate** — poll PR state via `gh pr view`; on `MERGED` invoke `minerva:cleanup` via the `Skill` tool with args `<NNN-slug> --yes`; on `OPEN` with auto-merge, `ScheduleWakeup` re-entry (`--cleanup-only <NNN-slug> --retry=N`, cap 12, delay sized per ship); otherwise surface manual instructions.

## Failure modes, escalation, budget caps

Binding caps: **one initial vote + one revision vote per decision** (6 subagent dispatches max); **propose-phase abort** when 2 of its 3 panels escalate; **global escalation counter** halts the run at **3**. Hard escalation triggers that skip the panel entirely: in-flight collision, worktree-creation failure, ship-phase failures (`other` classification, push rejection, `gh` auth failure), counter at 3. The full trigger list, final-report-on-bail format, and observability requirements live in `references/governance.md` — read it at the first escalation or before reporting any bail.

## Out of scope

Never modify any existing minerva skill at run time (this skill orchestrates by *invocation only*); never auto-cascade into new work units; never cap implementation time; review/promote ordering is fixed; quorums are not configurable. Rationale and detail: `references/governance.md`.
