# Scratchpad: guard-stale-script-resolution

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Balanced decisions 2026-08-28

- [decided] #104's diagnosis was wrong and I filed it. `~/.claude/plugins/minerva` is a symlink to
  the primary checkout; there is no deployed copy to lag. Corrected the issue body before scoping.
- [reviewed — folded] scope: one unit, one PR, no phases. Skeptic argued for phasing (docs vs the
  12-site mechanical edit). Folded its three high-severity dependencies — the adjacent knowledge
  entry needing delimitation, the byte-exact `test_skill_snippets.py` substitution, and an explicit
  no-op-for-consumers requirement — but kept one PR: its phasing argument rested on landing the
  #104 correction fast, and an issue edit is not gated on a merge, so that was done immediately.
- [reviewed — folded] approach: Skeptic rejected the printed-warning mechanism as unenforced —
  correct, and the same precedent I used to reject documentation-only. Guard is now a hard
  non-zero exit with a `MINERVA_SCRIPTS` escape hatch. Also folded: record WHY a session-scoped
  symlink repoint is rejected (concurrent worktrees) rather than calling it impossible.
- [decided] guard is one line invoking a single-sourced `scripts/plugin_guard.py`, not four lines
  duplicated twelve times. Twelve near-identical bash blocks is the six-copies shape this repo has
  already been burned by; a stale checkout missing the script fails loudly, which is the right
  signal anyway.
