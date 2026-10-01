# Proposal: derive-knowledge-aggregates

**Date**: 2026-10-01
**Status**: Draft

## Goal

Remove every shared, committed aggregate from `.minerva/knowledge/` (`index.md`, its
watermark, stored reciprocal `## Related` back-links and supersession banners, and
`overview.md`) by deriving them on read from the entries themselves. With nothing left
to reconcile, delete `minerva:cleanup`'s post-merge reconciliation step. Knowledge and
docs updates then ride each work unit's own PR "as normal", with no default-branch
follow-up PR.

## Why

Reconciliation exists only because the wiki stores caches of data the entries already
hold (`2026-08-05-decision-promote-add-only-reconcile-on-default`). Every aggregate is a
surface concurrent PRs fight over, so promote was made add-only and the aggregates were
moved to a post-merge, single-writer pass. That pass has had its own failure classes
since: stranded uncatalogued entries (`2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption`),
an unserialised second writer in seekless's CI job (`2026-08-14-constraint-a-ref-lock-binds-only-writers-that-share-the-ref`),
stale `minerva/reconcile` branches, and a `chore: reconcile knowledge index` PR after
every feature merge (#136, #138, #140).

Three of the four aggregates are fully derivable:

- `index.md` catalog line = `[[<stem>]] — <**Summary**>`; Type section = the `<type>` in the stem.
- The watermark exists only to track reconciliation.
- Reciprocal links = the forward links reversed (`grep '\[\[<stem>\]\]'`). Supersession = a
  `supersedes` forward edge, reversed.

`overview.md` (70 KB, ~17k tokens, read first by every session) is LLM prose, but its
load-bearing content is the grouping of entries into themes. That grouping can live on
the entry as a `**Theme**` field, and the overview becomes a derived, theme-grouped
listing. **Measured** on this repo's 119 entries: one line per entry with its summary is
23.4 KB, ~5.9k tokens (the committed `index.md` is ~24 KB today). Cross-cutting
narrative prose is lost; that loss is accepted, because `.minerva/` content exists only
to help an LLM execute work (project rule), the recurring cross-cutting lessons are
already their own `pattern` entries, and a new cross-cutting insight is promoted as a
new entry (add-only) rather than written into a shared narrative.

If nothing shared is ever written, entries are write-once, PRs cannot *textually*
conflict on `.minerva/knowledge/`, and there is nothing to reconcile. (Semantic drift —
two concurrent PRs coining near-duplicate themes — remains possible; it is surfaced by a
lint warning, not prevented.)

## Approach

**Scope: one work unit, one PR, no phases.** A coherent two-phase seam exists (phase 1:
add Theme + catalog + backfill while reconcile keeps running; phase 2: delete the
machinery). It is rejected as a size/risk trade-off, not an impossibility: phase 1 would
have to keep `index.md`/`overview.md` maintained alongside the new catalog — a throwaway
intermediate state that is reviewed once and never used — and the risk lives in the
deletions + migration, which a split does not reduce. Most of the diff is deletions and
mechanical doc edits.

1. **Entry schema.** Add a required `**Theme**: <theme>` metadata line beside `**Summary**`
   in the knowledge entry template (`skills/promote/references/wiki-maintenance.md`).
   Theme is a **single-valued, lowercase kebab-case** name (e.g. `knowledge-wiki`,
   `concurrency`). Promote lists existing themes with
   `knowledge_catalog.py --themes` (resolved via the existing `PLUGIN_SCRIPTS` runtime
   helper, so it works in consumer repos) and coins a new one only when none fits.
   Entries become **write-once**: promote writes forward `## Related` links in the new
   entry only; it never edits a neighbour, never writes a banner.

2. **New derive-on-read script `scripts/knowledge_catalog.py`** (plugin `scripts/`,
   symlinked from repo `scripts/` like the others). Default output: entries grouped by
   Theme, each line `[[<stem>]] (<type>) — <Summary>`, with `(superseded by [[X]])`
   when the entry is superseded. **Supersession is the union of three sources, deduped
   by stem**: another entry's `## Related` `supersedes` edge to it, its own legacy
   `superseded by` edge, and its own legacy `<!-- superseded-by: -->` banner. Union, not
   precedence, so a stored banner and a derived edge can never double-mark or contradict
   — they name successors, and every named successor is listed once. Flags: `--themes`
   (theme names + counts), `--links-to <stem>` (computed backlinks with labels),
   `--by-type`. Entries missing Theme go under `(unthemed)`; missing Summary falls back to
   the H1 title. Reuses `knowledge_lint` / `knowledge_spans` parsing. Ignores `index.md` /
   `overview.md` if present.

3. **Routing.** The CLAUDE.md/AGENTS.md routing section (this repo's, and the template in
   `skills/init/references/steps.md`) drops the overview/index lines. The orientation path
   is the theme-grouped catalog; routing gives a **portable POSIX `awk` one-liner** (no
   plugin path needed) that prints one `theme | stem | summary` line per entry, sorted by
   theme — the same content as the catalog script — and names `knowledge_catalog.py
   --links-to` for backlinks. init's existing stale-routing refresh (template-of-record
   markers) detects the old overview/index wording and offers the new section, and
   `minerva:migrate` reports stale routing, so a consumer that upgrades is told rather
   than left with dead links.

4. **Lint.** `knowledge_lint.py` drops index drift, watermark and missing-reciprocal
   checks. Keeps duplicate ids and broken `## Related` links (errors). Missing
   `**Summary**` / `**Theme**` is an **error for an entry whose filename id is a date on or after the 3.0
   cutoff (`2026-10-01`, a constant in `knowledge_lint.py`; legacy NNN ids count as older)** and a **warning for an older
   entry**. Keying on the entry's own date, not on whether legacy files exist, keeps the
   rule stable when an old plugin or a stale CI job recreates `index.md`, and when a
   consumer deletes `index.md` by hand: every new entry is enforced, an un-backfilled
   legacy corpus stays green. Adds a
   warning for a legacy `index.md`/`overview.md` still present (pointing at
   `minerva:migrate-fix`) and an advisory warning for a theme used by exactly one entry
   (drift signal; a fresh theme legitimately starts as one, so it never errors).
   `minerva:lint` (read-only, judged dims) stays; its doc is updated.
   **Mixed plugin versions:** a collaborator still on 2.x whose cleanup recreates
   `index.md` produces a legacy-aggregate warning (visible, never an error, and no textual
   conflict on new 3.x entries, since 3.x never writes that file; a 2.x cleanup may still
   write back-links into older entries, which is harmless); a CI job calling
   `knowledge_fix.py` hits the tombstone and fails. 3.0 is a breaking release and
   `COMPATIBILITY.md` says every collaborator should upgrade.

5. **Delete reconciliation machinery.**
   - `minerva:cleanup`: delete `references/reconciliation.md` and every reconcile step;
     cleanup only removes merged worktrees and prunes branches (no PR opened).
   - Delete skills `minerva:synthesize` and `minerva:lint-fix` (their only jobs were
     overview refresh and index/reciprocal repair) plus their evals; remove them from the
     three catalog surfaces + `pages/index.md` (`2026-05-21-constraint-minerva-skill-catalog-sync`).
   - Delete `synthesis_status.py` and `knowledge_edits.py` (its span editors serve only
     `knowledge_fix.py`; `test_promote_invariant.py`'s editor tests go with it) and their tests. **`knowledge_fix.py` becomes a tombstone**: it
     prints that reconciliation was removed in minerva 3.0, tells the caller to delete the
     CI job and run `minerva:migrate-fix`, and **exits non-zero**. Deliberately not an
     exit-0 stub: a CI job that "succeeds" doing nothing is the silent-success failure this
     repo has repeatedly recorded; a loud, explained failure is the migration signal.
   - Orchestrators (`propose-ship`, `propose-ship-auto`), `ship`, `status`
     (+ `workstream_status.py` knowledge-health), `promote`, `explore`, `round-table`,
     `propose`/`phasing.md`, `using-minerva` (+ `runtime.md`, `codex.md`, `guide.md`),
     `COMPATIBILITY.md`, READMEs: remove reconcile/synthesize/overview/index references.
   - `minerva_runtime.py`: never writes the `reconciliation` phase; keeps accepting it when
     reading an existing checkpoint (back-compat for in-flight runs and old traces), with a
     one-line comment and a test.
   - `run_trace.py` / `run_compatibility_evals.py` / `gh_stub.py`: drop reconcile-specific
     handling where present.
   - `minerva:init`: stops scaffolding/backfilling `index.md` (and never creates
     `overview.md`); the routing template changes per step 3.
   - `knowledge_rename.py` (used by `migrate-fix`) **keeps** its legacy `index.md` /
     watermark retargeting, since legacy corpora can still be renamed before backfill;
     it is allowlisted in the stale-reference test, and its docstring says the handling
     is legacy-only.
   - `migration_status.py` / `minerva:migrate`: the aggregate signal **inverts polarity**.
     A present `index.md` / `overview.md` is now the migration need ("legacy aggregate —
     run `minerva:migrate-fix`"), and absence is the migrated, desired state; the
     "requires a green synthesize pass" text goes. `entries_without_related` stays as an
     advisory signal (forward links are still the cross-reference surface). Adds
     "entries missing Theme/Summary" and "routing still names overview/index".

6. **Migration for existing corpora.** New `scripts/knowledge_backfill.py` (run behind
   `minerva:migrate-fix`'s confirmation gate; `minerva:migrate` reports the need and the
   already-migrated state):
   - fills a missing `**Summary**` from the entry's `index.md` catalog line; an entry with
     no line keeps no Summary and is reported for hand-writing;
   - fills a missing `**Theme**` from the `overview.md` `## ` section that links it
     (single-valued: the first linking section wins), normalised to kebab-case from the
     heading text before its first `:` (leading article dropped); entries the overview
     never linked are reported as `(unthemed)` for hand-assignment;
   - then deletes `index.md` and `overview.md`;
   - inserts metadata lines only — never modifies other bytes; a corpus with neither
     legacy file is a no-op (idempotent).
   Existing stored back-links and banners are left in place (still valid; read by the
   catalog's supersession union).

7. **This repo.** Run the backfill on `.minerva/knowledge/` (all 49 entries lacking a
   Summary have an `index.md` line; 9 entries the overview never linked get a theme by
   hand; 2 multi-section entries take the first), review the generated theme names, delete
   `index.md` / `overview.md`, update `CLAUDE.md`.

8. **Release + consumer fallout.** Bump the minerva plugin to **3.0.0** (breaking) in
   both `plugins/minerva/.claude-plugin/plugin.json` and
   `plugins/minerva/.codex-plugin/plugin.json` (and any marketplace manifest that pins
   it), and add
   a `COMPATIBILITY.md` upgrade section: removed skills (`minerva:synthesize`,
   `minerva:lint-fix` → "skill not found"), `knowledge_fix.py` tombstone, the CI reconcile
   job to delete (seekless), and the migration steps (`minerva:migrate` →
   `minerva:migrate-fix` → re-run `minerva:init` for routing). The PR body repeats it.

9. **Knowledge.** One decision entry superseding
   `2026-08-05-decision-promote-add-only-reconcile-on-default`,
   `2026-06-02-decision-knowledge-wiki-navigability-layer`,
   `2026-06-03-decision-synthesis-layer-separate-file-advisory` and
   `2026-08-05-constraint-reconciliation-state-is-not-a-scalar` (forward `supersedes`
   links only — banners are now derived). It records the accepted narrative loss. The
   general lessons that merely *arose* from reconciliation
   (`read-then-act-is-not-a-lock`, `a-ref-lock-binds-only-writers-that-share-the-ref`,
   `deferred-work-needs-a-trigger`) stay valid and are linked `see also`, not superseded.

10. **Tests.** Update/delete affected tests (`test_knowledge_lint`, `test_knowledge_fix`,
    `test_synthesis_status`, `test_skill_contracts`, `test_promote_invariant`,
    `test_fence_awareness`, `test_migration_status`, `test_workstream_status`,
    `test_site_catalog`, `test_orchestrator_mode`, `test_plugin_guard_sites`,
    `test_run_trace`, `test_compatibility_evals`, `test_minerva_runtime`,
    `test_knowledge_rename`); add `tests/test_knowledge_catalog.py` (including a test that
    runs the routing `awk` one-liner, as written in the init template, against a fixture
    corpus and asserts it yields the same theme/stem/summary set as the script),
    `tests/test_knowledge_backfill.py`, and a stale-reference test (below).

### Candidates considered

- **A (chosen) — derive everything, Theme on the entry.** As above.
- **B — derive index + backlinks; keep a hand-written `overview.md` refreshed only by an
  explicit `minerva:synthesize` run on its own PR.** Removes per-merge reconciliation but
  keeps a 17k-token file read first every session, a skill, a watermark, and a (rare)
  conflict surface; it lags the corpus between explicit runs by construction.
- **C — keep stored aggregates, regenerate them on the work branch at ship time
  (rebase + regenerate before merge).** Re-introduces conflicts whenever two PRs are
  rebased concurrently or a merge queue reorders them; GitHub ignores `.gitattributes`
  merge drivers, so `merge=union` can't help. Dominated by A.

## Success criteria

- `.minerva/knowledge/index.md` and `.minerva/knowledge/overview.md` do not exist in this repo; every date-id entry has a `**Theme**` and a `**Summary**` line, and `knowledge_lint` reports zero errors on it.
- `python3 scripts/knowledge_catalog.py .minerva/knowledge` prints every entry exactly once, grouped by theme; `--links-to <stem>` lists computed backlinks; supersession is derived from the union of `supersedes` edges, legacy `superseded by` edges and legacy banners, each successor listed once (tested).
- `knowledge_backfill.py` fills Summary/Theme from legacy `index.md`/`overview.md`, deletes them, changes no bytes outside the inserted metadata lines, and is a no-op on a migrated corpus (tested).
- `knowledge_lint` errors on a missing Summary/Theme for an entry dated on/after 2026-10-01 and warns for an older one, regardless of whether legacy files exist (tested).
- The routing one-liner in the init template produces the same theme/stem/summary set as `knowledge_catalog.py` on a fixture corpus (tested); `minerva:init` no longer creates `index.md`.
- `migration_status.py` reports a present `index.md`/`overview.md` as the migration need and absence as migrated (tested).
- A test (`tests/test_no_reconcile_references.py`) asserts that `reconcil|synthesi[sz]|overview\.md|index-watermark|lint-fix` appears nowhere under `plugins/minerva/`, `README.md`, `pages/`, `CLAUDE.md` (and `.minerva/reference/` if present) except an explicit allowlist of files with historical/back-compat mentions (`COMPATIBILITY.md`'s upgrade section, the `knowledge_fix.py` tombstone, `minerva_runtime.py`'s legacy-phase read, the migrate/migrate-fix/backfill migration docs and `migration_status.py`, `knowledge_lint.py`'s legacy-aggregate warning, `knowledge_rename.py`'s legacy retargeting).
- `plugins/minerva/skills/synthesize/`, `plugins/minerva/skills/lint-fix/`, `evals/synthesize/`, `evals/lint-fix/`, `synthesis_status.py`, `knowledge_edits.py` are gone; `knowledge_fix.py` exits non-zero with a migration message; the three skill catalogs + `pages/index.md` no longer list the two skills.
- `minerva:cleanup` opens no PR and has no reconciliation step; promote's template documents `**Theme**` and write-once entries.
- Both `plugins/minerva/.claude-plugin/plugin.json` and `plugins/minerva/.codex-plugin/plugin.json` are at version 3.0.0 and `COMPATIBILITY.md` has the upgrade section described in Approach step 8.
- `python -m pytest tests/ -q` passes.
- A new decision entry supersedes the four entries named in Approach step 9.

## Open Questions

- None blocking. Theme vocabulary drift is accepted and surfaced (singleton-theme warning, `--themes` at promote time); merging near-duplicate themes is a rare, deliberate multi-file edit.
