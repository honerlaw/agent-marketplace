---
name: a-test-loader-leaked-sys-path-across-plugins
description: Use when a test helper loads a plugin's modules by path — restore sys.path afterwards, or another plugin's same-named module is shadowed and its tests pass only in suite order.
metadata:
  type: bug
---

# A test loader that prepended one plugin's scripts to sys.path made another plugin's tests order-dependent

**Date**: 2026-11-23
**Type**: bug
**Theme**: silent-success
**Summary**: loader left lorestrom scripts on sys.path; minerva's same-named modules shadowed, subset run failed, full suite passed
**Context**: .minerva/work/2026-11-22-lorestrom-backend (see git history if the worktree has been cleaned up)

## Context

minerva and lorestrom ship modules with the same names (`plugin_guard.py`, copies of
`work_status.py` and the knowledge scripts), and the repo's root `scripts/` symlinks point at
minerva's. `tests/lorestrom_scripts.py` loads lorestrom's files under unique module names so the
symlinks cannot stand in for them.

## Finding

Loading lorestrom's `work_status.py` inserted lorestrom's scripts directory at the front of
`sys.path`, and the loader never removed it. Any later `import plugin_guard` in the same process
resolved to lorestrom's copy. The full suite passed only because of the order pytest collected
modules in; running `test_lorestrom_units.py`, `test_plugin_guard.py` and `test_minerva_runtime.py`
alone failed. The loader now saves `sys.path` and restores it in `finally`, and a test loads a
lorestrom module, then imports minerva's `plugin_guard` and checks its `__file__`.

## Implications

- A green full suite does not show isolation. When two plugins share module names, run each
  plugin's test files as a subset in a gate, not only the whole suite.
- Check `__file__` or `co_filename` of what a test imported when a name exists twice.

## Related
- [[2026-11-01-pattern-a-deletion-pass-needs-a-green-baseline]] — relates to: another way a suite reads green or red for a reason other than the code under test
