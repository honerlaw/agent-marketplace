# Scratchpad: lorestrom-migrate

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-11-25
- [reviewed — clean] scope check: one unit, one PR, no phases (tier: reviewer — not provably small, multi-file; parallel wave); dismissed non-blocking: live dry-run (stays an open question), in-flight scale and stale init-handover text (both folded at whole-proposal)
- [reviewed — folded] approach: A (released-unit import) + new migrate skill, init reduced to the link; folded record-key change, other-branch warning, batch size with one confirmation per run, changed-record handling, abandoned-import wording, storage/using-lorestrom/test surfaces (tier: reviewer — scrutiny: existing interface change, genuine ambiguity; parallel wave)
- [rechecked — residual folded] approach: C4 partially (changed records still landed in keep with no path out) — wired to the leftovers offer; new spec gaps (minerva-branches unlisted, gh absent) folded
- [reviewed — folded] whole-proposal: C1 removal statuses, C2 unit-state criterion, C3 batched in-flight yes, C4 clean agent file/.gitignore, C5 goal reworded + final report, C6 id/collision checks, C7 branches (tier: reviewer — scrutiny: blast radius not ruled out; parallel wave; restart check: approach pick unchanged, no scope/approach fold touched Goal or criteria — kept)
- [rechecked — residual folded] whole-proposal: removal offered per run over done units; changed-record wording; unit_file_key added beside an unchanged record_key so lifecycle writers keep their restriction

## Work notes 2026-11-25

- The migration code went into `lorestrom_backend.py` (now ~2,000 lines), not a new module: every skill runs one helper CLI, and a second module would need `lorestrom_runtime.REQUIRED_MODULES` and loader changes for no reader's benefit.
- `unit-import-list` reads every unit's state but prints files for one batch only (`--batch`, `--after`), so a 1,560-unit corpus never puts thousands of rows in the agent's context. The batch's Lorestrom lookups are per unit (`find_docs` with `minerva:unit`), not one paged list of every unit doc.
- No local import ledger: the next batch is whatever is still on disk after `--after`, and done units' files go in that run's removal, so re-runs stay cheap. Declining removal makes the next run re-check those units (one lookup each).
- `removal-plan` takes `{docs, units}` (the same lookup rows as `unit-import-plan`) and writes its paths to temp files (`--write-remove`, `--write-keep`) for `git --literal-pathspecs rm/commit --pathspec-from-file`: thousands of paths never pass through a command line or the agent's typing. The old list input is unchanged.
- `record_key` is untouched; `unit_file_key` builds the import's path-named record keys (whole-proposal fold-audit's NC4).
- Refactors in passing: `_walk` shared by `reference_list` and the unit listing; `_short`/`_heading` shared by `reference_payload` and the unit listing.
- Incomplete-import remedies (lint, status, the helper's lint message) now name `lorestrom:migrate`, since init no longer imports.
- Guards adapted: `.minerva/work` and `.minerva/worktrees` may be named only by migrate's files and storage's `unit.import`/`migrate.remove` sections; link.md no longer names the knowledge directory.
