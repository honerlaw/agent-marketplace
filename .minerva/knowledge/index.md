# Knowledge index
<!-- index-watermark: 030 -->

## Decisions

- [[001-decision-init-routing-detection-accepts-old-and-new-names]] — init's Routing-section detection accepts both old and new directory names
- [[005-decision-gitignore-before-worktree]] — add `.minerva/worktrees/` to `.gitignore` before running `git worktree add`
- [[006-decision-review-lens-ownership]] — minerva owns spec/knowledge review lenses; code-review owns quality
- [[011-decision-minerva-reference-tier]] — `.minerva/reference/` is the present-tense operational-doc tier, distinct from knowledge
- [[013-decision-behavioral-evals-provisional]] — behavioral skill-value evals are provisional: don't CI-gate, don't trust deltas yet
- [[014-decision-per-decision-skip-over-sizing-gate]] — gate per-decision and fail closed, not via an up-front sizing classifier
- [[017-decision-knowledge-wiki-navigability-layer]] — knowledge is a navigable wiki: maintained index.md + corpus-scan discovery (X′ over X)
- [[018-decision-phase-b-deterministic-lint-detector]] — Phase B split: a deterministic knowledge-lint CI gate ships first; the LLM-judged minerva:lint skill is deferred
- [[020-decision-minerva-lint-read-only]] — minerva:lint ships read-only (advisory judged dims); the gated fix-applier is deferred to Phase B.3
- [[022-decision-knowledge-fix-two-safety-models]] — the wiki fixer uses two safety models: entry body byte-identity vs index skeleton-preservation
- [[024-decision-synthesis-layer-separate-file-advisory]] — the synthesis layer is a separate overview.md with a new-scope-only watermark; its content is advisory, never CI-gated
- [[025-decision-synthesize-wired-post-promote-self-gating]] — minerva:synthesize is wired into both orchestrators as a self-gating post-promote/pre-ship step (delegation, not a panel)
- [[026-decision-migration-check-read-only-entry-re-blindspot]] — minerva:migrate is the read-only migration-shape check; its reason to exist is the ENTRY_RE false-clean blind spot every wiki tool shares
- [[027-decision-related-backfill-hand-authored-rename-redeferred]] — the initial ## Related backfill was hand-authored (the spike for any future skill); rename-APPLY stays deferred at zero live instances
- [[029-decision-routing-section-is-the-wiki-reading-protocol]] — the Routing section teaches the wiki reading protocol; stale sections get a gated refresh with markers derived from the template-of-record

## Bugs

- [[002-bug-promote-idempotency-check-misses-old-marker]] — promote idempotency check missed the old scratchpad marker format
- [[028-bug-knowledge-edits-not-fence-aware]] — the span editors read fenced examples as structure: crash/false-dedupe on any edge into 015 (third fence-trap instance; fixed)

## Patterns

- [[030-pattern-rejected-alternative-reinvented-at-runtime]] — rejected alternatives recur at runtime; prohibit in skill text, test-anchored

## Constraints

- [[003-constraint-post-promote-scratchpad-canonical-empty]] — the post-promote scratchpad is the canonical empty state downstream skills expect
- [[004-constraint-plugin-skills-auto-discovered-from-directory]] — plugin skills are auto-discovered from `skills/`; no manifest update needed
- [[007-constraint-skills-must-call-tools-not-prose]] — skills must invoke tools directly, not describe actions in prose
- [[008-constraint-enter-worktree-absolute-paths]] — `EnterWorktree` does not redirect absolute paths
- [[009-constraint-marketplace-plugin-registry-not-auto-discovered]] — marketplace registry isn't auto-discovered: update `marketplace.json` + README
- [[010-constraint-minerva-skill-catalog-sync]] — skill catalogs aren't auto-generated: three doc surfaces must stay synced
- [[012-constraint-skill-structural-contracts]] — every skill carries a declarative structural contract, enforced by an enumerating test
- [[015-constraint-knowledge-cross-reference-convention]] — entries cross-reference via a `## Related` block of wiki-links with a closed relationship vocabulary
- [[016-constraint-promote-narrowed-never-overwrite]] — promote edits existing entries only within the `## Related`/banner span; bodies are append-only
- [[019-constraint-knowledge-span-model-single-sourced]] — the wiki span model is single-sourced in scripts/knowledge_spans.py; import it, never re-derive
- [[021-constraint-skill-wraps-script-via-importable-api]] — a prose skill wraps a sibling Python tool via its importable API, anchored to the working-tree root; not the CLI, not CWD-relative
- [[023-constraint-wiki-edge-derivation-fence-aware]] — any tool deriving wiki cross-ref edges must be fence-aware (a fenced `## Related` example is not a real edge)
