# A same-size source mutation restored within a second can leave stale bytecode running

**Date**: 2026-09-26
**Type**: pattern
**Summary**: Deletion passes need python -B: same-size edits restored in-second reuse the mutated .pyc
**Context**: .minerva/work/2026-09-26-trace-orchestrator-run-time (see git history if the worktree has been cleaned up)

## Context
A scripted deletion pass
([[2026-08-28-pattern-an-assertion-is-untested-until-a-deletion-makes-it-fail]]) mutated one rule
at a time in `scripts/run_trace.py`, ran the tests and restored the file. Afterwards the full
suite failed on correct source: `rnd = 2 if …` behaved like the mutated `rnd = 1 if …`.

## Finding
Python checks a cached `.pyc` against the source's **mtime (whole seconds) and size**. Mutations
such as `2`→`1` or `min`→`max` keep the file's size, and restoring within the same second keeps
its mtime, so the mutated bytecode stays valid and runs against the restored source. Every later
mutation run can then report "killed" or "survived" for the wrong code. That makes the whole
pass untrustworthy, not just the one mutation.

## Implications
- Run deletion and mutation passes with bytecode caching off: `python -B`,
  `PYTHONDONTWRITEBYTECODE=1`, and `-p no:cacheprovider` for pytest. Clear existing
  `__pycache__` first.
- A test that fails on correct source right after a mutation pass is a cache symptom before it
  is a code bug.
- The same trap applies to any tool that edits and restores source faster than mtime resolution.

## Related
- [[2026-08-28-pattern-an-assertion-is-untested-until-a-deletion-makes-it-fail]] — builds on
