# Solo-decision protocol — full policy

Read once, in full, before the run's first strategic/tactical decision point. Its rules then apply to every decision that follows.

This is `propose-ship-quick`'s analog of `propose-ship-auto`'s panel protocol. Where `propose-ship-auto` convenes a 3-agent `minerva:round-table` panel, here **the main model decides directly**. The escalation path to the user is preserved — it is just reached by a fail-closed predicate instead of a failed panel vote.

## Default — the main model decides

At each strategic/tactical decision point (see the [Decision taxonomy](#decision-taxonomy)), the main model **decides directly**, fast, grounded in the run's context: the proposal, the diff, `CLAUDE.md`/`AGENTS.md`, and any `.minerva/knowledge/` entries already cited this session. It does **not** convene a panel. Operational decisions (commit messages, PR bodies, file paths) are executed without any decision ceremony, exactly as in `propose-ship-auto`.

This is the *common* path. A genuinely small change — the kind this skill targets — runs to completion with the main model deciding every point and the user never touched.

## Escalation predicate

Before committing to any decision, the main model applies an explicit test to *that specific decision*. It is the structural mirror of `propose-ship-auto`'s skip predicate, but **fail-closed in the opposite direction**: auto's predicate is fail-open toward deciding-without-a-panel (skip only if every clause holds); this predicate governs **decide-vs-escalate**.

**Decide directly only if you are confident on all of these. Escalate to the user if any holds — or if you are unsure whether it holds:**

- **genuine ambiguity** — after honestly enumerating the viable options, no option is dominant on the stated criteria (a coin-flip between materially different paths is the user's call, not yours);
- **high blast-radius / irreversible** — the decision is hard to walk back, or its surface is broad rather than bounded;
- **unfamiliar public interface or cross-cutting contract** — it introduces or changes a public interface, API, or cross-cutting contract you cannot confidently get right alone;
- **knowledge conflict** — it would violate or sits in tension with a documented `.minerva/knowledge/` constraint.

**Fails closed.** If any single clause holds, or you cannot honestly rule it out, **escalate** — compose a focused, multiple-choice question with `AskUserQuestion`, apply the user's answer as the decision, and continue. The predicate only ever decides *whether to escalate*; deciding directly is never the safe default under doubt. Because deciding-alone requires confidence on every clause, the worst case of a wrong escalation is one extra question; the worst case of a wrong decide-alone is an undetected bad call on an ambiguous or high-blast-radius decision — so the asymmetry favors escalation.

This is the inverse posture of `propose-ship-auto`: there, the *panel* is the default and the skip predicate is the (fail-closed) exception; here, *deciding alone* is the default and escalation is the (fail-closed) exception. Both fail toward the more conservative reviewer.

## Scope-fit escape

This skill is for small, low-risk changes. If, at any point, the change proves **not** small — scope explosion, a core assumption breaks open into a large redesign, or the work turns out to need sustained complex reasoning — **escalate**, recommending a switch to `minerva:propose-ship-auto` (panel-governed) or `minerva:propose-ship` (human-gated). Leave the work unit recoverable and emit the [final-report-on-bail](governance.md) shape so the user can resume under the heavier orchestrator. Do not silently grind a large change through the fast path.

## Never-bypassed self-checks

Three checks are **always** performed as rigorous main-model self-checks, **never** elided because the change "looks small" — their whole value is a deliberate second look at the model's own work:

- **Completion verification** — before advancing out of Work, build the success-criteria checklist (each criterion + concrete evidence + yes/no) and honestly confirm each is met against the diff. If any criterion is not cleanly met, treat it as a success-criteria divergence and replan (Phase 2.5) rather than shipping.
- **Mid-work divergence confirmation** — when a core assumption breaks or the approach/scope shifts, confirm whether it is load-bearing enough to warrant a replan. Escalate if unsure.
- **New-plan acceptance (replan)** — when replanning, re-read the drafted Original/What-changed/New-plan against the proposal before accepting it.

For each, the escalation predicate still applies: if the self-check leaves you genuinely uncertain, escalate rather than rubber-stamp.

## Hardcoded escalation triggers

These reach the user (or halt) regardless of the predicate — see `references/governance.md` for the full list and the bail-report format:

- in-flight work collision (pre-flight);
- worktree-creation failure (git error, missing gitignore, slug collision);
- ship-phase failures: CI auto-fix classified `other`, push rejection, `gh` auth failure;
- the global escalation counter reaching 3.

## Escalation counter

Maintain one counter across the run. It is **per-run** state owned by the main orchestration loop — `Skill`-tool delegations (Phases 4.5 / 6 / 7) run inline in that loop, so the counter persists across them; it is not shared with any other run. Increment it on **every** user escalation (predicate-driven or hardcoded). If it reaches **3**, halt before the next decision point and emit the final-report-on-bail. Recovery: run the individual minerva skills manually from the current state.

## Per-decision logging

After every decision point (regardless of outcome), append a one-line entry to the work unit's `scratchpad.md` under a `## Quick decisions YYYY-MM-DD` header — a distinct heading that does not collide with `minerva:work`'s own scratchpad sections:

```
## Quick decisions 2026-06-16
- [decided] scope check: single additive unit (one new file, no public interface change)
- [decided] approach: wrap the helper rather than fork it (dominant — fork duplicates 40 lines)
- [escalated to user] approach: two equally-viable layouts, no dominant choice — user picked option B
```

- `[decided]` — the main model decided directly; record the one-line rationale (and, for approach decisions, the rejected alternatives) so a later `minerva:review` / `minerva:promote` pass can audit the call.
- `[escalated to user]` — the predicate (or a hardcoded trigger) sent it to the user; record what was asked and the answer.
- `[synthesis]` — Phase 4.5 observability line (wrote / no-op); not a decision, recorded so a later pass can confirm the phase fired.

These entries are scratchpad data — `minerva:promote` treats them as routine noise unless a decision reveals a durable pattern, in which case it goes through the standard PROMOTE/MERGE/DISCARD partition.

## Decision taxonomy

Every strategic/tactical decision is **main-model-decided by default**, with the escalation predicate as the fail-closed exception. The `Never-elide?` column marks the decisions whose self-check is always performed (and which therefore escalate, never skip, on uncertainty).

| Phase | Decision | Default | Never-elide? |
|---|---|---|---|
| Pre-flight | In-flight work collision | Hardcoded user escalation | **Yes** — hardcoded |
| Propose | Scope check (single unit vs. decompose) | Main model decides | No — escalate only if genuinely ambiguous |
| Propose | Approach selection | Main model decides | No — escalate if no dominant option |
| Propose | Whole-proposal soundness | Main model decides | No — escalate if a public-interface/contract call is uncertain |
| Work | Mid-work load-bearing divergence | Main model confirms | **Yes** — precondition is a surfaced divergence |
| Replan | New-plan acceptance | Main model accepts | **Yes** — convened only after a confirmed divergence |
| Work | Completion verification | Main model self-checks | **Yes** — independent check on the model's own work |
| Review | Per-finding triage | Main model decides | No — escalate if a finding's disposition is contested |
| Review | Replan-vs-FIX | Main model decides | **Yes** — precondition is a surfaced load-bearing finding |
| Promote | Three-way partition (PROMOTE/MERGE/DISCARD/TODO) | Main model decides | No — escalate if an entry is genuinely ambiguous |
| Promote | TODO disposition | Main model decides | No |
| Promote→Ship | Synthesis refresh (Phase 4.5) | Delegated, self-gating | n/a |
| Ship | Commit message / PR title+body | Main model accepts draft | n/a — operational |
| Ship | CI auto-fix `other` bail | Hardcoded user escalation | **Yes** — hardcoded |
| Cleanup gate | PR state polling + cleanup | No decision | n/a |
