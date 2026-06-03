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
