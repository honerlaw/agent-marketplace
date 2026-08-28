# Scratchpad: observable-orchestrator-mode

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Balanced decisions 2026-08-28

- [decided] Phase 1 skipped — the work unit was created earlier this session with the USER adjudicating scope and approach directly, and the plan stress-tested through `minerva:grill-plan`. A human at both gates strictly dominates a Sonnet Skeptic, so re-running them would be ceremony.
- [decided] pre-flight in-flight check: the only in-flight unit is this run's own, created minutes earlier at the user's approval. A resume, not a collision — the check exists to detect *other* efforts. Counter stays 0.
- [decided] mode-argument spelling `--auto=<orchestrator>` carries the caller as its value, not a bare boolean. `ship` needs the caller identity to hand back to the right orchestrator's Phase 7, so a boolean would have needed a second channel.
- [decided] `cleanup` keeps `--yes` rather than gaining `--auto`. It skips one destructive-action confirmation, not a set of strategic gates; forcing one spelling would have made the test assume a spelling and false-positive on the one skill that already had this right.
- [decided] the invocation/citation boundary is drawn at the literal marker "via the `Skill` tool" plus an explicit per-orchestrator `## Delegated skills` inventory, rather than by classifying prose. Prose classification was tried on paper first and could not separate "Append the entry per `minerva:replan`'s 'On approval — file write'" (citation) from a real delegation without a brittle verb list.
- [decided] extracted `cleanup`'s "Merge detection per worktree" (1211 bytes) to `references/merge-detection.md`. Adding the required declaration pushed cleanup 341 bytes over the 9216 budget; extraction is what the budget test's own failure message prescribes.

## Findings 2026-08-28

- **The mutation check found a vacuous test, and nothing else would have.** `test_every_skill_tool_invocation_carries_its_mode_argument` passed while the argument was deleted from the ship invocation. Cause: `SKILL_MENTION_RE` required a closing backtick (`` `minerva:([a-z-]+)` ``), but an invocation is written ``Invoke `minerva:ship <date-slug> --auto=X` via the `Skill` tool`` — the skill name is followed by a space, not a backtick. The regex matched nothing on the single line the check exists to guard. Another instance of `2026-08-11-pattern-a-gate-blind-to-what-it-checks`, and the reason the proposal demanded verification by deletion rather than by assertion.
- **Both halves of a two-sided boundary need testing.** Widening the mention regex to fix the above could have started matching citations; re-running the green-direction check (a citation without the argument stays green) is what confirmed it did not. A boundary asserted in one direction only is half-tested.
- `~/.claude/plugins/minerva` is a symlink to the PRIMARY checkout, so skill prose edited in a linked worktree is not what the running session loads. Irrelevant to this unit's criteria (pytest resolves `REPO_ROOT` from `__file__`, so it reads the worktree copy) but it means prose changes cannot be exercised behaviorally from here. Reported by a sibling session; independently confirmed via `readlink -f`. Tracked by that session as #104 — not this unit's to fix.
- Extracting `cleanup`'s merge-detection section silently removed the only pointer to `references/phased-units.md`, which the reference-integrity tests caught. Moving a section moves every pointer inside it — check what the section was carrying, not just what it said.
