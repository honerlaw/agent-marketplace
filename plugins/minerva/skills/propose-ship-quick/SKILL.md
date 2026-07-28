---
name: propose-ship-quick
description: Runs the full minerva lifecycle end-to-end fast for a small, low-risk change — a small UI fix, a bug fix, a one-file tweak ("just ship this small fix", "quick propose and ship", "do the whole thing quickly"). Same lifecycle as `minerva:propose-ship-auto` (propose - work - review - promote - synthesize - ship - cleanup) with no scheduled human gates, but the main model adjudicates every strategic/tactical decision directly — no panels. User input is an exceptional fail-closed fallback (real ambiguity, high blast radius, an unfamiliar public interface, a knowledge constraint). If the change proves larger than small, it escalates recommending `minerva:propose-ship-balanced` (one reviewer), `minerva:propose-ship-auto` (panels), or `minerva:propose-ship` (human gates). Use for small low-risk end-to-end changes, or when the user invokes `minerva:propose-ship-quick`.
---

Run the full minerva lifecycle end-to-end with **main-model decisions** in place of human gates. This skill is the lightweight fast-path sibling of `minerva:propose-ship-auto`: same phases, same delegations, but where `propose-ship-auto` convenes a consensus panel, **the main model decides directly**. It is a **hybrid orchestrator** — it delegates to `minerva:synthesize` (Phase 4.5, self-gating), `minerva:ship`, and `minerva:cleanup` directly, and inlines the propose / work / review / promote / replan phases so the main model can adjudicate them inline.

The four orchestrators form a ladder by adjudication cost: `minerva:propose-ship` (human gates) · `minerva:propose-ship-quick` (main model decides) · `minerva:propose-ship-balanced` (one advisory reviewer) · `minerva:propose-ship-auto` (consensus panels). Reach for **quick** when the change is genuinely small and the main model's own judgment is enough; reach for **auto** when the work is ambiguous or high-stakes enough to want independent agents arguing it out.

The mechanism: at each strategic or tactical decision point, the main model **decides directly and fast**, grounded in context. Operational decisions (commit messages, PR bodies, file paths) are executed without ceremony, exactly as in `propose-ship-auto`. The escalation path is preserved: a fail-closed **escalation predicate** sends genuinely-undecidable decisions to the user, and never elides the post-divergence or completion-verification self-checks.

## Usage

- `minerva:propose-ship-quick "fix the off-by-one in the date picker"` — start a new quick run with the inline description as the seed.
- `minerva:propose-ship-quick` — start with current-session chat context as the seed (only sensible if the chat already discussed what to build).
- `minerva:propose-ship-quick --cleanup-only <NNN-slug> --retry=N` — internal re-entry from the cleanup-gate wake-up loop. Skips phases 1–6 and re-runs Phase 7.

## Pre-flight: in-flight work collision

Identical to `minerva:propose-ship`'s pre-flight. This check is **not** main-model-decided — a wrong call here destroys real work, so escalation to the user is hardcoded:

1. List `.minerva/work/NNN-*/` plus `.minerva/worktrees/NNN-*/.minerva/work/NNN-*/`.
2. If any unit has a `proposal.md` whose `## Status` is `Draft` or whose scratchpad is **not** the post-promote marker, treat it as in-flight.
3. If the seed overlaps a slug or goal, **stop and ask**:
   > "Found in-flight work unit `005-add-payments` — looks related. Resume that one (`minerva:work 005-add-payments`) or genuinely start fresh?"

Only proceed after the user confirms. This is the single mandatory — and **only guaranteed** — pre-run user interaction; everything else reaches the user only via the escalation predicate.

## Solo-decision protocol

The full policy — the **default** (main model decides), the fail-closed **escalation predicate**, the **scope-fit escape**, the **never-bypassed self-checks**, the **hardcoded escalation triggers**, the **escalation counter**, and **per-decision logging** — lives in `references/solo-decision-protocol.md`. **Read that file once, in full, before this run's first strategic/tactical decision point**; its rules then apply to every decision that follows.

Binding floor, even before the reference is read:

- The main model **decides each strategic/tactical decision directly**. It does **not** convene a `minerva:round-table` panel — that is the whole point of this skill, and the one behavior that distinguishes it from `propose-ship-auto`.
- Before deciding, the main model applies the **escalation predicate** silently per-decision. It **fails closed to the user**: on genuine ambiguity (no dominant option after honest analysis), high blast-radius / irreversibility, an unfamiliar public interface or cross-cutting contract, a conflicting `.minerva/knowledge/` constraint — it escalates instead of guessing.
- **Never elided:** completion verification, mid-work divergence confirmation, new-plan acceptance (replan), and every hardcoded escalation trigger. These are run as rigorous main-model self-checks regardless of how small the change looks; the model escalates on genuine uncertainty rather than rubber-stamping its own work.
- **Scope-fit escape:** if the change proves not small (scope explosion, deep complexity), escalate recommending a switch to `propose-ship-balanced` (one reviewer), `propose-ship-auto` (panels), or `propose-ship` (human gates).
- Every decision, escalation, and synthesis outcome logs one line to the work unit's `scratchpad.md` under a `## Quick decisions YYYY-MM-DD` header (`[decided]` / `[escalated to user]` / `[synthesis]`).

## Phases

Execute the phases in order. The full inline protocols live in `references/phases.md`. **Before executing each phase, read that phase's section there**; the map below locates the work, it is not the protocol:

1. **Propose (inline)** — assemble context → design synthesis → the main model decides scope, approach, and whole-proposal soundness (escalating on genuine uncertainty) → worktree + branch + file writes per `minerva:propose` → self-review.
2. **Work (inline)** — implement per `minerva:work`'s protocol; on a suspected load-bearing divergence the main model confirms it itself (escalate if unsure); completion-verification self-check on the success-criteria checklist + diff.
   - **2.5 Replan (inline, if triggered)** — draft Original plan / What changed / New plan; the main model accepts the new plan (escalate if unsure); append to `replan.md`.
3. **Review (inline)** — minerva audit + code review (PR mode delegates to `code-review:code-review`); the main model triages all findings; replan-vs-FIX decided by the main model if a load-bearing finding surfaces.
4. **Promote (inline)** — the main model partitions PROMOTE/MERGE/DISCARD/TODO and disposes TODOs; apply writes per `minerva:promote` Mode A; archive scratchpad.
   - **4.5 Synthesis (delegated, self-gating)** — invoke `minerva:synthesize` via the `Skill` tool with its auto-mode instruction (auto-accept the write gate only; its Step-2 self-gate is unchanged). Log the `[synthesis]` outcome line; if it wrote, ship must stage `.minerva/knowledge/overview.md` and note the refresh in the PR body.
5. **Ship gate** — no gate: silent advancement, except halt if the global escalation counter has reached 3.
6. **Ship (delegated)** — invoke `minerva:ship` via the `Skill` tool with its auto-mode instruction (auto-accept hard gates #1 commit message and #2 PR title/body; everything else unchanged). CI auto-fix bails classified `other` are escalated to the user — never silently decided.
7. **Cleanup gate** — poll PR state via `gh pr view`; on `MERGED` invoke `minerva:cleanup` via the `Skill` tool with args `<NNN-slug> --yes`; on `OPEN` with auto-merge, `ScheduleWakeup` re-entry (`--cleanup-only <NNN-slug> --retry=N`, cap 12, delay sized per ship); otherwise surface manual instructions.

## Failure modes, escalation, budget caps

Binding caps: **propose-phase abort** when the propose-phase decisions escalate to the point the strategic intent is too ambiguous for the main model to resolve; **global escalation counter** halts the run at **3**. Hard escalation triggers that skip the main model's judgment entirely: in-flight collision, worktree-creation failure, ship-phase failures (`other` classification, push rejection, `gh` auth failure), counter at 3. The full trigger list, final-report-on-bail format, and observability requirements live in `references/governance.md` — read it at the first escalation or before reporting any bail.

## Out of scope

Never modify any existing minerva skill at run time (this skill orchestrates by *invocation only*); never auto-cascade into new work units; never cap implementation time; review/promote ordering is fixed. This skill never convenes a `minerva:round-table` panel. Rationale and detail: `references/governance.md`.
