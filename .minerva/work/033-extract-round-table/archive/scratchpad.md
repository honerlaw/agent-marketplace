# Scratchpad: extract-round-table

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Panel decisions 2026-06-10

- [user-decided pre-auto] scope check / approach selection / whole-proposal acceptance: Phase 1 ran manually via `minerva:explore` → `minerva:propose` → `minerva:grill-plan` with per-section user approval before `minerva:propose-ship-auto` was invoked mid-stream; user decisions outrank panels, so the propose-phase panels were not convened.
- [user-decided pre-auto] approach selection record: full-protocol-move chosen over shared-reference-file (B — indirection no other skill uses) and thin-wrapper (C — inverted dependency).

- [3/3 accept] completion verification: all five success criteria met; behavior preservation mechanically verified (byte-identical briefs, diff-confined changes, 175/175 CI-scoped tests)

## Panel concerns 2026-06-10

- (medium) "Same commit" for criterion 5 is forward-looking: `plugins/minerva/skills/round-table/` and `evals/round-table/` are untracked; the Phase-6 ship handoff MUST enumerate both dirs among the staged paths (ship stages specific paths, never `-A`). CI cross_surface backstops partial commits.
- (medium) Criterion-4 evidence phrasing: "full pytest suite" = CI's 8-file scope; `test_browser.py`/`test_storage.py` fail collection and `test_pull.py` has 4 failures, all pre-existing on main. CI is the operative gate.
- (low) Two unitemized but behaviorally inert deltas in the moved text: escalation step 2's "Resume the flow from the next decision point" relocated to the caller's Delegation bullet; round-table's Logging adds a multiple-in-flight-units disambiguation ("ask which one") absent from the original.

- [3/3 accept] review triage: F1 ship-staging → FIX (bind into Phase-6 handoff), F2 criterion-4 wording → SUGGEST (rephrase at promote), F3 checklist exactness → IGNORE (already itemized). Arbiter amendments to F1: (a) derive staged paths from `git status --porcelain` at ship time and assert `plugins/minerva/skills/round-table/` + `evals/round-table/` are in the staged set; (b) CI is NO backstop for an omitted skill dir — contract-test discovery iterates on-disk skill dirs, the >=13 floor still passes, and no reverse catalog→skill check exists, so the staging verification is the sole guard.

- [3/3 accept] promote partition: PROMOTE P1 (knowledge 033, mechanism-vs-policy extraction decision), MERGE M1+M2 (Approach rewrite + criterion fixes), DISCARD D1 (panel log noise) + D2 (ship-staging binding — kernel already open in [[010]]), TODO none. Arbiter-bound execution amendments: criterion-3 deltas itemized in rewrite; P1 leads with rejected alternatives, attributes approach as user-decided pre-auto, includes the caller-mode load-once sentence; Phase-6 staging binding carried by the orchestrator.

## Review finding 2026-06-10

- SUGGEST (F2): when promote rewrites proposal.md, rephrase success criterion 4 from "the full pytest suite" to the CI-scoped 8-file suite (`.github/workflows/evals.yml`); `test_browser.py`/`test_storage.py`/`test_pull.py` failures pre-exist on main outside that scope.

## Work notes 2026-06-10

- Moved sections (Dispatch / Agent briefs / Vote semantics / Revision round / Escalation) are byte-identical in round-table except: quorum parameterized ("caller-specified, default 2/3"), Skeptic-dissent log line generalized ("the caller's next phase — or the user"), escalation step 3 (counter increment) replaced with caller-owns-run-level-state rule; the counter rule itself survives in propose-ship-auto's Delegation + Failure-modes sections.
- propose-ship-auto kept: skip predicate, no-ceremony-ratification, decision taxonomy, per-decision logging (skip/user-directed/synthesis prefixes), failure modes. Two stale internal links repointed (#escalation in no-ceremony; "specified below" in skip predicate).


## Panel decisions 2026-06-10 (post-promote)

- [synthesis] refreshed overview.md (watermark 030→033; 3 entries synthesized: 031, 032, 033)
