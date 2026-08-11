# Scratchpad: close-remaining-loose-ends

## Balanced decisions 2026-08-11
- [escalated to user] pre-flight + scope: the seed ("continue on all 5 things") overlapped the
  two stale Draft units, a hardcoded collision trigger. Asked two questions in one interaction.
  User chose: correct the stale records (not resume them), and BUILD the slug-first resolver in
  this unit despite being told it roughly doubles scope and would likely warrant
  propose-ship-auto. Affirmed after warning, so proceeding at balanced rather than re-raising.
- [decided] financials investigation (solo): before treating "repair or remove" as the user's
  call, checked — `git ls-files plugins/financials` returns ZERO tracked files; the plugin was
  deleted in 20d32e0 (PR #7) and only __pycache__ survives on disk. So repair was never an
  option and the question I'd handed the user had a dominant answer. Said so rather than
  letting them adjudicate a false choice.
- [reviewed — folded] scope check: single unit. Skeptic returned REVISE with two HIGH findings,
  both verified and both correct:
  (1) a Status-only edit would NOT clear the in-flight condition — the pre-flight predicate is
      an OR (Status is Draft OR scratchpad is not the post-promote marker), and neither unit has
      an archive/ or a marker. Confirmed on disk. Folded: full promote treatment on both.
  (2) provenance — items 1/2 trace to my own closing list (the "5 things" the user answered),
      but the adoption note (item 6) arrived from the peer AFTER the instruction. Folded by
      NAMING it as an addition in the proposal instead of folding it in silently.
  Also folded: reconciliation's skip branch is silent as well as misdiagnosed (same
  deferred-work shape); item 4's framing overstated (defect 7 is fixed — the live target is the
  calendar-invalid case plus defense-in-depth reporting); conftest's dead financials path;
  `**Status**:` is the real convention (51 of 52), not `## Status`.
- [reviewed — folded] approach (resolver): Skeptic returned REVISE with one HIGH finding I had
  missed entirely — the work-unit collision guard goes BLIND after any partial migration,
  because a renamed unit's legacy id leaves the filesystem and so leaves the safety map. A
  reference meaning a migrated work unit would then resolve "safely" to the wrong entry, which
  is precisely the failure the guard exists to prevent. Folded fail-closed: resolution refuses
  entirely unless the corpus is fully legacy. Also folded: `entries`/`work` are keyed by full
  stem so this needs a real {id: [stems]} grouping, NOT a dict lookup — and the Skeptic found
  this repo's own history has 001-gitignore-before-worktree AND 001-review-lens-ownership,
  two entries sharing legacy id 001, so the collision is real here; per-occurrence file+line
  records rather than the current {id: count} shape; and surfacing counts at migrate-fix's
  existing gate, since a flag nobody knows about is not a feature.
- [decided] whole-proposal soundness (solo): the riskiest piece is the only one that writes —
  the resolver — and it is fail-closed twice over (opt-in, and refusing outright on a
  partially-migrated corpus), so the default path stays byte-identical. Everything else is a
  deletion, a doc fix, or a report line.
- [decided] MD_LINK_RE (solo): confirmed as-designed, no change. Matches WIKILINK_STEM_RE's
  existing whole-repo reach, bounded by map-lookup-only, already pinned by a test.
- [decided] peer verification (solo): recorded partial. #4/#5/#7 confirmed on their real
  637-entry corpus; #1/#2/#3 need the pre-migration tree, which they have since hand-repaired.
  Declined their offer to reconstruct it — their user's repo and tokens, not mine to spend.
