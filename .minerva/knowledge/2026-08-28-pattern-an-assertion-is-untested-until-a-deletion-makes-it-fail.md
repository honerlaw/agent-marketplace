---
name: an-assertion-is-untested-until-a-deletion-makes-it-fail
description: Use when adding any contract test or corpus assertion — budget a deletion pass per assertion, not per file, because reading an assertion cannot establish that it can fail. Covers the two ways a per-item check silently degrades into an any-item check.
metadata:
  type: pattern
---

# An assertion is untested until you delete what it guards and watch it fail

**Date**: 2026-08-28
**Type**: pattern
**Summary**: Budget a deletion pass per assertion; five vacuous checks in one unit all read clean
**Context**: .minerva/work/2026-08-28-observable-orchestrator-mode (see git history if the worktree has been cleaned up)

## Context

[[2026-08-28-pattern-a-presence-assertion-must-be-scoped-to-what-it-guards]] established, from one
instance, that a whole-file presence check stays green when the enforcement is deleted, and that
mutation-testing is what exposes it. This entry is what a second unit found when it made that
mutation pass a *requirement* rather than a technique: the failure is more common than the scoping
rule alone predicts, and it has causes that scoping does not cover.

Two contract tests over skill prose, written by an author who had read that entry, contained
**five** vacuous assertions. Three were inside tests written specifically to prevent this class of
defect — one of them written to guard a finding a reviewer had raised minutes earlier. All five
passed, read correctly by eye, and were caught only by deletion.

## Finding

**Reading an assertion cannot establish that it can fail. Only removing its subject can.** The
discipline is a deletion pass **per assertion**, not per file: four of these five sat beside
assertions that were sound.

Beyond scoping (the prior entry's rule, which accounts for two of the five), two distinct causes —
both of which turn a *per-item* check into an *any-item* check:

1. **A discriminator shared across items.** The guarded token was `--auto=<orchestrator>`, identical
   for every skill named in a file. A check that each inlined skill names its mode argument was
   therefore satisfied for all of them by any single occurrence. The fix is to require the token and
   the item's own name on the same line — a per-item invariant needs a per-item discriminator.
2. **Accepting a union of spellings where the item declares one.** A reachability check accepted
   `--auto` *or* `--yes` for every skill. A line naming `minerva:synthesize` beside an unrelated
   `--yes` satisfied it, though synthesize declares `--auto`. Read each item's declaration and match
   that; the union is not a tolerant reader, it is a blind one.

The fifth is the inverse failure and worth naming because scoping advice does not predict it: a
regex that was too **strict** matched nothing at all. It required a closing backtick that real
invocation lines lack (``Invoke `minerva:ship <slug> --auto=X` via the `Skill` tool``), so it was
silently vacuous on the single line the check existed to guard. Over-narrow and over-broad produce
the identical symptom — a green suite — and neither is visible by reading.

## Implications

- **A contract test is not done when it passes.** It is done when you have deleted its subject,
  seen red, restored, and seen green again. Treat the deletion pass as part of writing the test.
- **Restore from a saved copy, not from git.** The files under test are usually
  tracked-and-modified, so `git checkout --` discards the unit's own work. Read the text, mutate,
  run, write the saved text back, and assert the restore succeeded.
- **Verify a boundary in both directions.** Where a check must fire on X but not on Y, mutate for
  both: the fix for an over-broad match is an over-narrow one, and only the Y-direction pass
  catches it.
- Expect this during review, not only during authoring. A reviewer asked to hunt for vacuous
  assertions found one the author had missed; the author then wrote a vacuous guard for it.

## Related
- [[2026-08-28-pattern-a-presence-assertion-must-be-scoped-to-what-it-guards]] — builds on
- [[2026-08-10-pattern-presence-assertions-rot-into-green-lies]] — builds on
- [[2026-08-11-pattern-a-gate-blind-to-what-it-checks]] — see also
- [[2026-08-11-pattern-a-tolerant-reader-needs-a-boundary]] — see also
- [[2026-08-28-pattern-a-coverage-claim-inherits-its-derivations-horizon]] — see also
- [[2026-08-30-pattern-anchor-the-clause-not-its-framing]] — see also
