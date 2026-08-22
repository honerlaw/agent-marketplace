# A skill cannot path-reference a sibling skill's reference file

**Date**: 2026-08-22
**Type**: constraint
**Summary**: the pointer gate resolves any `references/<file>.md` substring against the citing skill only

**Context**: .minerva/work/2026-08-22-backfill-followups-to-issues (see git history if the worktree has been cleaned up)

## Context

`tests/test_skill_budget.py::test_every_reference_pointer_resolves` guards progressive
disclosure: every `references/<file>.md` a `SKILL.md` mentions must exist, so a pointer never
dangles at the moment its detail is needed. It finds mentions with:

```python
REF_MENTION_RE = re.compile(r"references/[A-Za-z0-9._-]+\.md")
```

and resolves each against `SKILLS_DIR / skill / mention` — the **citing** skill's own
directory.

## Finding

The pattern is unanchored, so it matches that substring **anywhere in the line**, including
inside a fully-qualified path to a different skill. `minerva:backfill-followups` reuses
`minerva:promote`'s issue-filing protocol and tried to cite it three ways; all three fail the
gate:

- ``minerva:promote`'s `references/github-issues.md`` — reads as a local pointer.
- `plugins/minerva/skills/promote/references/github-issues.md` — the full path **still**
  contains `references/github-issues.md`, so it resolves against `backfill-followups/` and
  dangles.

**A cross-skill reference is therefore unrepresentable as a path** and must be phrased around
— e.g. "the `github-issues.md` protocol in `minerva:promote`'s own `references/` directory",
which carries no `references/<name>.md` substring.

This was a non-issue while every skill's references were private to it. It stops being one
now that skills deliberately reuse each other's protocols: `backfill-followups` delegates all
`gh` mechanics to `promote`'s file rather than restating them, and that is the pattern to
prefer, not an exception.

## Implications

- Cite another skill's reference file by **naming the owning skill plus the bare filename**.
  Never write a path containing `references/<name>.md` for a file you do not own.
- The gate is doing its job — a dangling local pointer is the failure it was built for. The
  limitation is that its model of "a reference" is *a file under this skill*, which is
  narrower than the references that now exist. Widening it means distinguishing a local
  pointer from a foreign path, and deciding whether a foreign path should resolve or be
  banned outright.
- Any future skill that reuses a sibling's protocol will hit this on its first CI run. The
  error message names a file "which does not exist under `<skill>/`", which reads as a typo
  rather than as an unrepresentable reference — expect to lose a few minutes to it.

## Related
- [[2026-08-11-pattern-a-gate-blind-to-what-it-checks]] — the general shape: the gate's model of its subject is narrower than the subject, so it is clean over what it cannot see
- [[2026-06-11-constraint-skill-progressive-disclosure]] — the constraint this gate enforces, and the reason the pointer must resolve at all
