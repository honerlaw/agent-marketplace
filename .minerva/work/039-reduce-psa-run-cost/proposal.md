# Proposal: reduce-psa-run-cost

**Date**: 2026-06-13
**Status**: Draft

## Goal

Reduce the cost of `minerva:propose-ship-auto` runs based on empirical benchmark evidence, without degrading round-table panel quality, and make those savings measurable in the benchmark.

## Why

The `psa-combined-score-everywhere` real run (2026-06-13) cost **$47.999** for the main session (Opus 4.8) plus an estimated **$10–15 uncaptured** for 27 Agent-spawned round-table subagents. Three root causes:

1. **Round-table subagents inherit the main session's Opus model.** `round-table/SKILL.md` specifies `subagent_type: general-purpose` but no `model:` parameter, so all 3 agents per panel default to the main session's model. Panel roles — Proponent defends, Skeptic critiques, Arbiter weighs — are structured judgment tasks that Sonnet handles comparably to Opus at ~1.67× cheaper input/cache rates and ~1.67× cheaper output rates.

2. **Subagent costs are invisible to the benchmark.** `run_analyzer.py` splits costs via the `isSidechain` field in the main transcript. Agent-spawned subagents write to *separate* JSONL files; they have no `isSidechain` flag in the main transcript. `run_benchmark.py record` accepts only one transcript path, so `subagent_cost_usd: 0.0` always appears in the baseline even when panels genuinely ran and spent real money.

3. **No context size guidance for panel CONTEXT blocks.** `round-table/SKILL.md` says "There is no size cap" for the CONTEXT inclusion list. A large `proposal.md` (5K+ tokens) included verbatim in all 3 agent prompts per panel wastes 1h-cache-write budget when only one section is relevant to the specific decision under review.

## Approach

Three targeted changes, in implementation order:

**Change 1 — `round-table/SKILL.md` Dispatch section:** After "Use `subagent_type: general-purpose` unless a more specialized agent fits the decision", add: "Pass `model: "sonnet"` in each Agent tool call for Proponent, Skeptic, and Arbiter." This follows the identical pattern as the existing `subagent_type` guidance — both are instructions to the LLM running the skill to include the named parameter in each Agent invocation. The `model` field is a valid Agent tool parameter (enum: `sonnet`/`opus`/`haiku`/`fable`) that overrides the inherited session model.

**Change 2 — `round-table/SKILL.md` CONTEXT section:** After "There is no size cap: the list bounds *what kinds* of input the panel sees, not how much.", add: "When `proposal.md` exceeds roughly 2,000 tokens, include only the section most relevant to the decision under review (e.g. `## Approach` for approach-selection panels, `## Success criteria` for completion-verification panels) rather than the full document."

**Change 3 — `scripts/run_benchmark.py record` subcommand:** Add a repeatable `--subagent <path>` flag following the existing `--flag value` parser pattern. `build_record` gains an optional `subagent_paths=[]` parameter; for each path it calls `analyze_transcript` and additively merges the result into `subagent_cost_usd` (sum) and `by_model` (sum per model key). The baseline record's `subagent_cost_usd` field then reflects actual panel spend when sibling transcript paths are provided. **Transcript paths are provided manually** — Claude Code writes Agent-spawned subagent transcripts as separate JSONL files in `~/.claude/projects/<encoded-cwd>/`; auto-discovery by session window is explicitly out of scope for this unit.

## Success criteria

1. `round-table/SKILL.md` Dispatch section includes: "Pass `model: "sonnet"` in each Agent tool call for Proponent, Skeptic, and Arbiter."
2. `round-table/SKILL.md` CONTEXT section includes context-trimming guidance for `proposal.md` exceeding ~2,000 tokens.
3. `run_benchmark.py record --subagent <path>` (repeatable) works; a baseline record produced with sibling transcript paths shows non-zero `subagent_cost_usd`.
4. A unit test for `build_record` with subagent paths is added to `tests/test_run_analyzer.py` and appended to the enumerated pytest list per [[035-constraint-ci-test-enumeration-explicit]]. `build_record` is a pure function — no conditionality on testability.
5. No skill catalog surfaces require updates (no skill is added or removed; per [[010-constraint-minerva-skill-catalog-sync]]).
6. `round-table/SKILL.md` remains ≤9KB after the additions per [[036-constraint-skill-progressive-disclosure]].

## Open Questions

None — the approach is fully determined by empirical evidence from the `psa-combined-score-everywhere` benchmark record.
