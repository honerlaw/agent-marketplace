# Scratchpad: remove-round-table-tier

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-11-19
- [user-directed] pre-flight: in-flight check found only this session's own unit, created minutes earlier by minerva:propose; the user invoked propose-ship-auto directly after its post-write gate — taken as "resume", no collision asked, counter not incremented
- [user-directed] scope check: one unit, one PR — chosen by the user in minerva:propose (no phases)
- [user-directed] approach selection: one PR (vs. two phases) — chosen by the user in minerva:propose after grill-plan
- [user-directed] whole-proposal soundness: every section approved by the user in minerva:propose; Phase 1 gates not re-run

## Work notes
- The Adjudicator dispatch line must say exactly "wait for results": `tests/test_skill_dispatch.py` pins that phrase on every dispatch-instructing line, and "waiting for results" slipped past the first draft. decision-protocol now registers 4 dispatch sites (Skeptic, fold-audit, Adjudicator, Verifier).
- `run_trace.parse_description` must test "adjudicator" BEFORE "fold-audit": an Adjudicator brief description naturally names the fold-audit that sent the decision there, and the old order classified it as a fold-audit.
- "A clause fires once per approved change" and the wave's "routed on a pending clause" restart condition were dropped, not reworded: both existed only to stop the interface clause re-convening panels. With no panel tier a re-fired clause just keeps a decision at reviewer.
- Capped rows (triage / partition / TODO) lost their special "up-move goes to the user" rule: with one ladder everywhere, the ceiling concept has nothing left to clamp.
- `pages/index.md` principle "Adversarial by default" rewritten as "Independent scrutiny, not debate" — it is a stated minerva bias, not just a catalog line.
- COMPATIBILITY.md gained an "Upgrading to 4.0" section, matching the 3.0 precedent for deleted skills (not in the proposal's file list; found while bumping its version line).
- Pre-existing, not this unit: `decision_telemetry.py` reports `2026-09-23-adaptive-propose-ship-auto/archive/scratchpad.md:8: unknown tag [reviewed — clean]` on main too (the tag carries markdown bold inside the brackets).
