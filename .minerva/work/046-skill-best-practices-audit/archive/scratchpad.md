# Scratchpad: skill-best-practices-audit

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Panel decisions 2026-07-21

- [user-directed] resume under propose-ship-auto: user chose "Resume 046 under auto" at the hardcoded pre-flight collision gate; Phase 1 (propose) satisfied by the human-approved proposal from the interactive propose run — section-by-section user approval outranks the three propose-phase panels, which are not re-run.

## Rubric (distilled 2026-07-21)

Sources (fetched live 2026-07-21):
- S1 Skill authoring best practices — https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- S2 Equipping agents for the real world with Agent Skills — https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- S3 Prompting Claude Fable 5 — https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5
- S4 Prompting best practices — https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- S5 Prompting Claude Sonnet 5 — https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5

Dimensions:
- R1 Description triggering quality — third person; what + when; specific key terms; ambient/contextual trigger scenarios present and prominent (not buried behind "when the user invokes X"); ≤1024 chars [S1]
- R2 Naming — gerund/action form, not vague [S1]
- R3 Conciseness — "Claude is already very smart"; every token justified; no over-explaining [S1]
- R4 Degrees of freedom — specificity matched to task fragility; over-prescription degrades fable output [S1, S3]
- R5 Progressive disclosure — body <500 lines; references one level deep; TOC in files >100 lines [S1]
- R6 Workflow clarity — numbered steps, checklists for complex flows, feedback loops [S1]
- R7 Content hygiene — consistent terminology; single default over option lists; no time-sensitive info [S1]
- R8 Instruction-tone calibration — aggressive MUST/CRITICAL language now over-triggers on opus 4.5+/sonnet 5/fable; positive instructions over negative [S4, S5]
- R9 Invocation explicitness & scope literalism — skill-to-skill handoffs name the Skill tool and the argument; scope stated explicitly (sonnet 5 won't generalize); fully-qualified tool names [S4, S5]
- R10 Model-behavior hazards — reasoning-echo instructions (reasoning_extraction refusal risk on fable); context-budget mentions; pause/checkpoint language that fights autonomy; fresh-context verifiers > self-critique [S3]

Cross-cutting at synthesis: ambient-trigger diagnosis, handoff diagnosis, cross-model robustness.

## Deterministic census (2026-07-21, main model)

- invokes-first descriptions ("Use when the user invokes `minerva:X`…"): 17/21. Exceptions: debug, explore, grill-plan, using-minerva — which are also the skills observed to ambient-trigger best. Supports the buried-ambient-trigger hypothesis.
- Description length > 1024ch (S1 frontmatter hard limit, truncation risk): propose-ship-balanced 1271, debug 1084, propose-ship-quick 1032. Ambient trigger phrases sit in the tail of these — the part truncation would cut. Candidate contract test (mechanism seed): assert desc ≤1024ch.
- SKILL.md bodies all ≤122 lines — comfortably under the 500-line guidance (9KB budget already enforces this).
- 8 fresh-context batch reviewers dispatched over all 21 skills (batches: 1 using-minerva/explore/propose, 2 grill-plan/work/replan, 3 review/promote/synthesize, 4 ship/cleanup/init, 5 lint/lint-fix/migrate, 6 debug/round-table, 7 propose-ship/propose-ship-auto, 8 quick/balanced).

## Work log 2026-07-21

- All 8 batches returned; 77 raw findings → 12 clusters + 4 mechanism seeds in findings.md. Coverage matrix complete (21 skills × R1–R10, grill-plan fully clean).
- Headline discovery: M1 description drop — lint/lint-fix render bare in live listings (verified in 3 independent contexts); ambient triggering structurally impossible for them until the loader is fixed.
- Rejected one reviewer finding at arbitration: "ScheduleWakeup not in harness" (tool exists here and is used by the cleanup gate); portability kernel kept in followups.
- Applied: 19 description rewrites (invocation-last house style, 3 over-limit trims, missing ambient scenarios added), 53+ body edits across 30+ files (Skill-tool handoffs, delegated-approver gate clauses, HARD-RULE softening, escalation-predicate calibration, stale Phase-B.3/future-unit/3-rung content, four-way partition, broken cross-file anchors, portability refs, provenance headers).
- Byte-budget regression caught by tests (propose-ship 9295, using-minerva 9435 > 9216) and trimmed back under (9206 / 9158). Suite: 311 passed; test_browser/test_storage/test_pull collection failures are pre-existing on main (`lib` module).
- Declined: C11 TOC pass, C12 governance dedup (both in followups.md with rationale).
- [1/3 accept — revision round] completion verification, vote 1: Proponent accept (independently re-ran tests + spot-checked diff); Skeptic revise — CONFIRMED defect: plugins/minerva/README.md lint/migrate rows retained the C7 stale phrases ("Phase B.3", "future migration-APPLY unit") violating catalog-sync constraint 010; the main session's earlier catalog grep had misread 160-char-truncated output as clean. Arbiter not dispatched (Skeptic defect independently verified by main model — revision round triggered directly). Fix: both README rows synced to the new descriptions; suite re-run green (311).
- [escalated to user] completion verification, vote 2: Proponent accept (verified fix + reran suite; disclosed and self-reverted an accidental `git checkout main -- .` in the worktree — tree verified clean afterward by the main model); Skeptic revise — CONFIRMED same-class defect in a third catalog surface: using-minerva decision-matrix migrate row still said "a future APPLY unit". At 3/3 quorum the second vote cannot reach consensus (Arbiter not dispatched: with a confirmed-valid Skeptic revise, no Arbiter verdict changes the sub-quorum outcome). Defect fixed pre-escalation (row synced, suite green, 9157B ≤ budget); systematic sweep of all four catalog surfaces now clean. Global escalation counter: 1.
- [escalation resolved] completion verification: user accepted completion ("Accept, continue run"); applied as the accepted path per round-table escalation step. Run continues to Phase 3 (review).
- [2/3 accept — quorum met] review triage: FIX all six self-introduced findings (F1 governance the-the artifact, F2 briefs dangling fragment, F3 verify-protocol predicate inconsistency, F4 review inline-vocabulary drift, F5 blank lines, F6 balanced ladder ordinal). Both Proponent and Skeptic independently verified all six against the diff and accepted; Arbiter not dispatched (2 accepts already meet the 2/3 quorum — no verdict could change the outcome). Skeptic execution notes honored: F4 swept all five inline references; F6 kept fully-qualified backticked names. All fixes applied, suite green (311), descriptions within limits (review 715ch, balanced 974ch). No replan-vs-FIX trigger: no finding load-bearing.

## Review finding 2026-07-21

- (record) Fresh-context docs review of the changeset produced 6 findings, all FIX-dispositioned and applied same-day; see Panel decisions log above. No SUGGEST/IGNORE items.
- [1/2 accept — revision round] promote partition, vote 1: Skeptic caught the orphaned-rubric pointer (findings.md → soon-archived scratchpad), K3's missing 010/034 relations, the unevaluated resume-under-auto precedent, K1 evidence overcount. All fixed: rubric inlined into findings.md, precedent → followups TODO, relations added, wording corrected.
- [2/2 accept — quorum met] promote partition, vote 2: both agents verified fixes landed; Arbiter not dispatched (quorum already met). Write-time notes honored: closed-vocabulary `builds on`, K1 body carries the inert-until-loader-fixed caveat.
- [skipped — small] TODO disposition: single unambiguous disposition (evidence: all forward-looking items already live in followups.md, the unit's designed TODO home; nothing else in scratchpad is forward-looking).
- Promote applied: knowledge entries 046-049 written; reciprocal Related lines in 007/010/030/031/034/036 (fence-aware, insert-iff-absent); index watermark 045→049; knowledge-lint clean; proposal Approach rewritten, Status Shipped (2026-07-21).
