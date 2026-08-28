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

- [reviewed — folded] completion verification: Verifier found a real hole — `reconciliation.md`
  guarded `knowledge_lint` while the same site also ran `synthesis_status.py` unguarded, and my
  `REGISTERED_SITES` pinned one (file, module) pair per file so the test could not see it. It also
  flagged unchecked transitive imports. Folded by switching to whole-directory comparison, which
  makes both unrepresentable rather than patched, and by counting guards against resolutions.

## The registration set was the thing hiding the bug

`REGISTERED_SITES` paired each file with one module name. That shape does not merely fail to
catch a second module at the same site — it *asserts there is only one*, to the test and to the
reader. `reconciliation.md` invokes `knowledge_lint` and `synthesis_status`; the set named the
first, the guard guarded the first, and the test confirmed the first. Everything agreed, and the
second was invisible at every layer simultaneously.

The general shape: a registry whose *cardinality* is wrong is worse than a missing registry,
because it manufactures agreement. A missing entry gets noticed when something fails; a wrong
arity produces a green test that certifies the incomplete picture.

The fix was not to add the missing pair. It was to remove the dimension — compare the whole
directory, so there is no module to name, no second module to forget, and no pairing to get
wrong. Deleting the parameter deleted the bug class along with the transitive-import hole nobody
had thought about yet.

## Per-module scoping looked precise and was just narrow

I chose a module argument to avoid firing on unrelated edits. That precision was imaginary: every
module in `scripts/` imports siblings, so "this one module is current" never implied "the code
that will run is current". Directory scope is coarser and strictly more correct, and the noise I
was avoiding is exactly the signal — if anything in the directory differs, the directory you would
import from is not the one you are editing.
