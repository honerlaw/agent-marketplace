# Replan log: trace-orchestrator-run-time

## 2026-09-26 — Active time is summed from turn spans, not from turn_duration.durationMs

**Original plan**: Approach step 2 and success criterion 2 defined active time as the sum of each
turn's `turn_duration.durationMs`, with each turn starting at marker time minus `durationMs`. The
Facts section cited "24 turns totalling 7,355 s of active time" for session `51b73da3`.

**What changed**: Implementing that produced overlapping turns and active time larger than wall
time. On session `51b73da3` run 0, "active" was 37.4 min against a 27.4 min wall, with 27.6 min
misattributed to `harness`. That contradicts criterion 3's partition guarantee.

`durationMs` is not a per-turn wall-clock time. Across the 150 marked turns in this project's
finished sessions (this live session excluded), comparing `durationMs` with the turn's span (the
event that began the turn → its marker):
- 126 agree within 2 s.
(The divergence write-up's first count, 32 shorter of 165, used the naive turn start (first raw
event, live session included). Starting each turn at its starting event instead is what moves
turns from "shorter" to "agree".)
- 13 are **shorter**. For example, `51b73da3` turn 2 has a 1,471 s span but a 476 s
  `durationMs`. The 995 s gap is an open `AskUserQuestion`, so `durationMs` excludes time spent
  waiting on the user. Under the new definition that wait stays in active time as `user`, which
  is intended: the question was on the critical path.
- 11 are **longer**, up to 12.4×. For example, a 440 s span reports 5,459 s. The best-fitting
  inference, from timing alone and not a confirmed harness mechanism, is that it is measured from
  a request that started many turns earlier.

The sample is this project's transcripts only. The fix does not depend on the finding
generalizing, because attribution stops relying on `durationMs` at all. This applies
`2026-08-11-pattern-a-tolerant-reader-needs-a-boundary`: `durationMs` was trusted as scoped to
"this turn" without checking that boundary. The corrected active time for `51b73da3` is 3,941 s
(sum of turn spans), not 7,355 s.

**New plan**: A turn is the events between consecutive `turn_duration` markers. It starts at the
event that began it, which is the first user event carrying an `origin` (human prompt,
task-notification, or subagent hand-back, which is `isMeta`), falling back to the first
non-tool-result user message. It ends at the marker. Bookkeeping lines written while idle (queue
operations, PR links, attachments) fall into the idle gap before the turn.

Active time is the sum of turn spans, partitioned into:
- `model`: no tool open, including bookkeeping lines written mid-generation;
- `tool:<Name>`: a tool call is open, including any permission-prompt wait;
- `user`: an `AskUserQuestion` is open;
- `harness`: a gap ending at a `system` event (hooks).

Between-turn gaps are classified by what started the next turn:
- `background-wait`: a task-notification or subagent hand-back;
- `scheduled-wait`: the previous turn armed `ScheduleWakeup` and no human started the next one;
- `user-idle`: a human prompt;
- `idle-other`: the fallback when none of those signals matches.

`durationMs` is kept only as a reported cross-check: its sum, the span sum, and the number of
turns that differ by more than 2 s.

The code moved ahead of this vote. `scripts/run_trace.py` already implements the new plan. Checked
against the corpus: across all 19 sessions, turns never overlap and active ≤ wall, both per
session and per run.

Success criterion 2 is replaced with: "Active time is the sum of per-turn spans (starting event →
`turn_duration` marker). On every session in this project, turns never overlap and active ≤ wall,
per session and per run. `durationMs` appears only as a cross-check (sums and the count of
disagreeing turns). Inter-turn gaps are classified as background-wait / scheduled-wait /
user-idle / idle-other. Covered by fixture tests, including a turn whose `durationMs` overshoots
its span and one where it undershoots (an open `AskUserQuestion`)." Success criterion 3 gains
`harness` in its partition list. The Facts line "7,355 s of active time" is annotated as the
`durationMs` sum, superseded by this entry.
