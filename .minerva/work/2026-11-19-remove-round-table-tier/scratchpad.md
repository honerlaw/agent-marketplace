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
- [reviewed — clean] completion verification: Verifier independently reproduced all 11 criteria, ran the full suite (1112 passed), found no interface change beyond the approved scope (tier: reviewer floor; code review dispatched alongside)
- [solo] review triage: 9 FIX / 0 SUGGEST / 0 IGNORE (tier: default-solo row — every finding had a writable failure scenario and was small enough to absorb; no item had two defensible dispositions; none was a load-bearing divergence, so no replan-vs-FIX gate)

## Work notes
- The Adjudicator dispatch line must say exactly "wait for results": `tests/test_skill_dispatch.py` pins that phrase on every dispatch-instructing line, and "waiting for results" slipped past the first draft. decision-protocol now registers 4 dispatch sites (Skeptic, fold-audit, Adjudicator, Verifier).
- `run_trace.parse_description` must test "adjudicator" BEFORE "fold-audit": an Adjudicator brief description naturally names the fold-audit that sent the decision there, and the old order classified it as a fold-audit.
- "A clause fires once per approved change" and the wave's "routed on a pending clause" restart condition were dropped, not reworded: both existed only to stop the interface clause re-convening panels. With no panel tier a re-fired clause just keeps a decision at reviewer.
- Capped rows (triage / partition / TODO) lost their special "up-move goes to the user" rule: with one ladder everywhere, the ceiling concept has nothing left to clamp.
- `pages/index.md` principle "Adversarial by default" rewritten as "Independent scrutiny, not debate" — it is a stated minerva bias, not just a catalog line.
- COMPATIBILITY.md gained an "Upgrading to 4.0" section, matching the 3.0 precedent for deleted skills (not in the proposal's file list; found while bumping its version line).
- Pre-existing, not this unit: `decision_telemetry.py` reports `2026-09-23-adaptive-propose-ship-auto/archive/scratchpad.md:8: unknown tag [reviewed — clean]` on main too (the tag carries markdown bold inside the brackets).

## Review triage 2026-11-19
Local-diff mode (fresh-context subagent). Minerva audit (inline): no findings — every Approach item maps to the diff; registries carry no panel mentions; skill-catalog-sync and dispatch-pin constraints hold.
1. medium — phases.md wave (b)/(d) vs Parked dispatches gave conflicting fold-audit timing → FIX: fold-audits go out as soon as their own fold is written; whole-proposal's only after the restart check.
2. medium — decision-protocol: user rung keyed on verdict `escalate` vs rulings-win rule → FIX: the rulings decide; the verdict only summarises (SKILL.md, governance aligned).
3. low — disputed items cited "by number" across two separately numbered lists → FIX: labels C<n> / F<n> in dispatch text and brief.
4. low — pages/index.md:28 still said "votes logged" → FIX.
5. low — eval contract duplicated "Verifier"/"fold-audit" anchors → FIX: removed the added duplicates.
6. low — governance claimed telemetry catches a skipped Adjudicator rung; it did not → FIX: telemetry now flags an Auto escalation with no adjudication after it, gated on dates ≥ 2026-11-19 so panel-era archives stay clean; tests added.
7. low — stale `paired_with_lineno` comment → FIX.
8. low — `adjudications:` render line untested → FIX: test added.
9. low — dead first half of an `or` assertion → FIX: rung headers asserted in decision-protocol, ladder summary in SKILL.md.
- Absorbed fix: decision_telemetry reported the 2026-09-23 transition run's `[reviewed — clean]` under a legacy `## Panel decisions` header as unknown, so the problem list never read clean; the Panel classifier now falls back to the closed vocabulary (test added). Surfaced at promote as a TODO, absorbed per deferral-bar outlet 0.
