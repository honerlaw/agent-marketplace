# Proposal: rename-triage-to-debug

**Date**: 2026-05-27
**Status**: Draft

## Goal

Rename `minerva:triage` to `minerva:debug` and rewrite the skill with structural guardrails that prevent the LLM from presenting guesses as findings. The current skill advises evidence gathering but nothing enforces it, leading to confident-sounding root causes that are actually pattern-matched guesses.

## Why

User tested the triage skill and found it presented confident diagnoses without actually examining logs, data, or runtime evidence. When pressed, the root cause turned out to be a guess. The problem is structural: the skill's two-phase workflow (Locate -> Root-cause) lets the agent skip evidence gathering because nothing gates hypothesis formation on having actual evidence. The name "triage" also implies prioritization across multiple issues, not single-bug investigation — "debug" is the accurate term.

## Approach

### Rename

Move `plugins/minerva/skills/triage/` to `plugins/minerva/skills/debug/`. Update frontmatter `name: debug`. Update all three catalog surfaces per knowledge entry 010-constraint-minerva-skill-catalog-sync.

### Three-phase evidence-gated workflow: Gather -> Diagnose -> Report

**Phase 1 — Gather (evidence collection only, no hypothesis output)**

1. Restate symptom in one sentence.
2. Load `.minerva/reference/` (dynamic discovery) and `.minerva/knowledge/` for past learnings.
3. Pull evidence from appropriate sources.
4. Evidence is defined as a bounded excerpt of tool invocation output, tagged with tool name + parameters. Agent narration is NOT evidence.
5. Each evidence artifact gets an ID (E1, E2, E3...) in the evidence ledger.
6. Minimum-breadth gate: must inspect artifacts from >=2 distinct artifact categories before Phase 2.

Artifact categories (closed enumeration): `source code`, `error output` (stack trace, exception, error message), `log output` (application/system logs), `test output` (test run results), `runtime state` (metrics, dashboard panels, process state), `configuration` (env vars, config files, feature flags), `version history` (git log, git diff, recent changes).

Phase-gate instruction: "Do not proceed to Phase 2 until the evidence ledger contains entries from >=2 distinct artifact categories. If it does not, continue gathering."

When evidence is genuinely unavailable (no access, tool errors, logs don't exist), the ledger records what was attempted, why it failed, and what would be needed. Confidence automatically caps at Suspected.

**Phase 2 — Diagnose (hypotheses must cite evidence IDs)**

1. Form hypotheses ONLY by citing evidence IDs from the ledger.
2. Confirm/disconfirm by gathering more evidence (added to ledger with new IDs).
3. Identify offending code: specific file + line range + what it does + what it should do.
4. Can loop back to Phase 1 for more evidence.

**Phase 3 — Report (structured output with derived confidence)**

- Symptom: one-sentence restatement
- Inspected Artifacts: what was opened/queried/run (scope — the inputs)
- Evidence Ledger: excerpts with IDs (findings — the outputs)
- Root Cause: every claim cites evidence IDs; uncited claims flagged as speculation
- Confidence (mechanically derived, non-overlapping tiers):
  - Confirmed: reproduced via repro/test AND root cause identified in code
  - Probable: multiple corroborating evidence from different artifact categories, no contradicting evidence
  - Suspected: single source or code-reading only, alternatives not ruled out
  - Unknown: couldn't narrow or contradictory evidence
- Recommended Fix: suggestions, not taken actions
- What I Did Not Check: ruled-out vs. ran-out-of-time

### Preserved sections (from existing skill)

- `.minerva/reference/` discovery mechanism
- Knowledge vs. reference explanation
- Mutation discipline (hard rule)
- Knowledge-base authority
- "When the user just wants context" section

### Catalog sync

Three surfaces updated in the same commit:
- `plugins/minerva/README.md` — row changed from triage to debug
- `plugins/minerva/skills/using-minerva/SKILL.md` — row changed
- `README.md` (repo root) — `minerva:triage` changed to `minerva:debug`

### Trigger backward compatibility

Frontmatter description includes "triage" as a trigger word so users who say "triage this" still match the skill.

## Success criteria

1. `plugins/minerva/skills/debug/SKILL.md` exists; `plugins/minerva/skills/triage/` does not.
2. Frontmatter `name: debug`, description triggers on live-incident framing, dev-bug framing, AND "triage" as backward-compat synonym.
3. Three-phase Gather -> Diagnose -> Report workflow with explicit phase gates.
4. Evidence defined as tool invocation output; evidence ledger with IDs required.
5. Artifact categories enumerated as a closed list; minimum-breadth gate (>=2 categories) before Phase 2.
6. Phase 2 hypotheses must cite evidence IDs.
7. Four-tier confidence score mechanically derived with non-overlapping criteria.
8. Report includes both Inspected Artifacts (scope) and Evidence Ledger (findings).
9. All three catalog surfaces updated: triage -> debug.
10. Mutation discipline, reference discovery, knowledge-base authority sections preserved.
11. Unavailable-evidence handling: ledger records attempts + failures, confidence caps at Suspected.

## Open Questions

None.
