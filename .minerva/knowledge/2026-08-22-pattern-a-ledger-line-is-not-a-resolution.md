# A ledger line is not a resolution

**Date**: 2026-08-22
**Type**: pattern
**Summary**: a record marking work handled must separate decided-and-done from decided-to-wait, or it buries it

**Context**: .minerva/work/2026-08-22-backfill-followups-to-issues (see git history if the worktree has been cleaned up)

## Context

`minerva:backfill-followups` was built to cure a specific staleness: 24 `followups.md` files
holding ~79 deferred items, where **nothing marked an item done**, so every scoping pass
re-read all of them to re-derive the same answer. The skill triages each item, files the live
ones as GitHub issues, and appends a `## Backfill disposition` section recording where each
one landed.

Its first run classified 33 items `open`. The operator chose to file 11 — the 8 `medium`
items plus 3 `manual` ones — and the other 25 were recorded honestly as
`open (low) — not filed at this pass; <why>`.

The skill's idempotency rule read: *an item already carrying a disposition line is skipped on
a re-run.*

## Finding

That rule is correct for a **resolved** item and wrong for a **deferred** one, and the
ledger's single "has a disposition" test could not tell them apart. Every one of those 25
live items would have been passed over by every future run, forever, with nothing to
resurface them. The prose said "still open"; the machinery said "handled".

**The tool built to cure the staleness had reproduced it one layer up.** The old failure was
an item in a file with nothing marking it done. The new failure would have been an item in a
file *marked as not-done*, which the reader now trusted to be complete — strictly worse,
because a ledger invites you to stop looking.

The fix is to type the dispositions rather than count them:

- **Terminal** — `→ #NN`, `shipped`, `obsolete`, `not-an-item`, a dropped `manual`. The item
  is done being decided; skip it.
- **Non-terminal** — `open (…) — not filed`. Still live. **Re-offer it every run.**

Re-running the skill then *is* the trigger that
[[2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption]] says deferral needs —
but only because the ledger distinguishes the two states. Without that split the re-run
exists and is a no-op, which is the most expensive kind of safeguard: one that looks like
coverage.

## Implications

- Any record that marks work as handled needs at least two terminal-ness classes. "Has a
  disposition" is not "is resolved", and a boolean `seen` flag over a mixed set is a bug
  waiting for someone to trust it.
- When a skip rule and a human-readable note disagree, the skip rule wins silently. Audit
  them against each other: if the prose can say "still open" while the code says "skip", the
  prose is decoration.
- Watch for this specifically in tools built to fix a bookkeeping failure. The same instinct
  that produces the fix — *write down what happened so nobody re-derives it* — produces the
  new record, and the new record inherits the old blind spot unless someone asks what
  re-reads it and when.
- The tell: a disposition vocabulary where one value means "we decided not to yet". If
  nothing treats that value differently from the values meaning "done", it is not deferral,
  it is deletion with a receipt.

## Related
- [[2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption]] — extends it: that entry says deferral needs a trigger, this one says the record must distinguish which items the trigger should pick up
- [[2026-08-11-pattern-a-gate-blind-to-what-it-checks]] — sibling shape: a check whose model of its subject is narrower than the subject
- [[2026-08-22-pattern-a-value-written-before-its-evidence-needs-re-verifying]] — see also
