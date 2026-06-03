# Knowledge index
<!-- index-watermark: 014 -->

## Decisions

- [[001-decision-init-routing-detection-accepts-old-and-new-names]] — init's Routing-section detection accepts both old and new directory names
- [[005-decision-gitignore-before-worktree]] — add `.minerva/worktrees/` to `.gitignore` before running `git worktree add`
- [[006-decision-review-lens-ownership]] — minerva owns spec/knowledge review lenses; code-review owns quality
- [[011-decision-minerva-reference-tier]] — `.minerva/reference/` is the present-tense operational-doc tier, distinct from knowledge
- [[013-decision-behavioral-evals-provisional]] — behavioral skill-value evals are provisional: don't CI-gate, don't trust deltas yet
- [[014-decision-per-decision-skip-over-sizing-gate]] — gate per-decision and fail closed, not via an up-front sizing classifier

## Bugs

- [[002-bug-promote-idempotency-check-misses-old-marker]] — promote idempotency check missed the old scratchpad marker format

## Patterns

## Constraints

- [[003-constraint-post-promote-scratchpad-canonical-empty]] — the post-promote scratchpad is the canonical empty state downstream skills expect
- [[004-constraint-plugin-skills-auto-discovered-from-directory]] — plugin skills are auto-discovered from `skills/`; no manifest update needed
- [[007-constraint-skills-must-call-tools-not-prose]] — skills must invoke tools directly, not describe actions in prose
- [[008-constraint-enter-worktree-absolute-paths]] — `EnterWorktree` does not redirect absolute paths
- [[009-constraint-marketplace-plugin-registry-not-auto-discovered]] — marketplace registry isn't auto-discovered: update `marketplace.json` + README
- [[010-constraint-minerva-skill-catalog-sync]] — skill catalogs aren't auto-generated: three doc surfaces must stay synced
- [[012-constraint-skill-structural-contracts]] — every skill carries a declarative structural contract, enforced by an enumerating test
