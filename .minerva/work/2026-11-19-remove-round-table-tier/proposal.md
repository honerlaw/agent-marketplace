# Proposal: remove-round-table-tier

**Date**: 2026-11-19
**Status**: Draft

## Goal
`minerva:propose-ship-auto` adjudicates every decision with at most a reviewer tier — **solo** or
**reviewer**, never a 3-agent panel. `minerva:round-table` is deleted, and minerva goes to
**4.0.0**. There is still exactly one autonomous orchestrator; this is not a sibling variant.

## Why
- **External evidence** (full report: `research.md` in this unit, a 2023–2026 deep-research pass):
  - At matched compute, multi-agent debate ties or loses to independent sampling plus a majority
    vote, at 2–3.4× the tokens (Huang et al., ICLR 2024; Choi, Zhu & Li, "Debate or Vote",
    NeurIPS 2025, which also proves symmetric debate cannot raise expected correctness; 2026
    preprints 2605.00914 and 2609.35875).
  - Assigned personas add no accuracy (Zheng et al., EMNLP 2024 Findings). Role-locked
    Proponent/Skeptic votes are not independent samples, so a 2/3 quorum reduces to the Arbiter
    and a 3/3 quorum hands the Skeptic a veto.
  - The Arbiter inherits documented LLM-judge biases: persuasion (2508.07805), position bias in
    close cases (2406.07791), self-preference (2404.13076), bandwagon/authority (2410.02736).
    LLM patch verifiers key on the agent's own confident narrative (R2E-Gym, 2504.07164).
  - Critics prompted to find problems have a high nitpick / false-defect base rate (CriticGPT,
    2407.00215; Jin & Chen, 2508.12358 / 2603.00539), which a unanimous quorum turns into
    escalations.
  - What the evidence does support: execution-grounded verification (Agentless; R2E-Gym; MAST,
    2503.13657) and a single fresh-context reviewer whose evidence-backed objections are triaged.
- **This repo's own logs agree.** Since round-table gained `accept with fixes`
  (`2026-09-23-pattern-a-unanimous-quorum-deadlocks-on-write-up-fixes`), every logged panel but one
  returned 3/3 accept — the panel's output was the fixes, which one Skeptic also produces. Only 3
  decisions ever moved reviewer → panel (all failed fold-audits on whole-proposal); the
  anti-circularity escape never fired.
- **Prior finding.** `2026-09-05-decision-balanced-rechecks-its-folds` measured that a panel's only
  marginal value over one Skeptic was re-verifying the revised artifact — which the fold-audit now
  does. Panels cost minutes per gate (completion ~10 min, whole-proposal ~8 min median,
  `2026-09-26-decision-price-orchestrator-phases-and-gates-in-run-trace`) for no measured gain.
- **Why not a sibling orchestrator.** `2026-09-23-decision-one-orchestrator-picks-each-decisions-tier`
  deleted quick/balanced because an up-front orchestrator choice is a guess made before the risky
  decision exists. Removing the panel tier in place keeps per-decision routing and adds no switch.

## Approach
1. **Two-tier ladder** (`references/decision-protocol.md`). Tier selection becomes:
   hardcoded trigger → user; **scrutiny predicate** (the four former panel clauses: genuine
   ambiguity, high blast radius / irreversible, existing interface change, knowledge tension) →
   reviewer, with the clause(s) that fired named in the reviewer's CONTEXT; solo predicate → solo;
   otherwise → reviewer. Triage, promote partition and TODO disposition stay solo unless the
   scrutiny predicate holds, then reviewer. Removed: the interface-clause doubt exception, "a
   clause fires once per approved change", and the Skeptic's `## Panel warranted?` section.
2. **Reviewer ladder at every Skeptic gate**: Skeptic → (after a fold) fold-audit → **Adjudicator**
   → user.
   - The Adjudicator is reached by a failed fold-audit (`[rechecked — escalated]`) or by the
     anti-circularity escape (`[reviewed — escalated]`).
   - It is deliberately narrow, so it is not the re-critique `2026-09-05` rejected: it rules only
     on the disputed items — `resolved | unresolved | critique mistaken — <evidence>` — raises
     **no new concerns**, and returns `proceed` or `escalate`.
   - Arbitration is strict: any load-bearing item `unresolved` → user. On the anti-circularity
     path (nothing folded yet), "critique mistaken" → proceed with the original decision; the
     Skeptic ruled right → user, because adopting a materially different decision with the budget
     spent would ship an unaudited rewrite.
   - Budget: at most **3 dispatches per Skeptic gate**. An Adjudicator escalation increments the
     global escalation counter. The same ladder applies on every Skeptic row, so the capped-row
     special case ("upward move goes to the user instead of a panel") disappears.
   - Reviewer-tier model policy is unchanged (`model: sonnet` in the Claude adapter).
3. **Sharper Skeptic brief.** Every concern cites evidence from the ARTIFACT or repo and is marked
   blocking / non-blocking; "no concerns" is a valid answer. When CONTEXT names a scrutiny clause
   that fired, the Skeptic tests exactly that clause. Three verdicts (accept / revise / reject) stay.
4. **Former panel floors become reviewer floors** (`references/phases.md`). Divergence
   confirmation, new-plan acceptance and replan-vs-FIX are Skeptic gates over the main model's
   call (never solo); the outcome is the call as it stands after its gate, replacing the
   2/3-vs-≤1/3 vote semantics.
5. **Completion is always the Verifier.** The completion-panel branch is removed. The Verifier
   brief gains one check: a diff that changes an existing interface or contract beyond what the
   proposal approved is an unmet criterion → Phase 2.5 replan. Code review keeps running alongside
   completion.
6. **Governance** (`references/governance.md`): panel budgets removed; the propose-wave restart's
   worst case for whole-proposal becomes 4 dispatches (1 stale + 3); the counter increments on
   Adjudicator escalations and hardcoded triggers; the propose-phase abort stays; the final report
   counts solo/reviewer decisions; round-table leaves the never-modify list; the "configurable
   quorum" out-of-scope bullet goes. The *Re-measure* section is rewritten for the new ladder
   (Adjudicator trigger rate, user-escalation rate vs. the panel era).
7. **Logging and telemetry.**
   - New tags `[adjudicated — proceed]` / `[adjudicated — escalated]`, written immediately after
     the `[rechecked — escalated]` or `[reviewed — escalated]` line that triggered them, naming the
     same gate.
   - `plugins/minerva/scripts/decision_telemetry.py` classifies both tags, keeps classifying legacy
     `[panel — …]` / bare vote lines and legacy headers (historical scratchpads), and reports an
     orphan `adjudicated` line as a problem.
   - `tests/test_decision_telemetry.py` drops the `round-table/SKILL.md` → `Panel` mapping and
     covers legacy panel-line classification with an inline fixture copied from round-table's
     current fenced example; the auto-example test requires both `adjudicated` tags and no panel
     tags.
   - `scripts/run_trace.py` gains an `adjudicator` role (reviewer tier) and keeps detecting legacy
     Proponent/Arbiter panel batches; a test covers the new role.
8. **Deletions and surface sync.**
   - Delete `plugins/minerva/skills/round-table/`, `evals/round-table/`, and the `panel` scenario in
     `scripts/run_compatibility_evals.py`.
   - Update: `skills/using-minerva/references/{claude,codex,runtime}.md` (panel operation / panel
     dispatch lines), `plugins/minerva/COMPATIBILITY.md`, `skills/using-minerva/SKILL.md`,
     `README.md`, `plugins/minerva/README.md`, `pages/index.md` (catalog entry plus the "Fail
     closed" and "Adversarial by default" principles), `skills/propose-ship/SKILL.md`,
     `skills/propose/references/cross-session.md`, `evals/propose-ship-auto/contract.json`,
     `skills/propose-ship-auto/SKILL.md` (description and summary).
   - Update assertions in `tests/test_skill_contracts.py` and `tests/test_skill_dispatch.py`.
   - Bump `plugins/minerva/.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` to 4.0.0.
   - `docs/superpowers/specs/2026-05-21-propose-ship-auto-design.md` is a historical spec and is
     left as is.
9. **Record.** `research.md` (this unit) holds the full research report. At promote, write a
   knowledge entry for this decision that supersedes
   `2026-06-10-decision-panel-mechanics-extracted-to-round-table` and builds on
   `2026-09-23-decision-one-orchestrator-picks-each-decisions-tier` and
   `2026-09-05-decision-balanced-rechecks-its-folds`; review
   `2026-09-23-pattern-a-unanimous-quorum-deadlocks-on-write-up-fixes` and
   `2026-09-26-decision-parallel-gate-waves-and-existing-interface-clause` for supersession.

## Success criteria
- `plugins/minerva/skills/round-table/` and `evals/round-table/` do not exist.
- `grep -rnE 'minerva:round-table|Proponent|Arbiter|quorum'` over `plugins/minerva/skills`,
  `README.md`, `plugins/minerva/README.md` and `pages/index.md` returns no matches.
- `grep -ci panel` returns 0 for `plugins/minerva/skills/propose-ship-auto/SKILL.md` and
  `plugins/minerva/skills/propose-ship-auto/references/phases.md`.
- `decision-protocol.md` defines exactly two tiers (solo, reviewer); the Skeptic → fold-audit →
  Adjudicator → user ladder; an Adjudicator brief with the rulings `resolved | unresolved |
  critique mistaken` and no new concerns; a 3-dispatch budget per Skeptic gate; and the rule that
  on the anti-circularity path a Skeptic ruled right goes to the user.
- The decision taxonomy puts divergence, new-plan acceptance and replan-vs-FIX on a reviewer floor
  and has no Ceiling or Panel-quorum column.
- `decision_telemetry.py` classifies `[adjudicated — proceed]`, `[adjudicated — escalated]` and the
  legacy panel fixture lines; a test asserts each.
- `run_trace.py` classifies an Adjudicator dispatch as role `adjudicator`, tier reviewer; a test
  asserts it.
- `python -m pytest tests/ -q` passes.
- Both minerva plugin manifests read `"version": "4.0.0"`.
- The minerva knowledge lint (`minerva:lint` detector) reports no mechanical defects.
- `scripts/run_compatibility_evals.py` defines no `panel` scenario.

## Open Questions
- None.
