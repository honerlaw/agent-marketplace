---
name: subtree-add-hides-path-history
description: Use when moving a directory with its history into a new repository — git subtree add keeps the old commits at the root, so path-limited log and blame stop at the merge; rewrite the split under the prefix instead.
metadata:
  type: pattern
---

# `git subtree add` keeps history that path-limited log and blame cannot reach

**Date**: 2026-11-26
**Type**: pattern
**Theme**: silent-success
**Summary**: subtree split plus add looks history-preserving, but `git log -- <prefix>` stops at the merge; rewrite the split under the prefix
**Context**: .minerva/work/2026-11-26-move-lorestrom-to-its-own-repo

## Context

Moving `plugins/lorestrom/` to a new repository, the plan was `git subtree split
--prefix=plugins/lorestrom` here, then `git subtree add --prefix=plugins/lorestrom <split>` there.
`git log` listed all six release commits and the tree was byte-identical, but
`git log --oneline -- plugins/lorestrom` showed one commit: the merge.

## Finding

The split commits hold the directory's files at their **root**. `subtree add` merges them in
with a commit that moves everything under the prefix, so before that merge no commit touches
`plugins/lorestrom/...`. Path-limited `git log`, `git blame` and GitHub's file history all stop
at the merge, though the commits are in the repository.

The fix was to rewrite the split so each commit already holds the files under the prefix, and
build the new repository's `main` on it (linear, no merge):

```sh
git branch -f moved split-branch
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch -f --tree-filter \
  'mkdir -p .tmp-move && find . -mindepth 1 -maxdepth 1 ! -name .tmp-move ! -name .git \
     -exec mv {} .tmp-move/ \; && mkdir -p plugins && mv .tmp-move plugins/lorestrom' moved
```

The rewritten commits keep their authors, dates and messages; their hashes change.

## Implications

- To check that history really moved, run the path-limited log in the new repository and count
  the commits. A plain `git log` count passes either way.
- `git filter-repo --to-subdirectory-filter` does the same in one step where it is installed.

## Related
- [[2026-11-26-decision-lorestrom-lives-in-its-own-repository]] — the move this was found in
