# Scratchpad: knowledge-lint-fix

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Panel decisions 2026-06-03

- [3/3 accept] scope check (r1): single unit — refactor → fixer → gate → register is one causal chain, wholly on the mutating + deterministic side of the already-cut seams; the un-gated fixer has no safe standalone use (unlike the 021 detector).
- [2/3 accept → revise] approach r1: X (deterministic fixer + thin gated skill) unanimously right vs Y (LLM-Edit mutation, untestable) / Z (--fix on read-only lint, violates 020); Skeptic: refinements.
- [2/3 accept] approach r2 (X′): separate scripts/knowledge_edits.py module (not bloat knowledge_spans.py); apply recomputes from live corpus (TOCTOU); tested reciprocal-label table; surgical verbatim Type relocation; per-file body_complement guard; mutating Bash-only skill, no read-only anchor. (Proponent's revise = 2 spec corrections, folded; escalation trigger ≤1/3 not met.)
- [2/3 accept → revise] whole-proposal r1: Skeptic 2 HIGH — "span-confined" incoherent for index.md fixes (need a separate skeleton-preserving model); naming collision (020 says SEPARATE skill, not extend lint).
- [3/3 accept] whole-proposal r2: two-safety-model split (entry body_complement / index skeleton-preserving); NEW minerva:lint-fix skill + evals/lint-fix/contract.json (lint untouched, honors 020); re-derive edits from parse_index/parse_entry not the message; index logic in knowledge_fix.py; docstring update. Token-boundary lint-fix vs lint proven safe.

## Carried constraints (from panels — honor during build)

- TWO safety models: ENTRY edits → body_complement byte-identity (`## Related`/banner only); INDEX edits → skeleton-preserving (H1 + 4 `## Type` headers incl. empty `## Patterns` + NNN order; no entry file touched). Each its own test.
- Editors move to scripts/knowledge_edits.py (import constants from knowledge_spans.py); test_promote_invariant.py imports them, 7 tests stay green; knowledge_spans.py docstring updated; detector FROZEN.
- Fixer re-derives edits from parse_index/parse_entry — NEVER the Finding message string.
- apply: recompute ONCE → atomic batch → single final verify-clean. No fix→recompute→fix loop.
- missing reciprocal: label from tested table (builds on→see also; supersedes↔superseded by; contradicts/see also symmetric; refuse if ∉vocab). Supersession writes BOTH banner + `superseded by` Related line. Reciprocal PAIRS atomic (validate both before any write; refuse whole pair).
- Index-editing logic in knowledge_fix.py (not knowledge_edits.py). Surgical (preserve skeleton/empty-Patterns/NNN order).
- minerva:lint-fix: mutating, gated (dry-run → confirm → apply), allowed-tools Bash/Read/Grep/Glob, NO read-only anchor. Catalog ×3 + evals/lint-fix/contract.json (no read-only / no FIX-SUGGEST-IGNORE anchors).
- NOT auto-fixed: missing catalog line (summary), broken links, judged dims (013).

## Implementation log 2026-06-03

- scripts/knowledge_edits.py: NEW — moved add_related_link/add_supersede_banner/_related_has_target/body_complement verbatim from test_promote_invariant.py (imports constants from knowledge_spans.py). test_promote_invariant.py now imports them; its 7 tests still pass. knowledge_spans.py docstring updated (constants unchanged). knowledge_lint.py: 0 changes (frozen, verified vs main).
- scripts/knowledge_fix.py: NEW — deterministic fixer. plan_index (canonical serializer: watermark=max NNN, drop stale lines, relocate wrong-Type verbatim, NNN-sorted, skeleton incl. empty ## Patterns — block-join to avoid double-blank). plan_reciprocals (parse forward `## Related` labels, RECIPROCAL table {builds on→see also, supersedes↔superseded by, contradicts/see also symmetric}, refuse if ∉vocab; supersedes also writes banner; validate all before write). apply: recompute-once → validate body_complement per entry → atomic write → final lint verify. --dry-run + --date (deterministic). CLI git-root-anchored.
- tests/test_knowledge_fix.py: 10 tests — each fix family + clean-noop + idempotent + body-preserved + index skeleton/order + invalid-label atomic refusal + dry-run-writes-nothing. All pass.
- plugins/minerva/skills/lint-fix/SKILL.md: mutating, gated (dry-run→confirm→apply), allowed-tools Bash/Read/Grep/Glob (no Edit/Write), NO read-only anchor. evals/lint-fix/contract.json (no read-only / no FIX-SUGGEST-IGNORE anchors). Catalog ×3 (plugin README, using-minerva, root README). test_knowledge_fix.py added to evals.yml.
- Verified: full gated suite 132 passed; drift gate clean; detector frozen; idempotent no-op on clean live corpus.
- Fixed during build: serializer emitted a double blank line for the empty ## Patterns section → switched to block-join (header + blank+rows only if non-empty; sections joined by one blank).

## Panel decisions 2026-06-03 (continued)

- [3/3 accept] completion verification: all 9 criteria met; both panelists ran the suite (132) + MUTATION PROBES (break plan_index→5 fails, plan_reciprocals→3, body-corrupt→pre-write AssertionError, no partial write). Minor: main() default date hardcoded → FIXED (today()).
- [2/3 accept] review triage (Proponent + Skeptic): 1 HIGH + 2 MED + 2 LOW, all FIX. #1 pinned to the _strip_fences-reuse branch (NOT editing the frozen detector). No Replan trigger (within-scope conformance fixes).

## Review finding 2026-06-03

Inline review (spec-fidelity + knowledge-compliance clean). 5 findings, all FIXED:
1. [HIGH] `_forward_related` was NOT fence-aware (detector is) → a fenced `## Related` example in an entry body (e.g. convention doc 015) could make the fixer invent a spurious banner/Related edit → FIXED: import `_strip_fences` from the frozen knowledge_lint; parse the LAST non-fenced `## Related`. Detector stays frozen. Test: test_fenced_related_example_not_treated_as_edge.
2. [MED] plan_index silently DROPPED a catalog line whose entry has an unknown declared_type (data loss) → FIXED: keep the line under its current section + record a refusal; never drop. Test: test_unknown_type_line_refused_not_dropped.
3. [MED] plan_index on a missing/empty index.md wrote a hollow skeleton → FIXED: refuse the rewrite + surface "run minerva:init". Test: test_missing_index_refused_not_fabricated.
4. [LOW] `--date` argv parsing stripped any token == date (path corruption) → FIXED: pop by index (del argv[i:i+2]).
5. [LOW] apply() partial-write atomicity (no IO-error rollback) → FIXED: documented the limitation (body_complement validation IS pre-write; IO-error rollback out of scope, low-risk local FS).
