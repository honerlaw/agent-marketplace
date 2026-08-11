# Replan: close-silent-reference-gaps

## 2026-08-11 — a seventh defect, found by the unit's own work

### Original plan

Fix the six defects reported by a peer session that ran `minerva:migrate-fix` against a
real 637-entry corpus: the lint/fix edge-model divergence, `rewrite_links`' two missing
path forms, `CONTEXT_PATH_RE`'s trailing punctuation, uncounted bare `[[NNN]]` shorthand,
and the two broken snippets in `migrate-fix/SKILL.md` and `lint/SKILL.md`.

### What changed

Defect 4 added a shorthand count to `knowledge_rename.plan()`. Running the CLI to check
that count against this repo surfaced something the six never touched — **the migration
is not idempotent for work directories**:

```
2026-08-07-reconcile-never-strands-entries/ -> 2026-08-10-08-07-reconcile-never-strands-entries/
2026-08-09-date-prefixed-identity/          -> 2026-08-10-08-09-date-prefixed-identity/
```

`WORK_DIR_RE` was `^(\d{3,})-(.+)$`. Against an already-migrated `2026-08-07-foo` it
captures `2026` as the id and `08-07-foo` as the slug, so the tool re-dates a directory
it already dated. On this repo a second run wanted to rename **all 50-odd** migrated work
units, and since `apply` rewrites every reference before moving, every `**Context**:
.minerva/work/…` path would have been retargeted to the corrupted name.

Confirmed **pre-existing on `origin/main`** — not introduced by this unit. The
knowledge-entry branch never had it: `ENTRY_RE` embeds the shared `ID_RE_SRC` alternation
with the date arm first, so `2026-08-07-decision-foo.md` yields `group(1) ==
"2026-08-07"` and the existing `is_date_id` guard skips it correctly. `WORK_DIR_RE` was
the codebase's single bare-`\d{3,}` outlier; `knowledge_fix._CATALOG_LINE_RE` and
`knowledge_spans.BANNER_MARKER_RE` already carry the full alternation.

This also falsified a claim `migrate-fix/SKILL.md` states as fact: "Already-dated entries
are skipped, so a second run is a no-op rather than a double-rename." True for entries,
false for work dirs.

### New plan

Fix it **in this unit** rather than deferring it. It is the same failure shape as the six
— a pattern wider than the reality it matches, failing silently in a writer — it lives in
`plan()`, the function this unit already modifies for defect 4, and it was found by this
unit's own work. Deferring would leave live data corruption in a tool that moves
directories.

1. `WORK_DIR_RE` uses the shared `ID_RE_SRC` grammar (date arm first), and `plan()`'s
   work branch gains the `is_date_id` guard the entry branch already has.
2. `migrate-fix/SKILL.md`'s idempotency bullet is corrected to state the guarantee
   accurately and to record what was wrong.
3. A regression fixture held to the same bar as the other seven: verified to FAIL against
   the pre-fix source with the exact corruption
   (`2026-08-07-already-migrated` → `2026-08-11-08-07-already-migrated`) and to pass
   after, while a genuine legacy `111-legacy-unit` still migrates.

**Success criteria gain a ninth item:** the migration is idempotent for work
directories as it already was for entries — a second run against a fully migrated corpus
plans zero renames. Verified on this repo: `plan: 0 entries, 0 work dirs`.

**One repair carried in the same diff, named so the record is not itself silent.** The
six-defect commit `c8ea4ad` added `tests/test_skill_snippets.py` without appending it to
the enumerated pytest list in `.github/workflows/evals.yml`, so those 4 tests — the
executable coverage for defects 5 and 6 — were dark to CI from the moment they landed.
That is criterion 8's own requirement and
[[2026-06-11-constraint-ci-test-enumeration-explicit]], and it is precisely the failure
this unit is about: a gate reading clean over work it never ran. Fixed here rather than
left as an unexplained line in the diff.

**Not in scope, named so it is not mistaken for a gap.** A calendar-invalid but
date-shaped directory (`2026-13-45-foo`) still re-migrates, because `is_date_id`
validates against the calendar. That is identical to the entry branch's existing
behaviour, so it is a property of the shared guard rather than a defect this fix
introduces.
