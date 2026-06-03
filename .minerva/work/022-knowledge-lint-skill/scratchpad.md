# Scratchpad: minerva-lint-skill

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Panel decisions 2026-06-03

- [1/3 accept → DECOMPOSE] scope r1: original bundled read-only judged-detection + corpus-mutating gated fixes. Skeptic+Arbiter: split per the 016/019 mutation risk seam + 013 (judged provisional → don't build an auto-fixer for unvalidated judgment). 021's own decomposition (018) named 3 capability classes; only mechanical was carved off in B.1. → B.2 = read-only; B.3 = gated fix-applier (deferred).
- [3/3 accept] scope r2: B.2 read-only is one cohesive unit (3 judged dims = one advisory pass; read-only = clean risk boundary; catalog+contract = mandatory skill envelope).
- [2/3 accept → revise] approach r1: X (read-only skill, detector + judged + review presentation) unanimously right vs Y (push orphans into detector — edits frozen tool, contradicts 021) / Z (rigid checklist). Skeptic: 4 refinements.
- [2/3 accept] approach r2 (X′): consume detector's importable lint_knowledge() API incl. warnings (not CLI exit code); orphan adjacency from parse_entry (no drift); reuse review PRESENTATION only (not FIX/SUGGEST/IGNORE); read-only via allowed-tools frontmatter + body directive (contract can only WITNESS, not forbid); repairs → hand/B.3 not promote; repo-root sys.path. (escalation trigger ≤1/3 not met; substance unanimous.)
- [3/3 accept] whole-proposal: all claims verified vs repo (importable API w/ warnings, parse_entry adjacency, {skill,frontmatter,anchors,cross_surface} harness positive-anchors-only, 3 surfaces). Folds: read-only = declaration+directive not contract-guaranteed; lint contract omits FIX/SUGGEST/IGNORE anchors; include frontmatter description; contract skill="lint".

## Carried constraints (from panels)

- Detector is FROZEN — consume via API (`lint_knowledge`, `parse_entry`), never edit scripts/knowledge_lint.py or knowledge_spans.py.
- Consume the full findings list (incl. warning-severity), NOT the CLI exit code (CLI exits 0 on warnings-only → would drop stale-slug).
- Orphan adjacency from parse_entry; orphan-as-defect verdict advisory only.
- Reuse review PRESENTATION format, NOT its FIX/SUGGEST/IGNORE triage machinery; don't copy review's triage anchors into lint's contract.
- Read-only: allowed-tools omits Edit/Write/MultiEdit + body directive; contract witnesses (allowed-tools + read-only anchor) but cannot guarantee absence of mutation.
- Repairs routed to hand/B.3, NOT promote (work-unit-bound).
- Judged dims advisory, never CI-gated (013), "spot-checked not exhaustive".

## Implementation log 2026-06-03

- plugins/minerva/skills/lint/SKILL.md: read-only skill. frontmatter allowed-tools = [Bash, Read, Grep, Glob] (omits Edit/Write/MultiEdit). Step 1 mechanical pass = python3 -c importing lint_knowledge (full findings incl. warnings). Step 2 judged pass = orphans (adjacency via parse_entry, snippet), contradictions, staleness — advisory, spot-checked. Step 3 = review-style presentation (mechanical + advisory sections), present-and-stop; repairs → hand/B.3, not promote. Read-only contract callout + body directive.
- evals/lint/contract.json: skill=lint; frontmatter.contains witnesses "allowed-tools"; anchors = knowledge_lint, lint_knowledge, .minerva/knowledge/, ## Related, read-only, any_of[orphan/contradiction/stale], any_of[advisory]. NO FIX/SUGGEST/IGNORE anchors. cross_surface all 3.
- Catalog (010): plugin README row (after debug), using-minerva matrix row (after debug), root README cell token (after debug). All 3 — verified by test_skill_contracts cross_surface (lint enumerated).
- Verified: both SKILL python snippets run on the live corpus (mechanical=[] clean; orphans=001/002/003/005/006/007/008/009/014 — standalone entries, advisory candidates). Full gated suite 117 passed (+5 lint contract cases). Detector FROZEN (scripts unchanged). drift gate clean; run_skill_evals --dry-run ok.
- No behavioral.json for lint (optional; the judged dims are advisory/provisional per 013).
