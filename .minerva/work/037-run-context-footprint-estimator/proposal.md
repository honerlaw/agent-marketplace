# Proposal: run-context-footprint-estimator

**Date**: 2026-06-12
**Status**: Draft

## Goal

Measure and benchmark the **real** context usage and cost of a full `minerva:propose-ship-auto` run, so we can tell whether a change improves or worsens it. Two mechanisms plus CI wiring:

1. **Run analyzer** — `scripts/run_analyzer.py` (importable API + thin CLI) parses a Claude Code **session transcript JSONL** and reports the run's exact token usage (uncached input, output, cache-write-5m, cache-write-1h, cache-read) and the derived USD cost, broken down by turn, by tool, and by main-loop vs subagent (sidechain). Token counts are **exact** — read straight from the transcript's own `usage` records, not estimated.
2. **Benchmark harness** — `scripts/run_benchmark.py` drives a **fixed canned task** through `claude -p "<task>" --output-format json`, captures the result, runs the analyzer over the produced transcript, and **appends a record to a tracked baseline** (`benchmarks/baseline.jsonl`) keyed by git SHA + task id, so runs are comparable across commits. A diff helper reports the delta between two records for the same task.
3. **CI wiring** — a workflow triggered on a **cron schedule and explicit `workflow_dispatch`/label only** (never per-PR), gated on an `ANTHROPIC_API_KEY` secret, that runs the harness and surfaces the metrics.

**Supersedes this unit's original framing.** The first draft proposed a *static* estimator counting skill-markdown bytes. That measures only the fixed instruction surface (~a few % of a real run) and is blind to the dynamic cost that dominates — tool results, multi-turn re-billing, and subagent panels. The user redirected to measuring a real run. The static estimator and a per-PR CI gate are **explicitly out of scope** (user-deselected).

## Why

We have no way to see **real** per-run cost. `tests/test_skill_budget.py` caps each `SKILL.md` at 9KB — a per-file check ([[036-constraint-skill-progressive-disclosure]]) blind to what a run actually loads. The dominant cost of a `propose-ship-auto` run is dynamic: tool-result accumulation across turns, the context window re-billed every turn, and 3-agent `round-table` panels (each its own context window). None of that lives in the skill files; all of it lives in the run's transcript, which already records **exact** per-message token usage. A small analyzer over that transcript, plus a repeatable harness that pins the numbers to a baseline, is the smallest thing that answers "did this change move our usage?".

This also discharges unit 035's deferred followup #2 (the token-measurement gate that 036 left unmet because *no measurement artifact existed*): this unit builds the artifact.

## Approach

**1. Token usage — exact, from the transcript.** Claude Code writes per-session JSONL to `~/.claude/projects/<encoded-cwd>/<session>.jsonl`; each assistant message carries `message.usage` with `input_tokens`, `output_tokens`, `cache_read_input_tokens`, and `cache_creation: {ephemeral_5m_input_tokens, ephemeral_1h_input_tokens}` (shape verified against a live transcript in this repo). The analyzer sums these per message, attributes each to main-loop vs subagent via the transcript's sidechain marker, and groups `tool_use` blocks by tool name. **No tokenizer is involved** — and deliberately so: the claude-api reference is explicit that `tiktoken` must never be used for Claude (it undercounts ~15–20%, worse on code). The transcript's counts are the ground truth; any *future* need to count tokens of arbitrary text would use Anthropic's `count_tokens` endpoint, never tiktoken.

**2. Cost — token usage × a pricing table.** Per-model rates (per 1M tokens), as of 2026-06, sourced from the `claude-api` skill / platform pricing docs (dated, with a pointer to re-verify — pricing drifts):

| Model | input $/1M | output $/1M |
|---|---|---|
| `claude-opus-4-8` | 5 | 25 |
| `claude-sonnet-4-6` | 3 | 15 |
| `claude-haiku-4-5` | 1 | 5 |
| `claude-fable-5` | 10 | 50 |

Cache multipliers applied to the **input** rate: cache-write 5m = **1.25×**, cache-write 1h = **2×**, cache-read = **0.1×**. Per-message cost is therefore:

```
cost = input_tokens                      * in_rate
     + output_tokens                     * out_rate
     + ephemeral_5m_input_tokens         * in_rate * 1.25
     + ephemeral_1h_input_tokens         * in_rate * 2.0
     + cache_read_input_tokens           * in_rate * 0.1
```

Rates are keyed by the transcript's per-message `model` (normalizing suffixes like `[1m]` — Opus 4.8's 1M context is standard-priced, no long-context premium), so a run that mixes a main Opus loop with cheaper subagents prices each correctly. An unknown model id is reported as `unpriced`, never silently $0.

**3. Headline cross-check.** The harness runs the task via `claude -p --output-format json`, whose result already carries Claude Code's own `total_cost_usd`. The analyzer's independently-derived cost is asserted within a small tolerance of that number — a guard against pricing-table drift or a parsing bug.

**4. Benchmark harness + baseline.** A fixed, in-repo canned task (small, single-unit, additive — exercises the panels without a large diff) is run via `claude -p`; the harness records `{timestamp, git_sha, task_id, model, total_cost_usd, input, output, cache_write_5m, cache_write_1h, cache_read, num_turns, num_subagents, by_tool}` as one line appended to `benchmarks/baseline.jsonl` (committed, append-only, diffable). A `--diff` mode prints the delta between the two most recent records for a task id.

**5. CI.** `.github/workflows/benchmark.yml` triggers on `schedule` (cron) + `workflow_dispatch` only — **not** `pull_request` — gated on the `ANTHROPIC_API_KEY` secret, runs the harness, and uploads/commits the baseline record. This keeps the noisy, real-dollar run off every PR while still tracking the trend.

The analyzer is importable (functions return structured data; CLI is a thin `__main__`), so the harness and any future per-skill report build on it without re-parsing.

## Success criteria

- `python3 scripts/run_analyzer.py <transcript.jsonl>` prints exact totals for all five usage classes (uncached input, output, cache-write-5m, cache-write-1h, cache-read) plus a derived USD cost, broken down by turn, by tool, and by main-loop vs subagent.
- The analyzer's derived cost is within a small tolerance of Claude Code's own `total_cost_usd` for the same session (cross-check passes on a real `propose-ship-auto` transcript).
- Pricing table covers Opus 4.8 / Sonnet 4.6 / Haiku 4.5 / Fable 5 with the documented cache multipliers (write 1.25×/2×, read 0.1×), dated and pointer-sourced; an unknown model id surfaces as `unpriced`, never $0.
- `scripts/run_benchmark.py` runs the fixed task via `claude -p --output-format json` and appends one comparable record to `benchmarks/baseline.jsonl` keyed by git SHA + task id; `--diff` reports the delta between two records for a task.
- A CI workflow runs the benchmark on `schedule` + `workflow_dispatch` **only** (asserted: no `pull_request` trigger), gated on `ANTHROPIC_API_KEY`, and is added to CI's workflow set.
- **No `tiktoken`/tokenizer dependency anywhere** — token counts come from the transcript's exact `usage`; the pricing table is the only Claude-specific constant.
- An importable-API test pins the cost math (synthetic `usage` → expected USD) and the sidechain/tool attribution against a fixture transcript; if CI-wired, appended to the enumerated pytest list per [[035-constraint-ci-test-enumeration-explicit]].

## Open Questions

- **Determinism / noise.** A full auto run is non-deterministic, so a single benchmark number is noisy. Record one run now and revisit N-run averaging once we've seen the variance? (Recommended.) Worth noting input/cache token counts are far more stable run-to-run than output tokens — the analyzer reports them separately so the stabler signal isn't drowned by output variance.
- **Pricing drift.** The table is a dated snapshot. Manual dated updates (recommended — simple, offline, CI-friendly), or a live check against the pricing docs? The `total_cost_usd` cross-check (criterion 2) catches drift loudly either way.
- **Canned task choice.** What task is representative of a real run yet cheap and stable enough to benchmark repeatedly (each run is a few $ and several minutes)? Leaning toward a small single-unit additive task that still triggers the panels.
- **Baseline storage.** Committed `benchmarks/baseline.jsonl` (diffable in git, append-only) vs. a CI artifact. Recommended: committed jsonl.
- **Phase attribution.** Transcripts don't label lifecycle phases (propose/work/review/…) explicitly; deriving phase boundaries would need heuristics on skill-invocation markers. Out of scope for v1 — by-tool and by-subagent breakdowns ship; by-phase is a followup.
