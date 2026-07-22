---
name: propose-ship
description: Runs the full minerva lifecycle end-to-end in one command with the user in the loop — a human decision gate at each phase transition. Orchestrates propose - work - review - promote - ship - cleanup by delegating to each skill in sequence with no logic duplication, folds an optional `minerva:synthesize` overview-refresh offer into the promote-ship gate, refuses to start if in-flight work exists for the same intent, advances out of the work phase only on explicit user signal, and waits for the PR to actually merge before invoking cleanup. Use when the user wants the whole lifecycle while staying in control — "propose and ship", "I want to approve each step" — or when they invoke `minerva:propose-ship`.
---

Orchestrate the full minerva lifecycle in one invocation by delegating to each skill in order. This skill contains no logic of its own — it is a thin conductor.

## Phase sequence

```
minerva:propose → minerva:work → minerva:review → minerva:promote → (minerva:synthesize?) → minerva:ship → minerva:cleanup
```

The `(minerva:synthesize?)` step is the optional overview-refresh offered inside the promote → ship gate (see Handoff rules); it runs only if the user accepts and self-gates on whether enough new scope accumulated.

Invoke each phase via the `Skill` tool in this exact order. Let each skill's own instructions handle all interactive parts, completion signals, and internal logic. Do not reproduce or shadow any skill's behavior here.

The `minerva:propose` phase creates the work unit's branch + worktree at `.minerva/worktrees/<NNN-slug>/` and enters it; every downstream phase enters that worktree automatically (or stays in it if already there). `minerva:cleanup` is the only phase that runs from outside the worktree — it removes it.

(Note: review runs **before** promote so review-derived scratchpad notes flow through the promote partition. This matches `using-minerva` and `review`. Re-cycle review/promote as needed. Cleanup runs only after the PR actually merges — see [Phase 7](#phase-7--cleanup-gate).)

## Pre-flight: detect in-flight work

Before invoking `minerva:propose`, check for in-flight work units that might collide with the user's intent:

1. List `.minerva/work/NNN-*/` plus `.minerva/worktrees/NNN-*/.minerva/work/NNN-*/`.
2. If any unit has a `proposal.md` whose `## Status` is `Draft` or whose scratchpad is **not** the post-promote marker, treat it as in-flight.
3. If the user's inline description (`minerva:propose-ship "add payments"`) clearly overlaps with an in-flight unit's slug or goal, **stop and ask**:
   > "Found in-flight work unit `005-add-payments` — looks related to what you just asked. Resume that one (`minerva:work 005-add-payments`) or genuinely start fresh?"

   Only proceed to `minerva:propose` after the user confirms a fresh start.

This avoids the foot-cannon where a user mid-flow says "ok run the whole thing" and accidentally spawns a parallel work unit.

## Handoff rules

- **propose → work**: hand off automatically once `minerva:propose` reaches its natural completion point (proposal written, self-reviewed, and user-approved).

- **work → review**: this is the trickiest handoff. `minerva:work` is session-spanning and has no discrete completion event. Advance to `minerva:review` only when the user explicitly signals work is done. Recognized signals:
  - The phrase `done`, `complete`, `ready to review`, `ready to ship`, `wrap it up`, `promote it`, or `ship it` in user input.
  - The user invoking `minerva:review`, `minerva:promote`, or `minerva:ship` directly.
  - The `minerva:work` skill itself signaling completion (success criteria checked off, surfaced as "ready for promote").

  The signal list is illustrative, not closed — any unambiguous completion statement (e.g. "looks good, let's move on") counts as an explicit signal. Absent such a signal, stay in work mode; do not advance silently or prompt the user repeatedly.

- **review → promote**: hand off automatically once `minerva:review` reaches its natural completion point AND triage is clean (zero pending, all FIX items applied). If review surfaced findings the user routed back to `minerva:replan`, return control to work and re-enter review afterward.

- **promote → ship gate**: this is the single explicit gate. After `minerva:promote` completes, briefly summarize what was promoted, what was merged into the proposal, and what was discarded. **Then, as part of this same gate, if promote added knowledge entries, offer to refresh the knowledge-wiki overview**: `minerva:synthesize` reports how much un-synthesized scope accumulated and self-gates on whether enough is there to be worth a refresh. If the user accepts the offer, invoke `minerva:synthesize` via the `Skill` tool — including its own write confirmation — **before** invoking ship, so the refreshed `.minerva/knowledge/overview.md` rides the same PR. The offer is optional and non-blocking; the user can decline and ship without it (the overview is advisory). After the synthesis offer resolves, wait for explicit user confirmation (`ship it`, `proceed`, `yes`) before invoking `minerva:ship`. If review found issues serious enough that the user has unresolved concerns about the implementation, pause here for explicit confirmation regardless. When `minerva:synthesize` wrote a refreshed overview, the ship hand-off must **name `.minerva/knowledge/overview.md` among the paths to stage** (ship stages specific paths, never `-A`) and **request** a PR-body line noting "overview.md refreshed (advisory navigation)".

- **ship → cleanup**: after `minerva:ship` returns, the PR may be `OPEN` (auto-merge pending), `MERGED`, or `CLOSED`. Cleanup runs only on `MERGED`. See [Phase 7](#phase-7--cleanup-gate) for the polling rules.

## Entry point

Always start at `minerva:propose` after the pre-flight check passes. Do not attempt to detect or resume mid-lifecycle state beyond the in-flight collision check above. If the user already has a work unit in progress and they actually want to resume it (not start a new one), they should invoke the individual skills directly — the pre-flight will surface this.

## Execution

1. Run pre-flight in-flight detection. Stop or proceed based on user response.
2. Invoke `minerva:propose` via the `Skill` tool. Wait for it to complete.
3. Invoke `minerva:work` via the `Skill` tool. Stay engaged through the work phase per the handoff rule above.
4. Invoke `minerva:review` via the `Skill` tool. Wait for it to complete. If review routes to `minerva:replan`, return to step 3 after the replan lands.
5. Invoke `minerva:promote` via the `Skill` tool. Wait for it to complete.
6. Apply the promote → ship gate: summarize the promote result, **offer `minerva:synthesize` if entries were added** (invoke it via the `Skill` tool before ship if the user accepts), then wait for explicit user confirmation.
7. Invoke `minerva:ship` via the `Skill` tool (naming `overview.md` in the staging set when synthesis refreshed it).
8. Run the cleanup gate ([Phase 7](#phase-7--cleanup-gate)).

## Phase 7 — cleanup gate

After `minerva:ship` returns, check PR merge state and decide what to do with the worktree:

1. Read the PR state for the work-unit branch: `gh pr view <branch> --json state,mergedAt 2>/dev/null`.
2. **`MERGED`** → invoke `minerva:cleanup <NNN-slug> --yes` via the `Skill` tool. The work unit is fully shipped and the worktree is safe to remove. Report the cleanup result and exit.
3. **`OPEN`, auto-merge enabled** → the PR will merge on its own when CI passes. Schedule a wake-up:
   - `ScheduleWakeup` with `delaySeconds: 300` and a `prompt` of `minerva:propose-ship --cleanup-only <NNN-slug> --retry=N` so the next firing re-enters this gate.
   - Cap the retries at **12** (~1 hour total). Carry the retry count in the wake-up `prompt`.
   - On cap exhaustion, surface "auto-merge still pending after ~1 hour — run `minerva:cleanup <NNN-slug>` manually once the PR merges" and exit.
4. **`OPEN`, auto-merge declined / not enabled** → no automatic merge is coming. Surface "merge the PR manually when ready, then run `minerva:cleanup <NNN-slug>`" and exit. Do **not** schedule a wake-up — the gate has no signal to wait on.
5. **`CLOSED` (not merged)** → the PR was closed without merging. Surface "PR closed without merging — worktree left in place at `.minerva/worktrees/<NNN-slug>/` for manual review. Run `minerva:cleanup <NNN-slug>` if you want to discard it." Exit.
6. **No PR found** → ship must have bailed before opening one. Skip cleanup and exit.

This phase is also the entry point when `propose-ship` is re-invoked via the wake-up (`--cleanup-only` flag) — in that mode, skip phases 1–7 and re-run phase 7 directly.

## Out of scope

This skill does not define what "done" means for any phase — each skill defines its own completion signal. It does not add checkpoints, summaries, or status messages between phases beyond the explicit work → review trigger words, the promote → ship gate (which now also carries the optional, in-gate `minerva:synthesize` overview-refresh offer), and the cleanup gate.
