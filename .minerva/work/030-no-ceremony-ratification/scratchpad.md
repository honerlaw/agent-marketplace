# Scratchpad: no-ceremony-ratification

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Notes 2026-06-06

- `tests/test_browser.py` / `tests/test_storage.py` fail pytest collection (`ModuleNotFoundError: No module named 'lib'`) on `main` too — pre-existing, unrelated to this unit. Scope test runs to `tests/test_skill_contracts.py tests/test_minerva.py` (94 passed).
- Origin of this unit: observed `propose-ship-auto` runs soliciting an up-front "ceremony + score-design ratification" and logging "STREAMLINED per user ratification + feedback memory" — the cited feedback memory did not exist in the project memory dir. The new section closes both the solicitation and the confabulated-evidence channels.

## Review triage 2026-06-06
- [FIXED] #1 low plugins/minerva/skills/propose-ship-auto/SKILL.md (Per-decision logging) — `[user-directed]` prefix introduced by clause (d) was absent from the log-prefix vocabulary section
- Review fix: propose-ship-auto/SKILL.md — added `[user-directed]` prefix line to Per-decision logging, cross-linked to No ceremony ratification

