# Scratchpad: skill-progressive-disclosure

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Panel decisions 2026-06-11

- [user-directed] in-flight collision: resume 035 under auto (user picked resume at hardcoded pre-flight escalation)
- [user-directed] scope check / approach selection / whole-proposal acceptance: all decided explicitly by the user in this session's manual explore→propose flow (section-by-section approval) — no panel re-vote convened; user decisions outrank panels

## Work notes 2026-06-11

- propose-ship-auto split: core 8041B + references/{panel-protocol,phases,governance}.md. Verbatim audit: 0 original lines lost. Zero contract retargets needed (anchors survive in core preamble/stubs).
- Divergence note (routine, not load-bearing): proposal anticipated deleting orchestrator phase prose duplicating delegated skills; in fact Phases 1–4 are INLINED (their delegated skills are never Skill-invoked in auto mode), so that prose is the executable spec — moved verbatim, zero deletions. Budget met by moves alone. Approach unchanged.
- Decision taxonomy moved into references/panel-protocol.md (read-before-first-decision file) to fit the 9KB core; core stubs re-point to it.
- using-minerva/promote/init/debug split (cores: 8425/4182/3524/4691B). Decision matrix kept in using-minerva core deliberately — it is the cross_surface target other contracts check. Verbatim audits clean.
- 13 contract anchors retargeted via new `file` field (debug→workflow.md ×1; init→steps.md ×8; promote→modes.md ×2, wiki-maintenance.md ×2). Rationale for all: prose moved verbatim by 035's progressive disclosure; contract follows the text instead of weakening.
- ship/review/propose split (cores: 3275/3103/5908B); 10 anchors retargeted (ship ×5, review ×5 → protocol.md). Verbatim audits clean.
- round-table rewritten per approach item 4 (the one sanctioned content edit): shared ARTIFACT+CONTEXT block stated once and leading (byte-identical across the 3 agents per dispatch), enumerated CONTEXT inclusion list (no cap), role briefs → references/briefs.md with role text verbatim except the relocated "You are the X… reviewing the artifact above" framing; Caller mode + Out of scope → references/caller-mode.md verbatim. Audit: 14 lines changed — 13 template-layout, 1 sanctioned input-scope narrowing (CONTEXT limited to session-cited knowledge entries, per approved Approach item 4). 2 anchors retargeted.
- Final sizes: all 19 SKILL.md ≤9216B (max: propose-ship 8981). Nine restructured cores total 53.3KB vs 137.7KB before (−61%).
- Pre-existing breakage (NOT this unit, identical on main): tests/test_browser.py, test_storage.py, test_pull.py import deleted `lib/` (old financials). Suite otherwise 238 passed.
- [1/3 accept → replan] completion verification: Skeptic+Arbiter revise — tests/test_skill_budget.py absent from evals.yml's enumerated pytest list, so criterion 1's "enforced in CI" is false as committed; also 26→25 retarget count error. Treated as success-criteria divergence per orchestrator rule; Phase 2.5 triggered.
- [vote 1: 1 accept / 1 revise, Arbiter skipped — outcome mathematically fixed at 3/3 quorum] new-plan acceptance (replan): draft failed on undispositioned advisories + overstated criteria
- [3/3 accept, revision round] new-plan acceptance (replan): revised entry accepted; Arbiter sanctioned write-time precision refinements (propose-consistent README example, fix-(b) finding recorded, inference parenthetical, financials failure modes)
