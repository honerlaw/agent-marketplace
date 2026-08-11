---
name: propose-ship-balanced
description: Runs the full minerva lifecycle end-to-end for a MEDIUM change — bigger than a one-file tweak, not ambiguous or high-stakes enough for panels ("ship this with a second opinion", "sanity-check the approach", "one reviewer, not a committee", a multi-file refactor). The middle rung of the autonomous ladder — third of four overall — between `minerva:propose-ship-quick` (solo) and `minerva:propose-ship-auto` (panels) — the main model decides directly but dispatches a SINGLE fresh-context advisory reviewer at the high-signal gates (scope check, approach selection, completion verification, plus the rare never-elide gates) and arbitrates the critique inline — no panel, no revision round. User input is only a fail-closed fallback; if the change proves larger it escalates recommending `minerva:propose-ship-auto` or `minerva:propose-ship`. Use for autonomous medium-sized changes that warrant one independent check, or when the user invokes `minerva:propose-ship-balanced`.
---

Run the full minerva lifecycle end-to-end with **main-model decisions plus a single independent reviewer at the high-signal gates** in place of human gates. This skill is the **middle rung** between `minerva:propose-ship-quick` (main model decides every gate solo) and `minerva:propose-ship-auto` (a 3-agent `minerva:round-table` panel at every gate). Like both, it is a **hybrid orchestrator**: it delegates to `minerva:ship` and `minerva:cleanup`, and inlines the propose / work / review / promote / replan phases.

The four orchestrators form a ladder by adjudication cost: `minerva:propose-ship` (human gates) · `minerva:propose-ship-quick` (main model solo) · `minerva:propose-ship-balanced` (one reviewer at high-signal gates) · `minerva:propose-ship-auto` (consensus panels). Reach for **balanced** when the change is bigger than a one-file fix and you want independent eyes on the load-bearing calls — scope, approach, and "is it really done" — without paying for 3-agent consensus everywhere.

## Usage

- `minerva:propose-ship-balanced "extract the auth middleware into its own module"` — start a new balanced run with the inline description as the seed.
- `minerva:propose-ship-balanced` — start with current-session chat context as the seed (only sensible if the chat already discussed what to build).
- `minerva:propose-ship-balanced --cleanup-only <date-slug> --retry=N` — internal re-entry from the cleanup wake-up loop; skips phases 1–6 and re-runs Phase 7.

## Pre-flight: in-flight work collision

Identical to `minerva:propose-ship`'s pre-flight. This check is **not** main-model-decided — a wrong call here destroys real work, so escalation to the user is hardcoded:

1. List `.minerva/work/*/` plus `.minerva/worktrees/*/.minerva/work/*/`.
2. If any unit has a `proposal.md` that `work_status` reports as in-flight, treat it as in-flight:

   ```bash
   python3 -c "import sys; sys.path.insert(0, '<scripts>'); from work_status import unit_state; print(unit_state('.minerva/work/<date-slug>')['in_flight'])"
   ```

   `in_flight` is `Status is Draft` **or** not promoted. Call it — do not restate it as a
   string comparison: the promote marker has eight spellings in this corpus and `Status`
   has two, and matching one spelling of either reads a finished unit as live work.
3. If the seed overlaps a slug or goal, **stop and ask** whether to resume that unit (`minerva:work <date-slug>`) or start fresh.

Only proceed after the user confirms. This is the only mandatory pre-run user interaction; everything else reaches the user via escalation.

## Verify protocol

The full policy — the **default** (main model decides), the **fixed reviewer-gate taxonomy**, the **single-reviewer mechanism** (decide-first, one dispatch, no re-dispatch), the **inline arbitration + behavioral "load-bearing critique" threshold** with its **anti-circularity escape**, the **Verifier brief** and **Skeptic brief**, the fail-closed **escalation predicate**, the **scope-fit escape**, the **never-bypassed self-checks**, the **hardcoded escalation triggers**, the **escalation counter**, and **per-decision logging** — lives in `references/verify-protocol.md`. **Read it once, in full, before this run's first decision point**; its rules then apply to every decision.

Binding floor, even before the reference is read:

- The main model **decides each strategic/tactical decision directly**, as in `propose-ship-quick`. It does **not** convene a `minerva:round-table` panel — that is `propose-ship-auto`'s mechanism.
- At the **fixed reviewer gates** — scope check, approach selection, completion-verification (every run), plus mid-work divergence / replan-acceptance / replan-vs-FIX (only when triggered) — after deciding, the main model dispatches **one** fresh-context agent (`subagent_type: general-purpose`, `model: sonnet`, `run_in_background: false`): a **Skeptic** at scope/approach/divergence/replan, a **Verifier** at completion. It arbitrates the critique inline (fold load-bearing points or escalate), **no** re-dispatch (one dispatch per gate). All other gates (whole-proposal soundness, review triage, promote partition, TODO disposition) are decided **solo**.
- Before committing any decision (including how to act on a reviewer critique) the main model applies the fail-closed **escalation predicate**: on genuine ambiguity (no dominant option, or a critique it cannot confidently adjudicate), high blast-radius / irreversibility, an unfamiliar public interface or cross-cutting contract, a conflicting `.minerva/knowledge/` constraint — or any real doubt — it escalates rather than guess or self-confirm.
- **Never elided:** completion verification, mid-work divergence confirmation, new-plan acceptance — run as reviewer gates however small the change looks. **Scope-fit escape:** if the change proves larger, escalate recommending `propose-ship-auto`/`propose-ship`.
- Every decision logs one line to `scratchpad.md` under a `## Balanced decisions YYYY-MM-DD` header (`[decided]` / `[reviewed — folded]` / `[reviewed — clean]` / `[escalated to user]`).

## Phases

Execute the phases in order. The full inline protocols live in `references/phases.md`. **Before executing each phase, read that phase's section there**; the map below locates the work, it is not the protocol:

1. **Propose (inline)** — assemble context → design synthesis → scope (reviewer gate), approach (reviewer gate), whole-proposal soundness (solo) → worktree + branch + file writes per `minerva:propose` → self-review.
2. **Work (inline)** — implement per `minerva:work`; suspected load-bearing divergence is a reviewer gate; completion-verification reviewer gate on the success-criteria checklist + diff.
   - **2.5 Replan (inline, if triggered)** — draft Original plan / What changed / New plan; new-plan acceptance is a reviewer gate; append to `replan.md`.
3. **Review (inline)** — minerva audit + code review (PR mode delegates to `code-review:code-review`); the main model triages all findings solo; replan-vs-FIX is a reviewer gate if a load-bearing finding surfaces.
4. **Promote (inline)** — the main model partitions PROMOTE/MERGE/DISCARD/TODO and disposes TODOs solo; apply writes per `minerva:promote` Mode A; archive scratchpad.
5. **Ship gate** — no gate: silent advancement, except halt if the escalation counter reached 3.
6. **Ship (delegated)** — invoke `minerva:ship` via the `Skill` tool with its auto-mode instruction (auto-accept hard gates #1 commit message and #2 PR title/body; everything else unchanged). CI auto-fix bails classified `other` are escalated to the user — never silently decided.
7. **Cleanup gate** — poll PR state via `gh pr view`; on `MERGED` invoke `minerva:cleanup` via the `Skill` tool with args `<date-slug> --yes`; on `OPEN` with auto-merge, `ScheduleWakeup` re-entry (`--cleanup-only <date-slug> --retry=N`, cap 12); otherwise surface manual instructions.

## Failure modes, escalation, budget caps

Binding caps: **one reviewer dispatch per reviewer gate**; **propose-phase abort** when the strategic intent is too ambiguous to resolve; **global escalation counter** halts the run at **3**. Hard escalation triggers (skip the main model's judgment): in-flight collision, worktree-creation failure, ship-phase `other`/push-rejection/`gh`-auth failure, counter at 3. The full trigger list, final-report-on-bail format, and observability requirements live in `references/governance.md` — read it at the first escalation or before reporting any bail.

## Out of scope

Never modify any existing minerva skill at run time (orchestrate by *invocation only*); never auto-cascade into new work units; never cap implementation time; review/promote ordering is fixed. This skill never convenes a 3-agent `minerva:round-table` panel — its independent review is a single advisory reviewer arbitrated by the main model. Rationale and detail: `references/governance.md`.
