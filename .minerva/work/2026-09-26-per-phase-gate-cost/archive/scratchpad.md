# Scratchpad: per-phase-gate-cost

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-09-26
- [solo] scope check: one unit, one PR, no phases (tier: solo predicate — additive to one dev tool + its tests + one doc, verified by tests, no existing-interface change; parallel wave)
- [reviewed — clean] approach: A — import run_analyzer's pricing helpers into run_trace; rejected B (per-phase cost in run_analyzer: phase inference there, module pinned by run_benchmark) and C (duplicate PRICING: drift). Skeptic notes carried into work: legacy isSidechain classification, a main-scope equality test against analyze_transcript, the gate-table alignment test needs updating, capture-session callouts (tier: reviewer — adds JSON/CLI output fields so solo denied; interface-clause doubt on capture-session-documented columns passed to the Skeptic, answered no: additive, every consumer co-updated in-unit; parallel wave)
- [reviewed — folded] whole-proposal: session-wide message.id dedup across main + sidecars, isSidechain lines as subagent_usd with no gate row, unpriced_models per run and session; criterion 3 fixture now carries a cross-source duplicate id and an isSidechain line (tier: reviewer — default; parallel wave; restart check: no staleness condition held)
- [rechecked — clean] whole-proposal: fold-audit confirmed items 1–3 addressed; low residual (phase subagent_usd vs sum of gate rows with legacy isSidechain lines) documented in Approach
- [reviewed — clean] completion verification: Verifier reproduced all 6 criteria (live JSON dump, hand-traced dedupe fixture, 1125 tests, run_analyzer diff empty) (tier: reviewer floor — no interface change beyond what approach/whole-proposal approved; code review dispatched alongside it)
- [solo] review triage: 4 FIX / 0 SUGGEST / 0 IGNORE — 1 (text never printed the session cost that equals run_analyzer → `session cost` line + doc), 2 (timestamp-less lines unbilled → bill from raw lines in file order via billing_lines), 3 (malformed usage/model crashed the whole trace → bills as empty), 4 (unlinked sidecar after the last main event missed by the last run → cost window uses cost_hi); plus the reviewer's test gaps (multi-run/gap spend, phase cost alignment, median over runs lacking a gate) (tier: default-solo row — every finding had a reproduced failure scenario and one dominant disposition; none changes the approach, so no replan-vs-FIX panel)
- [solo] promote partition: 1 PROMOTE (decision entry: cost priced per phase/gate + 8-run baseline — subagent gates 26% of spend, panels cost time not money) / 3 MERGE INTO PROPOSAL (billing_lines, cost_hi end-of-file ownership, malformed-usage tolerance → Approach rewrite) / 1 DISCARD (regex guard note — test detail) / 0 TODO (tier: default-solo row — no entry had two defensible buckets)

## Work notes
- Real-data check (session 142b3687, the #137 run): run_trace session cost $14.035653 vs run_analyzer $14.035654 (6-dp rounding); run phases sum exactly to the run's $10.85.
- The last run's final phase extends to +inf for cost when the run reaches end of file, so a message stamped at the file's last instant (or a later legacy sidechain line) is not lost to the half-open window.
- The no-pricing test matches rate-table assignments (`*PRICING*` / `*_MULT*` =), not mentions — the docstring names PRICING and MULTIPLEXERS exists.
- Review fixes verified on all 21 real sessions: session cost == run_analyzer total and every run's phases sum to its run cost (0 mismatches); 1131 tests pass.
