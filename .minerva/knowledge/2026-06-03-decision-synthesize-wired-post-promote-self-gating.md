# minerva:synthesize is wired into both lifecycle orchestrators as a self-gating post-promote / pre-ship step (delegation, not a panel decision)

**Date**: 2026-06-03
**Type**: decision
**Context**: .minerva/work/2026-06-03-wire-synthesize-into-orchestrators (see git history if the worktree has been cleaned up)

## Context

Unit 024 shipped `minerva:synthesize` as a manually-invoked maintenance skill and
explicitly deferred wiring it into the lifecycle orchestrators to a follow-up
([[2026-06-03-decision-synthesis-layer-separate-file-advisory]]). The user asked to wire it into
both `minerva:propose-ship` and `minerva:propose-ship-auto` while "allow[ing] the LLM to
decide IF it should run." This entry records how that wiring was done.

## Decision

**The seam is post-promote / pre-ship in both orchestrators.** Promote adds knowledge
entries, pushing the corpus past the wiki overview's synthesis-watermark — so
un-synthesized scope exists exactly then, and synthesizing before ship lets the refreshed
`overview.md` ride the same PR (rather than dangling uncommitted or trailing in a later
PR). Because `minerva:ship` stages **specific paths** (never `git add -A`), both
orchestrators **name `.minerva/knowledge/overview.md` in the ship hand-off's staging set**
and request a PR-body line noting the advisory refresh.

**The two orchestrators take the idiomatic shape of each, but it is the same feature:**

- **`minerva:propose-ship`** (user-gated, a thin conductor with a minimalism clause):
  the synthesis offer is **folded into the existing promote→ship gate** rather than added
  as a separate nudge — so it introduces **no new inter-phase interaction** and the
  `## Out of scope` minimalism sentence stays true. Order is explicit: summarize promote →
  offer `minerva:synthesize` if entries were added → (if accepted) run it incl. its own
  write gate → await ship confirmation → ship.
- **`minerva:propose-ship-auto`** (panel-gated): a new **Phase 4.5** between Promote and
  the Ship gate **always invokes** `minerva:synthesize` in auto-mode, leading with an
  auto-mode instruction that **auto-accepts only synthesize's write-confirmation gate**
  (mirroring how Phase 6 auto-accepts ship's hard gates) and leaves its decide-IF
  self-gate intact.

**This is delegation, NOT a panel decision.** The "decide IF to (re)synthesize" judgment
lives *inside* `minerva:synthesize` (its self-gate, driven by the deterministic
`synthesis_status` signal), so the orchestrator has nothing to vote on: **no consensus
panel is convened and no Decision-taxonomy panel row is added** (the taxonomy carries it
as an Operational, no-panel row). Phase 4.5 logs a `[synthesis]` outcome line for
observability — explicitly *not* a vote and *not* a skip (promote-invisible, like a skip).

## Implications

- A single-entry promote typically makes Phase 4.5 **no-op**: synthesize's own threshold
  ("one minor entry → stop") fires, so the auto path invokes synthesize most runs but
  usually writes nothing — the no-op is expected, not a bug.
- Auto-mode commits a refreshed `overview.md` with no human review; this is acceptable
  precisely because the overview is advisory and never CI-gated
  ([[2026-06-03-decision-synthesis-layer-separate-file-advisory]] / 013) — a bad link degrades
  navigation but never corrupts the record and self-repairs via the next run's
  deterministic `link_rot` signal.
- The auto-mode instruction is the established pattern for injecting gate-acceptance into
  a delegated skill without modifying it: Phase 6 does it for `minerva:ship`, Phase 4.5
  now does it for `minerva:synthesize`. The delegated skill stays unchanged.

## Related
- [[2026-06-03-decision-synthesis-layer-separate-file-advisory]] — builds on
- [[2026-05-31-decision-per-decision-skip-over-sizing-gate]] — see also
