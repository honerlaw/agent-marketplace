---
name: skills-treat-branch-and-ref-names-as-data
description: Use when writing or reviewing a skill step that runs git, gh or Python with a branch, ref or unit name — names come from the repository and are passed quoted from the shell, never typed in; unit ids are checked against `minerva_runtime.py units`.
metadata:
  type: decision
---

# Skills treat branch and ref names as data: the shell obtains them and passes them quoted

**Date**: 2026-11-22
**Type**: decision
**Theme**: skills-and-catalogs
**Summary**: no branch/ref name typed into a command or Python source; default branch via one snippet; unit ids checked by `units`
**Context**: .minerva/work/2026-11-22-untrusted-ref-names (see git history if the worktree has been cleaned up)

## Context

Skill steps told the agent to read a branch name (the default branch, a PR head, a unit branch)
and then write it into the next command, sometimes inside a double-quoted `python3 -c` source.
Branch and ref names come from the repository, which may not be the user's, and Git allows names
that are not safe as command text. A typed name also broke on ordinary names with quotes. A
separate behaviour bug rode along: in a clone holding only `origin/<default>`,
`git worktree add -b <unit> <path> <default>` checks the worktree out on a new local default
branch and never creates the unit branch.

## Finding

minerva 4.0.1 adds "Names are data" to the runtime contract:

- **Names stay in the shell.** A name is read inside the shell call that uses it, kept in a
  variable and passed quoted (after `refs/…`, as a flag value, or after `--`). Python receives it
  through `sys.argv`; Python source is single-quoted and holds no placeholder.
- **One default-branch snippet.** It unsets inherited values, prefers the local ref and falls
  back to origin's, and sets `BASE` (full ref) and `BASE_NAME`. Uses are `"${BASE:?}"`; a branch
  cut from it takes `--no-track`. The `:?` cannot stop a call from inside `$(…)` or a pipeline,
  so such lines start with `: "${BASE:?}" &&`.
- **Checked unit ids.** A unit id may appear as `<date-slug>` only once it equals a name printed
  by `minerva_runtime.py units`, which lists ids from directory names and unit-shaped local
  branches with the same `is_unit_id` rule as checkpoints, and counts what it refuses.
- **PR numbers from `gh --json`, titles from files, bare-mode names reduced in the shell.**

## Implications

- `tests/test_untrusted_names.py` is placeholder-first and fails closed: every `<placeholder>` in
  every skill code span or block must be classified, generic placeholders are refused in git/gh
  commands, name variables must be double-quoted, and `--no-track` is required on cuts from
  `BASE`. A new placeholder fails until someone decides what it holds.
- Free text other than names (titles, headlines, entry stems) is out of this rule's scope; issue
  filing already passes it through variables or files.
- The merge-detection fallback is now an exact fixed-string match, so it also sees a branch
  checked out in a worktree, which the old `^[* ]` pattern never matched.

## Related
- [[2026-08-22-pattern-a-denylist-safety-guard-fails-open]] — applies: the guard enumerates the allowed placeholders and variables instead of listing bad commands
- [[2026-06-03-constraint-skill-wraps-script-via-importable-api]] — builds on: the unit-id listing is a helper command, not a rule retyped in each skill
- [[2026-08-22-pattern-verifying-a-side-effecting-snippet-mutates-real-state]] — applies: executed snippet tests run read-only or in their own scratch repositories
