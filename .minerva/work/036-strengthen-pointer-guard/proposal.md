# Proposal: strengthen-pointer-guard

**Date**: 2026-06-11
**Status**: Shipped (2026-06-11)

## Goal

Close the deterministically checkable part of the prose-alias gap in the progressive-disclosure pointer guard: strengthen `tests/test_skill_budget.py` so malformed reference pointers fail CI and every reference file must carry at least one canonical, read-directive mention. (A prose alias pointing at a *nonexistent* file remains undetectable without LLM judgment — out of scope for the CI floor.)

This is followup #1 from unit 035. Followup #2 (unit 2 of the token-reduction program, subagent phase isolation) is **not in scope**: its recorded gate — token measurements from a real `propose-ship-auto` run on the restructured skills — is unmet; no measurement artifact exists yet.

## Why

035's review logged that `REF_MENTION_RE` catches only literal `references/<name>.md` mentions, so a pointer phrased loosely (`references/briefs` without `.md`, or a prose alias like "the briefs file") dangles silently and fails exactly at the moment the detail is needed. 035 amended its success criterion 4 down to match the weak check; this unit strengthens the check back toward the original intent — every reference reached through a mandatory read instruction — without LLM judgment, keeping the guard on the deterministic CI floor.

## Approach

What shipped: two deterministic, enumerating checks added to `tests/test_skill_budget.py` (no SKILL.md edits anywhere):

1. **Malformed-pointer scan** — any unfenced `references/<token>` not matching the canonical `references/<name>.md` form fails; trailing sentence punctuation after `.md` is tolerated (`rstrip('.')` before fullmatch — cannot mask `.bak`-style defects).
2. **Read-directive check** — every `references/*.md` must have at least one unfenced SKILL.md mention line containing word-bounded "read"; secondary verb-less mentions stay legal.

Fence handling imports the single-sourced grammar (`FENCE_RE` from `scripts/knowledge_spans.py` — indented + tilde fences) rather than re-deriving it; the unit's own hand-rolled first cut missed indented fences (caught by the completion panel) and tilde fences (caught when the partition panel spotted the re-derivation), which became knowledge entry [[037-constraint-fence-scans-import-fence-re]]. Toggle semantics and both violation classes are pinned by negative tests. Helpers are module-level; the module was already in CI's enumerated pytest list.

## Success criteria

- Both new checks exist in `tests/test_skill_budget.py` and pass for all 19 live skills.
- Negative tests prove each check fires: a fixture skill with a malformed pointer fails the malformed scan; a fixture whose reference is mentioned only without a read verb fails the read-directive check.
- Full pytest suite green (same three pre-existing financials exclusions as 035 — see that unit's replan.md).
- No `plugins/minerva/skills/**` files modified.
- No CI wiring needed: the module is already in the workflow's enumerated list ([[035-constraint-ci-test-enumeration-explicit]] satisfied by construction — verified, not assumed).

## Open Questions

- The read-verb list is fixed to "read" only — the current corpus uses it universally; widen (consult/see) only if a legitimate pointer style emerges later.
