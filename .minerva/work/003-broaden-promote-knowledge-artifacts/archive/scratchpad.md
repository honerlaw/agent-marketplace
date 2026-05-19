# Scratchpad: broaden-promote-knowledge-artifacts

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `/promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## 2026-05-18 — implementation notes

- `init.md` Routing section detection was updated to accept both `.minerva/knowledge/` and `.minerva/decisions/` (the old name) so that re-runs on projects that had the old Routing section don't incorrectly re-write it.
- `test_plugin_readme_lists_all_four_commands` asserts `"decisions" in readme.lower()` — still passes because the README prose says "decisions made, bugs fixed, patterns discovered." No test change needed there.
- Files updated: `promote.md`, `init.md`, `using-minerva/SKILL.md`, `README.md`, `tests/test_minerva.py`. All 12 tests pass.
