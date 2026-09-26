# Orchestrator cost is priced per phase and gate in run_trace, and the main thread, not panels, dominates it

**Date**: 2026-09-26
**Type**: decision
**Summary**: run_trace prices each phase/gate via run_analyzer; subagent gates are ~26% of auto-run cost, panels cost time more than money
**Context**: .minerva/work/2026-09-26-per-phase-gate-cost (see git history if the worktree has been cleaned up)

## Context
`scripts/run_trace.py` showed where a `minerva:propose-ship-auto` run spent its time, and
`scripts/run_analyzer.py` showed what the whole session cost, but nothing showed what a phase or a
gate cost. Without that, the speed-vs-cost trade between tiers could not be measured. For example,
nobody could say whether a panel buys its wall time at a high or a low price.

## Finding
- **Chosen:** `run_trace` imports `run_analyzer`'s `_zero_usage`, `_add_usage`, `usage_cost` and
  `normalize_model`. There is one pricing table, and `run_analyzer.py` is untouched because
  `run_benchmark` pins it.
  - Cost is billed from **every raw line**, in file order: the main file first, then the sidecars
    sorted, sharing one `message.id` set. This is exactly `analyze_transcript(...,
    include_subagent_files=True)`'s dedupe, and the time loader's filters (dropping untimestamped
    lines, deduping by uuid) do not apply to it.
  - A main-thread message is charged to the phase that holds its timestamp. A subagent's whole cost
    is charged to its launch phase and its gate row, the same rule the time view uses.
  - Legacy `isSidechain` lines count as subagent cost and belong to no gate row.
  - The text report prints a `session cost` line (the whole file) beside each run's cost, so its
    bottom line can be checked against `run_analyzer`.
- **Rejected:** per-phase cost inside `run_analyzer`, which would need phase inference in a module
  that `run_benchmark` pins; and a second rate table, which would drift.
- **Invariant, checked on all 21 real sessions:** the session cost equals `run_analyzer`'s total,
  and every run's phase costs sum to its run cost, with 0 mismatches.
- **Baseline: 8 propose-ship-auto runs, $122 in total, median run $13.45, September 2026.**
  - Subagent gates are **26%** of the spend. The main thread's own turns are the rest.
  - The propose phase costs $39 (median $4.32), work $30 and review $24.
  - One subagent gate costs little but takes a long time. Median per run:

    | Gate | Cost | Wall time |
    |---|---|---|
    | Completion panel | $1.08 | 9.6 min |
    | Whole-proposal panel | $0.74 | 7.9 min |
    | Approach panel | $0.55 | 5.1 min |
    | Scope reviewer | $0.30 | 3.0 min |

## Implications
- Panels and reviewers cost more in **time** than in **money**. Cutting a panel buys back minutes
  and saves well under $1. Cost is mostly main-thread cache reads, which grow with every turn, so
  it tracks the length of the main context, not the number of adjudications.
- To cut cost, look first at the main thread's context in propose and work, not at the tiers.
  To cut time, look first at the tiers.
- Re-read `run_trace.py --all` before and after any tier or model change. The phase and gate
  `cost` columns sit next to the time columns for exactly this comparison.

## Related
- [[2026-09-26-decision-trace-orchestrator-time-from-transcripts]] — builds on
- [[2026-09-26-reference-claude-code-transcript-timing-facts]] — see also
- [[2026-09-26-decision-parallel-gate-waves-and-existing-interface-clause]] — see also
