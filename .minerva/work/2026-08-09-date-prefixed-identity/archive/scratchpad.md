# Scratchpad: date-prefixed-identity

## Panel decisions 2026-08-09

- [user-directed] scope check: ONE unit covering both knowledge entries and work units. User instruction: "do the entire thing in one unit, do not stop to ask me to continue". A prior `propose-ship-balanced` scope check had resolved to decomposition (two units, entries first); the user overrode it. Not recast as predicate evidence.
- [user-directed] rename lives in a NEW `minerva:migrate-fix` skill rather than an apply-mode on `minerva:migrate` — user chose this when asked, preserving the `020` read-only/applier split and leaving `026`/`027` intact in spirit.
- [escalated to user] work-unit scope: user chose "Both entries and work units" over entries-only. Escalation counter: 1.
- [1/3 accept → revised] approach selection, round 1: Proponent accept; Skeptic revise (7 findings); Arbiter revise. Skeptic's headline claim — that retiring `knowledge_next_nnn.py` reopens knowledge `055`'s silent-duplicate hole — was judged MISTAKEN by the Arbiter and independently by the main model: under full-stem identity an identical stem is the same PATH, so git raises an add/add conflict. `055`'s premise is inverted, not ignored.
- [2/3 accept, skeptic dissented] approach selection, round 2: A1 adopted. Folded: dual-accepting alternation extended to `cleanup/SKILL.md:19` and `ship/references/protocol.md:9` bulk globs; date semantics restated as landing-commit (ship's `--squash` has `--merge`/`--rebase` fallbacks, so it is not uniformly the ship date); `propose`'s duplicate-slug check audited for date-compatibility.
- [0/3 accept → revised] whole-proposal acceptance, round 1: both reviewers independently flagged the same two gaps — the 532-occurrence wikilink rewrite had NO documented mechanism, and the proposal's own named worst case (a dated work unit invisible to `cleanup`/`ship` bulk scans) had no success criterion.
- [2/3 accept, skeptic dissented] whole-proposal acceptance, round 2: accepted with five Arbiter folds — (1) extend the allocation rewrite to `minerva:promote` and invert `test_promote_invariant.py:234`; (2) add `--follow` to date derivation; (3) add calendar validation so criterion 5 is achievable; (4) add criteria 15b/15c for the banner marker and allocator removal; (5) pin `width` in the composite sort key.

## Panel concerns 2026-08-09

Logged from dissenting Skeptics, for `minerva:review` to scrutinise:

- **Rename-history sensitivity (medium-high).** `--follow` is now specified, but the Arbiter noted the cited example (`9f40272` renaming `005-…`→`008-…`) happens to land on the same calendar day as the original add, so the fix is unverified against a real cross-day rename. Worth a fixture.
- **Criterion 8 is judgment-based, not mechanical** (contrast criterion 9's byte-identity assertion). Distinguishing fenced examples and superseded-entry prose from stray live links needs a read, not a script.
- **Regex/script surface was undercounted twice** across rounds. The sweep must be grep-enumerated, not driven off any count in the proposal.
- **`propose`'s steps 3–8 are a procedure, not a glob.** Risk of "just fix the regex" when the whole allocate-then-name flow must be rewritten.

## Notes

## Progress 2026-08-09

### Landed (2 commits, verified)

- `knowledge_lint.py` — dual-accepting `ID_RE_SRC` grammar; `is_date_id` /
  `is_conforming_id` (calendar validation, so `2026-13-45` is rejected);
  `id_sort_key` / `corpus_id_width` composite ordering; all 6 id-position regexes
  re-anchored. `parse_index` and `lint_knowledge` re-keyed NNN → full stem;
  duplicate-id check, the blanket quarantine, and both watermark reads deleted.
- `knowledge_spans.py` — `BANNER_MARKER_RE` carries the full stem.
- `knowledge_edits.py` — `add_supersede_banner` writes the stem marker and its
  idempotency guard compares stems (was `endswith(f"{nnn} -->")`).
- `knowledge_fix.py` — `_CATALOG_LINE_RE` alternation; `plan_index` no longer
  emits the `index-watermark` line.

**Verified:** live 56-entry all-`NNN` corpus lints 0 errors / 3 pre-existing
warnings — dual-acceptance holds, criterion 3 satisfied at the script layer.
Sort order `054 < 999 < 1000 < 2026-08-09` confirmed.

### Test state

18 failures caused by this change, all in deliberately-changed categories; they
need updating to the new intended behaviour, not reverting:

- `test_knowledge_lint.py` — `test_duplicate_nnn_is_detected`,
  `test_duplicate_nnn_does_not_indict_the_wrong_file` (both retired by design);
  `test_corruption_below_the_watermark_is_self_healed_not_errored`,
  `test_watermark_above_max_is_an_error`, `test_out_of_order_merge_stays_green`
  (watermark retired); `test_entry_missing_catalog_line`,
  `test_catalog_line_with_no_file`, `test_one_way_reciprocal_missing_back_nnn`
  (messages now name stems); `test_slug_mismatch_is_warning_not_error` — NOTE a
  real behaviour change: a catalog/filename slug mismatch was one cosmetic
  warning, and under stem keying it surfaces as an error + a pending warning.
  Decide deliberately whether to restore a softer signal.
- `test_knowledge_fix.py::test_index_skeleton_and_order_preserved` — asserts the
  watermark.
- `test_promote_invariant.py::test_banner_preserves_body`,
  `test_banner_and_related_together_preserve_body` — marker format.

`test_pull.py`'s 4 failures pre-exist on `main` (ModuleNotFoundError), unrelated.

### Not started

1. `synthesis_status.py:102` — still `int(n) > watermark`; must become per-record
   (un-synthesized iff stem not wikilinked from `overview.md`) and drop
   `SYNTH_WATERMARK_RE`. **This is the one place the old scalar floor is still
   live**, and it will crash on a date id.
2. `migration_status.py` — inherits `ENTRY_RE`; needs the calendar check wired in.
3. Delete `knowledge_next_nnn.py` + `test_knowledge_next_nnn.py`, and rewrite the
   FOUR promote references (`promote/SKILL.md:36,42`,
   `references/wiki-maintenance.md:66`, `references/modes.md:24,43`). Invert
   `test_promote_invariant.py:234` — it is a bare string-presence assertion that
   stays GREEN while promote points at a deleted script.
4. `propose/references/on-approval.md` steps 3–8 — a procedural rewrite, not a
   glob edit.
5. New `scripts/knowledge_rename.py` + `minerva:migrate-fix` skill: stem map,
   up-front batch collision refusal before any `git mv`, git date derivation
   (`git log --follow --diff-filter=A --reverse --format=%cs | head -1`,
   work dirs anchored on `<dir>/proposal.md`), fence-aware wikilink rewrite
   importing `knowledge_spans.py`.
6. Prose globs: `cleanup/SKILL.md:19`, `ship/references/protocol.md:9`.
7. Run the migration: 56 entries, ~52 work dirs, 532 wikilinks, 56 Context fields.
8. Prose sweep (root `CLAUDE.md`, init template, README, ~30+ skill files);
   register `migrate-fix` on 4 catalog surfaces incl. `pages/index.md` (038).
9. Knowledge: supersede `026`, `027`, `055`; amend `054`.
