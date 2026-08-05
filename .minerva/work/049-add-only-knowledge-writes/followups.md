# Followups: 049-add-only-knowledge-writes

## 2026-08-05

- **Backfill `**Summary**` into pre-existing knowledge entries.** Deliberately dropped
  from this unit during grilling: it is not a prerequisite, because `plan_index`
  preserves existing catalog lines verbatim and only needs a summary for entries with
  no line at all. So a legacy corpus keeps working untouched. The one thing backfill
  would buy is making `index.md` fully reconstructible from the corpus alone — today
  a legacy entry's summary exists *only* in `index.md`, so losing that file loses
  them. Mechanical when done: parse the catalog lines, write each into its entry.

- **`using-minerva/SKILL.md` has ~60 bytes of headroom against the 9216-byte cap.**
  It was already at 9157 before this unit. The next substantive addition to the
  plugin's most central routing table will need a compaction pass — most likely
  pushing scenario rows into `references/guide.md` per knowledge 036. Flagged by the
  completion-verification panel's Skeptic.

- **Reconciliation's serialization is prose, not a tested script.** The
  `minerva/reconcile` flow relies on a non-forced push being atomic (git's ref update
  is the lock; the `gh pr list` check is only an early-out). That reasoning is
  correct but lives in `cleanup/references/reconciliation.md` rather than in a tested
  Python helper, which is a departure from knowledge 021 — the standard this same unit
  applied to `knowledge_next_nnn.py`. If reconciliation grows any further coordination
  logic, extract it. Raised by the completion-verification panel's Skeptic.

- **Success criterion 1's second clause was unverifiable as written.** "A promote run
  leaves `git status` showing only additions" cannot be asserted in CI, because
  `minerva:promote` is LLM-executed prose with no callable entry point. `minerva:promote`
  rewrote the criterion at promote time to state what is actually guaranteed. If a
  future unit wants the stronger check, it needs a harness that executes a skill
  end-to-end — which does not exist in this repo today.

- **`plan_reciprocals` runs even when `plan_index` refuses** (`knowledge_fix.py` `plan()`
  invokes the two independently). So a refusal on the index side still lets neighbour
  entries be written, leaving a half-reconciled corpus. The panel corrected my initial
  scoping of this: it is NOT limited to "index.md is missing" — it fires on every
  `plan_index` early-return refusal, including an unrecognized type or a duplicate NNN
  sitting in an unknown section. Pre-existing (verified against `6d424a7`); recorded as
  SUGGEST rather than fixed because it is outside this unit's goal.

- **A doubled catalog line for one entry is invisible.** `parse_index` keys its catalog
  on NNN, so two lines for the same entry collapse to one and the fixer re-emits both
  verbatim. This is structurally the same defect class this unit fixed for entry *files*
  (duplicate-NNN detection), left asymmetrically for catalog *lines* — a deliberate
  scoping call, not an oversight. It matters slightly more now that `index.md` is
  machine-generated rather than hand-authored.

- **The live `index.md` has one entry out of ascending order** (`038` sits between `034`
  and `035`). Cosmetic, pre-existing, and invisible to the lint — but it means the very
  first reconciliation run that fires for another reason will also re-sort it, which
  will look like unrelated churn in that PR.
