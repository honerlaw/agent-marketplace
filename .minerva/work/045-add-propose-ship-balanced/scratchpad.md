# Scratchpad: add-propose-ship-balanced

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Panel decisions 2026-06-29

- [3/3 accept] scope check: single work unit — mirrors 042's add-propose-ship-quick deliverable shape; the single-reviewer mechanism has no second consumer so extraction (à la 033/round-table) would be a thin wrapper. (Skeptic accept; flagged vote-semantics-on-dissent + telemetry-provenance as proposal-phase gaps — both resolved in the approach.)
- [2/3 accept → revise → 3/3 accept] approach selection: Approach A v2 — standalone self-contained skill, single advisory reviewer (one sonnet agent) at scope/approach/completion (+ rare never-elide gates), main model arbitrates inline, no re-dispatch. Rejected B (extend round-table with a 1-agent mode — bloats its 3-role identity) and C (flag on quick — forbidden by never-modify-existing-skill). Round 1 Skeptic+Arbiter revise on 3 MUST-FIX spec gaps (Verifier brief; behavioral "load-bearing critique" threshold + anti-circularity escape; routing discriminators); all three folded into v2; round 2 unanimous.
- [3/3 accept] whole-proposal acceptance: proposal internally consistent, success criteria mechanically checkable, ready to write. 4 Skeptic items folded during authoring: (1, med) added a "Skeptic brief" contract anchor so SC-3's Skeptic-brief requirement is CI-enforced; (2, low) normalized the gate label to "replan-acceptance"; (3, low) stated which 3 gates fire every run vs. when-triggered; (4, low) noted pages/index.md is verified by test_site_catalog.py separately (the 042/010/034/038 pattern), not a cross_surface gap.

## Panel concerns 2026-06-29

- (med) contract.json must include a `"Skeptic brief"` anchor (in references/verify-protocol.md) — otherwise an implementer could drop the Skeptic brief and still pass CI. [folded into proposal Approach item 6 + Success criteria]
