# lint — presenting findings

## Step 3 — Present (read-only)

Present findings in `minerva:review`'s **finding presentation** format — numbered
items, a severity tag, a one-line description, and the entry reference. Reuse only
the *presentation*; do **not** run review's FIX / SUGGEST / IGNORE disposition
machinery (that path writes files and assumes a work-unit scratchpad — out of scope
here). Two grouped sections:

```
## Mechanical findings (deterministic — these fail the CI drift gate)
1. [error] broken-link — <message>  (entry stem)
2. [warning] metadata — <message>  (entry stem)
...

## Advisory findings (LLM-judged — spot-checked, not exhaustive; never CI-gated)
1. [orphan] <stem> — no inbound/outbound `## Related`; candidate for cross-linking
2. [contradiction] <stem> ↔ <stem> — <apparent conflict>
3. [stale] <stem> superseded by <stem> — no `supersedes` edge
...
```

Then **stop**. For each finding, state how it would be *remediated* — but do not
apply it:

- **Mechanical** findings are repaired by hand: fix the broken `## Related` target, write
  the missing `**Theme**` / `**Summary**` line (reuse a theme from
  `knowledge_catalog.py --themes` unless none fits), correct the invalid id. On a legacy
  corpus, `metadata` and `legacy` findings are closed together by `minerva:migrate-fix`'s
  backfill. A `theme` warning is closed by reusing the existing theme name, or left alone
  when the theme is genuinely new.
- **Advisory** findings are suggestions for the user to act on; never auto-apply
  them.

If both passes are clean, report: `knowledge-lint: <N> entries, no mechanical
findings; advisory pass surfaced nothing (spot-checked).`
