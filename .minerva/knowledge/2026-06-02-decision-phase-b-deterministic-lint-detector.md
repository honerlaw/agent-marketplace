# Phase B split: a deterministic knowledge-lint CI gate ships first; the LLM-judged `minerva:lint` skill is deferred

**Date**: 2026-06-02
**Type**: decision
**Context**: .minerva/work/2026-06-02-knowledge-lint-detector (see git history if the worktree has been cleaned up)

## Context

After the wiki navigability layer shipped (unit 020, see [[2026-06-02-decision-knowledge-wiki-navigability-layer]]), Phase B was "health-check the wiki" — Karpathy's lint pass. The original proposal bundled two very different capabilities: deterministic *mechanical* checks (index drift, broken `## Related` links, missing reciprocals) and LLM-*judged* checks (contradictions, stale claims, orphans) plus interactive gated fixes.

## Finding

Phase B was **decomposed along the deterministic-vs-LLM-judged fault line**:

- **B.1 (this unit) shipped** a deterministic, read-only detector — `scripts/knowledge_lint.py` — wired into the `evals.yml` CI gate. It is the first thing that **mechanically CI-enforces the wiki coherence conventions that were previously author-only** (the index and cross-reference rules recorded in [[2026-06-02-constraint-knowledge-cross-reference-convention]] / [[2026-06-02-decision-knowledge-wiki-navigability-layer]]): before this, those conventions were maintained by `minerva:promote` at write time but nothing caught drift introduced outside a promote.
- **B.2 is deferred** — the interactive `minerva:lint` skill (LLM-judged contradiction / staleness / orphan detection, `minerva:review`-style triage, and gated fixes) is its own future work unit; it will build on the detector by Bash-invoking it for the mechanical findings.

**Rationale.** This mirrors the units 017/018 precedent (a deterministic structural-contract floor shipped as one unit; the LLM-judged behavioral layer as a separate, provisional one) and honors [[2026-05-31-decision-behavioral-evals-provisional]]: LLM-judged output is provisional and must not co-gate with a deterministic floor. Bundling them would have lashed a provable, CI-gateable artifact to an unproven judgment layer.

## Implications

- The mechanical-coherence checks are now a **green-CI invariant** — a PR that lets the knowledge wiki drift (stale watermark, dangling `## Related` link, one-way cross-reference, miscatalogued entry) fails the `evals` gate.
- B.2 (the judgment layer + interactive fixes) is the natural next unit; it consumes the detector rather than reimplementing the mechanical checks.
- The detector only *implements* the conventions already recorded in 015/017 (corpus-as-source-of-truth, NNN-keyed reciprocity); it did not introduce new conventions, so those rules are not restated here — see those entries.

## Related
- [[2026-05-31-decision-behavioral-evals-provisional]] — builds on
- [[2026-06-02-decision-knowledge-wiki-navigability-layer]] — builds on
- [[2026-06-02-constraint-knowledge-span-model-single-sourced]] — see also
- [[2026-06-03-decision-minerva-lint-read-only]] — see also
- [[2026-08-09-pattern-read-authored-metadata-from-where-it-is]] — see also
