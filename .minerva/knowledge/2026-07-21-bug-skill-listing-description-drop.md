# Skill-listing pipeline drops some valid frontmatter descriptions

**Date**: 2026-07-21
**Type**: bug
**Context**: .minerva/work/2026-07-21-skill-best-practices-audit (see git history if the worktree has been cleaned up)

## Context
The 046 best-practices audit's trigger diagnosis required checking what the model
actually sees at trigger time. The only pre-loaded trigger surface for a skill is its
frontmatter name + description (Anthropic skill docs); everything else loads after
invocation.

## Finding
In live sessions, `minerva:lint` and `minerva:lint-fix` render in the available-skills
listing as bare names with **no description at all**, despite valid, well-formed
frontmatter in every on-disk copy (source repo, installed plugin, plugin cache).
Verified in 3 independent contexts (the main session and two fresh-context reviewers),
one of which also separately observed `minerva:replan` render bare. Formatting is
byte-identical in kind to sibling skills that render fine (single-line YAML scalar,
same character classes), so simple YAML errors are ruled out; the drop happens in the
listing/registration pipeline, outside the skill text. Root cause not yet identified;
no fix is known as of this entry.

## Implications
A bare name cannot win any trigger decision — for affected skills, ambient triggering
is structurally impossible no matter how good the description is. The corrected
lint/lint-fix descriptions written in unit 046 are therefore **inert until the
pipeline defect is fixed**; do not expect behavior change from further description
polish on affected skills, and do not interpret their non-triggering as a prose
problem. Countermeasure seeds (loader diagnosis + a contract test that renders the
listing and asserts every description survives non-empty) live in unit 046's
followups.md.

## Update 2026-08-22 — re-observed, and the requested countermeasure is not writable
Observed live again while draining the followup backlog (issue #76, which asked for "a
contract test that renders the listing and asserts every description survives non-empty").

**The affected set moved.** `backfill-followups`, `lint`, `migrate-fix` and `replan`
rendered bare. `lint-fix` — bare in the original observation above — rendered **fine**,
with no source change between the two observations. So the defect is not sticky to a
skill; it moves.

**Two on-disk correlates are now ruled out**, measured across all 23 skills:
- *Frontmatter shape.* The bare set spans both frontmatter forms — `replan` and
  `backfill-followups` have 2-line frontmatter, `lint` and `migrate-fix` have 7-line.
- *Description length.* `lint` (630 chars) rendered bare while `lint-fix` (627 chars)
  rendered fine — same directory, same format, 3 characters apart.

**Consequence for the countermeasure.** Combined with the finding above that frontmatter
is valid in every on-disk copy, every property a repo-side test can reach is known-good on
precisely the skills that are broken. A disk-side contract test would therefore pass while
the defect is live — the exact failure mode
[[2026-08-10-pattern-presence-assertions-rot-into-green-lies]] records, and its own entry
notes two defects that shipped under passing anchors of that shape. The test issue #76
asked for **cannot be written against this repo**; the observable surface is the loader,
which is outside it. #76 was left open and re-aimed at diagnosing the loader rather than
closed by a test that cannot fail on the defect it names.

## Related
- [[2026-07-21-constraint-skill-description-house-style]] — see also
