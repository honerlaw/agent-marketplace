# Claude Code session transcripts: what their timestamps do and don't mean

**Date**: 2026-09-26
**Type**: reference
**Summary**: durationMs is not per-turn wall time; subagents live in sidecar files; notifications carry true durations
**Context**: .minerva/work/2026-09-26-trace-orchestrator-run-time (see git history if the worktree has been cleaned up)

## Context
Building `scripts/run_trace.py`, a wall-time tracer for `minerva:propose-ship-auto` runs, meant
reconstructing time from the on-disk transcripts at `~/.claude/projects/<encoded-cwd>/`. Several
fields don't mean what they appear to. Two tools and one success criterion went wrong on them.
Measured on this project's transcripts (Claude Code 2.1.28x, 19 sessions, September 2026).

## Finding
- **`system` / `turn_duration.durationMs` is not the turn's wall time.** Of 150 marked turns in
  finished sessions, 126 match the turn's span (starting event → marker) within 2 s. In 13 it is
  shorter, because it excludes time an `AskUserQuestion` waited on the user. In 11 it is far
  longer, up to 12.4×. The best-fitting inference is that it is measured from a request that
  began many turns earlier. Summing it put one session's "active time" at 7,355 s against a
  6,105 s wall; the true figure is 3,941 s.
- **A turn starts at the event that began it, not at its first line.** That event is the first
  user event carrying `origin.kind`: `human`, `task-notification`, or `peer`. A subagent
  hand-back is `peer` and is also `isMeta: true`. Bookkeeping lines written while idle
  (`queue-operation`, `pr-link`, `attachment`, `system/away_summary`) come before it and are idle
  time.
- **Subagents are not `isSidechain` in the main file.** Each writes
  `<session>/subagents/agent-<id>.jsonl` plus `agent-<id>.meta.json`
  (`{agentType, description, toolUseId, model?}`). A reader of the main file alone sees zero
  subagent activity. `run_analyzer.py` reported 0 subagent messages for a session that ran 16.
- **A background Agent call's `tool_result` returns in about 1 s** with "Async agent launched …
  agentId: <id>". Its real duration is in the later `<task-notification>` (a `queue-operation`
  enqueue plus a user event), which carries `<tool-use-id>` and
  `<usage>…<duration_ms>N</duration_ms>` (also `subagent_tokens`, `tool_uses`). The `agentId` in
  the result text is the sidecar's file name, which links it when `meta.json` is missing. A
  foreground report appends it after the report, so take the last match.
- **Streamed assistant messages repeat.** They share `message.id`, have distinct `uuid` values
  and identical `usage`. Bill by `message.id` and dedupe tool blocks by block id.
- **Model ids in use** (September 2026): `claude-opus-5`, `claude-opus-5-5`, `claude-sonnet-5`,
  `claude-fable-5-1`. Their rates and per-model cache-read multipliers (Fable 5.1 and Mythos 5.1
  at 0.025×, Opus 5.5 at 0.05×, all others 0.1×) come from the `claude-api` skill's
  `shared/models.md` and `shared/prompt-caching.md`.

## Implications
- Measure turns as spans and keep `durationMs` only as a cross-check. `run_trace.py` reports
  both, plus the count of turns where they disagree.
- Any cost or time reader must open the sidecar directory. `run_analyzer.py` now does this
  opt-in (`include_subagent_files`) because `run_benchmark.build_record` cross-checks against
  Claude's main-only `total_cost_usd` and adds sidecars itself through `--subagent`. Folding them
  in by default would double-count and break that cross-check.
- These are observed harness behaviors, not a documented contract. Re-measure when Claude Code
  changes; `run_trace.py`'s cross-check line is the canary.

## Related
- [[2026-08-11-pattern-a-tolerant-reader-needs-a-boundary]] — see also
- [[2026-09-05-pattern-a-hand-count-is-a-claim-until-the-reader-reproduces-it]] — see also
