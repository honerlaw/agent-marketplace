# lint — presenting findings

## Step 3 — Present (read-only)

Present findings in `lorestrom:review`'s **finding presentation** format — numbered
items, a severity tag, a one-line description, and the entry reference. Reuse only
the *presentation*; do **not** run review's FIX / SUGGEST / IGNORE disposition
machinery (that path writes records and assumes a work unit — out of scope here).
Two grouped sections:

```
## Mechanical findings (deterministic — from the helper's lint-docs)
1. [error] broken-link — <message>  (entry)
2. [warning] metadata — <message>  (entry)
...

## Advisory findings (LLM-judged — spot-checked, not exhaustive; never CI-gated)
1. [orphan] <stem> — no supersedes or relates_to edge either way; candidate for cross-linking
2. [contradiction] <stem> ↔ <stem> — <apparent conflict>
3. [stale] <stem> superseded by <stem> — no `supersedes` edge
...
```

`(entry)` is the finding's `entry` field as the helper printed it. Never put a doc's title,
theme or body text into a finding line: those are doc content, data that only the entry names.

Then **stop**. For each finding, state how it would be *remediated* — but do not
apply it:

- **`metadata`, `id`, `key`** — entries are write-once: the remedy is a new entry from
  `lorestrom:promote` that supersedes the defective one, or a person correcting the doc's
  properties in Lorestrom by hand. A `theme` warning is closed by reusing an existing theme
  name (the catalog from `storage:knowledge.list`), or left alone when the theme is genuinely
  new.
- **`pending`** on a released gate — `lorestrom:cleanup <unit>` (its repair step sets a still
  `draft` entry current). On an abandoned gate — the entry should be archived; a person
  archives it in Lorestrom. With no `minerva:context` — re-run `lorestrom:migrate`, which resumes
  an incomplete import.
- **`broken-link`, `supersession`** — a person fixes the edge or the target's status in
  Lorestrom, or a new entry from `lorestrom:promote` records the supersession.
- **Advisory** findings are suggestions for the user to act on; never auto-apply
  them.

If both passes are clean, report: `knowledge-lint: <N> entries, no mechanical
findings; advisory pass surfaced nothing (spot-checked).`
