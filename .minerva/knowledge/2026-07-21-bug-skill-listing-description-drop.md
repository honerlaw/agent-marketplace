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

## Related
- [[2026-07-21-constraint-skill-description-house-style]] — see also
