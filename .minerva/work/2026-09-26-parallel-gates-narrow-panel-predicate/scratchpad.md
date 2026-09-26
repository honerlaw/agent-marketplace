# Scratchpad: parallel-gates-narrow-panel-predicate

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-09-26
- [reviewed — folded] scope check: one unit, one PR, no phases; Skeptic item 1 (phasing cost misstated as decomposition cost) judged not load-bearing — phasing's trigger is a diff too large to review in one PR, which ~500–850 lines is not, and phasing adds a PR/CI/merge-wait cycle; reasoning rewritten with the correct cost model. Folded items 2 (test_skill_dispatch REGISTERED_SITES + test_decision_telemetry named, test estimate raised), 3 (surface defined in Approach §2) and 4 (using-minerva / propose-ship summaries added to criterion 5) (tier: reviewer — multi-file so solo fails, no panel clause; parallel wave)
- [panel — 3/3 accept, 3 with fixes] approach: A — concurrent propose gate wave + narrowed interface clause + verify ∥ review; rejected B (2-agent mini-panel tier: new quorum/telemetry surface, problem is routing not panel size) and C (parallelize only scope+approach: leaves whole-proposal, the long pole, serial) (tier: panel — changes the orchestrator's cross-cutting protocol and sits in tension with 2026-09-23's fail-closed rule; parallel wave)
    - fix (skeptic/arbiter): route in gate order, batch dispatch in one message
    - fix (skeptic/arbiter): late upward move must not slip past the restart check — resolved by holding whole-proposal until scope/approach are final, then one restart check
    - fix (skeptic/arbiter): a consumer added in the same unit does not make an interface "existing"; name the fail-closed trade-off explicitly; record adjudicated surfaces in the decision-log reason; map all completion-panel outcomes in the discard rule; criterion 3 names the "Both predicates fail closed" line; run_trace overlap noted in Open Questions; Parked dispatches generalized to a wave
    - fix (proponent/arbiter): cross-reference 2026-07-27 (one-message dispatches already concurrent); disambiguate 6-run pick stability from 2026-09-05's 17/25 revision rate
- [panel — 3/3 accept, 3 with fixes] whole-proposal: sound (tier: panel — proposal changes a cross-cutting contract, the orchestrator's tier-selection protocol; parallel wave — dispatched with the draft's recommended approach applied; restart check: no staleness condition held, approach pick unchanged)
    - fix (skeptic): doubt→reviewer scoped to the narrowed interface clause only; ambiguity / blast-radius / knowledge-tension doubt still convenes a panel (arbiter judged the broader rule defensible; the narrower one was adopted as the conservative reading, matching the evidence)
    - fix (skeptic/arbiter): main model's specific doubt passed to the Skeptic in CONTEXT; once-per-surface suppresses only an already-approved change; discard rule covers inline-audit findings; reconciliation order made explicit (scope/approach folds merge first); governance states a restarted gate can reach 4 reviewer dispatches
    - fix (proponent/arbiter): test_skill_dispatch REGISTERED_SITES named; minor version bump justified (refinement, no skill/caller removed)
