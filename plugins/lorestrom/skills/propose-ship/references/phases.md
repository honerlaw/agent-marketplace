# Phase protocols — full walkthroughs

Read this file in full before executing the lifecycle; the SKILL.md core names the phases, this file is the protocol.

## Pre-flight: detect in-flight work

Before invoking `lorestrom:propose`, check whether the user's intent is **already in flight** — in this checkout, in another clone, or in a available live peer session.

**Read `skills/propose/references/in-flight-check.md` and run it.** It reads four evidence sources — this project's open units (the helper's `unit-state`, with the gate as the authority, never a property match), local and remote branches, open PRs, and available live peer sessions — each failing soft, so a repo with no remote, no tracker and no siblings passes through silently. It is **detection, not a lock**: `git worktree add -b` serializes only sessions choosing the *same slug*, so a clean result means no evidence was found, not that nobody else is working the goal.

A collision stops the run and asks. Only proceed to `lorestrom:propose` after the user confirms a fresh start.

This avoids the foot-cannon where a user mid-flow says "ok run the whole thing" and accidentally spawns a parallel work unit.

## Handoff rules

- **propose → work**: hand off automatically once `lorestrom:propose` reaches its natural completion point (proposal written, self-reviewed, and user-approved).

- **work → review**: this is the trickiest handoff. `lorestrom:work` is session-spanning and has no discrete completion event. Advance to `lorestrom:review` only when the user explicitly signals work is done. Recognized signals:
  - The phrase `done`, `complete`, `ready to review`, `ready to ship`, `wrap it up`, `promote it`, or `ship it` in user input.
  - The user invoking `lorestrom:review`, `lorestrom:promote`, or `lorestrom:ship` directly.
  - The `lorestrom:work` skill itself signaling completion (success criteria checked off, surfaced as "ready for promote").

  The signal list is illustrative, not closed — any unambiguous completion statement (e.g. "looks good, let's move on") counts as an explicit signal. Absent such a signal, stay in work mode; do not advance silently or prompt the user repeatedly.

- **review → promote**: hand off automatically once `lorestrom:review` reaches its natural completion point AND triage is clean (zero pending, all FIX items applied). If review surfaced findings the user routed back to `lorestrom:replan`, return control to work and re-enter review afterward.

- **promote → ship gate**: this is the single explicit gate. After `lorestrom:promote` completes, briefly summarize what was promoted (each entry is pending lore on the unit's gate until cleanup releases it), what was merged into the proposal, and what was discarded. Wait for explicit user confirmation (`ship it`, `proceed`, `yes`) before invoking `lorestrom:ship`. If review found issues serious enough that the user has unresolved concerns about the implementation, pause here for explicit confirmation regardless.

- **ship → cleanup**: after `lorestrom:ship` returns, the PR may be `OPEN` (auto-merge pending), `MERGED`, or `CLOSED`. Cleanup runs only on `MERGED`. See [Phase 7](#phase-7--cleanup-gate) for the polling rules.

## Entry point

Always start at `lorestrom:propose` after the pre-flight check passes. Do not attempt to detect or resume mid-lifecycle state beyond the in-flight collision check above. If the user already has a work unit in progress and they actually want to resume it (not start a new one), they should invoke the individual skills directly — the pre-flight will surface this.

## Execution

1. Run pre-flight in-flight detection. Stop or proceed based on user response.
2. Invoke `lorestrom:propose` via the skill loader. Wait for it to complete.
3. Invoke `lorestrom:work` via the skill loader. Stay engaged through the work phase per the handoff rule above.
4. Invoke `lorestrom:review` via the skill loader. Wait for it to complete. If review routes to `lorestrom:replan`, return to step 3 after the replan lands.
5. Before promote, run the helper's `phases` (`storage:unit.read`): on a phased unit whose next phase is not its final one (`phased` true and `next_position` not `total`), run promote's **Mode B** for each durable finding only — never Mode A, so no `storage:unit.finish` — because Mode A belongs before the final phase's ship (`skills/propose/references/phasing.md`). Otherwise invoke `lorestrom:promote` via the skill loader. Wait for it to complete.
6. Apply the promote → ship gate: summarize the promote result, then wait for explicit user confirmation.
7. Invoke `lorestrom:ship` via the skill loader. First tell the user: if ship ends this turn on its CI watch, nothing hands back to this skill (it passes ship no `--auto`), so once ship reports, re-enter with `lorestrom:propose-ship --cleanup-only <date-slug>`.
8. Run the cleanup gate ([Phase 7](#phase-7--cleanup-gate)).

## Phase 7 — cleanup gate

**Runtime continuation.** Read the saved checkpoint before this gate; preserve
caller, escalation/decision/reviewer counters, cleanup retries and its absolute
deadline. Save phase `cleanup` before waiting. The scheduled resume operation is
conditional on a real re-entry capability: without it, checkpoint and report
**pending — manual resume required**, with the exact host-correct
`lorestrom:propose-ship --cleanup-only <date-slug> --retry=N` prompt. Write that prompt
yourself: this skill passes ship no `--auto`, so the checkpoint's caller is null and the
helper's rendered prompt (`read --host`) is a bare `lorestrom:cleanup <date-slug>`, which would
skip a phased unit's loop. Count each retry before waiting;
cap at 12 or the original one-hour deadline, whichever comes first. Never reset
these limits when switching sessions.


After `lorestrom:ship` returns, check PR merge state and decide what to do with the worktree:

1. Read the PR state by the number ship reported (on resume, the checkpoint's PR number): `gh pr view <pr-number> --json state,mergedAt 2>/dev/null`. No branch name is typed.
2. **`MERGED`** → invoke `lorestrom:cleanup <date-slug> --yes` via the skill loader. Its `--yes` acts only on the run's own unit (`mine`, release.md). Cleanup releases the unit's gate on live merge evidence, so its pending entries become current, then removes the worktree. `--yes` never confirms a merge cleanup could not prove: a gate that waits on a confirmation is reported with cleanup's own question, and the run asks the user. Report the cleanup result and exit, unless the unit is phased (step 7).
3. **`OPEN`, auto-merge enabled** → the PR will merge on its own when CI passes. When a scheduler supports re-entry, schedule a wake-up:
   - the scheduled resume operation with `delaySeconds: 300` and a `prompt` of `lorestrom:propose-ship --cleanup-only <date-slug> --retry=N` so the next firing re-enters this gate.
   - Cap the retries at **12** (~1 hour total). Carry the retry count in the wake-up `prompt`.

   **Why a constant here, when `lorestrom:ship`'s CI watch refuses to guess an interval.**
   The two waits are shaped by different things. Ship waits on *checks settling*, whose
   duration is unknowable in advance — measured at ~10-26s in a docs-only repo and ~1000s
   for a full suite — so it lets `gh` report completion rather than polling on a guess.
   This gate waits on *auto-merge landing*, which does not track CI duration at all: it can
   queue behind a required review or a merge queue long after checks are green. There is no
   completion signal to subscribe to, so a constant is the honest shape, and 300s x the cap
   above is exactly what makes the ~1 hour bound a bound rather than an estimate
   ([[2026-07-29-pattern-wait-shape-matches-what-is-awaited]]).
   - On cap exhaustion, surface "auto-merge still pending after ~1 hour — run `lorestrom:cleanup <date-slug>` manually once the PR merges" and exit.
4. **`OPEN`, auto-merge declined / not enabled** → no automatic merge is coming. Surface "merge the PR manually when ready, then run `lorestrom:cleanup <date-slug>`" and exit. Do **not** schedule a wake-up — the gate has no signal to wait on.
5. **`CLOSED` (not merged)** → the PR was closed without merging. Surface "PR closed without merging — worktree left in place at `.lorestrom/worktrees/<date-slug>/` and the unit's gate left open for manual review. Run `lorestrom:cleanup <date-slug> --abandon` if you want to discard it." Never abandon the gate from this gate. Exit.
6. **No PR found** → ship must have bailed before opening one. Skip cleanup and exit.
7. **Phased unit — not done yet.** After cleanup returns on a `MERGED` phase, re-derive the phase progress with the helper's `phases` (`storage:unit.read`). If `complete` is false, follow the loop rules in `skills/propose/references/phasing.md`: return to Execution step 3 (`lorestrom:work`) for `next_branch`, cut from the freshly fetched default branch as `lorestrom:ship`'s Phase resolution says ("To **start** phase N", `skills/ship/references/protocol.md`), then Execution steps 4–8 (review, promote — Mode B unless it is the final phase — the promote → ship gate, ship and this gate again), with this skill's gates. Report the phases still outstanding at each transition. No-op for unphased units.

This phase is also the entry point when `propose-ship` is re-invoked via the wake-up (`--cleanup-only` flag) — in that mode, skip phases 1–7 and re-run phase 7 directly.
