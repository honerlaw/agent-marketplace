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
