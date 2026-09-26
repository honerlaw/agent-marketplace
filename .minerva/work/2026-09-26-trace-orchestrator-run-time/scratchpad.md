# Scratchpad: trace-orchestrator-run-time

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-09-26
- [reviewed — clean] scope check: one unit, one PR, no phases (tier: reviewer — judgment call, solo's mechanical-evidence clause fails; Skeptic accepted, noted but dismissed: test size likely ~1:1 with impl so total diff ~900–1300 lines, still within repo's one-PR norm (#131 shipped 2,213 lines); phasing the phase-inference heuristic out was weighed — not dominant, the proposal already has a fallback)
- [reviewed — folded] approach: option A (new root scripts/run_trace.py dev tool) over B (extend run_analyzer) and C (ship in plugin, host-coupled to Claude transcripts vs Codex parity); folded Skeptic item 2 (one session file holds multiple orchestrator runs — added run segmentation) plus low items 3 (partition vs overlap note), 4 (plugins/utils surface named), 5 (broaden capture-session description), 1 (dedupe re-implementation rationale) (tier: reviewer)
- [rechecked — clean] approach: fold-audit confirmed items 1–5 addressed; one low new concern (standalone non-orchestrator skill calls between runs fall into the prior run's tail) — not load-bearing, handled in implementation
- [reviewed — folded] whole-proposal: folded Skeptic items 1 (tier by (gate, round) grouping — real panels omit the word "panel") and 2 (deferral bar: absorb both run_analyzer defects in-unit) plus lows 3 (command-head definition), 4 (replan events not ordering warnings) (tier: reviewer)
- [rechecked — escalated] whole-proposal: fold-audit raised a load-bearing new concern — absorbed fix 9(b) double-counts against run_benchmark's manual --subagent flow → panel
- [panel — 0/3 accept] whole-proposal: all three revise — 9(b) unconditional sidecar discovery double-counts via build_record's subagent_paths AND flips cost_crosscheck_ok on cmd_run (Claude's total excludes subagent sessions); steps 1–8 sound (tier: panel — fold-audit escalation)
- [panel — 3/3 accept, 2 with fixes] whole-proposal: revised 9(b) to opt-in include_subagent_files=False (CLI on, --main-only), real-layout tests, per-model cache-read overrides (tier: panel — revision round)
    - fix (skeptic/arbiter): step 8 states the capture-session step invokes scripts/run_trace.py <transcript.jsonl>
    - fix (skeptic/arbiter): 9(b) states the main-file/sidecar non-overlap assumption; shared message-id dedupe guards hybrid transcripts
- note: approach fold-audit and whole-proposal Skeptic were dispatched in parallel (scope + approach Skeptics likewise) to cut wall time; no gate's artifact depended on an unresolved sibling
