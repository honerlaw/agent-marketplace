# A deletion pass reports every mutation as caught when the test file cannot collect

**Date**: 2026-11-01
**Type**: pattern
**Theme**: silent-success
**Summary**: a non-zero exit from a collection error reads as "caught"; a deletion pass must check its baseline first
**Context**: .minerva/work/2026-11-01-one-by-one-question-skill

## Context
The unit proved each contract anchor by deleting it and requiring the test run to fail. Mid-review a
`pytest.mark.parametrize` carried one id too few, so `tests/test_compatibility_evals.py` failed at
collection with exit code 2.

## Finding
The script judged "caught" from a non-zero exit, so a mutation to `run()` printed `caught` while no test in
that file had run. Only a baseline line printed after the pass (`baseline rc 2`) exposed it. The script's own
exit code was 0, and the line a reader looks at said the mutation was detected. A collection error, an import
error, or any other failure unrelated to the mutation produces the same result.

## Implications
Run the unmutated baseline first and abort unless it exits 0. To be stricter, require exit code 1 (tests ran
and failed) rather than any non-zero code; pytest uses 2 for an interrupted session and 5 for no tests
collected.

## Related
- [[2026-08-28-pattern-an-assertion-is-untested-until-a-deletion-makes-it-fail]] — builds on
- [[2026-09-26-pattern-a-same-size-mutation-can-leave-stale-bytecode]] — see also
