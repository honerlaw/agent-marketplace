# Proposal: drop-enterworktree-prefixed-paths

**Date**: 2026-06-27
**Status**: Draft

## Goal

Remove every minerva instruction to call the built-in `EnterWorktree` (and `ExitWorktree`) tool. Replace it with **explicit worktree-prefixed addressing**: the session's working directory stays the parent repo, and skills operate on a work unit's worktree by prefixing every file path with `.minerva/worktrees/<NNN-slug>/` and running every git command as `git -C .minerva/worktrees/<NNN-slug> …`. The `.minerva/worktrees/` home is unchanged.

## Why

`EnterWorktree`'s contract only reliably switches the session into worktrees under `.claude/worktrees/`. The already-in-a-worktree and pinned-subagent cases *require* that location; minerva's worktrees live under `.minerva/worktrees/`, so the `EnterWorktree path: ".minerva/worktrees/<NNN-slug>"` calls minerva sprinkles through its lifecycle are unsupported there and get rejected in exactly the contexts the orchestrators run in (re-entry, subagents). The skills only "work" today because the model improvises a fallback. Addressing the worktree by explicit prefix + `git -C` works in **every** context, with no dependence on a tool that may reject the path.

The tradeoff (chosen by the user over relocating to `.claude/worktrees/`): no session cwd switch means relative paths resolve to the parent repo, so the work phase must prefix every path it touches. That footgun is documented in knowledge entry 008; this change makes prefixed addressing the standing operating model and strengthens the guard language so the footgun is signposted rather than incidental.

## Approach

A single, consistent transformation applied across every site that currently names `EnterWorktree`:

1. **Creation sites** (`propose/references/on-approval.md` step 7; `propose-ship-auto/references/phases.md`; `propose-ship-quick/references/phases.md`): replace the `EnterWorktree path:` step with an "address the worktree directly" step — do not enter; keep cwd at the parent repo; prefix all later file paths with `.minerva/worktrees/<NNN-slug>/` and use `git -C`. Fix the downstream "inside the worktree" / "relative to the worktree root" phrasings (on-approval.md lines 5, 51; the post-write gate) to the prefixed-path model.
2. **Re-entry sites** (`work/SKILL.md` primary + resurrection paths; `replan`, `review/references/protocol.md`, `promote`, `ship/references/protocol.md` "Worktree entry" blocks): rename to "Worktree addressing"; replace the `EnterWorktree` call with the set-the-root + prefix-everything + `git -C` rule. Drop the now-moot "if already in the worktree, do nothing" branch (the session is never moved into the worktree). Keep the "docs only on default branch → operate on parent repo" branch. Fix `work/SKILL.md:56`'s "All paths below are relative to the worktree root" to "prefixed with the worktree root".
3. **propose/SKILL.md:44** summary line: drop `EnterWorktree` from the listed sequence.
4. **cleanup/SKILL.md:28**: reword the "Unlike other lifecycle skills, cleanup does not call `EnterWorktree`" contrast — no skill calls it anymore; state cleanup's actual invariant (it must run from the parent repo, never from inside a worktree being removed).
5. **Records**: `evals/README.md:31` illustrative anchor (swap `EnterWorktree` for a still-present substring like `git worktree add`); knowledge `007` (reword its two EnterWorktree mentions — the "call the concrete tool, not prose" principle stays, the example changes); knowledge `008` (keep slug/filename so `[[008-…]]` wikilinks resolve; rewrite H1 + Finding + Implications so it documents prefixed-path addressing as the standing model and notes EnterWorktree's removal); `index.md:41` catalog line to match 008's new summary; `overview.md:141` clause that references EnterWorktree.
6. **Promote phase** records the durable decision as a new `decision`-type knowledge entry and reconciles cross-refs; `minerva:synthesize` refreshes `overview.md` if scope warrants.

Canonical replacement wording (applied verbatim, adjusted per site):
> **Do not call `EnterWorktree`.** minerva worktrees live under `.minerva/worktrees/`, which that tool does not reliably enter; the session's working directory stays the parent repo. Set the worktree root to `.minerva/worktrees/<NNN-slug>/`, prefix **every** file path this skill reads or writes with it, and run **every** git command as `git -C .minerva/worktrees/<NNN-slug> …`. Relative paths resolve to the parent repo and will silently misroute edits onto the wrong branch (see `.minerva/knowledge/008-constraint-enter-worktree-absolute-paths.md`).

## Success criteria

- No operative minerva skill file instructs a call to `EnterWorktree` or `ExitWorktree` (`grep -rn 'EnterWorktree\|ExitWorktree' plugins/minerva/skills/` returns nothing).
- Every former call site instead names the prefixed-path + `git -C .minerva/worktrees/<NNN-slug>` mechanism, and no skill still claims paths are "relative to the worktree root" or that operations run "inside the worktree session".
- `cleanup/SKILL.md`'s worktree pre-flight no longer contrasts against other skills "calling EnterWorktree"; it states cleanup's own parent-repo invariant.
- `evals/README.md` no longer uses `EnterWorktree` as its example anchor, and the example substring it does use is actually present in `references/on-approval.md`.
- Knowledge 007 keeps its principle but drops the EnterWorktree mandate; knowledge 008 documents prefixed-path addressing as the standing model with its `[[008-…]]` slug unchanged; `index.md` line for 008 matches its new summary; `overview.md` has no stale EnterWorktree claim.
- The test suite passes (`pytest tests/test_skill_contracts.py tests/test_skill_budget.py`), confirming no contract anchor regressed.
- A new `decision`-type knowledge entry captures the EnterWorktree-removal decision (created at promote).

## Open Questions

- None blocking. (Relocating to `.claude/worktrees/` was considered and rejected by the user in favor of keeping the `.minerva/` home.)
