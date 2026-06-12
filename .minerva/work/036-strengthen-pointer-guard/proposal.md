# Proposal: strengthen-pointer-guard

**Date**: 2026-06-11
**Status**: Draft

## Goal

Close the prose-alias gap in the progressive-disclosure pointer guard: strengthen `tests/test_skill_budget.py` so malformed reference pointers and reference files lacking a mandatory read instruction fail CI.

This is followup #1 from unit 035. Followup #2 (unit 2 of the token-reduction program, subagent phase isolation) is **not in scope**: its recorded gate — token measurements from a real `propose-ship-auto` run on the restructured skills — is unmet; no measurement artifact exists yet.

## Why

035's review logged that `REF_MENTION_RE` catches only literal `references/<name>.md` mentions, so a pointer phrased loosely (`references/briefs` without `.md`, or a prose alias like "the briefs file") dangles silently and fails exactly at the moment the detail is needed. 035 amended its success criterion 4 down to match the weak check; this unit strengthens the check back toward the original intent — every reference reached through a mandatory read instruction — without LLM judgment, keeping the guard on the deterministic CI floor.

## Approach

Extend `tests/test_skill_budget.py` with two deterministic, enumerating checks (existing budget/orphan/dangling checks unchanged; no SKILL.md edits — scan evidence: zero malformed pointers and every reference file already has a read-verb mention line):

1. **Malformed-pointer scan** — any loose `references/<token>` occurrence in a SKILL.md that does not match the canonical `references/<name>.md` form fails (catches `references/briefs`, `references/phases.md.bak`-style typos at the pointer site).
2. **Read-directive check** — every `references/*.md` file must have **at least one** SKILL.md mention line containing the word "read" (case-insensitive, word-boundary). Per-file, not per-mention: secondary mentions without a read verb stay legal (three exist today in propose-ship-auto).

Check logic lives in module-level helpers; negative coverage via `tmp_path`-fixture tests proving each check catches its violation class. TDD: fixtures red first, then green.

## Success criteria

- Both new checks exist in `tests/test_skill_budget.py` and pass for all 19 live skills.
- Negative tests prove each check fires: a fixture skill with a malformed pointer fails the malformed scan; a fixture whose reference is mentioned only without a read verb fails the read-directive check.
- Full pytest suite green (same three pre-existing financials exclusions as 035 — see that unit's replan.md).
- No `plugins/minerva/skills/**` files modified.
- No CI wiring needed: the module is already in the workflow's enumerated list ([[035-constraint-ci-test-enumeration-explicit]] satisfied by construction — verified, not assumed).

## Open Questions

- The read-verb list is fixed to "read" only — the current corpus uses it universally; widen (consult/see) only if a legitimate pointer style emerges later.
