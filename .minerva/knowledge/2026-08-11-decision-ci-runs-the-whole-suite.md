# CI runs the whole suite; the enumerated module list is gone

**Date**: 2026-08-11
**Type**: decision
**Summary**: three dead test files forced an enumerated CI list for months; deleting them dissolved the constraint instead of guarding it
**Context**: .minerva/work/2026-08-11-close-remaining-loose-ends

## Context
`.github/workflows/evals.yml` ran a hand-written list of thirteen test modules rather than
`pytest`. The reason was three files — `tests/test_browser.py`, `tests/test_storage.py`,
`tests/test_pull.py` — that aborted collection with `No module named 'lib'`. The workflow
said so in a six-line comment and called fixing them "a separate follow-up".

They were never fixable. They test the `financials` plugin, **deleted in `20d32e0`**;
`git ls-files plugins/financials` returns zero tracked files and only stray `__pycache__`
survives on disk. The follow-up had been framed as "repair the import" for months, and
repair was never an available option — the subject was gone.

The enumerated list had a cost that outlived its cause. A new test module does not run in
CI until someone remembers to append it, and the failure is silent: the module simply
never runs and nothing goes red. `2026-06-11-constraint-ci-test-enumeration-explicit`
recorded that as a standing rule to obey. The unit immediately before this one obeyed it
and *still* shipped `tests/test_skill_snippets.py` dark to CI — four tests covering two
defects, invisible until a later commit caught it.

## Finding
**When a workaround has a cause, check whether the cause still exists before writing a
rule to live with it.** Deleting three files that test deleted code made bare `pytest`
pass (459 at the time), so the workflow now runs `python -m pytest tests/ -q` and
**collection is the enumeration**. A new test module cannot be dark again — not because
someone documented a step, but because there is no step.

This is strictly better than the obvious alternative, which was a guard test asserting
every `tests/*.py` appears in the workflow's list. That guard would have worked, and it
would have preserved the thing needing guarding. The rule and the guard were both
downstream of three files nobody had checked the status of.

The tell: a constraint whose justification is a *workaround* rather than a property of the
domain. "New modules must be appended to the list" is not a fact about testing; it is a
fact about one broken import, and it inherited that import's lifetime by accident.

## Implications
- A workflow comment explaining why something is excluded is a dated claim. This one named
  a follow-up that had already been made impossible by an unrelated deletion.
- Prefer removing a cause to documenting a rule about it. A rule needs a reader to obey it
  every time; a removed cause needs nothing.
- Verify a plugin's tracked state with `git ls-files`, not `ls` — `__pycache__` left on
  disk made a deleted plugin look present.
- When retiring a constraint, supersede its entry rather than deleting it, so the reasoning
  survives for anyone who finds the old rule quoted somewhere.

## Related
- [[2026-06-11-constraint-ci-test-enumeration-explicit]] — supersedes
- [[2026-08-11-pattern-a-gate-blind-to-what-it-checks]] — builds on
- [[2026-08-11-pattern-the-enumeration-is-what-fails]] — see also
