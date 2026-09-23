# Scratchpad: adaptive-propose-ship-auto

## Panel decisions 2026-09-23
- [escalated to user] scope check: panel 1/3 then 0/2 (Arbiter not dispatched — outcome fixed) — every vote kept one unit; revise votes were rationale/wording (decompose-cost vs phase-test framing, a misattributed test citation, a mislabelled line count). User chose one unit, one PR.
- [escalated to user] approach selection: A accepted by Proponent both rounds; Skeptic revise both rounds on clarifications (row ceiling vs step 2, default-solo evidence) — "not a rethink of approach A". Propose-phase abort tripped (2 of 3); user overrode it and chose A. User also added the round-table `accept with fixes` verdict to scope.
- [escalated to user] whole-proposal acceptance: Proponent accept both rounds; Skeptic revise both rounds — r1 substantive (never-elide floors, fail-closed reclassification, triage rows vs step 3, handoff artifact), all folded; r2 two carve-outs (Verifier asymmetry, capped-row upward move), folded. Counter reached 3 → run halted before worktree creation.
- [user-directed] continue after halt: user accepted the folded proposal as final and directed implementation; remaining gates run as main-model checks plus independent review at completion and code review.
- [reviewed — clean] completion verification: Verifier reproduced all 7 criteria incl. pytest 1015 passed; one historical phrasing nit in phasing.md, no action (tier: reviewer floor)

## Work notes
- Tier selection landed in a new `propose-ship-auto/references/decision-protocol.md`; `panel-protocol.md` deleted. Reviewer mechanism, Skeptic / fold-audit / Verifier briefs moved in from balanced's `verify-protocol.md`.
- Taxonomy table carries default / floor / ceiling / brief / quorum per row — the Skeptic's r2 point that cross-row interactions slipped through prose.
- Round-table: `accept with fixes` verdict in SKILL.md vote semantics + all three briefs (new `## Fixes` section); `evals/round-table/contract.json` anchor updated to the 4-verdict line.
- Runtime: `LEGACY_CALLERS` keeps quick/balanced checkpoints valid (caller can't change on resume) and renders their resume prompts through `propose-ship-auto`.
- Telemetry: new dated `## Decisions YYYY-MM-DD` header → orchestrator `Auto`; undated `## Decisions` is ignored because older scratchpads/proposals use it for prose. `tier_of()` + a `tiers:` render line.
- Version bumped 1.1.0 → 2.0.0 (two public skills removed). COMPATIBILITY.md eval commands updated (`balanced` → `auto`, `quick` → `auto-small`).
- Compatibility evals: `auto-small` replaces `quick`; `balanced` dropped; both auto scenarios require ≥1 independent dispatch (the completion Verifier floor).
- `phasing.md` line "made phasing safe to add to … four orchestrators at once" left as-is: historical fact about that unit.
