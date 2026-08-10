# Followups: knowledge-lint-detector

## 2026-06-02

- **Phase B.2 — the interactive `minerva:lint` skill.** Builds on the deterministic
  detector ([[2026-06-02-decision-phase-b-deterministic-lint-detector]]): a read-mostly
  `minerva:lint` SKILL.md that Bash-invokes `scripts/knowledge_lint.py` for mechanical
  findings, then adds the **LLM-judged** dimensions deferred from this unit — orphan
  detection, contradiction detection, stale/superseded-claim suggestions —
  presents everything in `minerva:review`'s finding/triage format, and applies
  **gated fixes** (index repair, missing-reciprocal insertion, supersession banners)
  respecting [[2026-06-02-constraint-promote-narrowed-never-overwrite]]. Per
  [[2026-05-31-decision-behavioral-evals-provisional]] the LLM-judged output stays
  advisory / off the deterministic CI gate. Adding this skill triggers the
  catalog-sync (010) + contract.json (012) obligations.

- **Duplicate-NNN detection in the linter** (deferred review finding). `parse_entry`
  keys the entry map by NNN, so two files sharing an NNN would silently collapse
  (last-writer-wins). It can't occur in a promote-managed corpus (NNN is
  auto-incremented), so it was deferred — but a drift detector could legitimately own
  a "duplicate NNN on disk" error. Cheap to add (~4 lines + a fixture) if it ever
  becomes a real risk.
