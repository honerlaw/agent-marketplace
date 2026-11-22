# Proposal: untrusted-ref-names

**Date**: 2026-11-22
**Status**: Draft

## Goal

minerva 4.0.1: the skills treat git branch and ref names, and the unit ids that become branch names, as untrusted data. No branch or ref name is pasted into shell command text or Python source. A unit id is pasted into command text only when it is a checked id, and never into Python source.

## Why

Branch names and work-unit directory names come from the repository, which may not be the user's. Git allows names that are not safe as command text. The user asked for this as a separate small patch release.

## Approach

### 1. Rules in the runtime contract

`skills/using-minerva/references/runtime.md`, read by every skill, gains "Names are data":

- **Branch and ref names** are obtained inside the shell call that uses them, held in a variable and passed quoted, after a `refs/…` prefix or `--` where the command takes one. Python receives them as arguments.
- **The default branch** comes from one snippet, which first unsets the two variables it sets. It takes the name from `refs/remotes/origin/HEAD`, else the first of `main` and `master` that exists locally or as `refs/remotes/origin/<name>`. It sets `BASE_NAME` to the name, for the one command that needs it (`git fetch origin "refs/heads/${BASE_NAME:?}"`), and `BASE` to the full ref: `refs/heads/<name>` when that exists, otherwise `refs/remotes/origin/<name>`. Every use is `${BASE:?}`, so a call that skipped the snippet fails instead of running on an empty value. A worktree or branch cut from it passes `--no-track`. Steps that fetch first and cut from origin keep using origin's ref, with its full prefix, and keep today's tracking: the user's decision covers only the fallback to origin.
- **Unit ids.** `minerva_runtime.py` (already a required module) gains a `units` command that takes no input. From the project root it reads the directory names under `.minerva/work`, `.minerva/worktrees` and `.minerva/worktrees/*/.minerva/work`, prints those its existing unit-id pattern (the one `state_path` already enforces) matches as a whole string with no `..`, and prints a count of those refused. The runtime contract's listing snippet calls it. A **checked id** is one that snippet printed, or a new id made by propose's slug step (only `[a-z0-9-]` after the date). An id from an argument, a branch name or a PR head must equal a printed one before use. Otherwise the skill stops on that id; a sweep over many units (cleanup with no argument) skips it and reports it.
- **Commit ids** used by a step come from git output inside the same shell call, never pasted by the agent. **PR numbers** come from `gh … --json number` output.

### 2. Each site rewritten, because a preamble does not bind a step

- **propose**: the worktree start point and gitignore read on-approval. The in-flight check gets staleness from commit ids found by the shell, and PR state per branch with `gh pr list --state all --head "$b"`. The unit path goes in as a Python argument.
- **work**: worktree re-creation. **review**: the merge-base diff.
- **ship**:
  - phase resolution, with the base and unit id as Python arguments;
  - the phase cut;
  - branch creation: the bare-mode name keeps `<git-user>/<slug>`, each part reduced to the allowed set, starting with a letter or digit, with a fixed word when empty;
  - pushing `HEAD`;
  - the merge strategy, one of three fixed flags;
  - the PR title passed as `--title "$(cat <file>)"` from a file the agent wrote.
- **cleanup**: merge detection (an exact, fixed-string match on branch names), the phased-units snippet (arguments), removal.
- **promote**: the idempotency snippet (path as argument), and the issue search, whose string is built from a quoted variable holding the checked id.
- **status**: the merged-branch fallback passes its name after `refs/heads/`. Its branch list and its Python call are already safe.
- **both orchestrators**: worktree creation, the reviewer diff, and PR lookup by number, or by `gh pr list --head "$b"` for a branch read in the shell.
- **Commands a skill only tells the user to run, and commit subjects**: covered by the unit-id rule, applied before such a command is printed as well as before one is run.

Outside this unit: other free text in commands, meaning commit messages apart from a unit id in the subject, issue text, and issue-match's search words, which come from the user's own request. The PR title is the exception, because bare mode derives it from a branch name.

The only script change is the `units` command, added to an existing required module. An explicit `MINERVA_SCRIPTS` directory older than 4.0.1 lacks it, so the listing snippet fails with that error rather than skipping the check. The other helpers already pass argument lists and use no shell.

### 3. Tests

- **A placeholder inventory that fails closed.** A non-executing extractor, using the shared fence grammar and handling double-backtick spans, reads every code span and fenced block in the shipped skills. Every `<…>` placeholder and `$…` expansion in them must be on a short allowlist, whatever command surrounds it, unless the span is listed as prose in an exemption list beside it. The allowlist: a checked unit id outside Python source, a phase number, PR and run numbers, agent-created temp paths, exactly the quoted variables the runtime snippets set (`"${BASE:?}"`, `"${BASE_NAME:?}"`, and `"$b"` for a branch read in the shell), and fixed flags. The prose exemption list names each exempted span. Any placeholder inside Python source fails. Every `worktree add -b` and `checkout -b` that starts from `BASE` must carry `--no-track`.
- **The unit-id half** cannot be seen in text: a checked id and an unchecked one read the same. So a test checks that the rule and listing snippet are in the runtime contract and that every skill file running a unit-id command carries the one-line pointer to that rule in its own target-resolution or worktree-addressing step, and `units` is executed against a valid name, a name with `..`, names starting with a dot or a dash, and a name with a newline, asserting both what it prints and its refused count. Its CLI is covered beside `minerva_runtime`'s existing command tests.
- **Executed snippets.** In temporary repositories, the read-only default-branch, phase-resolution and cleanup merge-detection snippets run for `main`, the `master` fallback, a default branch that exists only on origin, and an unusual valid name. A branch cut from `BASE` in the origin-only case is checked to have no upstream. Mutating commands are never executed from the skill text; the existing read-only guard on extracted blocks stays as it is.
- **Existing tests** that substitute the old placeholders (`tests/test_minerva_runtime.py`'s phase-snippet test, the status fragments test) extend their setup to supply `BASE` and the unit argument, keeping every assertion. The compatibility `gh` stub accepts the forms the rewrite uses.

### 4. Release 4.0.1

Bump both plugin.json files, the pinned tests, COMPATIBILITY, README, and the pages that name the version.

## Success criteria

1. No command in `plugins/minerva/skills` substitutes a branch or ref name into command text or Python source; names come from quoted shell expansions or arguments. A checked unit id counts as a unit id, not as a branch name.
2. The unit-id rule and listing snippet are in the runtime contract; `units` uses `minerva_runtime`'s existing unit-id pattern and passes its executed test; no unit id is interpolated into Python source.
3. The inventory test fails when any one of the original sites that substituted a branch or ref name, or put a placeholder into Python source, is restored (each restored from main in a throwaway copy), on a new unknown placeholder in any command, and when `--no-track` is dropped from a branch cut from `BASE`.
4. The executed snippets pass for `main`, the `master` fallback, an origin-only default branch (whose cut branch has no upstream) and an unusual valid name, leaving that name literal.
5. Behaviour is otherwise unchanged: the full suite, both dry-run evals and knowledge lint pass, with existing tests' setup extended where placeholders changed and no assertion weakened; every SKILL.md stays at or under 9216 bytes.
6. Version surfaces say 4.0.1.

## Open Questions

None.
