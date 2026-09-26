# Orchestrator wall time is measured from transcripts by a repo dev tool, and panels dominate it

**Date**: 2026-09-26
**Type**: decision
**Summary**: scripts/run_trace.py traces propose-ship-auto time; propose-phase reviewer waits dominate
**Context**: .minerva/work/2026-09-26-trace-orchestrator-run-time (see git history if the worktree has been cleaned up)

## Context
Before changing how `minerva:propose-ship-auto` routes decisions (for example with a fast
classifier for tier selection), the question was where a run actually spends its time. The
existing tools didn't answer it. `decision_telemetry.py` counts outcomes by tier and gate with no
time. `run_analyzer.py` counts tokens, and at the time priced no current model and saw no
subagent.

## Finding
- **Chosen:** `scripts/run_trace.py`, a stdlib, read-only dev tool in the repo root next to
  `run_analyzer.py`. It rebuilds spans from transcripts: runs → phases → gate × tier × role →
  tools (Bash by command head) → subagents, per run and across runs with `--all`. It is not
  shipped in the minerva plugin, because transcripts are a Claude-Code-only format and the plugin
  promises Codex parity (`plugins/minerva/COMPATIBILITY.md`). The `capture-session` utils skill
  is its entry point.
- **Rejected:** a timing mode in `run_analyzer.py` (two concerns in a module `run_benchmark`
  pins), and a plugin script wired into a skill (host coupling).
- **Phases are inferred, never guessed.** Signals are searched only within their own run (one
  session can hold several runs). Each boundary names its event, and a missing or out-of-order
  signal is a printed warning. Command signals are read from shell structure, never substrings.
  Heredoc bodies and quoted strings are set aside, because a proposal that mentions
  `git worktree add` or `.minerva/knowledge/` is not doing it. Substring matching was wrong on
  about half of the real matches.
- **Panel vs reviewer is decided by launch batch, not by keyword.** A Proponent and Skeptic
  dispatched together form a panel even when no description says "panel". A lone Skeptic at the
  same gate is a reviewer.
- **Baseline (16 orchestrator runs, 6 of them propose-ship-auto, September 2026):**
  - Across all orchestrator runs, the propose phase is the largest: 2.7 h active plus 1.7 h of
    waits, most of it background waits on reviewer and panel subagents.
  - The costliest gates by subagent time are code review (49 min over 12 runs), completion
    panels (49 min over 5 runs) and whole-proposal panels (39 min over 5 runs).
  - A Skeptic typically takes 3–4 min against a Proponent's 1–1.5 min, and a panel's Arbiter
    runs even after quorum is already reached.
  - This unit's own run used 24 subagent dispatches. Four panels (one with a revision round)
    took 15 agents; five single reviewer or fold-audit dispatches and four code reviews took the
    rest. By the time the trace was taken, subagent compute had summed to 1.1 h, with 44 min of
    wall-clock union.

## Implications
- Base orchestrator-speed decisions on `run_trace.py --all`, not intuition. The first levers it
  points at are panel wall time in the propose phase (sequential Skeptic → fold-audit → panel
  chains) and skippable Arbiters once quorum is mathematically settled.
- Dispatching independent gates in parallel (scope and approach Skeptics; a fold-audit alongside
  the next gate's Skeptic; code review alongside completion) worked in this run with no rework.
  The trace then shows overlapping phases: the verify window shrank to 35 s, and the completion
  Arbiter reads as an out-of-order verify signal during review. That is honest, not a tracer bug.
- A classifier-based router (for example jev) can only save time where it removes a dispatch.
  Measure that against this baseline.

## Related
- [[2026-09-23-decision-one-orchestrator-picks-each-decisions-tier]] — see also
- [[2026-09-05-decision-balanced-rechecks-its-folds]] — see also
- [[2026-09-26-reference-claude-code-transcript-timing-facts]] — builds on
