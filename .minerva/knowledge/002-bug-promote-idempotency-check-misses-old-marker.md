# minerva:promote idempotency check misses old marker format

**Date**: 2026-05-19
**Type**: bug
**Context**: .minerva/work/004-migrate-commands-to-skills

## Context

Work unit 004 migrated commands to skills, updating `promote/SKILL.md` to use `minerva:promote` invocation style throughout. This included updating the scratchpad archive marker from:

```
Summarized at /promote on YYYY-MM-DD — see archive/.
```

to:

```
Summarized at minerva:promote on YYYY-MM-DD — see archive/.
```

Work units 001, 002, and 003 were promoted before this change. Their active `scratchpad.md` files contain the old marker string. The idempotency check in `minerva:promote` Mode A looks for the new string and will not recognize the old one.

## Finding

Running `minerva:promote` on work units 001–003 will fail the idempotency check and attempt to re-run the promotion pass on already-archived work. The scratchpad content in those units is minimal (just the marker line) so the damage would be limited, but the pass would still run unnecessarily.

Fix options:
1. Update the idempotency check in `minerva:promote` to accept either marker string (preferred — forward-compatible).
2. Manually update the three existing markers to the new format.

## Implications

- Any work unit promoted before 2026-05-19 has the old marker. A future agent should not blindly run `minerva:promote` on these without checking.
- The simplest durable fix is option 1: update the idempotency check to match `Summarized at` (any prefix) followed by `promote on` and `see archive/`.
