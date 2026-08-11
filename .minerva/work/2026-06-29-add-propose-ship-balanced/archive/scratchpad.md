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

## Work notes 2026-06-29

- Implemented by mirroring propose-ship-quick: SKILL.md (9208B, under the 9216 budget after several trims), references/{verify-protocol,phases,governance}.md, evals/propose-ship-balanced/contract.json, + 4 catalog-surface edits.
- Two bugs caught by CI during work: (1) a `: ` colon-space in the SKILL.md description broke YAML frontmatter parsing → replaced with ` — `; (2) the using-minerva matrix row pushed using-minerva/SKILL.md over its 9216 budget → trimmed the row. Both fixed; re-ran green.
- Also fixed pre-existing staleness in pages/index.md ("Two orchestrators" → "Four orchestrators run the whole rail…") since it's site prose, not a minerva-skill edit.

## Panel decisions 2026-06-29 (work + review)

- [3/3 accept] completion verification: all 7 success criteria independently reproduced by both panelists (read files + ran the CI suite). SKILL.md 9208B ≤9216; 3 refs pointed-to; verify-protocol.md substantive (gate taxonomy, single-reviewer mechanism, behavioral load-bearing def + anti-circularity, Verifier brief, Skeptic brief, carried-over predicate/escape/checks/triggers/counter); phases.md covers 1–7 + 3 delegations; contract anchors (incl "Skeptic brief") resolve; skill in all 4 catalog surfaces; CI-scoped suite 311 passed (the 4 test_pull.py failures are pre-existing on main, outside the CI list). No mid-work divergence.
- [skipped — small] review triage: 1 LOW finding only (F1: `propose-ship-quick/SKILL.md:8` "three orchestrators" ladder line now stale) → deferred to followup per the proposal's Open Question; auto's out-of-scope rule forbids editing existing minerva skills this run. No medium+ finding, no load-bearing divergence → main LLM triaged directly.
