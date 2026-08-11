# An absolute-path guard for `.minerva/worktrees` matches every file when run inside one

**Date**: 2026-08-10
**Type**: bug
**Summary**: test paths relative to the repo root; minerva's own work happens inside the directory such guards exclude
**Context**: .minerva/work/2026-08-09-date-prefixed-identity

## Context
The migration rewrites every reference before moving anything. It walks the repo and skips
nested worktrees, so a unit's in-progress copy is not rewritten from under it:

```python
for p in root.rglob("*.md"):
    if ".git" in p.parts or ".minerva/worktrees" in str(p):
        continue
```

The run reported: **renamed 107 paths, rewrote 0 files.** Every rename succeeded and every
link was left dangling.

## Finding
**`str(p)` is the absolute path, and minerva does its own work inside
`.minerva/worktrees/<unit>/`** — so when any lifecycle skill runs, the absolute path of
*every file in the repo* contains that segment. The guard excluded the entire corpus.

The exclusion is correct in intent and correct when run from a main checkout. It inverts
precisely when the tool runs where minerva actually runs, which is the only place it ever
runs in practice.

Test the path **relative to the repo root**, and compare path components rather than
substrings:

```python
rel = p.relative_to(root)
if ".git" in rel.parts or rel.parts[:2] == (".minerva", "worktrees"):
    continue
```

## Implications
- Never substring-match a path segment. `".minerva/worktrees" in str(p)` also matches a
  file merely *named* that; `rel.parts` cannot.
- A partial-success report is the tell. "107 renamed, 0 rewritten" is two halves of one
  operation disagreeing — assert the invariant that ties them (a rename implies at least
  one rewritten reference) rather than trusting either count alone.
- Anything self-hosting needs a test that runs it **from inside** its own working
  directory, because that is where an absolute-path assumption flips.

## Related
- [[2026-08-10-decision-date-ids-make-identity-the-path]] — builds on
