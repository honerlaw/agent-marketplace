# Scratchpad: reconcile-never-strands-entries

> **PROMOTED 2026-08-07** — durable item is knowledge 057; this file is the archived
> raw record.

## Evidence

Six occurrences in two days on the Seekless project, all the same shape — a
reconciliation PR opened minutes before another unit merged, so that unit's entries were
never in it and no later run was scheduled:

- entries 580/581 — reconcile PR opened 03:09, unit PR merged 03:15
- entry 584 — reconcile PR opened 14:16, unit PR merged 14:27

Both recovered only because a human asked whether everything had merged. The skipped runs
each reported themselves successful.

## Test note

`tests/test_pull.py` fails to import (`ModuleNotFoundError: No module named 'lib'`), and
`test_browser.py` / `test_storage.py` fail to collect for the same reason. All
pre-existing on main and unrelated to this change. 413 tests pass.

Worth stating why that is a safe conclusion here when it was NOT safe in the sibling
case knowledge 585 records: pytest runs every test regardless of an unrelated failure, so
the 413 passes are complete for what this change touches. `npm run check`, in the case
585 is about, is a CHAIN — a failure partway through means the later steps never ran at
all. "Fails on main too" cleared this one; it did not clear that one.
