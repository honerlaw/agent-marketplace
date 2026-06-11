# Every minerva skill must carry a declarative structural contract, enforced by an enumerating test

**Date**: 2026-05-31
**Type**: constraint
**Context**: .minerva/work/017-skill-contract-eval-floor (see git history if the worktree has been cleaned up)

## Context
Before 017, the only structural guard on the minerva skills was hardcoded, per-skill assert functions in `tests/test_minerva.py`. Only 8 of the 13 skills had one, so coverage silently lagged the skill set. 017 replaced those per-skill asserts with a declarative, enumerated contract floor.

## Finding
Each skill under `plugins/minerva/skills/<name>/` must carry a companion `evals/<name>/contract.json` declaring its structural contract — required frontmatter, body anchors, and which catalog surfaces must list `minerva:<skill>`. `tests/test_skill_contracts.py` **enumerates every skill directory and fails if any one of them lacks a `contract.json`**, so a newly added skill cannot ship unguarded.

The format itself (anchor grammar including the `{any_of, ignore_case}` disjunction and the 1-element-`any_of` case-insensitive idiom, the `using-minerva` self-exclusion, and token-boundary matching for `minerva:<skill>`) is documented in **`evals/README.md`** — that is the source of truth, do not restate it here.

## Implications
- **Adding a minerva skill**: create `evals/<name>/contract.json` in the same change, alongside the three catalog updates from [[010-constraint-minerva-skill-catalog-sync]]. The contract's `cross_surface` block enforces that catalog presence per skill — so this floor **delivers part of** the drift-prevention automation 010 deferred: it covers the dirs→catalog direction as a pytest check (not the full CI/pre-commit bidirectional diff, and it won't catch an orphaned catalog row whose skill dir was deleted).
- **Editing a skill**: removing a load-bearing body anchor or renaming frontmatter reds that skill's contract test — update the contract deliberately and record why, rather than weakening it to pass.
- The behavioral "does this skill add value" half is now built as a separate tier: value cases live in a sibling `evals/<skill>/behavioral.json` read by `scripts/run_skill_evals.py` — **not** in `contract.json` (the once-reserved `behavioral` key was retired). That tier is PROVISIONAL; see [[013-decision-behavioral-evals-provisional]].
- Complements [[007-constraint-skills-must-call-tools-not-prose]] and [[004-constraint-plugin-skills-auto-discovered-from-directory]]: the runtime auto-discovers skills, but their structural integrity and catalog presence are now test-enforced.

## Related
- [[004-constraint-plugin-skills-auto-discovered-from-directory]] — builds on
- [[010-constraint-minerva-skill-catalog-sync]] — builds on
- [[016-constraint-promote-narrowed-never-overwrite]] — see also
- [[030-pattern-rejected-alternative-reinvented-at-runtime]] — see also
- [[034-constraint-site-fourth-catalog-surface]] — see also
