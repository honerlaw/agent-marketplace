# Proposal: per-phase-gate-cost

**Date**: 2026-09-26
**Status**: Draft

## Goal
`scripts/run_trace.py` reports the cost of a `minerva:propose-ship-auto` run next to its time:
USD plus the five billed token classes (input, output, cache-write-5m, cache-write-1h,
cache-read) by run, phase, gate × tier × role and subagent — for a single run and in the
`--all` cross-run aggregate (totals + medians) — so the speed-vs-cost tradeoff between
adjudication tiers is measurable.

## Why
The user asked whether tracing also tracks token cost. Today `scripts/run_analyzer.py` gives a
session-wide cost (by model, scope, tool) and `scripts/run_trace.py` gives time per phase and
gate, but only per-subagent `output_tokens` — so nobody can say what a phase or a gate *cost*.
The user: "there is probably a balance between speed and cost" → "yes please as a per phase per
gate cost". Parallel dispatch buys time nearly free; panels and fresh-context reviewers buy
confidence with tokens; the trace should price each lever.

## Approach
- **One pricing source.** `run_trace` imports `_zero_usage`, `_add_usage`, `usage_cost` and
  `normalize_model` from `run_analyzer`; it defines no rates. `run_analyzer.py` is unchanged
  (`run_benchmark` pins it — `2026-09-26-decision-trace-orchestrator-time-from-transcripts`).
- **Cost stream.** One session-wide `seen` `message.id` set spans the main file and all sidecar
  files, in `run_analyzer`'s order (main first, then sidecars sorted); the first source to
  present an id owns its cost, so no message is billed twice. Each message is priced at its own
  `message.model`.
  - Main-file assistant messages are cost points at their first copy's timestamp, charged to the
    phase window containing that timestamp. The cost stream reads the main file **unfiltered**
    (the time timeline still drops `isSidechain` lines); legacy `isSidechain` main-file messages
    count as `subagent_usd` (`run_analyzer`'s convention), are placed by timestamp alone and
    belong to no gate row — so a phase's `subagent_usd` can exceed the sum of its gate rows, and
    the docs say so.
  - A subagent's cost is the sum over its sidecar messages, charged to its launch phase and gate
    row — the same bucket-by-start rule the time columns use.
- **Output.** JSON: each phase gains `cost` = `{usd, main_usd, subagent_usd, tokens}`; each gate
  row gains `cost_usd` + `tokens` (existing `output_tokens` kept); each subagent gains `cost_usd`
  + `tokens`; run and session summaries gain cost totals; `unpriced_models` is reported per run
  and per session. Text: cost columns in the phase and gate tables and a cost line in the
  summary; `--all` adds per-phase and per-gate cost totals and medians.
- **Docs.** `plugins/utils/skills/capture-session/SKILL.md` Step 2b calls out the cost fields.
- **Rejected:** per-phase cost inside `run_analyzer` (needs phase inference there; the module is
  pinned by `run_benchmark`); a second PRICING table in `run_trace` (two tables drift).

## Success criteria
- `run_trace --json` carries `cost` on every phase window, `cost_usd` + `tokens` on every gate
  row and subagent, cost totals on run and session summaries, and `unpriced_models` per run and
  per session.
- A run's phase costs sum to the run's cost total (within rounding) — tested.
- On a fixture that includes a `message.id` duplicated across the main file and a sidecar and a
  legacy `isSidechain` line, the session total equals
  `analyze_transcript(path, include_subagent_files=True)["total_cost_usd"]` and the session
  main-scope cost equals its `by_scope["main"]["cost_usd"]`; `run_trace` defines no pricing rates
  of its own — tested.
- Text output shows cost in the phase and gate tables; `--all` reports per-phase and per-gate
  cost totals and medians — tested.
- `run_analyzer.py` is unchanged; the full test suite passes; the existing gate-table
  column-alignment test is updated to the new columns, not deleted.
- `capture-session` SKILL.md documents the cost view.

## Open Questions
- None.
