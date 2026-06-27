# Scratchpad: drop-enterworktree-prefixed-paths

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Quick decisions 2026-06-27
- [escalated to user] mechanism: relocate to `.claude/worktrees/` vs drop-EnterWorktree-use-prefixed-paths vs resilient-EnterWorktree-with-fallback — genuine high-blast-radius cross-cutting fork, no dominant option → user picked **drop EnterWorktree, use `.minerva/worktrees/<NNN-slug>/`-prefixed paths + `git -C`**, keeping the `.minerva/` worktree home.
- [decided] scope check: single work unit — one consistent prose transformation across ~13 skill/record files, no code logic. Broad but shallow; approach locked by the escalation, so fast path holds.
- [decided] keep knowledge 008's filename/slug stable (preserve `[[008-…]]` wikilinks) and rewrite its body, rather than rename or supersede-with-new-file — avoids churn across overview/index/005/007/archives.
- [decided] dogfood: created worktree 044 via `git worktree add` and operate via the `.minerva/worktrees/044-.../` prefix for this run — no EnterWorktree call.
- [decided] completion: criterion #1's literal "grep returns nothing" is met in spirit, not letter — the skills now contain explicit `EnterWorktree` *prohibitions* ("do not call…"), which is stronger than silence. Refine the criterion wording at promote to "no skill instructs a call; remaining mentions are prohibitions / historical context in 008." Minor wording refinement, not a load-bearing divergence → no replan.

## Notes
- 15 files edited, all via worktree-prefixed paths; verified parent repo `main` stayed clean (no misroute). The footgun the user accepted (Option B) was real and present this whole run — every Edit needed the `.minerva/worktrees/044-…/` prefix.
- Verification: `grep EnterWorktree plugins/minerva/skills/` → only prohibitions; no "relative to the worktree root" / "inside the worktree session" left; `pytest tests/test_skill_contracts.py tests/test_skill_budget.py` → 209 passed; `scripts/knowledge_lint.py` → clean.
- evals/README.md example anchor swapped `EnterWorktree` → `git worktree add` (still present in on-approval.md).
