# Followups: close-remaining-loose-ends

## 2026-08-11

- **Two units are the INVERSE inconsistency: a promote marker is present but `**Status**`
  still says `Draft`.** `2026-05-19-add-propose-ship-skill` and `2026-06-03-synthesize-skill`
  both carry the canonical marker and a populated `archive/`, so they are promoted, but
  their proposals read `Draft`. Under the pre-flight predicate's OR they still register as
  in-flight. Deliberately not repaired here: the unit's approved scope was the two units
  whose *scratchpad* limb was wrong, and editing more historical records without asking is
  scope the user did not grant. **Trigger to revisit:** the next time a pre-flight collision
  check names one of them, or before any tooling starts trusting `Status`.

- **The pre-flight in-flight predicate may itself be the defect.** It reads
  `Status is Draft OR scratchpad is not post-promote`. Its purpose is "do not start work
  that collides with unfinished work", but a unit whose `Status` is `Shipped` and whose
  scratchpad was merely never archived is not unfinished work — the rule over-triggers. It
  fails safe (an extra question to the user), which is why nobody noticed. Changing it means
  editing a predicate that appears verbatim in four orchestrator SKILL.md files, so it is its
  own unit. Note that this unit already fixed the *dangerous* half of the problem: the same
  check inlined in promote/ship/round-table and the orchestrators' Phase 4 could re-run a
  mutating pass, and now routes through `work_status`.

- **`## Status` vs `**Status**:` — the prose and the corpus disagree.** Every orchestrator's
  pre-flight says "a `proposal.md` whose `## Status` is `Draft`", and `promote`'s
  `references/modes.md` says to "update `## Status`". But 51 of 52 proposals use the inline
  `**Status**:` field and exactly one uses a `## Status` heading. `work_status.unit_state`
  parses only `**Status**:`, so that one unit reads `status=None`. No miss has resulted (the
  reader is an LLM, which reads both), so this is convention drift rather than a bug.
  **Trigger:** any tooling that starts making decisions on `Status` deterministically.

- **Shorthand resolution has a documented blind spot worth surfacing at the gate.** An entry
  git cannot date is excluded from `entries`, so it has no target stem. Collisions involving
  it are now detected (the id is grouped before the date lookup) and it refuses, but the
  operator only learns this from the refusal reason. `migrate-fix`'s gate could pair the
  `UNDATED (skipped)` list with the shorthand refusals explicitly, since the two interact.

- **The `financials` plugin left `__pycache__` on disk.** `plugins/financials/` contains only
  untracked compiled bytecode from a plugin deleted in `20d32e0`. Harmless and gitignored,
  but it is why `ls` made a deleted plugin look present during this unit's investigation.
  A `git clean -ndX` would show it.

## Backfill disposition (2026-08-22)

Triaged by `minerva:backfill-followups`. Every item above is unchanged; this section records where each one landed.

- **Two units are the INVERSE inconsistency: a promote marker is present but `**Status**` still says `Draft`.** → shipped — both now read `Shipped (…) — record closed retroactively 2026-08-11`
- **The pre-flight in-flight predicate may itself be the defect.** → open (low) — not filed at this pass; the predicate still ORs the two limbs, and it fails safe
- **`## Status` vs `**Status**:` — the prose and the corpus disagree.** → shipped — no orchestrator SKILL.md still says `## Status`
- **Shorthand resolution has a documented blind spot worth surfacing at the gate.** → open (low) — not filed at this pass; a presentation improvement to `migrate-fix`'s gate
- **The `financials` plugin left `__pycache__` on disk.** → obsolete — `plugins/` now holds only `minerva` and `utils`
