# Proposal: right-size-lifecycle-waits

**Date**: 2026-07-28
**Status**: Draft

## Goal
Close unit 047's three followups. The substantial one: minerva's lifecycle skills wait on external state with hardcoded polling constants (`delaySeconds: 270` for CI, `300` for PR merge) whose stated justification no longer holds and whose values are wrong at both ends of the repo-size range. Replace them with a stated, right-sized policy — and, where the byte budget allows the text, resume when the watched state actually settles rather than at an arbitrary poll boundary. Plus the two one-line corrections 047 recorded.

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
Approach A′ — the recommended A, materially revised after both propose-phase reviewer gates. One principle, applied at two fidelities according to what each site's problem shape and byte budget can carry.

**The principle:** size a wait from what is actually being waited on — for CI, this repo's own recent run durations — rather than from a constant; and prefer a mechanism that resumes when the state settles over one that resumes on a timer.

### 1. `ship/references/protocol.md` — the full policy (file is uncapped)
1. Check once immediately after the PR is opened.
2. If anything is pending, size the wait: take the **maximum** duration among the last ~10 completed runs of the same workflow (`gh run list --workflow <name> --limit 10 --json createdAt,updatedAt`). A max over a small window, not a percentile — the measured per-repo variance is tight (10-26s; 1005-1034s), so the extra machinery a percentile would need is not earned.
3. **Primary — a bounded background watcher.** Start a backgrounded `until` loop (Bash `run_in_background: true`) that re-checks every 30s and exits when no check is pending. The harness re-invokes on exit, so the run resumes when CI actually settles. Bound it explicitly: stop after `2 ×` the estimate, hard-capped at ~60 minutes.
4. **Always-armed durable fallback.** Independently arm one `ScheduleWakeup` at `max(1200, estimate)` clamped to `[60, 3600]`. This is not an either/or with step 3 — the `ScheduleWakeup` docs prescribe exactly this ("schedule a long fallback (1200s+) so the loop survives if the work hangs or never notifies"), and it is what preserves ship's documented "the session can do other work or end and be re-entered" property, which a detached process may not.
5. The 3-iteration auto-fix bound, the bail conditions, and cross-wake iteration tracking are **unchanged**.
6. The prompt-cache-TTL sentence is deleted, not re-numbered.

**What is deliberately not claimed.** A backgrounded loop does not make CI itself harness-tracked — only the wrapper process. Its benefit is *resume latency*, not the elimination of a turn boundary. The reviewer was right that the original framing overclaimed, and the text says the narrower true thing.

### 2. The four orchestrators' Phase 7 — minimal text, same principle
The merge poll is a trivial boolean check, not a branching fix loop, and three of the four `SKILL.md` files are near the 9216-byte cap (`propose-ship` **10 bytes free**, `propose-ship-balanced` 228, `propose-ship-quick` 320, `propose-ship-auto` 1145). So the mechanism stays `ScheduleWakeup`; only the sizing changes.

- The three orchestrators with a `references/phases.md` (uncapped) carry the sizing rule there: size the delay as ship's watch policy does — roughly the expected remaining CI duration, clamped `[60, 3600]` — retry cap 12 unchanged.
- Their `SKILL.md` one-liners get an equal-or-shorter edit pointing at that rule rather than restating a constant.
- **`propose-ship/SKILL.md` has no `references/` directory**, so its minimum-viable change is a byte-neutral-or-shorter edit inline. Named fallback if the principled phrasing will not fit in 10 bytes: trim the parenthetical `(~1 hour total)`, which the adjacent retry-cap sentence already implies.

### 3. Keep the prose surfaces honest
`ship/SKILL.md` (description + body) and `using-minerva/references/guide.md` both describe the mechanism as "ScheduleWakeup polling / ~270s intervals". Because §1 lands a **hybrid**, these must be rewritten to describe the hybrid — not merely have a number swapped. Leaving them as a re-numbered constant would reproduce the doc/reality mismatch this unit exists to remove. `ship/SKILL.md`'s description stays ≤1024 chars and in house style ([[047]]).

### 4. The two 047 leftovers (one line each)
- **Phase 4.5 logging destination** — Phase 4 archives `scratchpad.md` and replaces it with the post-promote marker that [[003]] says downstream skills depend on; Phase 4.5 then logs its synthesis outcome there. Name `archive/scratchpad.md` as the destination in the three autonomous orchestrators' `references/phases.md`.
- **`review/references/protocol.md`** — its local-diff dispatch pins no agent parameters. Pin `subagent_type: general-purpose`, and **deliberately leave the model unpinned** so it inherits the session tier: a code-quality review's value scales with model capability, unlike the structured accept/revise vote `round-table` pins to sonnet. The site must stay detected by `tests/test_skill_dispatch.py` ([[050]]).

### Rejected alternatives
- **B — keep `ScheduleWakeup`, only right-size it.** Simplest, and the reviewer made a real case that the tool docs bless it for exactly this "external work the harness cannot track" exception. A′ keeps B's mechanism everywhere the budget is tight and *adds* the watcher only where text is free and the wait is long — so B is not rejected so much as absorbed.
- **C — `Monitor`-based watch.** Ruled out by Monitor's own documentation: for a single "tell me when it's done" notification it directs you to Bash `run_in_background` instead. Monitor is for per-occurrence streams.

## Success criteria
1. `ship/references/protocol.md`'s CI-watch section specifies: the immediate first check; the `gh run list` max-of-last-10 estimate; the bounded background watcher; the always-armed `ScheduleWakeup` fallback at `max(1200, estimate)` clamped `[60, 3600]`; and contains **no** reference to a prompt-cache TTL.
2. The auto-fix loop's 3-iteration bound, bail conditions, and cross-wake iteration tracking are textually unchanged.
3. All four orchestrators' Phase 7 no longer hardcodes `delaySeconds: 300`; the three with `references/phases.md` state the sizing rule there.
4. `ship/SKILL.md` and `using-minerva/references/guide.md` describe the hybrid mechanism, with no "~270s" or "ScheduleWakeup polling"-only characterization left.
5. Phase 4.5 in the three autonomous orchestrators names `archive/scratchpad.md` as its log destination.
6. `review/references/protocol.md` pins `subagent_type: general-purpose`, leaves the model unpinned with the reason stated, and remains one of the five sites `tests/test_skill_dispatch.py` detects.
7. Every `SKILL.md` stays ≤ 9216 bytes — `propose-ship` in particular, at 9206.
8. Full CI-enumerated suite green; `knowledge_lint` clean.

## Open questions
- Whether the harness's own `run_in_background` mode inherits the documented 600 000 ms Bash `timeout` cap is **not** verified. A detached child was measured surviving 780s and beyond, so the OS-level lifetime is not the constraint; the design bounds the watcher explicitly and arms the durable fallback regardless, so neither answer changes the protocol.
