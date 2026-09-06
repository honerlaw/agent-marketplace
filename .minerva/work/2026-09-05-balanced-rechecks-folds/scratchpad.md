# Scratchpad: balanced-rechecks-folds

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Balanced decisions 2026-09-05
- [escalated to user] pre-flight: in-flight check found this very unit (proposed minutes earlier via minerva:propose + grill-plan, Status Draft) — hardcoded collision ask; user chose "resume that work" → enter Phase 2 on the existing worktree, Phase 1 skipped (already human-gated). Escalation counter = 1.
- [decided] Phase 2 setup: proposal read, no replan.md; implementing per minerva:work --auto=propose-ship-balanced. Open Questions: none blocking.
- [reviewed — folded] completion verification: Verifier accept — all 8 criteria reproduced (880 tests, CLI 38/30/5/3 across 14 units, 0 problems, desc 1014 chars, lint 0 errors). Folded its one out-of-criteria finding: the logging example still labelled whole-proposal soundness "(solo gate)" — contradicting the taxonomy row changed in the same file; example line now uses review triage as the solo-gate illustration. Dispatch parked (Agent tool exposes no run_in_background — #113); resumed on notification. Note: under the protocol this unit ships, this fold would now get a `[rechecked — …]` line; this run still executes the pre-change protocol, so it is the last balanced fold without one.
- [decided] review triage: 14 findings (minerva audit 3, code review 11) — 13 FIX (all belong to this diff: 2 medium + 9 low code/prose, 2 doc-convention), 1 SUGGEST (SKILL.md at 9215/9216 bytes — a standing fact), 0 IGNORE; none contested, none a load-bearing divergence (solo gate). Code review ran in local-diff mode (fresh-context subagent, model unpinned) — no PR yet.

## Work notes 2026-09-05
- SKILL.md landed at 9215/9216 bytes after four trims — one byte of slack under `test_skill_md_within_budget`. The next edit to balanced's core must move prose to references/ first.
- `decision_telemetry.py .` reproduces the hand tally that motivated this unit: Balanced 37 decided / 30 folded / 5 clean; escalated 3 (2 historical + this run's pre-flight collision); 14 units (13 + this one); `folded-unchecked 30`. (Success criterion 4, verified once.)
- The script's tag classification DISAGREES with the hand count on one claim. By tag, auto's revision rounds rank approach 17/25, whole-proposal 13/27, scope 7/22, partition 3/3, completion 0/18 — whole-proposal is the SECOND-most-revised gate, not the first (the hand count grepped `revis` in free text and over-counted). The argument survives (it is the only heavy-revision gate balanced ran solo; completion 0/18 vindicates the Verifier choice) and the approach is unchanged, so this is a rationale correction, not a divergence — corrected in verify-protocol.md and proposal.md. Candidate pattern: a hand-derived number in a proposal is a claim until a reproducible reader confirms it; the first thing the reader did was correct its own motivation.
- `[decided] <sentence with no gate name>` lines (~15 across the corpus) normalise to `other:<sentence>`. Kept as-is: they are honest noise, and folding them into a gate would invent structure the author did not write.

## Review triage 2026-09-05
- [FIXED]   #1  low  verify-protocol.md:21, governance.md:29, knowledge entry — script named by repo-root path; sibling prose uses `scripts/<name>.py` (24×)
- [FIXED]   #2  low  tests — mutation pass on the two new assertions (inverted cap test; tag-vocabulary test) not yet run
- [SUGGESTED] #3  low  SKILL.md is 9215 of 9216 bytes — the next core edit must move prose to references/ first
- [FIXED]   #4  med  decision_telemetry.py `paired_with` indexes the per-section list; `records` is flat → wrong partner from the 2nd section on
- [FIXED]   #5  med  SKILL.md:36, governance.md:29 say EVERY fold is followed by a re-check; Verifier folds are excluded by verify-protocol
- [FIXED]   #6  low  verify-protocol.md step 2 + Skeptic-brief intro omit whole-proposal from the Skeptic-gate list
- [FIXED]   #7  low  `split_gate` splits on ':' inside backticks (`minerva:ship`)
- [FIXED]   #8  low  `other:` gates compare case-sensitively → fold/re-check on a bespoke gate mis-pairs
- [FIXED]   #9  low  long `other:` gate payloads blow out the report column
- [FIXED]   #10 low  `[re-checked — …]` (the prose's own spelling) classifies unknown
- [FIXED]   #11 low  bare `1/3 accept` with no revision marker classifies panel-accept
- [FIXED]   #12 low  unreadable/non-UTF-8 scratchpad aborts the whole tally
- [FIXED]   #13 low  coverage: multi-section pairing, dateless header, outcome_totals, main(); contracts test read_text lacks encoding
- [FIXED]   #14 low  fold-audit arbitration: no stated precedence between `## Verdict` and per-item dispositions

- Review fix: decision_telemetry.py — re-check partner recorded by line number (`paired_with_lineno`), not a per-section index; backtick-aware gate split; `other:` gates compared lower-cased; `re-checked` spelling accepted; bare ≤1/3 vote → panel-revised; unreadable files reported and skipped; `other:` payloads truncated for display. +9 tests.
- Review fix: verify-protocol.md — whole-proposal named in the step-2 and Skeptic-brief gate lists; stated precedence: per-item dispositions govern over the `## Verdict` line.
- Review fix: SKILL.md / governance.md — "every fold is followed by a re-check" scoped to Skeptic gates (Verifier folds re-check via the replan loop); script named `scripts/decision_telemetry.py` per sibling convention (also in the knowledge entry).
- Review fix: mutation pass — reinserting the retired cap phrase reddened exactly the inverted test; dropping one tag from `EXACT_TAGS` reddened the vocabulary and recheck-outcome tests. Both guards fail on deletion.
- Process note: the two decision lines above were first appended under `## Work notes` and the tally did not see them — the first live catch by the tool this unit ships. Lines belong under `## Balanced decisions`; moved.

## Review finding 2026-09-05
- `propose-ship-balanced/SKILL.md` sits at 9211 of 9216 budget bytes; any growth of the core must move prose to `references/` first (standing fact, not a TODO).
