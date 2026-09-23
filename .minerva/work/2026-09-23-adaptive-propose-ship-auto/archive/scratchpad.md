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

## Review triage 2026-09-23
- [FIXED] #1 med evals/propose-ship-auto/contract.json lacked anchors for the migrated concepts — added Tier-selection order, Verifier asymmetry, Fold-audit re-check, No whole-run sizing, Verifier, fold-audit
- [SUGGESTED] #2 low both auto compatibility scenarios use the trivial calculator fixture with a ≥1 dispatch floor, so no eval exercises a reviewer-default or panel-tier decision — real, but closing it needs a new non-trivial fixture (too large to absorb) and is not critical/high → standing-fact knowledge entry
- [FIXED] #3 high round-table's bare `[3/3 accept]` classified `unknown` under `## Decisions` (would red test_live_corpus_properties) — telemetry now reads bare vote lines; protocol asks round-table to prefix `panel — `
- [FIXED] #4 med anti-circularity escape had no log tag — added `[reviewed — escalated]` (vocab, example, tier)
- [FIXED] #5 high legacy-caller resume would halt: prompt says --auto=propose-ship-auto but saved caller is legacy → "changed caller" — `canonical_caller()` makes them equal in the write check; ship/runtime prose says so; new progress with a legacy caller is refused; round-trip test added
- [FIXED] #6 med completion panel "2/3 proceeds" contradicted its 3/3 quorum — made the pre-existing exception explicit in phases.md and the taxonomy row
- [FIXED] #7 low `tiers:` counted lines, not decisions — relabelled `tier lines:` with a comment
- [FIXED] #8 low round-table prose still named `[skipped — small]` and "every strategic/tactical decision"
- [FIXED] #9 med host adapters still said "balanced reviewers" / "Balanced fold-audit" — now reviewer-tier (Skeptic, fold-audit, Verifier) on `model: sonnet`
- [solo] review triage: 8 FIX / 1 SUGGEST / 0 IGNORE (tier: default-solo row — every finding had a writable failure scenario; only #2 fails the absorb condition, and it is not urgent)
