# Findings: skill-best-practices-audit

**Audit date**: 2026-07-21 (all sources fetched live this date)

## Rubric sources

- S1 Skill authoring best practices — https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- S2 Equipping agents for the real world with Agent Skills — https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- S3 Prompting Claude Fable 5 — https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5
- S4 Prompting best practices — https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- S5 Prompting Claude Sonnet 5 — https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5

Fable-specific guidance **does exist publicly** (S3), resolving the proposal's open
question — no fallback needed. Rubric dimensions R1–R10 are defined in `scratchpad.md`
(§ Rubric); method: 8 fresh-context subagent reviewers over themed batches of 2–3
skills, deterministic census by the main model, synthesis and arbitration by the main
model.

## Coverage matrix

All 21 skills were assessed on all 10 dimensions by a fresh-context reviewer
(`ok`/`finding` verdict per cell) plus a cold-read trigger probe per skill. No skill
and no dimension was skipped. Verdict summary (dimensions with findings listed;
all others `ok`):

| Skill | Findings on |
|---|---|
| using-minerva | R7 R9 |
| explore | R1 R8 |
| propose | R1 R5 R9 |
| grill-plan | — (clean) |
| work | R1 R5 R7 R9 |
| replan | R1 R7 R9 |
| review | R1 R5 R7 R9 R10 |
| promote | R1 R7 R10 |
| synthesize | R1 R3 R10 |
| ship | R1 R5 R7 R10 |
| cleanup | R1 |
| init | R1 R3 R5 R7 |
| lint | R1 R7 |
| lint-fix | R1 |
| migrate | R1 R7 |
| debug | R1 R4 R5 R7 |
| round-table | R1 R3 R7 |
| propose-ship | R1 R9 R10 |
| propose-ship-auto | R1 R5 R7 R9 R10 |
| propose-ship-quick | R1 R3 R5 R7 R8 R9 R10 |
| propose-ship-balanced | R1 R3 R5 R7 R8 R9 |

## Anchor diagnoses

### Diagnosis 1 — ambient triggering fails

**Confidence: high** (two independent mechanical causes + converging cold-read probes)

Two distinct causes, one per lever class:

1. **[mechanism] Description drop in the rendered listing.** In live sessions,
   `minerva:lint` and `minerva:lint-fix` render as bare names with no description
   (verified independently by the main session and two fresh-context reviewers; one
   reviewer session also observed `minerva:replan` bare). On-disk frontmatter is valid
   in all copies (source, installed, cache), and formatting is byte-identical in kind
   to skills that render fine, so the drop is in the listing/registration pipeline,
   not the skill text. A bare name cannot win any trigger decision — for the affected
   skills, ambient triggering is *structurally impossible*, and no description rewrite
   can fix it. (S1: name+description "are the only elements pre-loaded into the system
   prompt".)
2. **[prose] Invocation-first description ordering.** 17 of 21 descriptions lead with
   "Use when the user invokes `minerva:X`", demoting ambient scenarios to trailing
   clauses. S1 requires descriptions to state what + when with specific triggers;
   S4/S5 establish that current models read literally and weight what leads. The
   census cross-check is striking: the only four skills that do NOT lead with
   invocation (debug, explore, grill-plan, using-minerva) are precisely the skills
   observed to ambient-trigger best. Compounding: three descriptions exceed S1's
   1,024-char limit (balanced ~1.3k, debug ~1.1k, quick ~1.05k) with their
   disambiguation/trigger payload in the truncation-risk tail; and several skills
   omit their primary ambient scenario entirely (synthesize: "entries promoted since
   last synthesis"; review: "implementation just finished"; init: any phrasing that
   doesn't name minerva; explore: loses "brainstorm" to superpowers:brainstorming's
   unconditional MUST-claim).

### Diagnosis 2 — mid-lifecycle handoffs fail

**Confidence: medium-high** (consistent textual pattern across all failing handoffs;
behavioral link is analytic, not telemetry-proven)

The handoffs that fail are exactly those written as bare prose — "invoke
`minerva:grill-plan` against that draft", "run the `minerva:replan` protocol",
"re-enter `minerva:review`", "invoke `minerva:cleanup <NNN-slug> --yes`" — while the
handoffs that work reliably name the mechanism: explore→propose ("invoke the skill
**via the `Skill` tool**, passing the converged direction as the inline argument"),
the orchestrators' ship/synthesize delegations (same form). S4's tool-usage guidance
(models act when told the mechanism explicitly) plus S5's literalism make the
difference load-bearing: "run the protocol" licenses inlining-from-memory, which is
precisely the observed failure ([[007]]'s tools-not-prose rule restated at the
handoff level). Classification: prose (each handoff site) — with one mechanism-flavored
residual: nothing enforces the pattern, so new skills will regress (seed: contract
test for handoff phrasing).

### Cross-model robustness (secondary)

- **Alignments worth keeping** (validated by reviewers): round-table's fresh-context
  Proponent/Skeptic/Arbiter matches S3's "fresh-context verifier subagents outperform
  self-critique"; debug's evidence-ledger confidence score is safe against fable's
  reasoning-extraction refusals; the orchestrators' async wake-up + capped-retry
  cleanup gate matches S3's async-check-in recommendation.
- **Fable/over-compliance hazards**: quick's and balanced's escalation predicates
  carry catch-all amplifiers ("any real doubt", "cannot rule it out") that
  over-comply on current models — a healthy run can exhaust the escalation cap
  (R8, applied). explore triple-states a HARD-RULE guarding a non-destructive action
  (R8, applied). Four delegated skills hard-gate on "the user" with no
  delegated-approver clause, stalling literal models inside autonomous orchestrators
  (R10, applied).

## Finding clusters and dispositions

77 raw findings deduped into 12 clusters. Disposition: **applied** (in this unit),
**declined** (rationale inline), **rejected** (finding wrong), or **seeded**
(mechanism → followups.md).

| # | Cluster | Members | Sev | Class | Disposition |
|---|---|---|---|---|---|
| C1 | Description: invocation-first ordering | 17 skills (all but debug, explore, grill-plan, using-minerva) | med | prose | **applied** — reordered to lead with what+ambient; invocation clause last |
| C2 | Description: >1024ch limit | propose-ship-balanced, debug, propose-ship-quick | high | prose | **applied** — trimmed under 1024 (cut body-material, kept triggers) |
| C3 | Description: missing ambient scenarios | explore (brainstorm precedence), init (minerva-free terms), synthesize (post-promote staleness), review (post-implementation), promote (post-review), propose-ship (positive differentiator), balanced (sanity-check phrases) | med | prose | **applied** — folded into the C1 rewrites |
| C4 | Handoffs not naming Skill tool | propose→grill-plan, work→replan (×2), replan→grill-plan, review→replan/re-entry, using-minerva router note, quick+balanced→cleanup, lint→lint-fix (with C7) | med | prose | **applied** — every handoff names the Skill tool + argument; auto's re-invocation ban got a post-compaction escape |
| C5 | Hard user-gates vs autonomous callers | review (triage gate), promote (partition gate), synthesize (write gate), ship (gates #1/#2) | med | prose | **applied** — one delegated-approver clause each |
| C6 | Over-aggressive tone / fail-closed amplifiers | explore HARD-RULE ×3, quick+balanced "any real doubt"/"cannot rule it out" | med | prose | **applied** — softened to single positive statement; escalation anchored to named clauses + negative calibration line |
| C7 | Stale roadmap content | lint "Phase B.3" ×4 (fixer shipped as lint-fix), migrate "future unit" ×4, quick's 3-rung ladder + escape missing balanced ×3 files, plus the matching stale rows in `plugins/minerva/README.md` (lint, migrate — caught by the completion-verification Skeptic after the first catalog check misread truncated grep output) | med | prose | **applied** |
| C8 | Terminology/anchor defects | "Three-way" vs four buckets (quick, balanced, auto), ship "Worktree entry" anchor, auto's broken cross-file anchors ×6, garbled CI sentence (quick, balanced), propose-ship closed signals list, "independent check" mislabel (quick) | med | prose | **applied** |
| C9 | Portability: repo-local knowledge refs in distributed skills | ship protocol.md, init steps.md ×2, balanced verify-protocol.md ([[014]], unit 039) | med | prose | **applied** — rationale inlined, repo-local paths dropped |
| C10 | Provenance headers / extraction lore | ~10 reference files "(verbatim from SKILL.md, work unit 035)", round-table extraction sentence ×4, using-minerva guide dangling heuristic ref, init design parentheticals, synthesize asymmetry section, round-table model-pin intent | low | prose | **applied** — retitled/compressed; intent stated at the model pin |
| C11 | TOCs for >100-line reference files | 8 files (propose, review, debug, ship, init, auto, balanced, work) | low | prose | **declined** — every one is under a read-in-full contract or mapped from its SKILL.md step list; batch TOC pass adds diff noise disproportionate to value. Recorded as an optional followup. |
| C12 | Governance/protocol dedup restructure | quick, balanced (triple-stated triggers/counter/escape) | low | prose | **declined** — structural refactor touching byte budgets and contract anchors; safer as its own unit (seeded). |
| — | ScheduleWakeup "not in harness" | propose-ship, propose-ship-auto | — | — | **rejected** — factually wrong: the tool exists and is exercised in this harness. The salvageable kernel (other harnesses may lack it) is noted in followups. |
| M1 | Rendered-listing description drop | lint, lint-fix (+replan in one session) | high | mechanism | **seeded** — loader diagnosis + rendered-listing contract test |
| M2 | Six-block target-resolution duplication | work, replan, review, promote, ship, cleanup | med | mechanism | **seeded** — shared source or byte-identity test |
| M3 | Cross-skill step-number coupling | quick, balanced phases.md → propose/promote/ship step numbers | med | mechanism | **seeded** — anchor-existence contract test |
| M4 | Description ≤1024 contract test | all skills | med | mechanism | **seeded** — complements C2 |

## Residual risk

Prose fixes to descriptions are behavior changes with no trusted eval
(knowledge 013); the lifecycle review gate and post-ship observation are the
containment. The M1 description-drop means C1/C3 rewrites for lint/lint-fix cannot
take effect until the loader defect is fixed — the prose is still corrected now so
the fix lands the moment the pipeline renders it.
