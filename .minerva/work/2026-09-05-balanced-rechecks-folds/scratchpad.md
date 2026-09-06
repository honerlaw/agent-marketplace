# Scratchpad: balanced-rechecks-folds

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Balanced decisions 2026-09-05
- [escalated to user] pre-flight: in-flight check found this very unit (proposed minutes earlier via minerva:propose + grill-plan, Status Draft) — hardcoded collision ask; user chose "resume that work" → enter Phase 2 on the existing worktree, Phase 1 skipped (already human-gated). Escalation counter = 1.
- [decided] Phase 2 setup: proposal read, no replan.md; implementing per minerva:work --auto=propose-ship-balanced. Open Questions: none blocking.

## Work notes 2026-09-05
- SKILL.md landed at 9215/9216 bytes after four trims — one byte of slack under `test_skill_md_within_budget`. The next edit to balanced's core must move prose to references/ first.
- `decision_telemetry.py .` reproduces the hand tally that motivated this unit: Balanced 37 decided / 30 folded / 5 clean; escalated 3 (2 historical + this run's pre-flight collision); 14 units (13 + this one); `folded-unchecked 30`. (Success criterion 4, verified once.)
- The script's tag classification DISAGREES with the hand count on one claim. By tag, auto's revision rounds rank approach 17/25, whole-proposal 13/27, scope 7/22, partition 3/3, completion 0/18 — whole-proposal is the SECOND-most-revised gate, not the first (the hand count grepped `revis` in free text and over-counted). The argument survives (it is the only heavy-revision gate balanced ran solo; completion 0/18 vindicates the Verifier choice) and the approach is unchanged, so this is a rationale correction, not a divergence — corrected in verify-protocol.md and proposal.md. Candidate pattern: a hand-derived number in a proposal is a claim until a reproducible reader confirms it; the first thing the reader did was correct its own motivation.
- `[decided] <sentence with no gate name>` lines (~15 across the corpus) normalise to `other:<sentence>`. Kept as-is: they are honest noise, and folding them into a gate would invent structure the author did not write.
- [reviewed — folded] completion verification: Verifier accept — all 8 criteria reproduced (880 tests, CLI 38/30/5/3 across 14 units, 0 problems, desc 1014 chars, lint 0 errors). Folded its one out-of-criteria finding: the logging example still labelled whole-proposal soundness "(solo gate)" — contradicting the taxonomy row changed in the same file; example line now uses review triage as the solo-gate illustration. Dispatch parked (Agent tool exposes no run_in_background — #113); resumed on notification. Note: under the protocol this unit ships, this fold would now get a `[rechecked — …]` line; this run still executes the pre-change protocol, so it is the last balanced fold without one.
