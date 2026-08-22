# Verifying a side-effecting snippet mutates real state

**Date**: 2026-08-22
**Type**: pattern
**Summary**: exercising a documented mutating command against the live repo leaves real artifacts behind

**Context**: .minerva/work/2026-08-22-followups-become-github-issues (see git history if the worktree has been cleaned up)

## Context

minerva skills document commands an agent is expected to run verbatim, and this repo
takes that seriously enough that `tests/test_skill_snippets.py` extracts fenced blocks
from `SKILL.md` files and **executes** them against fixtures. Most documented commands so
far have been read-only (`grep`, `gh pr view`, `python3 -c` over a corpus).

`minerva:promote`'s new GitHub-issue path is the first documented flow whose commands
**mutate remote state**: `gh label create`, `gh issue create`.

## Finding

While verifying that the new `ensure_label` helper correctly reports an unusable label,
the check was run against the live repository with a deliberately absent label name. The
account had admin rights, so the "failure" branch never executed — instead the command
did exactly what it was documented to do and **created a real label on the project's
repository**. It was deleted immediately and the label list confirmed back to its original
nine, but the verification had already mutated the thing it was verifying against.

The trap is specific: a test designed around *"this should fail"* silently becomes a test
that *succeeds and mutates* the moment it runs with more permission than assumed. The
stronger the credentials, the less the negative path is exercised and the more real the
side effect.

## Implications

- Exercise a mutating documented command against a **stub or a scratch target**, never the
  project's own repository: a `gh` shim earlier on `PATH`, or a throwaway repo. Reserve
  live runs for genuinely read-only commands.
- `bash -n` over the extracted block catches the syntax and quoting defects that motivate
  most of these checks, at zero side-effect cost. Reach for it first.
- Anything added to `tests/test_skill_snippets.py` that extracts a block containing
  `gh issue create`, `gh label create`, or any other mutating call must stub the binary.
  The existing tests are safe only because every block they extract is read-only — a
  property nothing currently enforces.
- If a live mutation does happen, revert it and say so plainly in the record. The stray
  label above is named here for exactly that reason.

## Related
- [[2026-05-19-constraint-skills-must-call-tools-not-prose]] — the constraint that puts runnable mutating commands in skill prose in the first place
- [[2026-08-10-pattern-presence-assertions-rot-into-green-lies]] — sibling testing-hazard: there the check cannot fail, here it cannot fail *safely*
- [[2026-08-22-pattern-a-denylist-safety-guard-fails-open]] — see also
