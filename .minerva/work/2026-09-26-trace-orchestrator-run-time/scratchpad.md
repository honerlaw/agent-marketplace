# Scratchpad: trace-orchestrator-run-time

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-09-26
- [reviewed — clean] scope check: one unit, one PR, no phases (tier: reviewer — judgment call, solo's mechanical-evidence clause fails; Skeptic accepted, noted but dismissed: test size likely ~1:1 with impl so total diff ~900–1300 lines, still within repo's one-PR norm (#131 shipped 2,213 lines); phasing the phase-inference heuristic out was weighed — not dominant, the proposal already has a fallback)
- [reviewed — folded] approach: option A (new root scripts/run_trace.py dev tool) over B (extend run_analyzer) and C (ship in plugin, host-coupled to Claude transcripts vs Codex parity); folded Skeptic item 2 (one session file holds multiple orchestrator runs — added run segmentation) plus low items 3 (partition vs overlap note), 4 (plugins/utils surface named), 5 (broaden capture-session description), 1 (dedupe re-implementation rationale) (tier: reviewer)
- [rechecked — clean] approach: fold-audit confirmed items 1–5 addressed; one low new concern (standalone non-orchestrator skill calls between runs fall into the prior run's tail) — not load-bearing, handled in implementation
- [reviewed — folded] whole-proposal: folded Skeptic items 1 (tier by (gate, round) grouping — real panels omit the word "panel") and 2 (deferral bar: absorb both run_analyzer defects in-unit) plus lows 3 (command-head definition), 4 (replan events not ordering warnings) (tier: reviewer)
- [rechecked — escalated] whole-proposal: fold-audit raised a load-bearing new concern — absorbed fix 9(b) double-counts against run_benchmark's manual --subagent flow → panel
- [panel — 0/3 accept] whole-proposal: all three revise — 9(b) unconditional sidecar discovery double-counts via build_record's subagent_paths AND flips cost_crosscheck_ok on cmd_run (Claude's total excludes subagent sessions); steps 1–8 sound (tier: panel — fold-audit escalation)
- [panel — 3/3 accept, 2 with fixes] whole-proposal: revised 9(b) to opt-in include_subagent_files=False (CLI on, --main-only), real-layout tests, per-model cache-read overrides (tier: panel — revision round)
    - fix (skeptic/arbiter): step 8 states the capture-session step invokes scripts/run_trace.py <transcript.jsonl>
    - fix (skeptic/arbiter): 9(b) states the main-file/sidecar non-overlap assumption; shared message-id dedupe guards hybrid transcripts
- [panel — 3/3 accept, 3 with fixes] divergence: turn_duration.durationMs is not per-turn wall time (overshoots up to 12.4x, excludes AskUserQuestion waits) — criterion 2 unsatisfiable; replan (tier: panel floor)
    - fix (all): recompute bucket counts at write time; note code moved ahead of the vote; soften the durationMs mechanism to an inference; dispose of the "shorter" category; cite the tolerant-reader pattern; report corrected 51b73da3 active (3,941 s)
- [panel — 3/3 accept, 2 with fixes] new-plan acceptance: active = sum of turn spans (starting event → marker), durationMs a cross-check only; criterion 2 replaced, criterion 3 gains harness (tier: panel floor)
    - fix (skeptic/arbiter): amend criterion 3 to include harness
    - fix (skeptic/arbiter): define idle-other in the New Plan
    - fix (skeptic/arbiter): criterion 2 fixture covers the undershoot case too; test added (test_duration_ms_undershoot_keeps_the_question_wait_as_user_time)
    - fix (skeptic/arbiter): reconcile 32/165 vs 13/150 (naive first-raw-event start vs starting event)
- [solo] review triage: 12 FIX / 0 SUGGEST / 0 IGNORE (tier: default-solo row — every finding had a writable failure scenario and was absorbable; none had two defensible dispositions, so the ambiguity clause did not fire; #9 naive-timestamp is defensive-only on real data but a one-line fix, so FIX dominates IGNORE)
- [panel — 3/3 accept, 2 with fixes] completion verification: all 10 criteria independently reproduced (1065 passed at 8a009db; 0 overlap/active>wall over 19 sessions; $21.69/$16.98/151 to the cent) (tier: panel — the diff changes run_analyzer's CLI default output, an interface change)
    - fix (proponent/arbiter): test pinning the round term of the panel-batch match — added (test_panel_batch_match_requires_the_same_round)
    - fix (arbiter, optional): disambiguate tier "review" vs "reviewer" — renamed to "code-review"
- [solo] review triage (round 2, fix-delta re-review): 7 FIX / 0 SUGGEST / 0 IGNORE (tier: default-solo row — each had a verified failure scenario and was absorbable; no item had two defensible dispositions)
- [solo] review triage (round 3, promote-time fix delta): 4 FIX / 0 SUGGEST / 0 IGNORE (tier: default-solo row — each verified and absorbable; the reviewer's own recommended fixes)
- note: approach fold-audit and whole-proposal Skeptic were dispatched in parallel (scope + approach Skeptics likewise) to cut wall time; no gate's artifact depended on an unresolved sibling

## Work notes
- Panel-tier rule refined in implementation: grouping is by (gate, round, launch batch), not only by (gate, round). A lone reviewer Skeptic and a later escalation panel at the same gate share (gate, round), for example this unit's own "Skeptic: whole-proposal soundness" and "Panel Skeptic: whole-proposal". A Skeptic is a panel member only when a same-gate Proponent went out in the same assistant message or within 10 s. Pinned by test_lone_skeptic_is_reviewer_even_when_a_later_panel_shares_its_gate. This refines the step-5 mechanism and does not change the decision.
- Phase verify/review signals come from Agent calls in the main thread, not from sidecar files, so a run whose sidecar is missing still gets its phases.
- A turn starts at the event that began it (first user event with an `origin`, where subagent hand-backs are `isMeta` + origin peer), not at its first raw line: queue-operations and pr-link lines written while idle belonged to the idle gap. Before this fix, 6.7 min of the user composing a prompt showed up as `harness`.
- In-turn gaps with no tool open are `model`, except those ending at a `system` event (hooks), which are `harness`. Bookkeeping lines land mid-generation.
- Deletion pass: 30 mutations over every attribution rule plus the analyzer fixes (script: session scratchpad mutate.py). The first run left 2 survivors: run end-bounding and the verifier default gate. Tests were tightened and all 30 are now killed.
- Gotcha: the first mutation pass was partly invalid. A same-size mutation (`rnd = 2` → `rnd = 1`, `min` → `max`) restored within the same second leaves a stale `.pyc`, because Python validates bytecode by mtime and size. The mutated code kept running after restore, and a full-suite run failed on correct source. Rerun with `python -B`, PYTHONDONTWRITEBYTECODE=1 and caches cleared: 30/30 killed. Full suite: 1064 passed.
- Real data (19 sessions, 6 propose-ship-auto runs): the propose phase dominates with a median of 19.4 min per run, and whole-proposal panels are the costliest gate by subagent time (38.8 min over 5 runs).

## Review triage 2026-09-26
Local-diff mode (independent fresh-context reviewer; no PR yet) plus the inline minerva audit. The code review ran in parallel with the completion panel to save wall time.
- A1 [medium] FIX — knowledge compliance (2026-08-28-constraint-worktree-reaching-paths-anchor-to-the-primary-checkout): from inside a worktree, default_project_dir encoded the worktree path, so `--all` silently read a nonexistent directory and reported 0 runs. Now anchored via `git rev-parse --git-common-dir`, and a missing directory exits 2.
- 1 [high] FIX — the trailing unmarked turn started at its first raw event, so 42 min of idle in bc949b50 counted as `model`. It now uses _starter_index; that run's active time is 18.2 min (was 1.0 h).
- 2 [medium] FIX — "recheck"/"re-check" substrings in slugs were classified as fold-audit. Only the explicit "fold-audit"/"fold audit" words count now.
- 3 [medium] FIX — promote was detected only from Write/Edit. Bash writes (redirect/tee/cp/mv into .minerva/knowledge/, or `cd` into it and then a redirect) and `Skill minerva:promote` now count too. Promote is now detected in 12 of 16 real runs (was 3).
- 4 [medium] FIX — a mid-work knowledge capture jumped the phase to promote and discarded later verify/review signals. A knowledge write before the run's last verify/review signal is now reported as a capture event instead.
- 5 [medium] FIX — aggregate phase totals included user-idle and post-run chatter (for example "cleanup 3.7h"). They are now active time only, with waits reported separately (waits_total_s).
- 6 [medium] FIX — a missing meta.json left the subagent unlinked. It is now linked through the `agentId:` in the Agent tool_result, which matches the sidecar file name.
- 7 [low] FIX — non-object meta JSON crashed; it is now read as {}.
- 8 [low] FIX — a single malformed transcript killed `--all`. Transcripts that can't be read are now skipped and listed under `skipped`, and null text / string durationMs no longer crash.
- 9 [low] FIX — naive timestamps are now read as UTC, not local time.
- 10 [low] FIX — CLI argument errors (missing --project-dir value, unknown session) now print a message and exit 2 instead of a traceback.
- 11 [low] FIX — added tests for every fix above, plus the round term of the panel-batch match (surviving mutation found by the completion Proponent) and the "New-plan panel" gate vocabulary. Also renamed tier "review" to "code-review" for readability (completion Skeptic, low).
Deletion pass re-run over the extended rule set: 49/49 mutations killed (bytecode caching disabled). Full suite: 1084 passed.

## Review triage 2026-09-26 (round 2 — re-review of the fix delta 8a009db..8fcd6cd)
- R1 [high] FIX — `_writes_knowledge` was a substring search: about 16 of its 31 real matches were false (heredoc bodies of proposal/scratchpad, reads, `gh issue comment`). It is now structural: heredoc bodies and quoted strings are set aside, write targets are taken from `>`/`>>`/tee/cp/mv/git mv (destination only), `cd` is honoured, and index.md/overview.md are excluded. After the fix, 12 of 13 distinct real matches are true entry writes. The remaining one is this session's own Python heredoc containing a nested `EOF` terminator, a disclosed narrow limitation.
- R2 [medium] FIX — missed writes via `K=.minerva/knowledge; cat > $K/x.md` and Python `Path(...).write_text`. `$VAR` is now expanded from same-command assignments, and Python heredoc bodies are checked for write_text/open(..., "w") on an entry.
- R3 [medium] FIX — a post-ship review agent made the real promote writes look like captures. last_check now counts only verify/review signals before the first ship/cleanup.
- R4 [low] FIX — agentId linkage read the first 2000 chars and took the first match. It now reads the full text and takes the last match.
- R5 [low] FIX — default_project_dir re-anchored submodules and plain subdirectories. It now re-anchors only inside a linked worktree (git-dir != common-dir, under .../worktrees/).
- R6 [low] FIX — tier column too narrow for "code-review", now width 12.
- R7 [low] FIX — active post-run work was still charged to cleanup. A run now ends at the first human request after its cleanup boundary; a `--cleanup-only` resume does not end it.
- Test-quality gotcha: a generated parametrize edit silently failed to match (escaped `\n` in the search text), so two positive cases (the `$K` form and the Python write) were never added, and 5 mutations survived because of it. Found through the deletion pass, not by reading. Final deletion pass: 60/60 killed. Full suite: 1102 passed.

## Promote-time fix 2026-09-26 (found while drafting the partition; sent back through review)
- `git worktree add` detection was still a substring check, the same flaw R1 fixed for knowledge writes. On real data it produced 12 "work during cleanup" warnings that were really cleanup's `git worktree add -B minerva/reconcile`. The work signal now reads shell structure (`_shell_only`) and requires `-b <branch>` other than minerva/reconcile. Write/Edit of index.md/overview.md (cleanup's reconciliation) no longer counts as promote. Out-of-order warnings across the corpus dropped from 23 to 7. Deletion pass: 63/63. Suite: 1108 passed.
- Round-3 review of that fix (all 40 real `worktree add` commands checked): widened the exclusion to the whole `minerva/` branch namespace (`-b minerva/synthesize` was a real false work signal in 495d20d8); accepted git's permuted options (`add <path> -b x`, `--track -b`, `git -c k=v`); quoted strings may span lines (a multi-line commit message mentioning `git worktree add -b` was a false signal); pinned `-q -b` and a lowercase `-b minerva/…` negative. Real corpus: 15/15 signals are genuine work-unit creations. Deletion pass 66/66, suite 1115 passed. No fourth review round: these are the reviewer's own recommended fixes, each pinned by a test and a mutation and verified against every real command.
