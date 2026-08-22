# A skill may path-reference a sibling skill's reference file, via a qualified pointer

**Date**: 2026-08-22
**Type**: decision
**Summary**: the pointer gate now resolves `plugins/minerva/skills/<skill>/references/<f>.md` against the NAMED skill, dissolving the constraint that made cross-skill citation unrepresentable

**Context**: .minerva/work/2026-08-22-close-open-issue-backlog (see git history if the worktree has been cleaned up)

## Context

[[2026-08-22-constraint-a-skill-cannot-path-reference-a-sibling-skills-reference-file]]
recorded that a cross-skill reference could not be written as a path.
`test_skill_budget.REF_MENTION_RE` was unanchored, so a fully-qualified
`plugins/minerva/skills/promote/references/github-issues.md` matched as bare
`references/github-issues.md` and was resolved against the **citing** skill, where it
dangled. `minerva:backfill-followups` had to phrase around it in prose.

That constraint was inert while every skill's references were private to it. It stopped
being inert once skills began reusing each other's protocols verbatim instead of restating
them — which is the pattern to prefer, since a restated protocol is a second derivation that
drifts.

## Finding

The gate now recognises two pointer forms. A **bare** `references/<f>.md` resolves under the
citing skill, as before. A **qualified** `plugins/minerva/skills/<skill>/references/<f>.md`
resolves under the skill it names. Qualified mentions are matched and stripped **before** the
bare pass, because a qualified path literally contains a bare-looking tail and attributing
that tail to the citing skill was the entire defect.

Two properties are deliberately preserved:
- **The orphan check stays local.** `test_every_reference_file_is_pointed_to` still requires
  a reference file to be pointed at from its **own** skill's `SKILL.md`. A foreign mention
  does not satisfy it, or a file could become undiscoverable from the skill that owns it.
- **Qualification is not an escape hatch.** A qualified pointer to a nonexistent file is
  still a dangling pointer and still fails.

`minerva:backfill-followups` now cites `minerva:promote`'s protocol by real path, which is
the proof the constraint is dissolved rather than worked around.

## Implications

Prefer citing a sibling's protocol by qualified path over restating it. When two skills must
agree on a procedure, one file and one pointer beats two copies and a plea — the failure
mode of the copies is silent drift, and the failure mode of the pointer is a red test.

## Related
- [[2026-08-22-constraint-a-skill-cannot-path-reference-a-sibling-skills-reference-file]] — supersedes
- [[2026-06-11-constraint-skill-progressive-disclosure]] — see also
