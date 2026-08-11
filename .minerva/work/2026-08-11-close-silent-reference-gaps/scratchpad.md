# Scratchpad: close-silent-reference-gaps

## Balanced decisions 2026-08-11
- [decided] seed: the six defects came from a peer Claude session that ran `minerva:migrate-fix`
  against a real external 637-entry corpus. All six re-verified against THIS repo's source
  before proposing — the peer read an install at `~/.claude/plugins/minerva/`, so its line
  numbers were treated as hints, not facts. Two were reproduced mechanically (the
  CATALOG/RELATED divergence table, and the grep false-positive) rather than taken on report.
- [reviewed — folded] scope check: single unit. Skeptic accepted, and flagged three things
  worth folding: (a) defect 4 is an output-contract addition, not a pattern fix, so the
  proposal now says so explicitly; (b) defects 5/6 live in markdown snippets with no
  executable coverage — `test_skill_contracts.py` anchors are presence-only, the exact rot
  shape knowledge 2026-08-10 warns about — so the tests now EXTRACT and EXECUTE the snippets;
  (c) defect 1's semantic direction was unresolved. Not folded: a 2-unit split (edge-model vs
  reference-model), which the Skeptic itself said would not change the answer.
- [reviewed — folded] approach: option B (extract a shared `related_edges()`), over fixing
  each site independently and over shipping 1+2 first. Skeptic independently raised the same
  load-bearing gap as the scope Skeptic — `related_edges()` must COMMIT to one semantic for a
  multi-target Related line, and it noted the existing pinned test
  `test_second_link_on_a_related_line_counts_as_a_back_link` uses exactly that fixture shape.
  Folded by resolving it, and the code decided it rather than taste: `plan_reciprocals`
  ALREADY has a `label is None` -> refusal branch, so widening the edge set turns the reported
  failure (neither planned nor refused) into a visible refusal with no new machinery. Also
  folded the Skeptic's point that `plan()` currently never reads file bodies, so defect 4
  needs a factored file walk.
- [decided] whole-proposal soundness (solo): bounded and measurable. Measured before
  committing — 0 of this repo's 62 entries have a divergent Related line, so the widening is
  inert on the live corpus and cannot move the CI gate. That is why criterion 7 requires
  fixtures that fail BEFORE their fix; a clean lint run proves nothing here.
- [reviewed — folded] mid-work divergence: a SEVENTH defect, found because defect 4 made me
  run the rename CLI on this repo — `WORK_DIR_RE` matched a bare NNN only, so already-migrated
  work dirs were re-dated (`2026-08-07-foo` -> `2026-08-10-08-07-foo`), on all 50-odd of this
  repo's units. Pre-existing on main; the entry branch never had it because `ENTRY_RE` embeds
  the shared grammar. Decided: fix in-unit + replan. Skeptic accepted and named five things,
  all folded — a fail-before fixture (criterion parity), the missing `ID_RE_SRC` import, the
  now-false idempotency claim in migrate-fix/SKILL.md, the entry branch's non-gap, and the
  calendar-invalid edge case.
- [reviewed — folded] new-plan acceptance: replan entry accepted. Skeptic caught that commit
  c8ea4ad added `tests/test_skill_snippets.py` WITHOUT enumerating it in evals.yml — so the
  four tests covering defects 5/6 were dark to CI from the moment they landed, which is this
  unit's own thesis turned on itself. Named in the replan rather than left as an unexplained
  line in the diff. Also fixed an off-by-one ("eighth" -> "ninth" criterion).
- [reviewed — folded] completion verification: Verifier reproduced all 9 criteria independently
  (reverting sources in an isolated copy, re-running the extracted snippets, checking no
  pre-existing test was weakened) and returned accept.
- [decided] review triage (solo): 4 findings from the code-review pass, 3 FIXED not noted.
  (1) MEDIUM, and the one that mattered: the new shorthand scan was NOT fence-aware, so a
  fenced `[[139]]` example counted as a live reference — the exact silent-miscount shape this
  unit exists to close, reproduced inside the feature built to report it. Violates
  [[2026-06-11-constraint-fence-scans-import-fence-re]]. (2) the corrected grep had widened
  `{3,}` to `+`, admitting any bracketed number; `{3,}` is the legacy id's own width, so the
  date exclusion alone does the job. (3) `related_out_stems`/`related_mention_stems` became
  byte-identical after the extraction and the comment describing them as different was now
  false — collapsed to one set, comment rewritten. (4) LOW: `MD_LINK_RE` is not
  directory-anchored — kept deliberately (it matches `WIKILINK_STEM_RE`'s existing whole-repo
  reach and is bounded by map-lookup-only), but pinned with a test so the intent is explicit.
