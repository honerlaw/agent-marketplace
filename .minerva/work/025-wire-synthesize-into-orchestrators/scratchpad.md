# Scratchpad: wire-synthesize-into-orchestrators (025)

## Panel decisions 2026-06-03

- [3/3 accept] scope check: single unit (wire both orchestrators). Skeptic agreed it's
  one cohesive unit (decomposition is WORSE for drift per 010 lockstep); revise was
  about folding 3 specs into the proposal, not decomposing.
- [2/3 accept → revise → 3/3 accept] approach selection (A″ over B/C): round 1 Skeptic
  revise (minimalism-clause contradiction + nudge shape); round 2 folded — fold offer
  INTO the existing promote→ship gate; PR-body mention + advisory asymmetry close
  concerns 6/7. 6 LOW build-time items carried.
- [2/3 accept → revise → 3/3 accept] whole-proposal (v2): round 1 Skeptic revise on 3
  MEDIUMs — idempotency short-circuit re-point, OUTCOME line-shape pinning, taxonomy row.
  Round 2 folded all three + the LOW [synthesis]-is-not-a-vote note + Phase-4.5
  "Continue to Phase 5" terminator + taxonomy Phase column "Promote→Ship".

## Build-time items (from approach + proposal panels)

1. propose-ship: fold synthesis into the existing promote→ship gate; explicit order
   (offer → run synthesize incl Step-4 gate → await ship confirmation → ship). Edit the
   ACTUAL minimalism sentence preserving all 3 triggers.
2. propose-ship-auto: Phase 4.5 auto-invokes synthesize (auto-accept Step-4 only),
   terminates "Continue to Phase 5"; re-point Phase 4 step 2 + step 8 to Phase 4.5.
3. PR-body: ship handoff REQUESTS the "overview.md refreshed" line (assert instruction
   exists, not that it lands through ship's user gate #2).
4. overview.md NAMED in ship handoff staging set (ship stages specific paths, never -A).
5. [synthesis] OUTCOME line under `## Panel decisions` (wrote / no-op forms); add an
   in-body note it's an observability line, NOT a vote (promote-invisible like a skip).
6. Decision-taxonomy row: `Promote→Ship | Synthesis refresh (Phase 4.5) | Operational |
   No panel (synthesize self-gates) | n/a`.
7. minerva:synthesize literal token + anchor in BOTH contracts (lockstep, 012).
8. Retire synthesize's own out-of-scope wiring bullet; entry 024 untouched (016); new
   025 builds on 024.

## Notes
