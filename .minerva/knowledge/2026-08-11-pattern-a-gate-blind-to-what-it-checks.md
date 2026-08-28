# A gate that shares the tool's blind spot certifies the blind spot

**Date**: 2026-08-11
**Type**: pattern
**Summary**: lint read clean before AND after 182 references broke, because its model of "a reference" was the writer's model; a clean gate is evidence only over what the gate can see
**Context**: .minerva/work/2026-08-11-close-silent-reference-gaps

## Context
`knowledge_rename` moves every entry in a corpus and retargets the references. It handled
`[[wikilinks]]`, `<!-- superseded-by: -->` markers and `**Context**: .minerva/work/…`
paths — but not an entry referenced by *path*: `.minerva/knowledge/<stem>.md` in prose or
backticks, or a markdown link `[text](<stem>.md)`.

**182 unique references broke in one real migration.** All 182 resolved before; none
after. And `knowledge_lint` reported the corpus clean on **both** sides — because the
linter's edge model is also `[[wikilinks]]` only. The gate could not see the form that
broke, so it certified the breakage.

Two more instances surfaced in the same subsystem, both in checks whose job was to confirm
a migration had worked:

- `migrate-fix`'s verification grep, `\[\[[0-9]{3,}-`, matches the `2026` of every
  correctly-migrated `[[2026-05-19-…]]` link — **6,005 hits on a corpus with 26 real
  leftovers**, while the skill text told the reader to expect near-zero. The check that
  proves success reported catastrophic failure every run.
- `minerva:lint`'s orphan query keyed its graph on `nnn`, which under date ids **is the
  date**. 642 entries collapsed into ~85 buckets, so a linked entry made its same-day
  neighbours look linked: **0 orphans reported against 14 real ones.**

## Finding
**A validation gate is evidence only over the forms it models. When the gate's model is
inherited from — or coincides with — the model of the thing it validates, a clean result
carries no information about the shared blind spot.**

This is worse than an absent gate. An absent gate prompts a manual check; a green one ends
the investigation. Every instance above was found by accident — by running the tool on a
real corpus and reading the output — never by the gate.

Three practical consequences:

1. **A clean gate does not license "no regression".** When a change adds a form the gate
   cannot see, the coverage must come from a **fixture that fails before the fix**. On the
   repo where this was fixed, 0 of 62 entries exhibited the divergent shape at all, so a
   clean lint run proved exactly nothing and every fix needed a synthetic corpus.
2. **A check written in the same idiom as its subject inherits its bugs.** The
   date-id migration broke the tools that verify date-id migrations, because they were
   written when ids were `NNN` and the pattern `[0-9]{3,}` silently began matching years.
   After changing an identifier's *shape*, re-read every pattern that matches it — most
   will still match, wrongly.
3. **Prefer a check that dereferences the thing.** The orphan query got this right in
   spirit (it imports the detector's own parser "so the edge model can't drift") and wrong
   in fact (it then keyed on the wrong field). Importing the right module is not the same
   as using the right field from it.

## Implications
- When a writer gains a new reference form, ask what *else* would notice if that form
  broke. If the answer is nothing, the form needs its own detection, not just its own
  rewriting.
- Snippets embedded in documentation are code and rot like code. Both broken checks here
  lived in `SKILL.md` files, where the test layer only ever asserted substring presence —
  green over a snippet that had never been run
  ([[2026-08-10-pattern-presence-assertions-rot-into-green-lies]]). Test them by
  **extracting the snippet from the markdown and executing it** against a fixture; a
  rewrite that reintroduces the bug then fails CI, while a rewording still passes.
- A count is a check too. A reference the tool will not rewrite must still be *reported*:
  not rewriting bare `[[139]]` shorthand is defensible (resolving by number alone was
  wrong in ~6 of 23 cases — usually the same-numbered work unit), but doing it silently is
  not, because after the rename that number appears in no filename at all.
- The tell: a tool and its verifier that share a regex, a parser, or an author's mental
  model of what the data looks like.

## Related
- [[2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant]] — see also
- [[2026-08-10-pattern-presence-assertions-rot-into-green-lies]] — builds on
- [[2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption]] — see also
- [[2026-06-03-decision-migration-check-read-only-entry-re-blindspot]] — builds on
- [[2026-08-11-decision-ci-runs-the-whole-suite]] — see also
- [[2026-08-22-constraint-a-skill-cannot-path-reference-a-sibling-skills-reference-file]] — see also
- [[2026-08-22-pattern-a-ledger-line-is-not-a-resolution]] — see also
- [[2026-08-28-pattern-a-decider-and-an-executor-are-different-surfaces]] — see also
- [[2026-08-28-pattern-a-presence-assertion-must-be-scoped-to-what-it-guards]] — see also
- [[2026-08-28-bug-a-worktree-glob-sees-every-unit-in-the-project]] — see also
