# Proposal: right-size-lifecycle-waits

**Date**: 2026-07-28
**Status**: Shipped (2026-07-28)

## Goal
Close unit 047's three followups. The substantial one: minerva's lifecycle skills wait on external state with hardcoded polling constants (`delaySeconds: 270` for CI, `300` for PR merge) whose stated justification no longer holds. Give each wait a stated, defensible policy, and where possible resume when the watched state actually settles rather than at an arbitrary poll boundary. Plus the two one-line corrections 047 recorded.

**Outcome, stated plainly** (it narrowed during the run — see `replan.md`): the CI watch stops guessing an interval entirely. The **merge poll keeps its 300s constant** — investigation showed sizing that one by CI duration makes it strictly worse — and gains the rationale it was missing. So this unit removes one unjustified constant and *justifies* the other; it does not eliminate both.

## Why
`ship/references/protocol.md:89` justifies its cadence as *"stays under the 5-minute prompt-cache TTL — see ScheduleWakeup docs"*. That premise is stale: this session type uses a 1-hour TTL, under which the sentence explains nothing — almost any legal delay satisfies it. So the number is now unjustified rather than merely mis-tuned.

And it is mis-tuned in both directions. Measured this session with `gh run list`:

| repo | observed durations |
|---|---|
| agent-marketplace | 10s, 12s, 13s, 13s, 15s, 17s, 18s, 21s, 26s |
| onerlaw/seekless | CI 1005s / 1026s / 1029s / 1034s · Deploy 248s / 457s / 653s · e2e 185s |

A fixed 270s idles ~4.5 minutes on a repo whose CI finishes in 18 seconds, and burns four wake-ups on one whose CI takes 17 minutes. The same fixed-constant pattern sits in all four orchestrators' Phase 7 merge poll at `300`.

Each `ScheduleWakeup` also **ends the turn** — the "it stopped and says it's waiting" symptom unit 047 fixed at the panel gates and explicitly did not address here.

## Approach
*(Rewritten at promote to match what shipped. The run began on "Approach A′" — estimate CI duration from `gh run list` and drive a bounded hand-rolled poll loop — and the Phase 3 review invalidated it; see `replan.md` for the pivot and its evidence.)*

**The principle as it ended up:** match the *shape* of the wait to what is actually being awaited, and prefer the tool's own blocking primitive over any interval you would have to invent.

### 1. `ship/references/protocol.md` — no interval is guessed at all
1. Check once immediately after the PR is opened, with `gh pr checks <pr> --json name,state,bucket`. State vocabulary is `bucket` (`pass`/`fail`/`pending`/`skipping`/`cancel`) throughout — the section previously named a `conclusion` field that does not exist (a hard error) and a `state: COMPLETED` value `gh` never emits. Both inherited bugs are fixed.
2. Nothing pending → straight to result handling.
3. **Primary wait — `gh`'s own blocking watch.** A detached `gh pr checks <pr> --watch --fail-fast` (Bash `run_in_background: true`) exits exactly when checks settle or the first one fails; the harness re-invokes on exit. This deletes the interval, the bound arithmetic, the rate-limit exposure and the zero-checks edge case in one move — every one of which the hand-rolled loop had to design around, and one of which (a missing `MAX_POLLS` floor) shipped a regression past a reviewer.
4. **Durable fallback — a re-arming keep-alive.** One `ScheduleWakeup` at 1800s, prompt pinned as `minerva:ship <NNN-slug> --watch-iteration=<N>` so the 3-iteration bound survives a resume. It is *not* a budget: each firing that still finds work pending schedules the next, so a slow-CI repo is never cut off. It exists for a dead watcher, a wedged check, or an ended session.
5. **Stale-wake-up exit.** A fallback firing after the work already merged now reports "already shipped as #N" and exits, instead of falling into the branch that opens a second PR.
6. The 3-iteration auto-fix bound, its bail conditions, and cross-wake iteration tracking are **unchanged**.

**What is deliberately not claimed.** A detached watcher does not make CI itself harness-tracked — only the watcher process. The benefit is resume latency, nothing more.

### 2. The orchestrators' Phase 7 — the constant stays, the rationale arrives
Sizing this wait by CI duration was drafted and then **withdrawn**: when the cleanup gate runs, CI is already green and auto-merge is queued behind a required review or a merge queue, so "remaining CI time" collapses toward zero and the 12-retry cap degrades from a ~1 hour bound to ~12 minutes. A constant is the correct answer for a wait that is not proportional to anything measurable.

- The three orchestrators with `references/phases.md` keep `delaySeconds: 300` and gain the missing rationale there.
- Their `SKILL.md` one-liners are unchanged.
- **`propose-ship/SKILL.md` is untouched.** It has no `references/` directory and 10 bytes of headroom against the 9216-byte cap, so there was nowhere to put the rationale; the terse pointer tried instead was dangling, since its Phase 7 runs after `minerva:ship` has exited. The resulting asymmetry with its three siblings is recorded in `followups.md` as a progressive-disclosure extraction.

### 3. Keep the prose surfaces honest
`ship/SKILL.md` (description + body) and `using-minerva/references/guide.md` both describe the mechanism as "ScheduleWakeup polling / ~270s intervals". Because §1 lands a **hybrid**, these must be rewritten to describe the hybrid — not merely have a number swapped. Leaving them as a re-numbered constant would reproduce the doc/reality mismatch this unit exists to remove. `ship/SKILL.md`'s description stays ≤1024 chars and in house style ([[047]]).

### 4. The two 047 leftovers (one line each)
- **Phase 4.5 logging destination** — Phase 4 archives `scratchpad.md` and replaces it with the post-promote marker that [[003]] says downstream skills depend on; Phase 4.5 then logs its synthesis outcome there. Name `archive/scratchpad.md` as the destination in the three autonomous orchestrators' `references/phases.md`.
- **`review/references/protocol.md`** — its local-diff dispatch pins no agent parameters. Pin `subagent_type: general-purpose`, and **deliberately leave the model unpinned** so it inherits the session tier: a code-quality review's value scales with model capability, unlike the structured accept/revise vote `round-table` pins to sonnet. The site must stay detected by `tests/test_skill_dispatch.py` ([[050]]).

### Rejected alternatives
- **A′ — estimate CI duration, drive a bounded hand-rolled poll loop.** The plan this unit started with; withdrawn mid-run. Its bound had no floor, so a fast repo got a single immediate poll and then fell through to the long fallback — worse than the constant being removed. Superseded by `gh pr checks --watch`, which needs no estimate at all. Full reasoning in `replan.md`.
- **B — keep `ScheduleWakeup`, only right-size it.** Not rejected so much as *vindicated at one of the two sites*: the merge poll ended up exactly here, keeping its constant with a stated reason.
- **C — `Monitor`-based watch.** Ruled out by Monitor's own documentation: for a single "tell me when it's done" notification it directs you to Bash `run_in_background` instead. Monitor is for per-occurrence streams.

## Success criteria
1. *(amended by `replan.md` 2026-07-28)* `ship/references/protocol.md`'s CI-watch section specifies: the immediate first check; a detached `gh pr checks <pr> --watch --fail-fast` as the primary wait; an always-armed 1800s `ScheduleWakeup` whose prompt is pinned including `--watch-iteration=<N>`; `bucket`-based check-state vocabulary throughout; and contains **no** reference to a prompt-cache TTL.
2. The auto-fix loop's 3-iteration bound, bail conditions, and cross-wake iteration tracking are textually unchanged.
3. *(replaced by `replan.md` 2026-07-28)* The three orchestrators with `references/phases.md` state **why** the merge poll keeps `delaySeconds: 300` — the wait is not CI-shaped, and `300 × 12` is what makes the retry cap a ~1 hour bound; `propose-ship/SKILL.md` is unmodified.
4. `ship/SKILL.md` and `using-minerva/references/guide.md` describe the hybrid mechanism, with no "~270s" or "ScheduleWakeup polling"-only characterization left.
5. Phase 4.5 in the three autonomous orchestrators names `archive/scratchpad.md` as its log destination.
6. `review/references/protocol.md` pins `subagent_type: general-purpose`, leaves the model unpinned with the reason stated, and remains one of the five sites `tests/test_skill_dispatch.py` detects.
7. Every `SKILL.md` stays ≤ 9216 bytes — `propose-ship` in particular, at 9206.
8. Full CI-enumerated suite green; `knowledge_lint` clean.

## Open questions
- Whether the harness's own `run_in_background` mode inherits the documented 600 000 ms Bash `timeout` cap is **not** verified. A detached child was measured surviving 780s and beyond, so the OS-level lifetime is not the constraint; the design bounds the watcher explicitly and arms the durable fallback regardless, so neither answer changes the protocol.
