# Scratchpad: run-context-footprint-estimator

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Seed run finding 2026-06-12

- Analyzer validated against two real transcripts: pong run ($0.1267 reported →
  $0.12621 derived) and the seed auto run ($0.6464728 reported → $0.64589
  derived, within 0.1%). Cross-check passes.
- **Bug caught by the cross-check (now fixed + regression-tested):** Claude Code
  writes each assistant message to the transcript multiple times as it streams
  (same `message.id`, identical `usage`); the first analyzer summed per line and
  overshot ~2.5x. Fix: dedupe usage by `message.id`, tools by block id.
- **Headless limitation (finding):** a full `minerva:propose-ship-auto` run via
  `claude -p` does NOT complete the lifecycle — it bails at Phase 1 on
  worktree-creation ("environment not configured for autonomous operation"); the
  worktree/`EnterWorktree` flow needs the interactive harness. The seed
  ($0.65, 40 turns, 28 msgs) therefore measures propose + context-assembly +
  panel-machinery load, not a full run. A representative full-run baseline needs
  a transcript from an interactive auto run (feed it via `run_benchmark.py
  record`), not a headless `run`.
