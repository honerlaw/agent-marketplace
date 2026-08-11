# Replan: 048-right-size-lifecycle-waits

## 2026-07-28 — the merge poll keeps its constant; the CI watch uses `gh`'s own watch

### Original plan
One principle — "size a wait from what is actually being waited on, never from a constant" — applied to both waiting sites. `ship`'s CI watch would estimate CI duration from `gh run list` history and drive a hand-rolled bounded poll loop; the four orchestrators' Phase 7 merge poll would drop its fixed `delaySeconds: 300` and size itself the same way. Success criterion 3 recorded that as "All four orchestrators' Phase 7 no longer hardcodes `delaySeconds: 300`".

### What changed
The Phase 3 code review produced two findings that survived verification and invalidate that plan for the merge gate specifically:

1. **Sizing the merge poll by CI duration makes it strictly worse.** When the cleanup gate runs, CI is already green — auto-merge is queued behind a required review or a merge queue, not behind CI. So "expected remaining CI time" tends to zero, clamps to the 60s floor, and 12 retries covers ~12 minutes instead of the ~1 hour the old constant gave. The gate would give up 5× sooner, in exactly the fast repo the change targets. Verified by walking the arithmetic against this repo's measured 10-26s runs.

2. **`gh pr checks` has a native blocking watch.** `--watch` (with `--fail-fast`) blocks until checks finish, which is a better primitive than the hand-rolled loop: no interval to choose, no `MAX_POLLS` floor to get wrong, no rate-limit exposure, no zero-checks edge case. The review had separately shown the hand-rolled loop's `MAX_POLLS = min(120, ceil(2 × estimate/30))` had **no floor** — at a 10s estimate it computed to a single immediate poll, so the watcher exited instantly and the run fell through to the 1200s fallback. That is a regression against the 270s constant this unit set out to remove.

Two further verified defects in the same section were inherited, not introduced: `gh pr checks --json … ,conclusion` is a hard error (`conclusion` is not a field), and `state: COMPLETED` is a value `gh` never emits (`state` is `SUCCESS`/`FAILURE`; the normalized field is `bucket`).

### New plan
Split the principle by what is actually being waited on, rather than applying one rule to both sites:

- **`ship`'s CI watch** — no interval is guessed at all. A detached `gh pr checks <pr> --watch --fail-fast` resumes the run when checks settle; a single long (1800s) `ScheduleWakeup`, with its prompt pinned including `--watch-iteration=<N>`, stays armed as the survives-anything fallback. The `gh run list` estimate is dropped entirely — it was only load-bearing for the poll interval that no longer exists. All check-state vocabulary unifies on `bucket == "pending"`, and the two inherited `gh` errors are fixed.
- **The orchestrators' Phase 7 merge poll** — `delaySeconds: 300` **stays**, because a constant is the right answer here: the wait is not CI-shaped, and `300 × 12` is what makes the retry cap a ~1 hour wall-clock bound. What the unit adds is the rationale that was missing, stated in the three `references/phases.md` files. `propose-ship/SKILL.md` reverts to its original text untouched — with the constant retained there is nothing to say that its headroom could carry (the file is 9206 bytes against the test-enforced 9216 cap: **10 bytes**), and the pointer it briefly gained was dangling anyway (its Phase 7 runs after `minerva:ship` has exited). It is left inconsistent with its three siblings, which now carry the rationale it lacks; that asymmetry is the price of the byte cap and is recorded as a followup (extract `propose-ship` into a `references/` split, as its siblings already are).

**Two gaps closed after the replan-acceptance gate flagged them:** (a) the 1800s fallback is a **re-arming keep-alive, not a budget** — each firing that still finds work pending schedules the next, so a repo with 40-minute CI is not cut off; the protocol now says so explicitly. (b) `gh pr checks --watch --fail-fast` was **exercised**, not assumed: on `gh` 2.92.0 both flags are accepted, the command returns immediately on a settled PR, and it runs detached. It has not been observed blocking through a live pending run; this unit's own ship phase is the first such exercise.

### Success criteria changes
Criterion 3 is replaced. Was:

> 3. All four orchestrators' Phase 7 no longer hardcodes `delaySeconds: 300`; the three with `references/phases.md` state the sizing rule there.

Now:

> 3. The three orchestrators with `references/phases.md` state *why* the merge poll keeps `delaySeconds: 300` (the wait is not CI-shaped; 300 × 12 is the ~1 hour cap); `propose-ship/SKILL.md` is unmodified.

Criterion 1 is amended: the CI-watch section specifies the detached `gh pr checks --watch --fail-fast`, the 1800s pinned-prompt fallback, and `bucket`-based state — not a `gh run list` estimate or a hand-rolled loop. All other criteria stand.
