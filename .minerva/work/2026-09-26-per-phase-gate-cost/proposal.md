# Proposal: per-phase-gate-cost

**Date**: 2026-09-26
**Status**: Shipped (2026-09-26)

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
*(Rewritten at promote to describe what shipped; review fixes are folded in.)*

- **One pricing source.** `scripts/run_trace.py` imports `_zero_usage`, `_add_usage`,
  `usage_cost` and `normalize_model` from `run_analyzer` and defines no rates. `run_analyzer.py`
  is unchanged.
- **Billing stream.** `billing_lines()` reads every parseable line in file order. Nothing is
  dropped: a line with no timestamp takes the previous line's time. `cost_points()` bills each
  assistant message once through one session-wide `message.id` set: the main file first, then the
  sidecars sorted. That is `analyze_transcript(..., include_subagent_files=True)` exactly. A
  malformed `usage`, `cache_creation` or `model` bills as empty or `unknown` and no longer crashes
  the trace. A sidecar with no timestamped event is billed to the session only.
- **Attribution (`_cost`).**
  - A main-file message is charged to the phase window that holds its timestamp.
  - A subagent's whole cost is charged to its launch phase and gate row.
  - Legacy `isSidechain` lines count as `subagent_usd` with no gate row.
  - A run that reaches the end of the file owns everything after its last event, including an
    unlinked subagent that starts there.
- **Output.**
  - JSON: phase `cost` = `{usd, main_usd, subagent_usd, tokens, unpriced_models}`; run and
    session `cost`; gate rows and subagents carry `cost_usd` and `tokens`. `output_tokens` is
    kept.
  - Text: a `session cost` line, each run's `cost` line, and a `cost` column in the phase and
    gate tables.
  - `--all`: per-run `cost_usd`, plus per-phase and per-gate `cost_total_usd` and
    `cost_median_usd`.
- **Docs.** `plugins/utils/skills/capture-session/SKILL.md` Step 2b calls out the cost view.

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
