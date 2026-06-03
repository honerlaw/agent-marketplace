# `.minerva/reference/` is the present-tense operational-doc tier — distinct from `.minerva/knowledge/`'s past-tense atomic learnings

**Date**: 2026-05-22
**Type**: decision
**Context**: .minerva/work/014-add-triage-skill (see git history if the worktree has been cleaned up)

## Context

Prior to this work unit, `.minerva/` had two read tiers documented in the persistence hierarchy: always-read knowledge (`.minerva/knowledge/`) and searchable per-unit work (`.minerva/work/`). When designing `minerva:triage` — a generic skill that reads project-specific operational docs (topology, observability conventions, CLI recipes, bug-pattern catalogs) — those docs needed somewhere to live. They didn't fit `.minerva/knowledge/`: existing knowledge entries are atomic, past-tense, named `NNN-<type>-<slug>.md` (~30-80 lines each, one concept per file). Operational reference docs are thematic, present-tense, named by topic, and replace-on-change.

The triggering example was the seekless project's bespoke `debug-seekless` skill, which carried six reference docs (`topology.md`, `observability.md`, `doctl-recipes.md`, `database.md`, `bug-patterns.md`, `external-services.md`) totaling ~700 lines. Forcing them into the existing atomic-knowledge convention would either break the convention (large thematic files alongside small atomic ones) or require awkward decomposition into many tiny files.

## Finding

`.minerva/reference/` was added as a third tier of the `.minerva/` layout, separate from `.minerva/knowledge/`. The load-bearing distinction is **time-shape**:

- **`.minerva/knowledge/`** — atomic, past-tense, durable learnings (decisions / bugs / patterns / constraints). Named `NNN-<type>-<slug>.md`. Append-only, low churn. "What we learned." Always-read.
- **`.minerva/reference/`** — thematic, present-tense, operational facts about how the system is configured *right now*. Named by topic (no NNN). Replace-on-change, higher churn. "How the system works now." Read on demand by skills that need them.

Knowledge accumulates over the project's lifetime. Reference is a snapshot that gets rewritten as the system evolves. New durable learnings still flow to `.minerva/knowledge/` via `minerva:promote`; updates to operational facts overwrite the relevant `.minerva/reference/<topic>.md` file directly.

Discovery convention for `.minerva/reference/`: **filename-driven**, not frontmatter-driven. Consuming skills `ls` the directory, pick relevant files by filename + symptom restatement, and additionally always load any file whose name matches a pattern-catalog shape (`bug-patterns.md`, `incidents.md`, `patterns.md`). No NNN convention, no frontmatter tags, no manifest. This is intentional — the reference folder stays human-curated and the directory listing alone is the index.

## Implications

- Projects using minerva can place present-tense operational docs in `.minerva/reference/`. Skills like `minerva:debug` discover them at runtime without per-project configuration.
- Files in `.minerva/reference/` should be named descriptively (`topology.md`, `observability.md`, `database.md`, etc.) so consuming skills can pick relevance from filename + symptom alone. Avoid generic names (`docs.md`, `notes.md`) that won't help discovery.
- Pattern-catalog files (recurring bug shapes optimized for rapid skim) should be named `bug-patterns.md`, `incidents.md`, or `patterns.md` so the always-load discovery rule picks them up.
- New durable learnings still go to `.minerva/knowledge/`. The `.minerva/reference/` tier is for operational facts, not promoted knowledge — they coexist, and a single triage may read from both.
- `minerva:init` does not yet scaffold `.minerva/reference/`. New projects create it manually until init is updated (tracked in this work unit's `followups.md`).
- The `using-minerva` skill and `plugins/minerva/README.md` document the persistence hierarchy with the two-tier model; both need updating to include the reference tier (tracked in this work unit's `followups.md`).
- Skills that read `.minerva/reference/` must not bake in specific filenames — use `ls` + filename-driven selection, plus always-load for pattern-catalog-shaped files. This keeps the skill project-agnostic.

## Related
- [[017-decision-knowledge-wiki-navigability-layer]] — see also
