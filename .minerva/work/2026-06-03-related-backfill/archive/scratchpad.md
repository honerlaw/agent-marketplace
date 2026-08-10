# Scratchpad: related-backfill (027)

## Panel decisions 2026-06-03

- [3/3 accept] scope check: ONE backfill unit; rename-APPLY RE-DEFERRED (zero live
  non-conforming files → no fixture, YAGNI). 5 conditions folded: editor-routed writes;
  justification gate + honest non-empty residual; closing synthesize; forward-edges-only
  (fixer owns reciprocals); record the re-deferral at promote.
- [2/3 accept → revise → 3/3 accept] approach (A′): round-1 Skeptic folds — vocab fenced
  to see also/builds on (retroactive supersedes = banner machinery); closing synthesize
  invoked WITH the in-place-drift rationale (bare count would self-skip); atomic
  forwards+reciprocals commit (CI gates the detector).
- [2/3 accept → revise → 3/3 accept] whole-proposal (v2): synthesize pinned POST-promote
  (watermark → corpus max 027); atomic commit stated as a HARD CI requirement
  (test_live_knowledge_clean errors on missing reciprocals); standalone = zero edges; the
  disposition table below is the pinned completion artifact.

## Per-edge disposition table (pre-write; post-self-review-gate)

All labels `see also` (within the fence; no supersedes/contradicts — none of these are
strict lineage). The corpus is reciprocity-clean today, so nothing currently links any of
the 9: every edge below is net-new. Forward edges are authored on the listed entry;
`knowledge_fix.py` creates the neighbor's reciprocal (and the `## Related` block itself on
002/008, which receive edges but author none).

| Entry | Disposition | Forward edge | Justification (body-grounded) |
|---|---|---|---|
| 001 | edge | → [[2026-06-02-decision-knowledge-wiki-navigability-layer]] — see also | Both shape init's Routing-section detection: 001 makes the name-matching lenient (old + new dir names); 017 widened that same detection window 4→6 lines when init learned to scaffold the wiki. |
| 002 | edge (receives) | — (reciprocal of 003 → 002) | 003's body cites 002 verbatim ("see …002… for prior history"); authoring the forward on 003's side is the grounded direction. Fixer creates 002's block. |
| 003 | edge | → [[2026-05-19-bug-promote-idempotency-check-misses-old-marker]] — see also | 003's canonical-empty-state contract is built on the promote marker whose format history 002 records; 003's own body cites 002 for that history. |
| 005 | edge | → [[2026-05-20-constraint-enter-worktree-absolute-paths]] — see also | The two halves of the worktree workflow's operational lore: 005 sequences `.gitignore` before `git worktree add`; 008 governs path construction after `EnterWorktree`. |
| 006 | **legitimately standalone** | — | The only entry about review-lens ownership; no other entry addresses the minerva:review / code-review responsibility split. Any edge would be manufactured. |
| 007 | edge ×2 | → [[2026-05-20-constraint-enter-worktree-absolute-paths]] — see also; → [[2026-06-03-constraint-skill-wraps-script-via-importable-api]] — see also | 007 mandates naming the concrete tool call (EnterWorktree) in skill prose and 008 documents that same tool's absolute-path semantics — the call-discipline and path-discipline halves of one contract (both born in the worktree units). 021 is the concrete invocation pattern (importable API + git-root anchor) for the script-wrapping instance of 007's general rule. |
| 008 | edge (receives ×2) | — (reciprocals of 005 → 008 and 007 → 008) | See 005/007 rows. Fixer creates 008's block with both lines. |
| 009 | edge ×2 | → [[2026-05-19-constraint-plugin-skills-auto-discovered-from-directory]] — see also; → [[2026-05-21-constraint-minerva-skill-catalog-sync]] — see also | 009's body explicitly says it "complements [[004]]" (auto-discovery applies inside a plugin, not between plugins) — promoting that prose link to a real edge. 009 and 010 record the same class of rule: human-facing registries are NOT auto-generated and must be manually synced (marketplace.json + README vs the three skill-catalog surfaces). |
| 014 | edge | → [[2026-06-03-decision-synthesize-wired-post-promote-self-gating]] — see also | 014 defines the per-decision skip / never-skippable / taxonomy discipline for the auto-orchestrator; 025 is the first extension of that taxonomy after 014 — it classified synthesis as delegation (an Operational no-panel row, "not a vote and not a skip") using exactly 014's framework. |

**Self-review gate (pre-write):** each edge re-read against both bodies; all eight kept as
load-bearing; no edge added to reach a count — 006 stays standalone. Expected residual
after backfill: `entries_without_related == ["006-decision-review-lens-ownership.md"]`
(non-empty = PASS).

- [3/3 accept] completion verification: all due criteria independently verified (Related-only
  diff 32/+0/−0 across exactly 13 files; both weakest edges grounded VERBATIM in target
  bodies; residual == ["006"] honest; 162 tests; detector clean; criteria 5/7 correctly
  not-yet-due post-promote).
- [skipped — small] review triage: ZERO findings (evidence: diff is pure ## Related
  additions already triple-verified by the completion panel for 015/016 compliance; no
  code changed → no code-review surface).
- [skipped — small] promote partition: single unambiguous PROMOTE (entry 027, contents
  mandated verbatim by success criterion 7: backfill decision + rename-APPLY re-deferral
  + reusable-backfill-skill candidate followup); disposition table already materialized
  in the corpus as real edges → archive; panel lines → routine noise.

- [2/2 accept] mid-work divergence (never-skippable): fixer crashed pre-write adding
  027's reciprocal into 015 — knowledge_edits.py not fence-aware (third 023-trap
  instance; crash + verified silent false-dedupe + dormant add_related_link variant).
  Replan warranted.
- [3/3 accept] new-plan acceptance (never-skippable): fence-aware fix with
  header-location-only semantics (fenced lines NEVER dropped from the complement),
  add_related_link folded in, three regression tests, BUG entry 028, criterion 8 added.
  See replan.md.
- promote: entries 027 (decision: backfill methodology + rename re-deferral + skill
  candidate followup) + 028 (bug: the fence-trap instance, builds on 023); reciprocals
  via the now-fixed fixer (015's reciprocal — the previously-impossible write — landed);
  detector clean; residual == ["006"]; 165 tests green.

## Notes
